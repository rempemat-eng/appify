"""The rocket and the lander (Matt, 20 Oct: "of course to reach the moon and such places you
need an animation of a rocket ship of sorts"; the lander to the moon stays).

Run: python3 scripts/art/rocket.py   (ROCKET_PREVIEW=dir writes a sheet of every piece)

The space elevator's journey is replaced by a launch: a two-stage rocket on its pad at the
Skyport, its gantry's arms swinging back, ignition, smoke rolling over the pad, lift-off,
the cloud layers, the stars, stage separation and docking under Halcyon. The way back lands
the upper stage on its legs. The shuttle to Lumen is a lander that undocks, burns, kicks up
regolith that falls straight back (no air, no billowing) and settles on its legs.

Everything is drawn here, in the house palette (docs/vision/house-style.md, PR #121): six
tones a family from one body colour, shade towards dusk violet and light towards lamp
yellow, each family's own edge tone for its outline (broken to tone 1 where a lit top or
left edge is closed), light from the upper left, glows as light sources with no outline.
Every mark is a thing (Claude A, 20 Oct, after Matt's "make sure the detail makes sense and
looks right"): painted panels in rings with their seams, rivets only on the seams, a few
stencils (a stage number, a hazard band, an arrow at a hatch), hinged hatches, valves,
connector plates, handrails, lamps, each part seated with its shadow; frost, soot and
scorching only where the real thing has them; clean skin where the real thing is clean.
The vehicles and the station pass detail_bar's 'machinery' bar (counts and cleanliness) on
their bodies. Until #121's house_palette.py is on main,
the ramps used here are a snapshot of what it computes (HOUSE below); once it lands, read
them from it. Sizes follow the size guide (#124): an adult is 25 px and a storey 32, so the
rocket stands about five storeys (164 px) beside a gantry of six.

The pictures go to assets/journeys/rocket/ (2x; the sky's gradient column at 1x) with
lib/rocket-sizes.ts (sizes and anchors) and lib/rocket-assets.ts (the pictures, imported one by
one so they bundle on native), which components/rocket-journey.tsx reads. The beats themselves are
in lib/rocket-flight.ts. Deterministic: no randomness, only hashed noise, so the bytes
reproduce (npm run check:art-repro).
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, smooth_noise  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'journeys', 'rocket')
SCALE = 2          # most pictures (crisp under data-pixel; see docs/vision/region-canvas.md)
SKY_SCALE = 1      # the sky's gradient column: a soft fade, nothing to keep crisp

# --- the house palette (a snapshot of scripts/art/house_palette.py on PR #121) -----------
HOUSE = {
    'hull': ['#64607A', '#848399', '#A4A5B7', '#C4C8D2', '#E0DEE0', '#FAF2E9'],
    'hull_warm': ['#6C6685', '#8C89A5', '#ACACC3', '#CCCFDF', '#E4E1E8', '#FBF1ED'],
    'hull_cool': ['#5C5773', '#7C7991', '#9C9CAF', '#BBBECA', '#DCD9DC', '#FAF1EA'],
    'panel': ['#272342', '#424260', '#5E627C', '#7A8296', '#9A9BA7', '#B7B2B2'],
    'panel_warm': ['#2F284B', '#4B476A', '#676787', '#8388A2', '#A3A1B3', '#C1B8BC'],
    'panel_cool': ['#221B3A', '#3D3957', '#585873', '#74788D', '#93919E', '#B0A7A8'],
    'iron': ['#1A132D', '#2E2943', '#424056', '#565868', '#737078', '#8E8583'],
    'iron_warm': ['#1C112F', '#322A47', '#48445D', '#5F5E72', '#7D7682', '#988C8C'],
    'iron_cool': ['#1C122D', '#2D2640', '#3F3A51', '#504F60', '#6D6670', '#877C7A'],
    'berry': ['#34001F', '#630735', '#8E2348', '#B2465A', '#CE6364', '#DD8472'],      # rescue red
    'berry_warm': ['#3E021E', '#70082F', '#9D243E', '#C1494E', '#DC6858', '#E98B6A'],
    'berry_cool': ['#300123', '#5D013C', '#82204F', '#A34060', '#BF5C6A', '#CF7C75'],
    'sky': ['#1C2862', '#2F4A85', '#456CA5', '#5E8EC0', '#7BAACF', '#A0C2D2'],          # signal blue
    'sky_warm': ['#14306C', '#245390', '#3976B0', '#5399CB', '#74B5D9', '#9ECCDB'],
    'sky_cool': ['#1D1D58', '#323F7B', '#48609A', '#6182B6', '#7C9EC5', '#9DB6C9'],
    'brass': ['#5D2D0A', '#814D15', '#A36E26', '#C2903C', '#DAAD54', '#EFC67A'],        # hazard ochre
    'brass_warm': ['#663400', '#8A5504', '#AB7619', '#CA9933', '#E6B450', '#FACE7A'],
    'brass_cool': ['#56220E', '#7B4119', '#9D622A', '#BD833E', '#D6A052', '#E6BB74'],
    'slate': ['#1F1A3C', '#38395A', '#535876', '#6E7890', '#8E91A1', '#ACA7AA'],
    'concrete': ['#1B122D', '#362E47', '#514B60', '#6C6878', '#8A8088', '#A49793'],
    'concrete_warm': ['#1E1432', '#3B304E', '#594E68', '#776D81', '#958691', '#AF9D9B'],
    'concrete_cool': ['#1C122D', '#332B45', '#4B455B', '#645F70', '#817780', '#9C8D8B'],
    'asphalt': ['#1C112F', '#281F3C', '#332D47', '#3E3C50', '#5A525F', '#736769'],
    'asphalt_warm': ['#1C1032', '#2B2041', '#3A304E', '#484159', '#645868', '#7D6D71'],
    'asphalt_cool': ['#1C1130', '#261C39', '#302841', '#393347', '#544956', '#6D5E5F'],
    'void': ['#1B1033', '#20193B', '#252340', '#2A2C44', '#454253', '#5F565B'],
    'regolith': ['#100C08', '#3C3630', '#686159', '#8E877E', '#ABA190', '#C5B8A1'],
    'regolith_warm': ['#17110A', '#443D32', '#70695C', '#978F81', '#B5A993', '#CFC0A5'],
    'regolith_cool': ['#0C0604', '#362E28', '#625850', '#877D74', '#A39686', '#BCAE96'],
    'snow': ['#757390', '#9597B0', '#B6BBCE', '#D6DEEA', '#E6EAEC', '#F5F4EB'],
    'snow_warm': ['#797B9B', '#999FBB', '#B9C3DA', '#D9E7F6', '#E5EFF3', '#F2F5ED'],
    'snow_cool': ['#6D6A88', '#8D8DA8', '#ADB1C6', '#CDD4E2', '#E3E4E9', '#F9F2EC'],
    'stone': ['#332937', '#514850', '#70676A', '#8E8782', '#ABA194', '#C5B8A4'],
    'stone_warm': ['#3B2F3B', '#5A4E54', '#796E6D', '#988E85', '#B5A897', '#CFC0A8'],
    'stone_cool': ['#2D212F', '#4B3F48', '#695E60', '#877D78', '#A49689', '#BDAE99'],
    'dusk': ['#210142', '#3D2167', '#584187', '#7262A4', '#927BB2', '#AF93B4'],
    'dusk_warm': ['#28004F', '#442573', '#634492', '#8364AC', '#A37DB9', '#BE97BB'],
    'dusk_cool': ['#210044', '#3A1F62', '#543C7E', '#6D5997', '#8D72A4', '#A88AA8'],
    'slate_warm': ['#271F45', '#413E64', '#5C5E81', '#787E9C', '#9897AC', '#B6AEB5'],
    'slate_cool': ['#1A1233', '#333051', '#4E4F6D', '#696E87', '#888697', '#A59DA1'],
    'water': ['#0E2058', '#1E427A', '#336499', '#4C86B4', '#6BA2C2', '#92B8C5'],
    'water_warm': ['#032A5E', '#084C84', '#226FA2', '#3E91BD', '#63ADCA', '#90C3CC'],
    'water_cool': ['#12164E', '#233771', '#385990', '#507AAB', '#6C95BA', '#8FADBD'],
    'leaf': ['#002B1A', '#194B28', '#3A6B3A', '#5C8A4C', '#83A15A', '#A8B471'],
    'leaf_warm': ['#093213', '#2B5120', '#4B712F', '#6D9041', '#93A751', '#B6BA6D'],
    'leaf_cool': ['#01211A', '#02432C', '#25633D', '#488250', '#70995D', '#98AC70'],
    # glows: light sources, deep to a near-white core, no outline
    'lamp': ['#67450A', '#9B6912', '#CB8D26', '#F0B050', '#F5D49C', '#FFF6E6'],
    'lava': ['#532000', '#8B3B01', '#C3570A', '#F27222', '#FCB68A', '#FFF5ED'],
    'neon_cyan': ['#014751', '#0F7180', '#159BB0', '#2CC0D8', '#96DEE7', '#E3FDFE'],
    'neon_pink': ['#50052E', '#8D0A56', '#C81C7D', '#F04A9E', '#FDA6C1', '#FFF4F6'],
    'glowflora': ['#015243', '#077F69', '#21AA8F', '#36D0B0', '#9FE6CC', '#E6FEF2'],
}
EDGE = {'hull': '#393341', 'panel': '#231E2E', 'iron': '#1E1826', 'berry': '#291221', 'sky': '#20203A',
        'brass': '#37221E', 'slate': '#201A2C', 'concrete': '#1F1726', 'asphalt': '#1F1727',
        'void': '#1E1729', 'regolith': '#1A1518', 'snow': '#3F3949', 'stone': '#28202A',
        'dusk': '#20142F', 'water': '#1B1E36', 'leaf': '#19211F'}
GLOWS = ('lamp', 'lava', 'neon_cyan', 'neon_pink', 'glowflora')


def fam_of(name: str) -> str:
    for tag in ('_warm', '_cool'):
        if name.endswith(tag):
            return name[:-len(tag)]
    return name


def T(name: str, tone: int) -> str:
    return HOUSE[name][max(0, min(5, tone))]


def sib(fam: str, n: float, spread: float = 0.33) -> str:
    """One of a family's three siblings, picked by a noise value."""
    return f'{fam}_warm' if n < spread else f'{fam}_cool' if n > 1 - spread else fam


# --- a sprite drawn as (family, tone) per pixel, closed by the house outline ------------
class Spr:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.px: dict = {}

    def set(self, x: int, y: int, name: str, tone: int):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[(x, y)] = (name, max(0, min(5, tone)))

    def get(self, x, y):
        return self.px.get((x, y))

    def has(self, x, y):
        return (x, y) in self.px

    def clear(self, x, y):
        self.px.pop((x, y), None)

    def rect(self, x0, y0, w, h, name, tone):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.set(x, y, name, tone)

    def hline(self, x0, y, w, name, tone):
        for x in range(x0, x0 + w):
            self.set(x, y, name, tone)

    def vline(self, x, y0, h, name, tone):
        for y in range(y0, y0 + h):
            self.set(x, y, name, tone)

    def step(self, x, y, d):
        """Move a pixel along its own ramp (the only way shade and light change)."""
        p = self.px.get((x, y))
        if p and p[0] not in GLOWS:
            self.px[(x, y)] = (p[0], max(0, min(5, p[1] + d)))

    def tile(self) -> Canvas:
        """The pixels exactly, w x h, no outline and no border: a looping background tile."""
        cv = Canvas(self.w, self.h)
        for (x, y), (name, tone) in self.px.items():
            cv.set(x, y, T(name, tone))
        return cv

    def render(self, outline: bool = True) -> Canvas:
        """The pixels, and (outline) a one-pixel outline outside the silhouette in the edge
        tone of the family it closes, broken to tone 1 where it closes a lit (4, 5) top or
        left edge. Glows get no outline."""
        cv = Canvas(self.w + 2, self.h + 2)
        for (x, y), (name, tone) in self.px.items():
            cv.set(x + 1, y + 1, T(name, tone))
        if outline:
            for y in range(-1, self.h + 1):
                for x in range(-1, self.w + 1):
                    if (x, y) in self.px:
                        continue
                    best = None
                    for (dx, dy, side) in ((0, 1, 'top'), (1, 0, 'left'), (0, -1, 'bottom'), (-1, 0, 'right')):
                        p = self.px.get((x + dx, y + dy))
                        if p and p[0] not in GLOWS:
                            best = best or (p, side)
                    if not best:
                        continue
                    (name, tone), side = best
                    f = fam_of(name)
                    lit = side in ('top', 'left') and tone >= 4
                    cv.set(x + 1, y + 1, T(f, 1) if lit else EDGE.get(f, '#211A22'))
        return cv


# --- materials ------------------------------------------------------------------------
def cyl_tone(x, cx, r):
    k = (x - (cx - r)) / max(1, 2 * r)
    return 4 if k < 0.16 else 3 if k < 0.55 else 2 if k < 0.86 else 1


# --- the rocket -------------------------------------------------------------------------
RW = 32          # the rocket's diameter
STAGE1_H = 96    # the booster, from its engine bells' foot to its top
STAGE2_H = 68    # the upper stage with its crew capsule and nose


def skin(s: Spr, x0, y0, w, y1, cx, r, fam, seed, rings, seams=(), paint=None, rivets=True):
    """A painted cylinder's skin between rows y0 and y1, as a real one is built: rings of
    panels (each panel one sibling of the paint, so a ring reads as panels, not noise), a ring
    seam as a dark line with a lit lip under it and a row of rivets on that lip, a vertical
    seam or two a tone down, and the cylinder's light: a lit left third with a one-pixel
    sheen line, the body, the shade, the dark limb. `paint` maps a row to another family
    (a livery band) or None."""
    edges = sorted(set([y0] + list(rings) + [y1]))
    for y in range(y0, y1):
        ring = max(i for i, e in enumerate(edges) if e <= y)
        top = edges[ring]
        fam_y = (paint(y) if paint else None) or fam
        for x in range(x0, x0 + w):
            k = (x - (cx - r) + 0.5) / (2 * r)
            t = 4 if k < 0.3 else 3 if k < 0.6 else 2 if k < 0.85 else 1
            if 0.11 < k < 0.16:
                t = 5                                                        # the sheen
            if k > 0.93:
                t = 2                                                        # light thrown back on the limb
            sx = cx + (seams[ring % len(seams)] if seams else 99)
            side = 0 if x < sx else 1 if x < sx + 11 else 2                  # (three panels round the ring)
            name = sib(fam_y, noise2(ring, side, seed), 0.34)
            if y == top and y != y0:
                t = max(0, t - 2)                                            # the ring seam
            elif y == top + 1 and y != y0 + 1:
                t = min(5, t + 1)                                            # its lit lip
            elif seams and x in (sx, sx + 11):
                t = max(0, t - 1)                                            # the vertical seams
            s.set(x, y, name, t)
            if rivets and y == top + 1 and top != y0 and (x - x0) % 3 == 1 and 0.06 < k < 0.94:
                s.set(x, y, 'iron', 4 if k < 0.6 else 3)                     # rivets, on the seam only


def stencil(s: Spr, x, y, glyph: str, fam='iron', tone=1):
    """A stencilled glyph, 3 x 5 px: '1', '2', or an arrow '>' / '<'."""
    rows = {'1': ('.#.', '##.', '.#.', '.#.', '###'), '2': ('##.', '..#', '.#.', '#..', '###'),
            '>': ('#..', '##.', '###', '##.', '#..'), '<': ('..#', '.##', '###', '.##', '..#')}[glyph]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '#':
                s.set(x + i, y + j, fam, tone)


def hinged_hatch(s: Spr, x, y, w, h, fam='hull', lit=True, hinge_left=True):
    """An access hatch: a recessed frame (its top and left edges dark, its bottom and right
    lit), the door a tone off the skin, two hinge knuckles on one side, a handle on the other,
    and a lit lower lip."""
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            edge_dark = yy == y or xx == x
            edge_lit = yy == y + h - 1 or xx == x + w - 1
            t = 1 if edge_dark else 4 if edge_lit else (3 if lit else 2)
            s.set(xx, yy, sib(fam, 0.5), t)
    hx = x if hinge_left else x + w - 1
    for hy in (y + 1, y + h - 3):
        s.set(hx, hy, 'iron', 4); s.set(hx, hy + 1, 'iron', 2)                  # hinges
    gx = x + w - 3 if hinge_left else x + 2
    s.set(gx, y + h // 2 - 1, 'iron', 4); s.set(gx, y + h // 2, 'iron', 2)      # the handle


# --- parts: what every mark on the vehicles and the station is -------------------------
def hskin(s: Spr, x0, x1, cy, r, fam, seed, rings, seams=(), paint=None, rivets=True, taper=(0, 0)):
    """A cylinder lying on its side, seen side on (the station's modules), built like skin():
    lit along its top third with a one-pixel sheen line, the body, the shade, the limb lit back
    from below; ring seams across it (a dark line, a lit lip on its right, rivets on the lip
    only), one seam along each ring, each panel one sibling of the paint. `paint(x, y)` gives
    a livery band its family; `taper` (left, right) narrows the ends into end cones."""
    edges = sorted(set([x0] + list(rings) + [x1]))
    for x in range(x0, x1):
        ring = max(i for i, e in enumerate(edges) if e <= x)
        left = edges[ring]
        rr = r - max(0, taper[0] - (x - x0)) - max(0, taper[1] - (x1 - 1 - x))
        sy = cy + (seams[ring % len(seams)] if seams else 99)
        for y in range(cy - rr, cy + rr):
            k = (y - (cy - rr) + 0.5) / (2 * rr)
            t = 4 if k < 0.3 else 3 if k < 0.6 else 2 if k < 0.85 else 1
            if 0.11 < k < 0.16:
                t = 5                                                        # the sheen
            if k > 0.93:
                t = 2                                                        # light thrown back on the limb
            fam_y = (paint(x, y) if paint else None) or fam
            name = sib(fam_y, noise2(ring, 0 if y < sy else 1, seed), 0.34)
            if x == left and x != x0:
                t = max(0, t - 2)                                            # the ring seam
            elif x == left + 1 and left != x0:
                t = min(5, t + 1)                                            # its lit lip
            elif y == sy:
                t = max(0, t - 1)                                            # the seam along it
            s.set(x, y, name, t)
            if rivets and x == left + 1 and left != x0 and (y - cy) % 3 == 1 and 0.06 < k < 0.94:
                s.set(x, y, 'iron', 4 if k < 0.6 else 3)                     # rivets, on the seam only


def collar(s: Spr, x0, w, cy, r, fam='panel'):
    """A berthing collar between two modules: a ring a little proud of them, lit along its top,
    its left face catching the light, its right face in shade, bolts round it."""
    for x in range(x0, x0 + w):
        for y in range(cy - r, cy + r):
            k = (y - (cy - r) + 0.5) / (2 * r)
            t = 4 if k < 0.3 else 3 if k < 0.6 else 2 if k < 0.85 else 1
            if x == x0:
                t = min(5, t + 1)
            elif x == x0 + w - 1:
                t = max(0, t - 2)
            s.set(x, y, fam, t)
        if 0 < x - x0 < w - 1:
            for y in range(cy - r + 3, cy + r - 2, 5):
                s.set(x, y, 'iron', 4 if y < cy else 3)                       # its bolts


def porthole(s: Spr, px_, py, rad=3):
    """A round window lit from inside: a warm pane brighter where the cabin lamp pools low, a
    glint at its upper left, its steel frame lit on the upper left and dark on the lower right."""
    for y in range(py - rad - 2, py + rad + 3):
        for x in range(px_ - rad - 2, px_ + rad + 3):
            d = (x - px_) ** 2 + (y - py) ** 2
            if d <= rad * rad:
                s.set(x, y, 'lamp', 2 if y < py - 1 else 3 if y <= py + 1 else 4)
            elif d <= (rad + 1.5) ** 2:
                s.set(x, y, 'iron', 4 if (x - px_) + (y - py) < 0 else 1)
    s.set(px_ - 2, py - 2, 'lamp', 5); s.set(px_ - 1, py - 2, 'lamp', 5)


def grapple(s: Spr, x, y):
    """A grapple fixture for the station's arm: a square base plate lit on its upper left and
    dark on its lower right, the pin standing proud in the middle, a white target bar."""
    s.rect(x, y, 7, 7, 'panel', 3); s.hline(x, y, 7, 'panel', 4); s.vline(x, y, 7, 'panel', 4)
    s.hline(x, y + 6, 7, 'panel', 1); s.vline(x + 6, y, 7, 'panel', 1)
    s.rect(x + 2, y + 2, 3, 3, 'iron', 2); s.hline(x + 2, y + 2, 3, 'iron', 4); s.hline(x + 2, y + 4, 3, 'iron', 1)
    s.vline(x + 5, y + 1, 3, 'hull', 5)


def connectors(s: Spr, x, y, caps):
    """A connector plate: lit along its top, dark along its foot, a row of 2 x 2 connectors,
    each capped in its own colour (lit on top, in shade under)."""
    w = 3 * len(caps) + 1
    s.rect(x, y, w, 5, 'panel', 3); s.hline(x, y, w, 'panel', 4); s.hline(x, y + 4, w, 'panel', 1)
    for i, fam in enumerate(caps):
        s.hline(x + 1 + 3 * i, y + 1, 2, fam, 4); s.hline(x + 1 + 3 * i, y + 2, 2, fam, 2)


def pipe(s: Spr, x0, x1, y, fam, clamp=9):
    """A fluid line along a module: lit on top, in shade under, held by clamps."""
    s.hline(x0, y, x1 - x0, fam, 4); s.hline(x0, y + 1, x1 - x0, fam, 2)
    for x in range(x0 + 3, x1 - 1, clamp):
        s.vline(x, y - 1, 3, 'iron', 3); s.set(x + 1, y + 1, 'iron', 1)


def placard(s: Spr, x, y, w=7):
    """A white label plate with two stencilled lines of text."""
    s.rect(x, y, w, 5, 'hull', 5); s.hline(x, y + 4, w, 'hull', 2)
    s.hline(x + 1, y + 1, w - 3, 'iron', 1); s.hline(x + 1, y + 3, w - 4, 'iron', 2)


def floodlight(s: Spr, x, y, face=1):
    """An external floodlight: a steel housing lit on top, its lamp face shining (a glow)."""
    s.rect(x, y, 5, 3, 'iron', 2); s.hline(x, y, 5, 'iron', 4); s.hline(x, y + 2, 5, 'iron', 1)
    s.hline(x + 1, y + face, 3, 'lamp', 5)


def seat(s: Spr, x, y, w, h):
    """Seat a part on the skin: its shadow, one tone down, on the skin just right of it and
    under it (the light comes from the upper left)."""
    for (xx, yy) in [(x + w, y + j) for j in range(1, h + 1)] + [(x + i, y + h) for i in range(1, w + 1)]:
        p = s.get(xx, yy)
        if p and fam_of(p[0]) in ('hull', 'snow', 'berry'):
            s.step(xx, yy, -1)


def vrail(s: Spr, x, y0, y1):
    """A handrail standing upright on the skin: the bar lit on its left, its stand-offs."""
    s.vline(x, y0, y1 - y0, 'brass', 4); s.vline(x + 1, y0, y1 - y0, 'brass', 2)
    s.set(x + 2, y0, 'iron', 2); s.set(x + 2, y1 - 1, 'iron', 2)


def valve_box(s: Spr, x, y):
    """A coolant valve on a fluid line: a brass box lit on top, its hand wheel."""
    s.rect(x, y, 5, 4, 'brass', 3); s.hline(x, y, 5, 'brass', 5); s.hline(x, y + 3, 5, 'brass', 1)
    s.hline(x + 1, y - 1, 3, 'iron', 3)


def booster() -> Spr:
    """The first stage, four storeys: built as one is. Top down: the interstage's hazard band;
    the forward panels with the nap-moon roundel; a rescue-red livery band; the stage number
    stencilled on a white panel; the cryogenic tank sweating a band of white rime with a crisp
    lower edge and its vent valve; the ribbed intertank; the fuel tank with a signal-blue
    stripe and an access hatch (hinged, an arrow at it); the darker thrust section with the
    cable raceway; the engine skirt, sooted at its foot; two nozzle bells. Four fins of solid
    signal-blue metal (the near two, their faces lit or in shade, a dark trailing edge sooted)."""
    w, h = RW + 20, STAGE1_H
    s = Spr(w, h)
    cx, r = w // 2, RW // 2
    x0 = cx - r
    # the interstage: hazard chevrons, clean diagonals 3 px wide, lit like the cylinder
    for y in range(0, 6):
        for x in range(x0, x0 + RW):
            t = cyl_tone(x, cx, r) + (1 if y == 0 else 0)
            s.set(x, y, 'brass' if ((x + y) // 3) % 2 else 'iron', min(5, t))
    for x in range(x0, x0 + RW):
        s.set(x, 6, 'iron', 1)
    red = lambda y: 'berry' if 16 <= y < 22 else 'sky' if y in (34, 35, 61, 62) else None   # noqa: E731
    skin(s, x0, 7, RW, 36, cx, r, 'hull', 11, rings=(14, 22, 29), seams=(5, -6, 7), paint=red)
    # the nap-moon roundel on the forward panels: a dusk disc, a lamp-yellow crescent
    mx, my = cx - 6, 10
    for y in range(my - 3, my + 4):
        for x in range(mx - 3, mx + 4):
            d = (x - mx) ** 2 + (y - my) ** 2
            if d <= 11:
                s.set(x, y, 'dusk', 3 if x + y < mx + my else 2)
                if d <= 6 and (x - mx - 1.5) ** 2 + (y - my + 1) ** 2 > 3.2:
                    s.set(x, y, 'lamp', 4 if x < mx else 3)                       # the crescent
    stencil(s, cx + 3, 23, '1')                                                # the stage number
    hinged_hatch(s, x0 + 7, 28, 7, 6, hinge_left=False)                        # the LOX tank's manhole cover
    for (tx, ty, n) in ((cx - 8, 24, 5), (cx - 8, 26, 3)):                     # a stencilled line of text
        for i in range(n):
            if i != 3:
                s.set(tx + i, ty, 'iron', 1)
    for x in range(cx - 3, cx + 9, 4):                                        # white dashes on the red band
        s.hline(x, 19, 2, 'hull', 5)
    # a camera pod on the forward panels, looking down the stage: its housing and glass lens
    s.rect(cx + 7, 9, 5, 5, 'panel', 3)
    s.hline(cx + 7, 9, 5, 'panel', 4); s.hline(cx + 7, 13, 5, 'panel', 1)
    s.set(cx + 8, 11, 'slate', 1); s.set(cx + 9, 11, 'slate', 2); s.set(cx + 8, 12, 'slate', 2); s.set(cx + 9, 12, 'slate', 3)
    s.set(cx + 8, 11, 'lamp', 4)                                               # a glint on the lens
    # the cryogenic tank: white rime in horizontal streaks, lit like the tank, crisp scalloped edge
    for y in range(36, 51):
        for x in range(x0, x0 + RW):
            t = cyl_tone(x, cx, r)
            streak = (y - 36) // 3
            name = sib('snow', noise2(streak, 0, 13), 0.34)
            if (y - 36) % 3 == 0:
                t = min(5, t + 1)                                              # each streak's lit top
            s.set(x, y, name, t)
    for x in range(x0, x0 + RW):
        drip = 1 if (x - x0) % 5 in (1, 2) else 0                              # the scalloped lower edge
        for y in range(51, 51 + drip):
            s.set(x, y, 'snow', max(1, cyl_tone(x, cx, r) - 1))
        s.set(x, 51 + drip, 'hull', max(0, cyl_tone(x, cx, r) - 2))             # its shadow on the skin
    s.rect(x0 + 4, 40, 5, 4, 'iron', 2)                                        # the fill coupling, frosted over
    s.hline(x0 + 4, 40, 5, 'snow', 5); s.set(x0 + 5, 42, 'brass', 3); s.set(x0 + 7, 42, 'brass', 2)
    s.rect(x0 - 3, 44, 3, 3, 'iron', 3)                                        # the vent valve, frosted
    s.hline(x0 - 3, 44, 3, 'snow', 4); s.set(x0 - 3, 47, 'iron', 1)
    # the umbilical plate where the gantry's lower arm meets the stage: two brass connectors
    s.rect(x0 + RW - 8, 30, 7, 6, 'panel', 3)
    s.hline(x0 + RW - 8, 30, 7, 'panel', 4); s.hline(x0 + RW - 8, 35, 7, 'panel', 1)
    for ux in (x0 + RW - 7, x0 + RW - 4):
        s.set(ux, 32, 'brass', 4); s.set(ux + 1, 32, 'brass', 3); s.set(ux, 33, 'brass', 2); s.set(ux + 1, 33, 'brass', 1)
    # the intertank: ribbed (stringers), darker metal
    for y in range(53, 59):
        for x in range(x0, x0 + RW):
            t = cyl_tone(x, cx, r) - (1 if (x - x0) % 2 else 0)
            if y in (53, 58):
                t = cyl_tone(x, cx, r) - 2 if y == 53 else cyl_tone(x, cx, r) + 1
            s.set(x, y, 'panel', max(0, min(5, t)))
    s.rect(x0 + 8, 55, 2, 2, 'lava', 4); s.set(x0 + 8, 55, 'lava', 5)          # the range beacon, lit red
    for lx in (x0 + 17, x0 + 20):                                              # the intertank's vent louvres
        s.vline(lx, 54, 3, 'iron', 0); s.vline(lx + 1, 54, 3, 'panel', 4)
    # the LOX fill line, from the umbilical plate down over the rime into the intertank, frosted
    for y in range(36, 53):
        fx_ = x0 + RW - 7
        s.set(fx_, y, 'brass', 4); s.set(fx_ + 1, y, 'brass', 2)
        if y % 5 == 1:
            s.hline(fx_ - 1, y, 4, 'iron', 3); s.hline(fx_ - 1, y - 1, 4, 'snow', 5)   # a clamp, rime on it
    # the fuel tank: white panels, a signal-blue stripe, an access hatch with its arrow
    skin(s, x0, 59, RW, 75, cx, r, 'hull', 14, rings=(67,), seams=(4, -7), paint=red)
    hinged_hatch(s, cx + 2, 65, 7, 7)
    stencil(s, cx - 3, 66, '>')
    for (nx, ny) in ((x0 + 2, 73), (x0 + RW - 9, 73)):                        # NO STEP marks above the fins
        s.hline(nx, ny, 4, 'berry', 2)
    # the ground umbilical plate: three connectors, one capped in rescue red
    s.rect(x0 + 7, 62, 6, 5, 'panel', 3); s.hline(x0 + 7, 62, 6, 'panel', 4); s.hline(x0 + 7, 66, 6, 'panel', 1)
    s.set(x0 + 8, 64, 'brass', 4); s.set(x0 + 10, 64, 'brass', 3); s.set(x0 + 12, 64, 'berry', 4)
    # the nap flag decal: a dusk field with a lamp star
    s.rect(cx + 9, 69, 5, 4, 'dusk', 3); s.hline(cx + 9, 69, 5, 'dusk', 4)
    s.set(cx + 10, 70, 'lamp', 5); s.set(cx + 11, 71, 'lamp', 4)
    # the thrust section: darker panels, the raceway, rivets on its seam, a warning triangle
    skin(s, x0, 75, RW, 84, cx, r, 'panel', 15, rings=(79,), seams=(3,))
    for k in range(3):
        s.hline(cx - 1 - k, 76 + k, 1 + 2 * k, 'brass', 4 if k < 2 else 3)
    s.set(cx - 1, 77, 'iron', 0)
    # the drain valve plate on the fuel tank's foot
    s.rect(cx - 10, 71, 4, 3, 'panel', 3); s.hline(cx - 10, 71, 4, 'panel', 4); s.set(cx - 9, 72, 'brass', 4)
    # the external feed line on the right, on brackets, from the rime down to the skirt
    for y in range(52, 84):
        px_ = x0 + RW - 4
        s.set(px_, y, 'hull', 4); s.set(px_ + 1, y, 'hull', 2); s.set(px_ + 2, y, 'hull_cool', 1)
        if y % 7 == 3:
            s.hline(px_ - 1, y, 4, 'iron', 2)                                # a bracket
    for y in range(8, 84):                                                    # the cable raceway (not over the rime)
        if 36 <= y <= 52:
            continue
        s.set(x0 + 4, y, 'panel', 4)
        s.set(x0 + 5, y, 'panel', 2)
        if y % 8 == 0:
            s.set(x0 + 3, y, 'iron', 2); s.set(x0 + 6, y, 'iron', 1)            # its clamps
    # the engine skirt, flaring a little, sooted toward its foot
    for y in range(84, 88):
        for x in range(x0 - 1, x0 + RW + 1):
            t = cyl_tone(x, cx, r + 1)
            name = 'iron' if y < 86 else 'iron_cool'
            s.set(x, y, name, max(0, t - (y - 84)))
    s.hline(x0 - 1, 84, RW + 2, 'iron', 4)
    # two nozzle bells: a lit band on the left third, cooling rings, a sooted lip
    for bx in (cx - 7, cx + 6):
        for k in range(h - 88):
            y = 88 + k
            half = 2 + k * 3 // 7
            for x in range(bx - half, bx + half + 1):
                kk = (x - (bx - half) + 0.5) / (2 * half + 1)
                t = 4 if kk < 0.3 else 3 if kk < 0.6 else 2 if kk < 0.85 else 1
                if k % 3 == 2:
                    t = max(0, t - 1)                                         # a cooling ring
                s.set(x, y, 'iron', t)
        for x in range(bx - 5, bx + 6):
            s.set(x, h - 1, 'iron', 0)                                        # the sooted lip
        s.set(bx - 1, 88, 'brass', 4); s.set(bx, 88, 'brass', 3)               # the gimbal's brass
    # fins: solid painted metal, root along the thrust section, swept, the lit face on the
    # near-left fin, the shaded face on the near-right one, a dark trailing edge sooted
    for (side, fx) in ((-1, x0 - 1), (1, x0 + RW)):
        lit = side < 0
        for k in range(22):
            y = 62 + k
            reach = min(9, 1 + k * 9 // 12)
            for d in range(reach):
                x = fx + side * d
                face = 4 if lit else 2
                if d == reach - 1:
                    face = 5 if lit else 3                                     # the leading edge, lit
                if k >= 20:
                    face = 1 if lit else 0                                     # the trailing edge
                    if d < reach - 2:
                        s.set(x, y, 'iron', 1)                                 # soot on it
                        continue
                s.set(x, y, 'sky' if d % 4 else 'sky_cool', face)
            s.set(fx, y, 'sky', 2 if lit else 1)                               # the root fillet
    return s


def cone_skin(s: Spr, cx, y0, y1, r0, r1, fam, seed, rings, seams):
    """A cut cone's skin (a capsule), built like skin(): rings of panels with a seam, a lit lip
    and rivets on it, one vertical seam a ring, the cylinder's light across each row."""
    edges = sorted(set([y0] + list(rings) + [y1]))
    for y in range(y0, y1):
        rr = r0 + ((y - y0) * (r1 - r0)) // max(1, y1 - y0 - 1)
        ring = max(i for i, e in enumerate(edges) if e <= y)
        top = edges[ring]
        sx = cx + seams[ring % len(seams)]
        for x in range(cx - rr, cx + rr):
            k = (x - (cx - rr) + 0.5) / (2 * rr)
            t = 4 if k < 0.3 else 3 if k < 0.6 else 2 if k < 0.85 else 1
            if 0.11 < k < 0.16:
                t = 5
            if k > 0.93:
                t = 2
            name = sib(fam, noise2(ring, 0 if x < sx else 1, seed), 0.34)
            if y == top and y != y0:
                t = max(0, t - 2)
            elif y == top + 1 and top != y0:
                t = min(5, t + 1)
            elif x == sx:
                t = max(0, t - 1)
            s.set(x, y, name, t)
            if y == top + 1 and top != y0 and (x - (cx - rr)) % 3 == 1 and 0.06 < k < 0.94:
                s.set(x, y, 'iron', 4 if k < 0.6 else 3)


def nozzle(s: Spr, bx, y0, n, top_half=2, soot=True):
    """An engine's nozzle bell: widening downwards, a lit band on its left third, cooling rings
    every third row, a sooted lip, the gimbal's brass at its throat."""
    for k in range(n):
        y = y0 + k
        half = top_half + k * 3 // 6
        for x in range(bx - half, bx + half + 1):
            kk = (x - (bx - half) + 0.5) / (2 * half + 1)
            t = 4 if kk < 0.3 else 3 if kk < 0.6 else 2 if kk < 0.85 else 1
            if k % 3 == 2:
                t = max(0, t - 1)
            if soot and k == n - 1:
                t = 0
            s.set(x, y, 'iron', t)
    s.set(bx - 1, y0, 'brass', 4); s.set(bx, y0, 'brass', 3)


def leg(s: Spr, hx, hy, fx, fy, side, sx, sy, pad=3):
    """A landing leg out on its struts: the leg itself (two pixels, its outer face lit or in
    shade), the shock strut from the skirt to its knee (a steel cylinder, its brass piston rod),
    the footpad edge on (a disc: its top lit, a dark rim)."""
    lit = side < 0
    n = max(abs(fx - hx), abs(fy - hy), 1)
    for k in range(n + 1):
        x, y = hx + (fx - hx) * k // n, hy + (fy - hy) * k // n
        s.set(x, y, 'panel', 4 if lit else 2)
        s.set(x - side, y, 'panel', 2 if lit else 1)
    kx, ky = hx + (fx - hx) * 2 // 3, hy + (fy - hy) * 2 // 3
    m = max(abs(kx - sx), abs(ky - sy), 1)
    for k in range(m + 1):
        x, y = sx + (kx - sx) * k // m, sy + (ky - sy) * k // m
        rod = k > m * 3 // 5
        s.set(x, y, 'brass' if rod else 'iron', (4 if lit else 3) if rod else (3 if lit else 2))
        s.set(x, y + 1, 'brass' if rod else 'iron', 2 if rod else 1)
    for d in range(-pad, pad + 1):
        s.set(fx + d, fy, 'panel', 4 if d < 0 else 3 if d < 2 else 2)
        s.set(fx + d, fy + 1, 'panel', 1)
    s.hline(fx - 1, fy - 1, 3, 'panel', 3); s.set(fx - 1, fy - 1, 'panel', 4)


def upper_stage(legs: int = 0) -> Spr:
    """The second stage and its crew capsule, built as one is. The capsule: a cut cone of
    white panels (ring seams, rivets on their lips), the docking ring at its nose with its
    status lamps, a lamp-lit porthole with the companion's sleepy silhouette inside, the
    side hatch (hinged, a stencilled arrow at it, where the gantry's crew arm meets it).
    The stage: a signal-blue band, white panels with the stage number stencilled, a
    rescue-red line, RCS quads at its shoulders, the landing legs folded along it, the
    engine skirt and one nozzle bell. `legs` 0 folded, 1 half out, 2 deployed, 3 compressed
    (touchdown): the way back lands it on them."""
    w, h = RW + 30, STAGE2_H + 10
    s = Spr(w, h)
    cx, r = w // 2, RW // 2
    x0 = cx - r
    nose_h, cap_h = 14, 22
    body_top = nose_h + cap_h
    body_bot = STAGE2_H - 6
    cone_skin(s, cx, 0, body_top, 5, r, 'hull', 31, rings=(3, nose_h, nose_h + 12), seams=(2, -3, 4, -6))
    # the docking ring at the nose: steel, two-pixel status lamps round it, a brass seat
    for x in range(cx - 5, cx + 5):
        s.set(x, 0, 'iron', 4 if x < cx - 2 else 3 if x < cx + 2 else 2)
        s.set(x, 1, 'neon_cyan', 4) if (x - cx + 5) % 4 < 2 else s.set(x, 1, 'iron', 1)
        s.set(x, 2, 'brass', 4 if x < cx - 2 else 3 if x < cx + 2 else 2)
    # the porthole, lamp-lit from the cabin
    pcx, pcy = cx - 5, nose_h + 9
    porthole(s, pcx, pcy, 3)
    seat(s, pcx - 5, pcy - 5, 10, 10)
    # the side hatch where the crew arm meets the capsule: hazard-ochre rescue markings round it,
    # its own small window, an arrow stencilled at it
    hx_, hy_ = cx + 1, nose_h + 2
    s.rect(hx_ - 1, hy_ - 1, 9, 14, 'brass', 3)
    for y in range(hy_ - 1, hy_ + 13):
        for x in range(hx_ - 1, hx_ + 8):
            if ((x + y) // 2) % 2:
                s.set(x, y, 'iron', 1)
    hinged_hatch(s, hx_, hy_, 7, 12, hinge_left=True)
    s.rect(hx_ + 2, hy_ + 2, 3, 3, 'lamp', 3); s.set(hx_ + 2, hy_ + 2, 'lamp', 5); s.hline(hx_ + 2, hy_ + 5, 3, 'iron', 4)
    seat(s, hx_ - 1, hy_ - 1, 9, 14)
    stencil(s, cx + 9, nose_h + 9, '<', 'berry', 2)
    s.rect(cx - 12, nose_h + 15, 5, 4, 'dusk', 3); s.hline(cx - 12, nose_h + 15, 5, 'dusk', 4)   # the nap flag
    s.set(cx - 11, nose_h + 16, 'lamp', 5); s.set(cx - 10, nose_h + 17, 'lamp', 4)
    seat(s, cx - 12, nose_h + 15, 5, 4)
    # the stage: panels under a signal-blue band and a rescue-red line, its number stencilled
    paint = lambda y: 'sky' if body_top + 2 <= y < body_top + 6 else 'berry' if y in (body_bot - 5, body_bot - 4) else None   # noqa: E731
    skin(s, x0, body_top, RW, body_bot, cx, r, 'hull', 33, rings=(body_top + 8, body_top + 17), seams=(4, -6, 5), paint=paint)
    stencil(s, cx + 3, body_top + 10, '2')
    for x in range(x0 + 3, x0 + RW - 3, 5):                                    # white dashes on the blue band
        s.hline(x, body_top + 4, 2, 'hull', 5)
    hinged_hatch(s, cx + 8, body_top + 10, 6, 6, hinge_left=False)            # a service panel
    seat(s, cx + 8, body_top + 10, 6, 6)
    s.rect(x0 + 2, body_top + 10, 4, 5, 'panel', 3); s.hline(x0 + 2, body_top + 10, 4, 'panel', 4)   # the stage umbilical
    s.hline(x0 + 2, body_top + 14, 4, 'panel', 1); s.set(x0 + 3, body_top + 12, 'brass', 4); s.set(x0 + 4, body_top + 12, 'berry', 4)
    s.rect(x0 + 2, body_top + 7, 2, 2, 'glowflora', 3); s.set(x0 + 2, body_top + 7, 'glowflora', 5)   # its 'connected' lamp
    s.rect(x0 + RW - 7, body_top + 1, 4, 3, 'brass', 3); s.hline(x0 + RW - 7, body_top + 1, 4, 'brass', 5)   # a relief valve
    s.set(x0 + RW - 6, body_top + 3, 'iron', 0)
    for (ra, rb) in ((x0 + 3, x0 + 12), (cx + 2, cx + 11)):                     # handrails, on stand-offs
        s.hline(ra, body_top + 6, rb - ra, 'brass', 4 if ra < cx else 3); s.hline(ra, body_top + 7, rb - ra, 'brass', 2)
        s.set(ra + 1, body_top + 8 - 0, 'iron', 2); s.set(rb - 2, body_top + 8, 'iron', 2)
    placard(s, cx - 9, body_top + 10, 7); seat(s, cx - 9, body_top + 10, 7, 5)
    connectors(s, x0 + 3, body_top + 19, ('brass', 'sky')); seat(s, x0 + 3, body_top + 19, 7, 5)
    s.rect(cx + 6, body_top + 19, 5, 4, 'panel', 3); s.hline(cx + 6, body_top + 19, 5, 'panel', 4)   # a camera, looking down
    s.hline(cx + 6, body_top + 22, 5, 'panel', 1); s.rect(cx + 7, body_top + 20, 2, 2, 'slate', 1)
    s.set(cx + 7, body_top + 20, 'lamp', 5); seat(s, cx + 6, body_top + 19, 5, 4)
    # RCS quads at the shoulders: a block lit on top, its nozzles out, up and down
    for (qx, lit, out) in ((x0 - 3, True, x0 - 4), (x0 + RW, False, x0 + RW + 3)):
        s.rect(qx, body_top - 4, 3, 5, 'panel', 3 if lit else 2)
        s.hline(qx, body_top - 4, 3, 'panel', 4 if lit else 3); s.hline(qx, body_top, 3, 'panel', 1)
        s.set(out, body_top - 2, 'iron', 2)                                     # the side nozzle
        s.set(qx + 1, body_top - 5, 'iron', 3); s.set(qx + 1, body_top + 1, 'iron', 1)
    # the engine: a short skirt, one bell
    for y in (body_bot, body_bot + 1):
        for x in range(x0 + 2, x0 + RW - 2):
            s.set(x, y, 'iron', min(5, cyl_tone(x, cx, r - 2) + (1 if y == body_bot else -1)))
    nozzle(s, cx, body_bot + 2, 6, 2)
    # the landing legs: folded flat along the body, or out on their struts
    foot = STAGE2_H + 4 if legs == 2 else STAGE2_H + 2
    hinge_y = body_bot - 18
    for side in (-1, 1):
        lit = side < 0
        hx = cx + side * r if side > 0 else cx - r - 1
        if legs == 0:
            for y in range(hinge_y, body_bot + 2):
                s.set(hx, y, 'panel', 4 if lit else 2)
                s.set(hx + side, y, 'panel', 2 if lit else 1)
            s.rect(hx + (side if side < 0 else 0), body_bot + 1, 2, 2, 'panel', 3 if lit else 1)   # the folded pad
            s.set(hx, hinge_y, 'brass', 4 if lit else 3)                              # the hinge pin
            continue
        spread = {1: 7, 2: 13, 3: 14}[legs]
        fx = hx + side * spread
        fy = body_bot + 4 if legs == 1 else foot if legs == 2 else foot - 2
        leg(s, hx, hinge_y, fx, fy, side, hx - side, body_bot - 8, pad=2 if legs == 1 else 3)
        s.set(hx, hinge_y, 'brass', 4 if lit else 3)
    return s


def flame(stage: int, frame: int, small: bool = False) -> Spr:
    """An engine's flame, a light source (no outline): a near-white core, lamp yellow, lava
    orange at the edge, shock diamonds in the plume. Frames 0 to 1 grow (ignition), 2 to 5
    flicker at full."""
    length = (10, 22, 40, 42, 38, 41)[frame] if not small else (6, 12, 18, 20, 17, 19)[frame]
    width = (5, 8, 11, 12, 11, 12)[frame] if not small else (3, 5, 6, 7, 6, 7)[frame]
    if stage == 1:          # the booster's two engines share one wide plume
        width += 6
    w, h = width * 2 + 4, length + 2
    s = Spr(w, h)
    cx = w // 2
    for y in range(h):
        k = y / max(1, length)
        half = width * (1.0 - 0.55 * k) * (0.85 + 0.15 * math.sin(k * 6 + frame))
        wob = (smooth_noise(y, frame * 7, 3, 71) - 0.5) * 2
        for x in range(w):
            d = abs(x - cx - wob) / max(0.5, half)
            if d > 1.0:
                continue
            if k > 0.92 and noise2(x, y + frame * 13, 72) > 0.5:
                continue
            core = d < 0.35 and k < 0.55
            name, tone = ('lamp', 5) if core else ('lamp', 4) if d < 0.62 and k < 0.75 else ('lava', 3) if d < 0.85 else ('lava', 2)
            if k > 0.7:
                tone = max(1, tone - 1)
            # shock diamonds: brighter bands down the plume
            if not small and stage and 0.3 < k < 0.8 and int(y + frame) % 9 < 2 and d < 0.5:
                name, tone = 'lamp', 5
            s.set(x, y, name, tone)
    return s


def lumps(s: Spr, balls: list, fam: str, seed: int, squash: float = 1.0, warm=None, thin=False,
          flat_bottom=None):
    """Billowing lumps (smoke, steam, cloud): each ball shaded on its own, the lower (nearer)
    balls drawn over the ones behind, lit at their upper left with a rim of tone 4 and a
    glint of 5, the body 3, the underside 2 and 1, a darker crevice where a front lump
    overlaps the one behind. `warm` (glow name) lights the undersides of the lower balls
    from below (a flame under smoke). `thin` breaks a puff up as it disperses."""
    order = sorted(range(len(balls)), key=lambda i: balls[i][1])        # back (higher) to front (lower)
    owner = {}
    for i in order:
        bx, by, br = balls[i]
        for y in range(int(by - br * squash) - 1, int(by + br * squash) + 2):
            for x in range(int(bx - br) - 1, int(bx + br) + 2):
                dy = (y - by) / squash
                if (x - bx) ** 2 + dy * dy <= br * br and (flat_bottom is None or y <= flat_bottom):
                    owner[(x, y)] = i
    cy_all = sum(b[1] for b in balls) / len(balls)
    for (x, y), i in owner.items():
        bx, by, br = balls[i]
        if thin and noise2(x // 2, y // 2, seed + 9) > 0.5:
            continue
        # distance from a lit point at the ball's upper left: curved crescents of light
        lx, ly = bx - br * 0.42, by - br * 0.42 * squash
        dl = math.hypot(x - lx, (y - ly) / squash) / br
        u = dl * 1.25 - 0.9                                            # -0.9 lit .. ~+1.2 shaded
        rim = (x - bx) ** 2 + ((y - by) / squash) ** 2 > (br - 1.6) ** 2
        tone = 4 if u < -0.35 else 3 if u < 0.35 else 2 if u < 0.85 else 1
        if rim and u < -0.3:
            tone = 5 if noise2(x, y, seed + 2) > 0.45 else 4
        up = owner.get((x - 1, y - 1))
        if up is not None and up != i and balls[up][1] < by:
            tone = max(0, tone - 1)                                    # the crevice under a lump behind
        name = sib(fam, noise2(int(bx), int(by), seed + 3), 0.3)
        if warm and by > cy_all and u > 0.15:
            name, tone = warm, (2 if u > 0.55 else 1)                  # lit from the flame below
        s.set(x, y, name, tone)


def puff(size: int, kind: str, seed: int) -> Spr:
    """A puff of smoke or steam, size px across: a cluster of lumps. 'fire' is smoke lit from
    below by the plume; 'thin' a puff breaking up."""
    fam = 'snow' if kind == 'steam' else 'stone'
    s = Spr(size + 4, size + 4)
    c = size / 2 + 2
    balls = [(c, c + size * 0.06, size * 0.36)]
    n = max(2, size // 6 + 1)
    for i in range(n):
        a = 2 * math.pi * i / n + noise2(i, size, seed) * 0.9
        balls.append((c + math.cos(a) * size * 0.25, c + math.sin(a) * size * 0.2,
                      size * (0.2 + noise2(i, 1, seed) * 0.12)))
    lumps(s, balls, fam, seed, squash=0.9, warm='lava' if kind == 'fire' else None, thin=kind == 'thin')
    return s


def puff_sheet(kind: str, sizes=(6, 10, 14, 19, 25, 32, 40), seed=0) -> tuple:
    """Growth frames of a puff, then two breaking-up frames and an empty one, all in boxes
    of the largest size, stacked top to bottom (the renderer shows one at a time)."""
    box = max(sizes) + 4
    frames = []
    for i, sz in enumerate(sizes):
        frames.append(puff(sz, kind, seed + i).render(outline=kind != 'thin'))
    last = sizes[-1]
    frames.append(puff(last, 'thin', seed + 50).render(outline=False))
    frames.append(puff(last - 4, 'thin', seed + 51).render(outline=False))
    frames.append(Canvas(4, 4))   # gone
    sheet = Canvas(box, box * len(frames))
    for i, f in enumerate(frames):
        sheet.paste(f, (box - f.w) // 2, i * box + (box - f.h) // 2)
    return sheet, box, len(frames)


# --- the pad, the gantry and the city ------------------------------------------------------
GANTRY_H = 192   # six storeys
TILE_W = 256     # the looping background tiles' width


def gantry_tower() -> Spr:
    """The service tower: an iron lattice of two legs and diagonal bracing in bays of 16 px
    (half a storey), a lift cage, walkway decks every storey with hazard-ochre toe boards,
    a lightning mast and a red beacon on top."""
    w, h = 28, GANTRY_H
    s = Spr(w, h)
    for y in range(8, h):
        for (lx, lit) in ((2, True), (22, False)):
            s.set(lx, y, 'iron', 4 if lit else 2)
            s.set(lx + 1, y, 'iron', 3 if lit else 1)
            s.set(lx + 2, y, 'iron', 2 if lit else 0)
        bay = (y - 8) % 16
        # diagonal bracing: an X in each bay
        for (xx, tt) in ((4 + bay * 18 // 16, 3), (21 - bay * 18 // 16, 2)):
            s.set(xx, y, 'iron_warm' if tt == 3 else 'iron_cool', tt)
        if bay == 0:
            s.hline(2, y, 23, 'iron', 3)
            s.hline(2, y + 1, 23, 'iron', 1)
    for k, y in enumerate(range(16, h, 32)):                       # the walkway decks, a storey apart
        s.hline(-1 + 1, y, 27, 'panel', 4)
        s.hline(1, y + 1, 26, 'brass', 3 if k % 2 else 4)        # the hazard-ochre toe board
        s.hline(1, y + 2, 26, 'iron', 1)
        for x in range(1, 27, 4):
            s.set(x, y - 3, 'iron', 3); s.set(x, y - 2, 'iron', 3); s.set(x, y - 1, 'iron', 2)   # the rail's posts
        s.hline(1, y - 4, 26, 'iron', 4)
    for y in range(20, h - 4):                                    # the lift cage running up the middle
        s.set(12, y, 'panel', 3); s.set(15, y, 'panel', 2)
        if y % 6 == 0:
            s.hline(12, y, 4, 'panel', 3)
    s.rect(11, 112, 6, 9, 'panel', 3)                             # the car, parked mid-tower
    s.hline(11, 112, 6, 'panel', 4)
    s.set(13, 116, 'lamp', 4); s.set(14, 116, 'lamp', 3)
    for y in range(0, 8):                                         # the lightning mast
        s.set(13, y, 'iron', 3); s.set(14, y, 'iron', 1)
    s.set(13, 0, 'berry', 4); s.set(14, 0, 'berry', 3)             # its beacon (the lamp glows apart)
    s.rect(0, h - 6, 28, 6, 'concrete', 2)                         # its footing
    s.hline(0, h - 6, 28, 'concrete', 4)
    return s


def gantry_arm(frame: int, level: int) -> Spr:
    """A swing arm from the tower to the rocket, seen from the side: swinging back about its
    pivot, it foreshortens (frames 0 full, 1 two thirds, 2 a third, 3 stowed). Level 0 is the
    crew access arm with its white room at the hatch, level 1 the umbilical arm with its
    hoses hanging to the rocket's flank."""
    full = 34
    length = (full, full * 2 // 3, full // 3, 4)[frame]
    w, h = full + 2, 20
    s = Spr(w, h)
    x0 = w - length
    for x in range(x0, w):                                          # the truss: chords and a zig-zag web
        s.set(x, 2, 'iron', 4); s.set(x, 3, 'iron', 2)
        s.set(x, 9, 'iron', 3); s.set(x, 10, 'iron', 1)
        zig = (x - x0) % 8
        s.set(x, 4 + (zig if zig < 4 else 7 - zig) * 5 // 4, 'iron_warm', 3)
    s.hline(x0, 1, length, 'brass', 4)                              # hazard-ochre top rail
    if level == 0 and frame < 2:                                     # the white room at the hatch end
        s.rect(x0, 0, 9, 12, 'hull', 3)
        s.hline(x0, 0, 9, 'hull', 5)
        s.vline(x0 + 8, 0, 12, 'hull', 1)
        s.rect(x0 + 2, 3, 4, 4, 'lamp', 3)                          # its lit window
        s.set(x0 + 2, 3, 'lamp', 4)
    if level == 1:                                                  # the hoses, sagging to the flank
        for k, (hx, sag, fam) in enumerate(((x0 + 2, 6, 'brass'), (x0 + 5, 8, 'iron'))):
            if frame >= 3:
                break
            reach = max(1, min(10, length // 3))
            for t in range(reach + 1):
                x = hx - t
                y = 11 + int(sag * math.sin(math.pi * t / max(1, reach)) * (1.0 if frame == 0 else 0.5))
                s.set(x, y, fam, 3 if t < reach // 2 else 2)
    return s


def pad_mount() -> Spr:
    """The launch mount: a concrete table over the flame trench, hold-down clamps, the
    deflector's mouth glowing faintly with the pad lights, hazard-ochre edge markings."""
    w, h = 84, 26
    s = Spr(w, h)
    for y in range(0, h):
        for x in range(w):
            if y < 4:
                s.set(x, y, sib('concrete', noise2(x // 8, 0, 41), 0.3), 4 if y == 0 else 3)
            elif 8 <= y < 22 and 22 <= x < 62:
                s.set(x, y, 'asphalt', 0 if y > 12 else 1)                  # the trench's mouth, deep in shade
            else:
                n = noise2(x // 7, y // 5, 42)
                s.set(x, y, sib('concrete', n, 0.3), 2 if x < w * 0.6 else 1)
                if (x // 7 + y // 5) % 3 == 0 and y % 5 == 0:
                    s.set(x, y, 'concrete', 0)
    for x in range(0, w, 6):                                        # hazard markings on the table's edge
        for k in range(3):
            s.set(x + k, 4, 'brass', 3); s.set(x + k, 5, 'brass', 2)
    for (cx_, lit) in ((26, True), (56, False)):                    # hold-down clamps
        s.rect(cx_ - 2, -0, 5, 4, 'iron', 3 if lit else 1)
        s.set(cx_ - 2, 0, 'iron', 4)
    for x in range(24, 60, 5):
        s.set(x, 22, 'lamp', 2)                                     # pad lights in the trench's sill
    return s


def skyline(seed=61) -> Canvas:
    """The neon city behind the Skyport at night, one 256 px loop: towers of concrete and
    painted cladding as dark masses, lit windows in lamp and neon, rooftop masts with red
    beacons, a lit sign or two, the harbour's water glinting at their feet."""
    h = 176
    s = Spr(TILE_W, h)
    x = 0
    k = 0
    while x < TILE_W:
        bw = 18 + int(noise2(k, 0, seed) * 26)
        bh = 40 + int(noise2(k, 1, seed) * 110)
        far = noise2(k, 2, seed) > 0.55
        fam = 'asphalt' if far else 'concrete'
        top = h - 24 - bh
        for yy in range(top, h - 24):
            for xx in range(x, min(TILE_W, x + bw)):
                t = 1 if far else 2
                if xx == x and not far:
                    t = 3                                        # the lit west edge
                if yy == top:
                    t = min(5, t + 2) if xx < x + bw // 2 else t + 1
                s.set(xx, yy, sib(fam, noise2(k, yy // 12, seed + 4), 0.3), t)
        # windows: lit panes in rows, a few dark, a few neon
        for wy in range(top + 5, h - 30, 6):
            for wx in range(x + 3, x + bw - 3, 4):
                n = noise2(wx, wy, seed + 5)
                if n < 0.42:
                    continue
                g = 'neon_cyan' if n > 0.93 else 'neon_pink' if n > 0.89 else 'lamp'
                tone = 2 if far else 3
                s.set(wx, wy, g, tone); s.set(wx + 1, wy, g, tone - 1)
                if not far:
                    s.set(wx, wy + 1, g, tone - 1)
        if noise2(k, 3, seed) > 0.6 and bh > 70:                  # a rooftop mast and beacon
            mx = x + bw // 2
            for yy in range(top - 12, top):
                s.set(mx, yy, 'iron', 2)
            s.set(mx, top - 13, 'neon_pink', 4)
        if noise2(k, 4, seed) > 0.75 and not far:                 # a vertical neon sign
            sx = x + bw - 4
            for yy in range(top + 10, min(h - 30, top + 34)):
                s.set(sx, yy, 'neon_pink' if k % 2 else 'neon_cyan', 3 if yy % 4 else 4)
        x += bw + (1 if noise2(k, 5, seed) > 0.5 else 0)
        k += 1
    for yy in range(h - 24, h):                                   # the harbour water at the towers' feet
        for xx in range(TILE_W):
            t = 1 if yy > h - 20 else 2
            name = 'water'
            if (xx + yy * 3) % 23 == 0 and noise2(xx, yy, seed + 8) > 0.4:
                name, t = 'lamp', 2                                # a lit window's reflection
            s.set(xx, yy, name, t)
    return s.tile()


def pad_deck() -> Canvas:
    """The Skyport's launch apron, one 256 px loop: concrete slabs lit at their upper left,
    expansion joints, painted lanes and blast-scorch near the middle, a hazard band at the
    near edge and the apron's floodlights."""
    h = 96
    s = Spr(TILE_W, h)
    for y in range(h):
        for x in range(TILE_W):
            row, col = y // 12, (x + (y // 12 % 2) * 16) // 32
            n = noise2(col, row, 81)
            t = 3 if y < 2 else 2
            if y % 12 == 0:
                t = 1
            elif y % 12 == 1:
                t = 3
            elif (x + (y // 12 % 2) * 16) % 32 == 0:
                t = 1
            if smooth_noise(x, y, 18, 82) > 0.72:
                t = max(0, t - 1)                                 # scorch drifts
            s.set(x, y, sib('concrete', n, 0.3), t)
    for x in range(TILE_W):
        for y in (40, 41):
            if (x // 10) % 2 == 0:
                s.set(x, y, 'brass', 3 if y == 40 else 2)         # a painted lane
        for y in range(h - 8, h - 4):
            s.set(x, y, 'brass' if (x + y) // 4 % 2 else 'iron', 3 if y == h - 8 else 2)
    for lx in range(20, TILE_W, 64):                              # flush floodlights
        s.rect(lx, 22, 4, 2, 'iron', 1)
        s.set(lx + 1, 22, 'lamp', 4); s.set(lx + 2, 22, 'lamp', 3)
    return s.tile()


# --- the sky, clouds and stars --------------------------------------------------------
SKY_COL_W, SKY_COL_H = 64, 1600


def sky_column() -> Canvas:
    """The night sky over the city, bottom to top: the city's dusk-violet glow at the
    horizon, deeper violet, then the void, then black space. Stepped bands with a 2 x 2
    checker at each join (house style: dither only for an atmospheric fade)."""
    steps = [T('dusk', 1), T('dusk', 0), T('void', 3), T('void', 2), T('void', 1), T('void', 0), '#120C22', '#0A0814', '#05040A']
    cv = Canvas(SKY_COL_W, SKY_COL_H)
    n = len(steps)
    for y in range(SKY_COL_H):
        k = (SKY_COL_H - 1 - y) / (SKY_COL_H - 1)            # 0 at the bottom .. 1 at the top
        f = min(n - 1.001, max(0.0, (k ** 0.8) * (n - 1) * 1.25))
        i = int(f)
        frac = f - i
        for x in range(SKY_COL_W):
            c = steps[i]
            if frac > 0.82 and (x + y) % 2 == 0 and i + 1 < n:
                c = steps[i + 1]
            cv.set(x, y, c)
    return cv


def stars(seed=91, size=256, dense=1.0) -> Canvas:
    """A loop of stars (both ways): faint pairs, brighter ones with a lamp-white core, a few
    with a cross of light, the odd cool blue one."""
    cv = Canvas(size, size)
    for i in range(int(110 * dense)):
        x = int(noise2(i, 0, seed) * size)
        y = int(noise2(i, 1, seed) * size)
        b = noise2(i, 2, seed)
        if b < 0.6:
            cv.set(x, y, T('snow', 1) if b < 0.3 else T('hull', 2))
        elif b < 0.9:
            cv.set(x, y, T('lamp', 5)); cv.set(x + 1, y, T('snow', 2))
        else:
            core = T('neon_cyan', 5) if b > 0.97 else T('lamp', 5)
            cv.set(x, y, core)
            for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cv.set((x + dx) % size, (y + dy) % size, T('snow', 3))
            for (dx, dy) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                cv.set((x + dx) % size, (y + dy) % size, T('snow', 1))
    return cv


def clouds(seed: int, h: int = 72) -> Canvas:
    """A loop of night cloud: banks of moonlit lumps in slate, lit at their upper left, their
    bellies flattened and in dusk shade, a trailing wisp or two; clear sky between banks."""
    s = Spr(TILE_W, h)
    banks = []
    for b in range(3):
        bx = noise2(b, 0, seed) * TILE_W
        width = 50 + noise2(b, 1, seed) * 50
        base = h * 0.66 + (noise2(b, 2, seed) - 0.5) * 10
        for i in range(7):
            x = bx + (i / 6 - 0.5) * width
            r = 7 + noise2(b * 10 + i, 3, seed) * 9 * (1 - abs(i / 6 - 0.5))
            banks.append((x, base - r * 0.55, r))
    tiles = [(x + off, y, r) for (x, y, r) in banks for off in (-TILE_W, 0, TILE_W)]
    lumps(s, tiles, 'slate', seed, squash=0.75, flat_bottom=int(h * 0.7))
    for (x, y) in list(s.px):
        name, tone = s.px[(x, y)]
        if tone <= 1:
            s.px[(x, y)] = ('dusk', 1)                                      # the bellies in dusk shade
        if not 0 <= x < TILE_W:
            del s.px[(x, y)]
    for x in range(TILE_W):                                                # wisps
        if smooth_noise(x, 0, 24, seed + 3) > 0.6:
            s.set(x, int(h * 0.72), 'dusk', 2)
    return s.tile()


# --- Halcyon from below, the moon, the lander --------------------------------------------
def station_underside() -> Canvas:
    """Halcyon seen side on and a little from below as a vehicle comes up to it, built as a
    station is: a Warren truss across the whole width (near diagonals lit, the far face's
    seen through it, darker), a rotary joint on each side and beyond it a solar wing (two
    blankets of dark cells on a mast, a glint across them); radiators hanging off the truss
    inboard (white panels with their fluid lines, hinged); under the truss's middle three
    modules joined by berthing collars: the lab (a science window, an experiment pallet), the
    node (the nap-moon roundel, a closed berthing port, floodlights) and the hab (three lit
    crew windows, the airlock hanging under it with its hinged hatch); yellow handrails on
    stand-offs, one rescue-red livery line; an antenna dish and a beacon mast on the truss;
    and under the node the docking adapter: a hazard-chevron collar, the ring of status lamps
    (components/rocket-journey.tsx lights them), guide petals and a docking target beside it."""
    w, h = 360, 120
    s = Spr(w, h)
    cx = w // 2
    TT, TB = 22, 33                                                     # the truss's chords

    def zig(x, off):
        z = (x + off) % 24
        return TT + 2 + (z if z < 12 else 23 - z) * (TB - TT - 3) // 11

    # the truss: the far face's diagonals seen through, the chords, the near diagonals, posts
    for x in range(w):
        y = zig(x, 12)
        s.set(x, y, 'iron', 2); s.set(x, y + 1, 'iron', 1)
    for x in range(w):
        s.set(x, TT, 'panel', 4); s.set(x, TT + 1, 'panel', 2)
        s.set(x, TB, 'panel', 3); s.set(x, TB + 1, 'panel', 1)
    for x in range(w):
        y = zig(x, 0)
        s.set(x, y, 'panel', 3); s.set(x, y + 1, 'panel', 1)
        if x % 24 == 0:
            s.vline(x, TT + 2, TB - TT - 2, 'panel', 3); s.vline(x + 1, TT + 2, TB - TT - 2, 'panel', 1)
    # the rail cart that runs along the truss's top: a box on the rails, its brass rollers
    s.rect(148, 17, 14, 5, 'panel', 3); s.hline(148, 17, 14, 'panel', 4); s.vline(161, 17, 5, 'panel', 1)
    for bx in (150, 158):
        s.set(bx, 21, 'brass', 4); s.set(bx + 1, 21, 'brass', 2)
    s.rect(152, 18, 4, 2, 'iron', 1); s.set(153, 18, 'glowflora', 4)
    # a rotary joint on each side: a drum round the truss, its bearing rings in brass
    for jx in (58, 294):
        for x in range(jx, jx + 8):
            for y in range(TT - 4, TB + 6):
                t = cyl_tone(x, jx + 4, 4)
                name = 'brass' if y in (TT - 3, TB + 4) else 'iron'
                if y == TT - 4:
                    t = min(5, t + 1)
                s.set(x, y, name, t)
    # the solar wings beyond the joints: a mast, two blankets of cells, a glint across them
    for (wx0, wx1) in ((0, 52), (308, 360)):
        mx = (wx0 + wx1) // 2
        for (y0, y1) in ((0, 18), (39, 76)):
            for y in range(y0, y1):
                for x in range(wx0, wx1):
                    if x in (mx - 1, mx, mx + 1):
                        continue
                    frame = (x - wx0) % 6 == 0 or (y - y0) % 5 == 0
                    g = (x - wx0) + (y - y0) * 2
                    glint = 30 <= g % 70 < 36
                    s.set(x, y, 'sky_cool' if not frame else 'sky', (3 if glint else 1) if not frame else (4 if glint else 2))
        for y in range(0, 76):                                           # the mast
            s.set(mx - 1, y, 'iron', 4); s.set(mx, y, 'iron', 2); s.set(mx + 1, y, 'iron', 1)
        for (by, bh) in ((18, 3), (36, 3)):                             # the blanket boxes at the roots
            s.rect(wx0 + 4, by, wx1 - wx0 - 8, bh, 'hull', 3)
            s.hline(wx0 + 4, by, wx1 - wx0 - 8, 'hull', 4); s.hline(wx0 + 4, by + bh - 1, wx1 - wx0 - 8, 'hull', 1)
    # radiators hanging off the truss inboard of the joints: three white panels on hinges
    for rx in (70, 258):
        s.vline(rx + 15, TB + 2, 3, 'iron', 3); s.vline(rx + 16, TB + 2, 3, 'iron', 1)   # the stem
        for i, py0 in enumerate((38, 53, 68)):
            name = sib('snow', noise2(i, rx, 211), 0.34)
            for y in range(py0, py0 + 13):
                for x in range(rx, rx + 32):
                    k = (x - rx) / 31
                    t = 4 if k < 0.45 else 3
                    if (y - py0) % 3 == 2:
                        t -= 1                                           # a fluid line
                    if y == py0:
                        t = 5
                    if x == rx:
                        t = 5
                    if x == rx + 31 or y == py0 + 12:
                        t = 2
                    s.set(x, y, name, t)
            if i < 2:                                                    # the hinge to the next panel
                s.hline(rx + 1, py0 + 13, 30, 'iron', 1)
                for hx in (rx + 6, rx + 24):
                    s.hline(hx, py0 + 13, 2, 'iron', 4)
    # an antenna dish on a boom, and the beacon mast
    s.vline(136, 7, TT - 7, 'iron', 4); s.vline(137, 7, TT - 7, 'iron', 2)
    for x in range(129, 145):
        for y in range(2, 8):
            if ((x - 136.5) / 7.6) ** 2 + ((y - 2) / 5.4) ** 2 <= 1:
                s.set(x, y, 'hull', 5 if y == 2 else 4 if x < 134 else 3 if x < 140 else 2)
    s.vline(136, 0, 2, 'iron', 3); s.hline(135, 0, 3, 'brass', 4)              # the feed on its strut
    s.vline(226, 10, TT - 10, 'iron', 4); s.vline(227, 10, TT - 10, 'iron', 2)
    s.rect(226, 8, 2, 2, 'lava', 4); s.set(226, 8, 'lava', 5)                  # the beacon, lit red
    # struts from the truss down to the lab and the hab
    for sx in (116, 146, 214, 244):
        s.vline(sx, TB + 2, 4, 'iron', 4); s.vline(sx + 1, TB + 2, 4, 'iron', 2)
    # the modules: the lab, the node, the hab, joined by collars, one livery line across them
    cy = 54
    livery = lambda x, y: 'berry' if y in (59, 60) else None   # noqa: E731
    hskin(s, 106, 156, cy, 15, 'hull', 201, rings=(121, 139), seams=(-5, 6, -5), paint=livery, taper=(4, 0))
    cloth = lambda x, y: livery(x, y) or ('stone' if 173 <= x < 188 else None)   # noqa: E731
    hskin(s, 160, 200, cy, 20, 'hull', 203, rings=(172, 188), seams=(-8, 7, -8), paint=cloth)
    for y in range(cy - 20, cy + 20):                                          # the node's blanket, quilted
        for x in range(174, 188):
            p = s.get(x, y)
            if p and fam_of(p[0]) == 'stone' and ((x - 174) % 4 == 3 or (y - cy) % 4 == 3):
                s.step(x, y, -1)
    hskin(s, 204, 254, cy, 15, 'hull', 205, rings=(220, 237), seams=(6, -5, 6), paint=livery, taper=(0, 4))
    collar(s, 156, 4, cy, 17)
    collar(s, 200, 4, cy, 17)
    # the lab: a porthole at its end, the science window, an experiment pallet, a stencil
    porthole(s, 115, 48, 3)
    for y in range(43, 50):
        for x in range(124, 135):
            edge = y in (43, 49) or x in (124, 134)
            s.set(x, y, 'iron', (4 if (y == 43 or x == 124) else 1) if edge else 0)
            if not edge:
                s.set(x, y, 'lamp', 2 if y < 46 else 3)
    s.hline(125, 44, 3, 'lamp', 5)                                             # the glint on it
    s.rect(129, 45, 2, 4, 'lamp', 1); s.vline(132, 45, 4, 'lamp', 1)           # racks inside, a screen lit
    s.rect(126, 46, 2, 2, 'neon_cyan', 3)
    s.rect(143, 42, 3, 3, 'brass', 3); s.hline(143, 42, 3, 'brass', 5); s.hline(143, 44, 3, 'brass', 1)   # sample canisters
    s.rect(148, 43, 3, 2, 'sky', 3); s.hline(148, 43, 3, 'sky', 5)
    s.rect(142, 45, 11, 8, 'panel', 3); s.hline(142, 45, 11, 'panel', 4)
    s.vline(142, 45, 8, 'panel', 4); s.hline(142, 52, 11, 'panel', 1); s.vline(152, 45, 8, 'panel', 1)
    s.rect(144, 47, 3, 3, 'slate', 1); s.set(144, 47, 'slate', 3)              # a sensor's lens
    s.rect(148, 47, 3, 2, 'glowflora', 3); s.set(148, 47, 'glowflora', 5)      # its status lamp
    s.hline(148, 50, 3, 'iron', 1)
    stencil(s, 127, 52, '1')
    # the node: the nap-moon roundel, a closed berthing port, floodlights under it
    mx, my = 170, 45
    for y in range(my - 4, my + 5):
        for x in range(mx - 4, mx + 5):
            d = (x - mx) ** 2 + (y - my) ** 2
            if d <= 17:
                s.set(x, y, 'dusk', 3 if x + y < mx + my else 2)
                if d <= 9 and (x - mx - 1.5) ** 2 + (y - my + 1) ** 2 > 4.5:
                    s.set(x, y, 'lamp', 4 if x < mx else 3)                       # the crescent
    bx_, by_ = 188, 54
    for y in range(by_ - 7, by_ + 8):
        for x in range(bx_ - 7, bx_ + 8):
            d = (x - bx_) ** 2 + (y - by_) ** 2
            if 25 < d <= 49:
                s.set(x, y, 'iron', 4 if (x - bx_) + (y - by_) < -2 else 2 if (x - bx_) + (y - by_) < 3 else 1)
            elif d <= 25:
                s.set(x, y, 'panel', 1 if (x - bx_) + (y - by_) < -4 else 3)   # the cover, its rim's shadow
    for (ax, ay) in ((bx_ - 4, by_), (bx_ + 3, by_), (bx_, by_ - 4), (bx_, by_ + 3)):
        s.set(ax, ay, 'iron', 4); s.set(ax + 1, ay, 'iron', 2)                 # its latches
    for fx in (164, 194):                                                     # floodlights, aimed down
        s.rect(fx, 72, 4, 2, 'iron', 2); s.hline(fx, 72, 4, 'iron', 3)
        s.hline(fx, 74, 4, 'lamp', 5); s.hline(fx + 1, 75, 2, 'lamp', 4)
    # the hab: three lit crew windows, handrails, its stencil
    for wx in (211, 227, 244):
        porthole(s, wx, 48, 3)
    stencil(s, 230, 52, '2')
    # the yellow handrails along the lab and the hab, on stand-offs
    for (x0_, x1_) in ((110, 152), (208, 250)):
        for y in (41, 66):
            s.hline(x0_, y, x1_ - x0_, 'brass', 4 if y < cy else 3)
            for x in range(x0_ + 2, x1_, 8):
                s.set(x, y + 1, 'iron', 2)
    # the working parts on the modules: grapple fixtures for the arm, connector plates, label
    # plates, the coolant lines along their lower flanks, floodlights, a camera, a vent valve,
    # the cable trays along their tops
    for (part, x, y, w_, h_) in ((grapple, 111, 52, 7, 7), (grapple, 162, 60, 7, 7)):
        part(s, x, y); seat(s, x, y, w_, h_)
    placard(s, 131, 52); seat(s, 131, 52, 7, 5)
    placard(s, 216, 53); seat(s, 216, 53, 7, 5)
    connectors(s, 141, 54, ('brass', 'berry', 'sky')); seat(s, 141, 54, 10, 5)
    connectors(s, 206, 53, ('sky', 'brass')); seat(s, 206, 53, 7, 5)
    connectors(s, 161, 52, ('berry', 'brass')); seat(s, 161, 52, 7, 5)
    s.rect(240, 53, 6, 5, 'panel', 3); s.hline(240, 53, 6, 'panel', 4); s.hline(240, 57, 6, 'panel', 1)
    s.rect(241, 54, 2, 2, 'slate', 1); s.set(241, 54, 'lamp', 5); seat(s, 240, 53, 6, 5)   # a camera, its lens
    for (x0_, x1_) in ((109, 155), (205, 252)):
        pipe(s, x0_, x1_, 62, 'sky')
        s.rect(x0_ + 1, 37, x1_ - x0_ - 2, 2, 'panel', 3); s.hline(x0_ + 1, 37, x1_ - x0_ - 2, 'panel', 4)
        s.hline(x0_ + 1, 38, x1_ - x0_ - 2, 'panel', 1)
    valve_box(s, 127, 61); valve_box(s, 223, 61)
    floodlight(s, 150, 64)
    floodlight(s, 207, 64)
    s.rect(191, 65, 4, 3, 'brass', 3); s.hline(191, 65, 4, 'brass', 4); s.set(192, 67, 'iron', 0)   # a vent valve
    # the node's name plate, and handrails either side of its berthing port and between windows
    s.rect(174, 37, 13, 5, 'hull', 5); s.hline(174, 41, 13, 'hull', 2); seat(s, 174, 37, 13, 5)
    for (tx, n) in ((175, 3), (179, 2), (182, 4)):
        s.hline(tx, 39, n, 'dusk', 2)                                          # HALCYON, stencilled
    for (vx, y0_, y1_) in ((177, 46, 62), (198, 46, 62), (219, 43, 53), (236, 43, 53), (137, 43, 52)):
        vrail(s, vx, y0_, y1_)
    s.hline(187, 54, 3, 'brass', 4); s.hline(187, 55, 3, 'brass', 2)          # the cover's handle
    placard(s, 179, 63, 6); seat(s, 179, 63, 6, 5)
    s.rect(177, 33, 9, 3, 'iron', 3); s.hline(177, 33, 9, 'iron', 4); s.hline(177, 35, 9, 'iron', 1)   # the truss fitting
    s.set(178, 34, 'brass', 4); s.set(184, 34, 'brass', 4)
    for (cx_, lit) in ((161, True), (192, False)):                             # cameras on the node's shoulders
        s.rect(cx_, 38, 5, 4, 'panel', 3 if lit else 2); s.hline(cx_, 38, 5, 'panel', 4); s.hline(cx_, 41, 5, 'panel', 1)
        s.rect(cx_ + 1, 39, 2, 2, 'slate', 1); s.set(cx_ + 1, 39, 'lamp', 5)
        s.rect(cx_ + 3, 36, 2, 2, 'lamp', 4); s.set(cx_ + 3, 36, 'lamp', 5)     # and their lights
        seat(s, cx_, 38, 5, 4)
    s.rect(126, 35, 4, 2, 'sky', 2); s.hline(127, 34, 2, 'sky', 4); s.hline(126, 35, 2, 'sky', 4)   # a navigation antenna
    for x in range(196, 208):                                                  # the coolant jumper over the collar
        y = 66 + (1 if 199 <= x <= 204 else 0)
        s.set(x, y, 'sky', 4); s.set(x, y + 1, 'sky', 2)
    s.rect(195, 65, 2, 3, 'brass', 3); s.rect(207, 65, 2, 3, 'brass', 3)      # its quick-disconnects
    for (lx, g) in ((184, 'glowflora'), (191, 'glowflora')):                  # the port's alignment lamps
        s.rect(lx, 44, 2, 2, g, 3); s.set(lx, 44, g, 5)
    for sx_ in (121, 134):                                                      # the science window's shutters, open
        s.rect(sx_, 42, 2, 9, 'panel', 2); s.vline(sx_, 42, 9, 'panel', 4); s.hline(sx_, 50, 2, 'panel', 1)
    # the airlock under the hab: a short upright can, its hazard ring, its hinged hatch, an arrow
    for y in range(69, 84):
        for x in range(229, 249):
            t = cyl_tone(x, 239, 10)
            name = 'hull_cool'
            if y in (70, 71):
                name = 'brass' if ((x + y) // 2) % 2 else 'iron'
            if y == 83:
                t = max(0, t - 2)
            s.set(x, y, name, t)
    hinged_hatch(s, 236, 73, 8, 9)
    stencil(s, 231, 75, '>')
    # the docking adapter under the node: a cone, the hazard collar, the lamp ring, guide petals
    for y in range(74, 96):
        half = 15 - (y - 74) // 3 if y < 80 else 12
        for x in range(cx - half, cx + half):
            t = cyl_tone(x, cx, half)
            name = 'hull_cool'
            if 80 <= y < 86:
                name = 'brass' if ((x + y) // 3) % 2 else 'iron'           # hazard chevrons on the collar
            if y == 77:
                t = max(0, t - 2)
            if y == 78:
                t = min(5, t + 1)
            if y in (91, 95):
                name, t = 'iron', 1
            if y in (93, 94):
                name, t = 'iron', (3 if y == 93 else 2)
            s.set(x, y, name, t)
    for x in range(cx - 12, cx + 12, 3):
        s.set(x, 92, 'neon_cyan', 4)                                         # the ring of status lamps
    for px_ in (cx - 9, cx + 6):                                             # guide petals on the soft ring
        s.hline(px_, 93, 3, 'brass', 4); s.set(px_ + 1, 94, 'brass', 3)
    # the docking target beside it: a dark plate with a white cross on a standoff
    s.rect(cx + 18, 75, 7, 7, 'iron', 0)
    s.vline(cx + 21, 76, 5, 'hull', 5); s.hline(cx + 19, 78, 5, 'hull', 5)
    s.set(cx + 21, 74, 'iron', 3)
    return s.render()


def moon_ground() -> Canvas:
    """Lumen's ground, one 256 px loop: grey to brown-grey regolith in calm broad patches,
    grit as sibling clusters, craters with a lit rim, a nearly black inner shadow and a lit
    far wall, boulders with black shadows (house style: the airless moon)."""
    h = 120
    s = Spr(TILE_W, h)
    for y in range(h):
        for x in range(TILE_W):
            n = smooth_noise(x, y, 34, 111)
            name = 'regolith_warm' if n > 0.62 else 'regolith_cool' if n < 0.36 else 'regolith'
            t = 3 if y > 2 else 4
            if noise2(x // 2, y // 2, 112) > 0.93:
                t = 4                                                       # grit clusters
            elif noise2(x // 2, y // 2, 113) > 0.95:
                t = 2
            s.set(x, y, name, t)
    for i in range(7):                                                      # craters
        ccx = noise2(i, 0, 114) * TILE_W
        ccy = 20 + noise2(i, 1, 114) * (h - 34)
        rr = 5 + noise2(i, 2, 114) * 12
        for y in range(int(ccy - rr * 0.6) - 2, int(ccy + rr * 0.6) + 3):
            for x in range(int(ccx - rr) - 2, int(ccx + rr) + 3):
                X = x % TILE_W
                d = ((x - ccx) / rr) ** 2 + ((y - ccy) / (rr * 0.55)) ** 2
                if d > 1.25 or not (0 <= y < h):
                    continue
                name = s.get(X, y)[0] if s.get(X, y) else 'regolith'
                if d > 1.0:
                    t = 4 if (x - ccx) + (y - ccy) * 1.8 < 0 else 2           # the raised rim
                else:
                    near = (y - ccy) < 0 or (x - ccx) < -rr * 0.3
                    t = 0 if (near and d > 0.45) else 4 if (not near and d > 0.5) else 2
                s.set(X, y, name, t)
    for i in range(10):                                                     # boulders and their black shadows
        bx, by = int(noise2(i, 5, 115) * TILE_W), int(10 + noise2(i, 6, 115) * (h - 16))
        rr = 1 + int(noise2(i, 7, 115) * 3)
        for y in range(by - rr, by + rr):
            for x in range(bx - rr, bx + rr + 1):
                s.set(x % TILE_W, y, 'regolith', 4 if x < bx else 2)
        for x in range(bx + 1, bx + rr + 4):
            s.set(x % TILE_W, by + rr - 1, 'regolith', 0)
            s.set(x % TILE_W, by + rr, 'regolith', 0)
    return s.tile()


def lumen_pad() -> Spr:
    """Lumen's landing pad: a disc of sintered regolith, its edge ringed with landing lights,
    a painted signal-blue ring and an ochre cross for the lander's feet."""
    w, h = 96, 24
    s = Spr(w, h)
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            d = ((x - cx) / (w / 2)) ** 2 + ((y - cy) / (h / 2)) ** 2
            if d > 1:
                continue
            t = 4 if y < 3 else 3 if (x - cx) + (y - cy) * 3 < 0 else 2
            name = 'regolith_cool'
            if 0.55 < d < 0.66:
                name, t = 'sky', 3 if y < cy else 2
            if abs(x - cx) < 1.5 and d < 0.5 or abs(y - cy) < 1 and d < 0.5:
                name, t = 'brass', 3
            s.set(x, y, name, t)
            if 0.9 < d <= 1 and int(x) % 8 == 0:
                s.set(x, y, 'lamp', 4)
    return s


def lander(legs: int) -> Spr:
    """The lander (Lumen's shuttle, the same craft drawn anew), built as one is. The descent
    stage: an eight-sided box seen across three faces (lit, front, shade), wrapped in gold foil
    blankets, each blanket one sibling with its seams, a lit fold along its top and one crease
    (a dark fold with its lit side); the front's lower blankets in black foil; the nap flag on
    it, a label plate, rescue-red RCS quads at its corners, the ladder down the front. The
    cabin: a cut cone of white panels (ring seams, rivets on their lips), the rescue-red livery,
    two lamp-lit windows, the square front hatch (hinged, an arrow at it), the docking ring
    on top with its lamps, a dish antenna on its boom. A nozzle bell under it, and four legs
    (the far pair darker) with their struts and footpads. legs 0 extended (in flight),
    1 touching, 2 compressed, 3 settled."""
    w, h = 76, 72
    s = Spr(w, h)
    cx = w // 2
    extend = {0: 0, 1: 0, 2: -3, 3: -2}[legs]
    # the far legs, behind, darker
    for (hx, fx) in ((26, 14), (50, 62)):
        n = max(abs(fx - hx), abs(66 + extend - 44))
        for k in range(n + 1):
            s.set(hx + (fx - hx) * k // n, 44 + (66 + extend - 44) * k // n, 'panel', 1)
    nozzle(s, cx, 50, 9, 4)
    # the descent stage: three faces of foil blankets
    faces = ((8, cx - 14, 4), (cx - 14, cx + 14, 3), (cx + 14, w - 8, 2))   # (x from, to, light)
    for y in range(32, 52):
        inset = max(0, 3 - (y - 32)) + max(0, (y - 48))
        for x in range(8 + inset, w - 8 - inset):
            fi = 0 if x < cx - 14 else 1 if x < cx + 14 else 2
            fa, fb, base = faces[fi]
            bw = 7 if fi != 1 else 9
            col, row = (x - fa) // bw, (y - 34) // 8
            black = fi == 1 and row == 1 and 2 <= col <= 2
            name = 'iron' if black else ('brass', 'brass_warm', 'brass_cool')[(col + row + fi) % 3]
            t = base - (1 if black else 0)
            bx, by = (x - fa) % bw, (y - 34) % 8
            if y in (32, 33):
                name, t = 'hull', (5, 4, 3)[fi] if y == 32 else (4, 3, 2)[fi]       # the deck's lit edge
            elif y >= 50:
                name, t = 'iron', 1 if y == 51 else 2                               # the underside
            elif x == fa and fi:
                t = max(0, base - 2)                                                # the corner between faces
            elif by == 0 or bx == 0:
                t = max(0, t - 2)                                                   # a seam between blankets
            elif by == 1:
                t = min(5, t + 1)                                                   # the blanket's lit fold
            else:
                c = (col * 5 + row * 3 + fi) % 4                                    # its one crease
                if bx - 2 == (by - 2) * (1 if c % 2 else -1) + (1 if c % 2 else bw - 3) and 2 <= by <= 5:
                    t = max(0, t - 1)
                elif bx - 3 == (by - 2) * (1 if c % 2 else -1) + (1 if c % 2 else bw - 3) and 2 <= by <= 5:
                    t = min(5, t + 1)
            s.set(x, y, name, t)
    # the nap flag on the front, a label plate, the RCS quads, the ladder
    s.rect(cx - 10, 35, 7, 5, 'dusk', 3); s.hline(cx - 10, 35, 7, 'dusk', 4); s.hline(cx - 10, 39, 7, 'dusk', 2)
    s.set(cx - 9, 36, 'lamp', 5); s.set(cx - 8, 36, 'lamp', 4); s.set(cx - 8, 37, 'lamp', 4)
    placard(s, cx + 4, 35, 7)
    for (qx, lit) in ((4, True), (w - 9, False)):
        s.rect(qx, 36, 5, 5, 'berry', 3 if lit else 2)
        s.hline(qx, 36, 5, 'berry', 4 if lit else 3); s.hline(qx, 40, 5, 'berry', 1)
        s.set(qx + (0 if lit else 4), 38, 'iron', 0)                               # the side nozzle
        s.set(qx + 2, 35, 'iron', 3); s.set(qx + 2, 41, 'iron', 1)                 # up and down
    for y in range(32, 50):                                                         # the ladder's rails and rungs
        s.set(cx - 3, y, 'iron', 3); s.set(cx + 2, y, 'iron', 1)
        if y % 3 == 1:
            s.hline(cx - 2, y, 4, 'iron', 4 if y < 41 else 3)
    # the cabin: a cut cone of white panels, its livery, windows, hatch, ring, dish
    cone_skin(s, cx, 4, 32, 12, 20, 'hull', 123, rings=(12, 22), seams=(-5, 6, -7))
    for x in range(cx - 19, cx + 19):                                               # the rescue-red livery
        if s.has(x, 28):
            t = 4 if x < cx - 6 else 3 if x < cx + 8 else 2
            s.set(x, 28, 'berry', t); s.set(x, 29, 'berry', max(1, t - 1))
    for (wx, lit) in ((cx - 11, True), (cx + 4, False)):                            # two lamp-lit windows
        for y in range(13, 19):
            for x in range(wx, wx + 7):
                edge = x in (wx, wx + 6) or y in (13, 18)
                if edge:
                    s.set(x, y, 'iron', (4 if (y == 13 or x == wx) else 1) if lit else (3 if (y == 13 or x == wx) else 0))
                else:
                    s.set(x, y, 'lamp', 2 if y < 16 else 3)
        s.hline(wx + 1, 14, 2, 'lamp', 5)                                            # the glint
        seat(s, wx, 13, 7, 6)
    hinged_hatch(s, cx - 4, 20, 8, 8)                                               # the front hatch
    seat(s, cx - 4, 20, 8, 8)
    stencil(s, cx + 5, 21, '<', 'berry', 2)
    vrail(s, cx - 7, 20, 28); vrail(s, cx + 9, 20, 28)                              # handrails at the hatch
    connectors(s, cx + 2, 43, ('brass', 'sky')); seat(s, cx + 2, 43, 7, 5)          # the service connectors
    s.rect(cx - 4, 0, 8, 4, 'iron', 2); s.hline(cx - 4, 0, 8, 'iron', 4)            # the docking ring on top
    s.hline(cx - 3, 1, 2, 'neon_cyan', 4); s.hline(cx + 1, 1, 2, 'neon_cyan', 4)
    s.hline(cx - 4, 3, 8, 'brass', 3)
    s.vline(cx + 13, 0, 8, 'iron', 4); s.vline(cx + 14, 0, 8, 'iron', 2)            # the dish on its boom
    for (x, y, t) in ((cx + 10, 1, 4), (cx + 11, 0, 5), (cx + 12, 0, 4), (cx + 13, 0, 3), (cx + 14, 0, 3),
                      (cx + 15, 0, 2), (cx + 16, 1, 2), (cx + 11, 1, 3), (cx + 15, 1, 1)):
        s.set(x, y, 'hull', t)
    s.rect(cx - 17, 23, 4, 3, 'panel', 3); s.hline(cx - 17, 23, 4, 'panel', 4)       # a docking light
    s.hline(cx - 16, 25, 2, 'lamp', 5)
    # the near legs, in front: the leg, its struts to the stage's foot, the footpad
    for (hx, hy, fx, side) in ((16, 44, 4, -1), (60, 44, 72, 1)):
        lit = side < 0
        fy = 68 + extend
        n = max(abs(fx - hx), abs(fy - hy))
        for k in range(n + 1):
            x, y = hx + (fx - hx) * k // n, hy + (fy - hy) * k // n
            s.set(x, y, 'panel', 4 if lit else 2)
            s.set(x - side, y, 'panel', 2 if lit else 1)
        kx, ky = hx + (fx - hx) * 3 // 5, hy + (fy - hy) * 3 // 5                   # the knee
        sx_ = cx + side * 9
        m = max(abs(kx - sx_), abs(ky - 51), 1)
        for k in range(m + 1):                                                       # the shock strut, its piston
            x, y = sx_ + (kx - sx_) * k // m, 51 + (ky - 51) * k // m
            rod = k > m // 2 + (2 if legs >= 2 else 0)
            s.set(x, y, 'brass' if rod else 'iron', (4 if lit else 3) if rod else (3 if lit else 2))
            s.set(x, y + 1, 'brass' if rod else 'iron', 2 if rod else 1)
        for d in range(-3, 4):                                                       # the round footpad
            s.set(fx + d, fy, 'panel', 4 if d < 0 else 3 if d < 2 else 2)
            s.set(fx + d, fy + 1, 'panel', 1)
        s.hline(fx - 1, fy - 1, 3, 'panel', 3); s.set(fx - 1, fy - 1, 'panel', 4)
        s.set(hx, hy, 'brass', 4 if lit else 3)                                      # the hinge
    return s


def lander_shadow() -> Canvas:
    """The lander's shadow on the regolith: airless, so hard and nearly black (house style:
    the moon's shadows three tones down, to tone 0), a flattened octagon with the legs'
    stubs, thrown down and to the right."""
    w, h = 52, 9
    s = Spr(w, h)
    for y in range(h):
        for x in range(w):
            d = ((x - w / 2 + 0.5) / (w / 2 - 6)) ** 2 + ((y - h / 2 + 0.5) / (h / 2)) ** 2
            if d <= 1:
                s.set(x, y, 'regolith', 0)
    for (x0, y0) in ((0, 6), (w - 7, 6)):
        s.hline(x0, y0, 7, 'regolith', 0)
    return s.tile()


def planet() -> Canvas:
    """The home world seen from far off: a lit crescent of ocean and land with a thin air
    line, its night side lost in the dark (a light source would be wrong: it is lit)."""
    r = 26
    s = Spr(2 * r + 2, 2 * r + 2)
    for y in range(2 * r + 2):
        for x in range(2 * r + 2):
            dx, dy = x - r - 1, y - r - 1
            d = dx * dx + dy * dy
            if d > r * r:
                continue
            lit = -(dx + dy) / (r * 1.4)
            if lit < -0.15:
                continue                                                     # the night side
            land = smooth_noise(x, y, 9, 131) > 0.58
            name = 'leaf' if land else 'water'
            t = 4 if lit > 0.55 else 3 if lit > 0.2 else 2
            if d > (r - 1.5) ** 2:
                name, t = 'sky', 4                                           # the thin air line
            s.set(x, y, name, t)
    return s.render(outline=False)


def rcs_sheet() -> tuple:
    """A thruster's puff: three frames of a small white jet and its spray, then nothing."""
    frames = []
    for k, n in enumerate((2, 4, 5)):
        p = Spr(10, 6)
        for i in range(n):
            p.set(i, 2, 'snow', 5 - i // 2)
            p.set(i, 3, 'snow', 4 - i // 2)
        if k == 2:
            for (x, y) in ((6, 1), (7, 4), (8, 2)):
                p.set(x, y, 'snow', 2)
        frames.append(p.render(outline=False))
    frames.append(Canvas(2, 2))
    box_w, box_h = 12, 8
    sheet = Canvas(box_w, box_h * len(frames))
    for i, f in enumerate(frames):
        sheet.paste(f, 0, i * box_h)
    return sheet, box_w, box_h, len(frames)


def sheet_of(sprites: list, outline: bool = True, anchor: str = 'bottom') -> tuple:
    """Frames of one size stacked top to bottom, centred, anchored at their bottom (a thing
    standing) or their top (a flame hanging from its nozzle)."""
    canv = [sp.render(outline) if isinstance(sp, Spr) else sp for sp in sprites]
    bw = max(c.w for c in canv)
    bh = max(c.h for c in canv)
    sheet = Canvas(bw, bh * len(canv))
    for i, c in enumerate(canv):
        sheet.paste(c, (bw - c.w) // 2, i * bh + (bh - c.h if anchor == 'bottom' else 0))
    return sheet, bw, bh, len(canv)


def rows(cv: Canvas) -> tuple:
    """The first and last rows with anything drawn (rendered px)."""
    box = cv.img.getbbox()
    return (box[1], box[3] - 1) if box else (0, 0)


def save(cv: Canvas, name: str, scale: int = SCALE):
    cv.save(os.path.join(OUT, f'{name}.png'), scale)


def main():
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        os.remove(os.path.join(OUT, old))
    meta = {}

    def put(name, cv, scale=SCALE, **extra):
        save(cv, name, scale)
        top, foot = rows(cv)
        meta[name] = {'w': cv.w, 'h': cv.h, 'top': top, 'foot': foot, **extra}

    put('booster', booster().render(), cx=(RW + 20) // 2 + 1)
    for legs in range(4):
        put(f'upper{legs}', upper_stage(legs).render(), cx=(RW + 30) // 2 + 1, skirt=STAGE2_H - 6 + 1)
    sh, bw, bh, n = sheet_of([flame(1, f) for f in range(6)], outline=False, anchor='top')
    put('flame-booster', sh, frame=[bw, bh], frames=n)
    sh, bw, bh, n = sheet_of([flame(2, f, small=True) for f in range(6)], outline=False, anchor='top')
    put('flame-upper', sh, frame=[bw, bh], frames=n)
    for kind in ('steam', 'smoke', 'fire'):
        sh, box, n = puff_sheet(kind, seed={'steam': 140, 'smoke': 150, 'fire': 160}[kind])
        put(f'puff-{kind}', sh, frame=[box, box], frames=n)
    sh, bw, bh, n = rcs_sheet()
    put('rcs', sh, frame=[bw, bh], frames=n)
    put('tower', gantry_tower().render())
    for level in (0, 1):
        sh, bw, bh, n = sheet_of([gantry_arm(f, level) for f in range(4)])
        put(f'arm{level}', sh, frame=[bw, bh], frames=n)
    put('mount', pad_mount().render(), cx=43)
    put('skyline', skyline())
    put('deck', pad_deck())
    put('sky', sky_column(), scale=SKY_SCALE)
    put('stars', stars())
    put('clouds-low', clouds(171))
    put('clouds-high', clouds(181, 60))
    put('station', station_underside(), cx=181, port=96)
    put('moon-ground', moon_ground())
    put('lumen-pad', lumen_pad().render(), cx=49)
    for legs in range(4):
        put(f'lander{legs}', lander(legs).render(), cx=39)
    sh, bw, bh, n = sheet_of([flame(0, f, small=True) for f in range(6)], outline=False, anchor='top')
    put('flame-lander', sh, frame=[bw, bh], frames=n)
    put('planet', planet())
    put('lander-shadow', lander_shadow())

    preview = os.environ.get('ROCKET_PREVIEW')
    if preview:
        os.makedirs(preview, exist_ok=True)
        names = list(meta)
        from PIL import Image
        imgs = [Image.open(os.path.join(OUT, f'{k}.png')) for k in names]
        W = 1400
        x, y, rh = 0, 0, 0
        place = []
        for im in imgs:
            if x + im.width > W:
                x, y, rh = 0, y + rh + 8, 0
            place.append((x, y))
            x += im.width + 8
            rh = max(rh, im.height)
        sheet = Image.new('RGBA', (W, y + rh), (60, 56, 80, 255))
        for im, p in zip(imgs, place):
            sheet.alpha_composite(im.convert('RGBA'), p)
        sheet.save(os.path.join(preview, 'rocket-sheet.png'))

    ident = lambda k: 'rocket' + ''.join(p.capitalize() for p in k.replace('-', '_').split('_'))  # noqa: E731
    sizes = [
        '// Generated by scripts/art/rocket.py. Do not edit by hand.',
        '/* eslint-disable */',
        '/** The rocket and lander journeys\' pictures (scripts/art/rocket.py), in art px: their size, top',
        ' *  and foot (the first and last rows drawn), cx (the centre column), skirt (an upper stage: the row',
        ' *  that sits on the booster), port (the station: the row a vehicle docks against), and for a sheet',
        ' *  the box of one frame and how many frames are stacked top to bottom. Pictures: rocket-assets.ts. */',
        'export type RocketSize = { w: number; h: number; top: number; foot: number; cx?: number; skirt?: number; port?: number; frame?: readonly [number, number]; frames?: number };',
        'export const rocketSizes = {',
        *[f"  '{k}': {{ " + ', '.join(f'{a}: {json.dumps(b)}' for a, b in v.items()) + ' },' for k, v in meta.items()],
        '} as const satisfies Record<string, RocketSize>;',
        'export type RocketArtKey = keyof typeof rocketSizes;',
        '/** The rocket\'s diameter and stage heights, the gantry\'s height, the looping tiles\' width, the sky',
        ' *  column\'s height and the pictures\' scales. */',
        f'export const ROCKET = {json.dumps({"diameter": RW, "stage1": STAGE1_H, "stage2": STAGE2_H, "gantry": GANTRY_H, "tile": TILE_W, "skyH": SKY_COL_H, "skyScale": SKY_SCALE, "scale": SCALE})} as const;',
        '',
    ]
    lines = [
        '// Generated by scripts/art/rocket.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        "import { rocketSizes, type RocketArtKey, type RocketSize } from './rocket-sizes';",
        *[f"import {ident(k)} from '@/assets/journeys/rocket/{k}.png';" for k in meta],
        'export type RocketArt = RocketSize & { source: ImageSourcePropType };',
        '/** Each picture with its size and anchors (rocket-sizes.ts). */',
        'export const rocketArt = {',
        *[f"  '{k}': {{ ...rocketSizes['{k}'], source: {ident(k)} }}," for k in meta],
        '} as const satisfies Record<RocketArtKey, RocketArt>;',
        "export { ROCKET, type RocketArtKey } from './rocket-sizes';",
        '',
    ]
    targets = []
    for name, text in (('rocket-sizes.ts', sizes), ('rocket-assets.ts', lines)):
        target = os.path.join(ROOT, 'lib', name)
        with open(target, 'w') as f:
            f.write('\n'.join(text))
        targets.append(target)
    import subprocess
    subprocess.run(['npx', 'oxfmt', '--write', *targets], cwd=ROOT, check=False, capture_output=True)
    print('ok rocket', len(meta), 'pictures')


if __name__ == '__main__':
    main()
