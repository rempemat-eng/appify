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
left edge is closed), light from the upper left, metal as plates with seams, rivets and a
sheen, glows as light sources with no outline. Until #121's house_palette.py is on main,
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
def plates(s: Spr, x0, y0, w, h, fam, seed, pw=10, ph=8, round_x=None, other=None, rivets=True,
           round_y=None, other_share=0.1, mask=None, stagger=True):
    """Machined plates (house style, metal): each plate a sibling, the odd one in a second
    family (primer), seams as a dark line with a lit line under it, rivets as a lit head
    over its shadow, a slow sheen lighter at the upper left. `round_x` (cx, r) shades the
    plates as a cylinder seen from the side: lit on the left third, dark at the right;
    `round_y` (cy, r) as one lying down: lit along its top. `mask(x, y)` limits the plating to
    a shape."""
    for y in range(y0, y0 + h):
        row = (y - y0) // ph
        off = (row % 2) * (pw // 2) if stagger else 0   # (aligned: machined plates, never a bond)
        for x in range(x0, x0 + w):
            if mask and not mask(x, y):
                continue
            col = (x - x0 + off) // pw
            n = noise2(col, row, seed)
            name = sib(fam, n)
            if other and noise2(col, row, seed + 7) > 1 - other_share:
                name = sib(other, noise2(col, row, seed + 8))
            tone = 3
            if round_y:
                cy, r = round_y
                k = (y - (cy - r)) / max(1, 2 * r)   # 0 at the top .. 1 at the bottom
                tone = 4 if k < 0.2 else 3 if k < 0.55 else 2 if k < 0.85 else 1
                if 0.1 < k < 0.17 and (x - x0 + off) % pw not in (0, 1):
                    tone = 5 if noise2(x // 3, y // 2, seed + 3) > 0.55 else 4
            if round_x:
                cx, r = round_x
                k = (x - (cx - r)) / max(1, 2 * r)   # 0 at the left edge .. 1 at the right
                tone = 4 if k < 0.16 else 3 if k < 0.55 else 2 if k < 0.86 else 1
                if 0.08 < k < 0.14 and (y - y0) % ph not in (0, 1):
                    tone = 5 if noise2(x // 2, y // 3, seed + 3) > 0.55 else 4   # the sheen band
            jit = noise2(col, row, seed + 11)
            if jit > 0.84:
                tone = min(5, tone + 1)            # the odd plate a tone off
            elif jit < 0.14:
                tone = max(0, tone - 1)
            py, pxx = (y - y0) % ph, (x - x0 + off) % pw
            if py == 0:
                tone = max(0, tone - 2)            # the seam
            elif py == 1:
                tone = min(5, tone + 1)            # its lit line
            elif pxx == 0 and not round_x:
                tone = max(0, tone - 2)
            elif pxx == 1 and not round_x:
                tone = min(5, tone + 1)
            elif pxx == 0 and round_x and noise2(col, row, seed + 1) > 0.35:
                tone = max(0, tone - 1)
            s.set(x, y, name, tone)
            if rivets and (py == 3 or (not stagger and py == ph - 2)) and pxx in (2, pw - 3) \
                    and noise2(x, y, seed + 5) > 0.25:
                # a steel rivet: its head lit, its shadow under it on the plate
                s.set(x, y, 'iron', 5 if tone >= 3 else 4)
                s.set(x, y + 1, name, max(0, tone - 2))


def hatch(s: Spr, x, y, w, h, fam='hull', lit=True):
    """A small access hatch set in the plating: a recessed frame (dark top and left), a lit
    lower lip, a bolt at each corner, a handle."""
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            t = 1 if (yy == y or xx == x) else 4 if (yy == y + h - 1 or xx == x + w - 1) else (3 if lit else 2)
            s.set(xx, yy, sib(fam, 0.5), t)
    for (bx, by) in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
        s.set(bx, by, 'iron', 3)
    if w > 5:
        s.hline(x + 2, y + h // 2, w - 4, 'iron', 2)


def decal(s: Spr, x, y, kind: str):
    """Small painted markings: a hazard tag, a warning triangle, a stencilled number, a
    status strip."""
    if kind == 'tag':
        s.rect(x, y, 4, 2, 'brass', 4); s.hline(x, y + 2, 4, 'brass', 2)
        s.set(x + 1, y, 'iron', 1)
    elif kind == 'warn':
        for k in range(3):
            s.hline(x + 2 - k, y + k, 1 + 2 * k, 'brass', 4 - (k == 2))
        s.set(x + 2, y + 1, 'iron', 0)
    elif kind == 'stencil':
        for k in range(4):
            s.set(x, y + k, 'iron', 1); s.set(x + 2, y + k, 'iron', 1)
        s.set(x + 1, y, 'iron', 1); s.set(x + 1, y + 3, 'iron', 1)
    elif kind == 'strip':
        s.hline(x, y, 5, 'berry', 4); s.hline(x, y + 1, 5, 'berry', 2)


def rail(s: Spr, x0, x1, y, fam='brass'):
    """A grab rail on stand-offs: the bar lit on top, its posts, their shadows."""
    s.hline(x0, y, x1 - x0, fam, 4)
    s.hline(x0, y + 1, x1 - x0, fam, 2)
    for x in range(x0, x1, 6):
        s.set(x, y + 2, 'iron', 2)


def band(s: Spr, x0, y0, w, h, fam, cx, r, seed, chevrons=None):
    """A painted livery band round a cylinder, lit like it; `chevrons` (fam2) paints hazard
    stripes in two families."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            k = (x - (cx - r)) / max(1, 2 * r)
            tone = 4 if k < 0.16 else 3 if k < 0.55 else 2 if k < 0.86 else 1
            name = fam
            if chevrons and ((x + (y - y0)) // 3) % 2:
                name = chevrons
            if y == y0:
                tone = min(5, tone + 1)
            if y == y0 + h - 1:
                tone = max(0, tone - 1)
            s.set(x, y, sib(name, noise2(x // 4, y, seed), 0.2), tone)


def cyl_tone(x, cx, r):
    k = (x - (cx - r)) / max(1, 2 * r)
    return 4 if k < 0.16 else 3 if k < 0.55 else 2 if k < 0.86 else 1


# --- the rocket -------------------------------------------------------------------------
RW = 32          # the rocket's diameter
STAGE1_H = 96    # the booster, from its engine bells' foot to its top
STAGE2_H = 68    # the upper stage with its crew capsule and nose


def booster() -> Spr:
    """The first stage, four storeys of it: white plates (the odd one in primer), a forward
    skirt in hazard-ochre and iron chevrons, the nap moon on its shoulder, a rescue-red
    livery band, a frost band where the cold tank sweats in the night air, a signal-blue roll
    pattern on the thrust section, a cable raceway with its clamps, access hatches and vent
    grilles, four swept fins (the near two in full, the far one edge-on), and two engine
    bells under a sooted heat shield with their turbopump plumbing."""
    w, h = RW + 20, STAGE1_H
    s = Spr(w, h)
    cx, r = w // 2, RW // 2
    x0 = cx - r
    body_top, body_bot = 7, h - 14
    plates(s, x0, body_top, RW, body_bot - body_top, 'hull', 11, pw=11, ph=10, round_x=(cx, r), other='panel',
           other_share=0.3)
    band(s, x0, 0, RW, 6, 'brass', cx, r, 12, chevrons='iron')                       # the forward skirt
    for x in range(x0, x0 + RW):
        s.set(x, 6, 'iron', 1)
        s.set(x, 7, 'hull', min(5, cyl_tone(x, cx, r) + 1))                           # its lit lip
    # the nap moon on the shoulder: a dusk crescent on a white roundel
    mx, my = cx - 6, 15
    for y in range(my - 4, my + 5):
        for x in range(mx - 4, mx + 5):
            d = (x - mx) ** 2 + (y - my) ** 2
            if d <= 16:
                s.set(x, y, 'hull', 5 if x + y < mx + my - 2 else 4)
            if d <= 9 and (x - mx - 2) ** 2 + (y - my + 1) ** 2 > 6:
                s.set(x, y, 'dusk', 3 if x < mx else 2)
    band(s, x0, 28, RW, 7, 'berry', cx, r, 13)                                      # the livery band
    for x in range(x0, x0 + RW):
        s.set(x, 35, 'hull', max(0, cyl_tone(x, cx, r) - 2))                          # the band's shadow
    # the frost band over the cold tank: snow siblings, crisp scalloped lower edge, sparkles in pairs
    for y in range(44, 54):
        for x in range(x0, x0 + RW):
            if y == 53 and (x // 3) % 2:
                continue
            t = cyl_tone(x, cx, r) + (1 if y < 46 else 0)
            s.set(x, y, sib('snow', noise2(x // 3, y // 2, 15), 0.35), min(5, t))
    for (fx, fy) in ((x0 + 4, 46), (x0 + 9, 50), (x0 + 15, 47), (x0 + 22, 51)):
        s.set(fx, fy, 'snow', 5); s.set(fx + 1, fy, 'snow', 5)
    # the roll pattern on the thrust section: quarters of signal blue and white
    for y in range(body_bot - 24, body_bot - 6):
        for x in range(x0, x0 + RW):
            q = ((x - x0) * 2 // RW + (y - (body_bot - 24)) // 9) % 2
            if q:
                s.set(x, y, sib('sky', noise2(x // 6, y // 9, 16), 0.2), cyl_tone(x, cx, r))
    # a cable raceway down the left third, clamped every half storey
    for y in range(9, body_bot - 2):
        s.set(cx - 10, y, 'panel', 4)
        s.set(cx - 9, y, 'panel', 2)
        if y % 16 == 0:
            s.set(cx - 11, y, 'iron', 2); s.set(cx - 8, y, 'iron', 1)
    for (hx, hy) in ((cx + 2, 12), (cx - 4, 38), (cx + 5, 58)):                     # access hatches, bolted
        s.rect(hx, hy, 6, 5, 'hull_cool', 2)
        s.hline(hx, hy, 6, 'hull_cool', 1)
        s.hline(hx, hy + 5, 6, 'hull', 4)
        s.set(hx + 1, hy + 1, 'hull', 4); s.set(hx + 4, hy + 3, 'hull_cool', 1)
    for k in range(3):                                                              # a vent grille
        s.hline(cx + 6, 38 + k * 2, 6, 'iron', 1)
        s.hline(cx + 6, 39 + k * 2, 6, 'hull', 2)
    for (dx, dy, kind) in ((3, 64, 'warn'), (-12, 60, 'tag'), (4, 18, 'strip'), (-2, 76, 'tag')):
        decal(s, cx + dx, dy, kind)                                                 # markings
    for (fx, fy) in ((cx - 6, 23), (cx + 9, 31), (cx - 3, 57), (cx + 8, 70), (cx - 13, 74), (cx + 10, 49), (cx - 13, 40)):
        s.set(fx, fy, 'brass', 4); s.set(fx + 1, fy, 'brass', 3)                    # brass fittings
        s.set(fx, fy + 1, 'brass', 2); s.set(fx + 1, fy + 1, 'brass', 1)
    for (tx, ty) in ((cx + 1, 52), (cx - 9, 14), (cx + 6, 78)):                    # signal-blue inspection tags
        s.rect(tx, ty, 3, 2, 'sky', 4); s.hline(tx, ty + 2, 3, 'sky', 1)
    for (lx, ly, g) in ((cx + 12, 9, 'glowflora'), (cx - 12, 66, 'neon_cyan')):
        s.set(lx, ly, g, 4); s.set(lx, ly + 1, g, 2)                               # status lamps
    for y in range(22, 27):                                                         # the stage number, stencilled
        s.set(cx + 4, y, 'iron', 1)
    s.set(cx + 3, 23, 'iron', 1)
    # the heat shield, sooted, and the plumbing between it and the bells
    s.rect(x0 - 1, body_bot, RW + 2, 4, 'iron', 2)
    s.hline(x0 - 1, body_bot, RW + 2, 'iron', 4)
    for x in range(x0 - 1, x0 + RW + 1):
        if noise2(x, 3, 17) > 0.6:
            s.set(x, body_bot + 2, 'iron', 1)
    for (px_, fam) in ((cx - 3, 'brass'), (cx + 2, 'brass')):
        s.vline(px_, body_bot + 4, 3, fam, 3)
    for bx in (cx - 8, cx + 3):                                                     # two bells, lit left
        for k in range(h - (body_bot + 4)):
            y = body_bot + 4 + k
            half = 2 + k * 4 // 9
            for x in range(bx - half, bx + half + 1):
                t = 4 if x == bx - half + 1 else 3 if x < bx else 2 if x < bx + half - 1 else 1
                s.set(x, y, sib('iron', noise2(x, 0, 18), 0.2), t)
            s.set(bx - half, y, 'brass', 2)                                         # a sooted copper lip
            if k % 3 == 1:
                for x in range(bx - half + 1, bx + half):
                    s.step(x, y, -1)                                                # the bell's cooling bands
        for x in range(bx - 6, bx + 7):
            s.set(x, h - 1, 'iron', 0)
    # fins: swept trapezoids, root 20 px along the body, tip 9, span 9, a lit leading edge
    for (side, fx) in ((-1, x0 - 1), (1, x0 + RW)):
        lit = side < 0
        for k in range(20):
            y = body_bot - 20 + k
            reach = min(9, 1 + k * 9 // 11)
            if k < 11 and reach < 1:
                continue
            for d in range(0, reach):
                x = fx + side * d
                t = (4 if lit else 2) if d < reach - 1 else (3 if lit else 1)
                if k == min(19, 11 + (d * 8) // 9) or (k > 11 and d == reach - 1 and k == 19):
                    t = 5 if lit else 3                                             # the leading edge
                if k == 19:
                    t = 2 if lit else 0
                s.set(x, y, sib('sky', noise2(d // 3, k // 4, 21), 0.25), t)
            s.set(fx, y, 'iron', 1 if lit else 0)                                    # the root fillet
    for k in range(16):                                                             # the far fin, edge-on
        s.set(cx + 1, body_bot - 16 + k, 'sky', 1 if k > 2 else 2)
    return s


def upper_stage(legs: int = 0) -> Spr:
    """The second stage and its crew capsule: plates under a signal-blue stripe, the capsule
    with its lit porthole (the companion's silhouette inside), a hazard-ochre hatch frame,
    RCS quads, the docking ring at the nose. `legs` 0 folded, 1 half out, 2 deployed,
    3 compressed (touchdown): the way back lands it on them."""
    w, h = RW + 30, STAGE2_H + 10
    s = Spr(w, h)
    cx, r = w // 2, RW // 2
    x0 = cx - r
    nose_h, cap_h = 14, 22
    body_top = nose_h + cap_h
    body_bot = STAGE2_H - 6
    # the docking ring and nose: a cut cone of plates, the ring at the very top
    for y in range(0, nose_h + cap_h):
        rr = 5 + (y * (r - 5)) // (nose_h + cap_h - 1)
        for x in range(cx - rr, cx + rr):
            name = sib('hull', noise2(x // 6, y // 7, 31), 0.3)
            t = cyl_tone(x, cx, rr)
            if y in (nose_h, nose_h + 1):
                t = max(0, t - 2) if y == nose_h else min(5, t + 1)
            s.set(x, y, name, t)
    for x in range(cx - 6, cx + 6):                                                 # the docking ring
        s.set(x, 0, 'iron', 3 if x < cx - 2 else 2)
        s.set(x, 1, 'iron', 2 if x < cx else 1)
        s.set(x, 2, 'brass', 4 if x < cx - 2 else 3 if x < cx + 2 else 2)
    for x in range(cx - 5, cx + 5, 2):
        s.set(x, 1, 'neon_cyan', 4)                                                 # its status lamps
    # the porthole: a recess, lamp-lit from inside, a small sleepy silhouette with ears
    pcx, pcy = cx - 3, nose_h + 9
    for y in range(pcy - 4, pcy + 5):
        for x in range(pcx - 4, pcx + 5):
            d = (x - pcx) ** 2 + (y - pcy) ** 2
            if d <= 16:
                s.set(x, y, 'lamp', 2 if y < pcy - 1 else 3 if y < pcy + 2 else 4)
            elif d <= 26:
                s.set(x, y, 'iron', 1 if (x > pcx or y > pcy) else 3)
    for (x, y) in ((pcx - 2, pcy), (pcx - 1, pcy), (pcx, pcy), (pcx + 1, pcy), (pcx + 2, pcy),
                   (pcx - 2, pcy + 1), (pcx + 2, pcy + 1), (pcx - 2, pcy - 1), (pcx + 2, pcy - 1),
                   (pcx - 1, pcy + 1), (pcx, pcy + 1), (pcx + 1, pcy + 1), (pcx - 1, pcy + 2), (pcx + 1, pcy + 2)):
        s.set(x, y + 1, 'iron', 1)                                                   # the companion's head and ears
    s.set(pcx - 2, pcy - 3, 'lamp', 5); s.set(pcx - 1, pcy - 3, 'lamp', 5)          # a glint on the glass
    # the hatch: a hazard-ochre frame with its handle, beside the porthole
    hx, hy = cx + 3, nose_h + 4
    s.rect(hx, hy, 7, 12, 'hull_cool', 2)
    for y in range(hy, hy + 12):
        s.set(hx, y, 'brass', 3 if (y // 2) % 2 else 1)
        s.set(hx + 6, y, 'brass', 2 if (y // 2) % 2 else 0)
    s.hline(hx, hy, 7, 'brass', 4)
    s.hline(hx, hy + 11, 7, 'brass', 1)
    s.set(hx + 4, hy + 6, 'iron', 3); s.set(hx + 4, hy + 7, 'iron', 1)
    # RCS quads at the capsule's shoulders
    for (qx, lit) in ((cx - r - 2, True), (cx + r, False)):
        s.rect(qx, body_top - 4, 3, 5, 'panel', 3 if lit else 1)
        s.set(qx + (0 if lit else 2), body_top - 2, 'iron', 0)
    # the stage body, its stripe and its plates
    plates(s, x0, body_top, RW, body_bot - body_top, 'hull', 33, pw=9, ph=8, round_x=(cx, r))
    band(s, x0, body_top + 3, RW, 4, 'sky', cx, r, 34)
    band(s, x0, body_bot - 6, RW, 2, 'berry', cx, r, 35)
    # its engine: one bell under a short skirt
    s.rect(x0 + 2, body_bot, RW - 4, 2, 'iron', 2)
    s.hline(x0 + 2, body_bot, RW - 4, 'iron', 3)
    for k in range(6):
        half = 2 + k // 2
        for x in range(cx - half, cx + half + 1):
            s.set(x, body_bot + 2 + k, 'iron', 3 if x < cx - half + 2 else 1 if x > cx + half - 2 else 2)
        s.set(cx - half, body_bot + 2 + k, 'brass', 1)
    # the landing legs: folded flat along the body, or swung out on their struts
    foot = STAGE2_H + 4 if legs == 2 else STAGE2_H + 2
    for side in (-1, 1):
        hinge_x = cx + side * (r - 1)
        hinge_y = body_bot - 18
        lit = side < 0
        if legs == 0:
            for y in range(hinge_y, body_bot + 2):
                s.set(hinge_x + side * 1, y, 'panel', 3 if lit else 1)
            s.set(hinge_x + side * 1, body_bot + 2, 'iron', 1)
            continue
        spread = {1: 7, 2: 13, 3: 14}[legs]
        fx, fy = hinge_x + side * spread, (body_bot + 4 if legs == 1 else foot if legs == 2 else foot - 2)
        n = max(abs(fx - hinge_x), abs(fy - hinge_y))
        for k in range(n + 1):
            x = hinge_x + (fx - hinge_x) * k // n
            y = hinge_y + (fy - hinge_y) * k // n
            s.set(x, y, 'panel', 4 if lit else 2)
            s.set(x + side, y, 'panel', 2 if lit else 1)
        # the strut from the skirt to the leg's knee (shorter when compressed)
        kx, ky = hinge_x + side * (spread * 2 // 3), hinge_y + (fy - hinge_y) * 2 // 3
        sx_, sy_ = cx + side * (r - 3), body_bot
        m = max(abs(kx - sx_), abs(ky - sy_), 1)
        for k in range(m + 1):
            s.set(sx_ + (kx - sx_) * k // m, sy_ + (ky - sy_) * k // m, 'iron', 3 if lit else 1)
        for d in range(-2, 3):                                                       # the footpad
            s.set(fx + d, fy, 'panel', 4 if d < 0 else 2)
            s.set(fx + d, fy + 1, 'panel', 1)
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
    """Halcyon seen from below and the side as a vehicle comes up to it: a long module of
    white plates with a rescue-red livery band, the docking port in the middle (a collar
    with hazard-ochre chevrons and a ring of cyan status lamps), a truss running off to
    both sides with radiator panels and the dark blue cells of a solar wing."""
    w, h = 360, 120
    s = Spr(w, h)
    cx = w // 2
    # the truss, both ways
    for x in range(0, w):
        for y in (30, 38):
            s.set(x, y, 'panel', 3 if y == 30 else 2)
        z = x % 10
        s.set(x, 31 + (z if z < 5 else 9 - z) * 6 // 5, 'panel_cool', 2)
    # a solar wing on each side: cells in a frame, a lit diagonal glint
    for (wx, ww) in ((6, 92), (w - 98, 92)):
        for y in range(8, 30):
            for x in range(wx, wx + ww):
                fr = (x - wx) % 12 == 0 or (y - 8) % 7 == 0
                name, tone = ('panel', 3) if fr else ('sky_cool', 1 if (x + y) % 9 else 2)
                if not fr and (x - wx) - (y - 8) * 2 in range(10, 13):
                    tone = 3                                               # the glint
                s.set(x, y, name, tone)
        for y in range(39, 52):                                            # radiator panels below the truss
            for x in range(wx + 20, wx + ww - 20):
                s.set(x, y, 'hull_cool', 4 if (x - wx) % 6 == 0 else 3 if y < 44 else 2)
    # the module: a cylinder lying along the truss, seen side on: plates lit along the top,
    # the odd one in panel primer, end rings, the livery band, portholes, hatches, rails,
    # stencils, an antenna mast and a sensor pod
    mx0, mx1 = cx - 70, cx + 70
    plates(s, mx0, 18, mx1 - mx0, 56, 'hull', 101, pw=10, ph=7, round_y=(46, 28), other='panel', other_share=0.24,
           stagger=False)
    for x in range(mx0 + 2, mx1 - 2):                                      # a cable run with its clamps
        s.set(x, 40, 'iron', 3 if x % 11 else 4)
        s.set(x, 41, 'iron', 1)
        if x % 11 == 0:
            s.set(x, 39, 'iron', 2); s.set(x, 42, 'iron', 1)
    for (qx, qy) in ((mx0 + 52, 20), (mx0 + 92, 22), (mx0 + 70, 58), (mx0 + 116, 30), (mx0 + 4, 26)):   # quilted blankets
        for y in range(qy, qy + 8):
            for x in range(qx, qx + 12):
                t = 4 if (x - qx) % 4 == 1 and (y - qy) % 4 == 1 else 3 if (x + y) % 4 else 2
                s.set(x, y, sib('snow', noise2(x // 4, y // 4, 105), 0.3), t)
    for x in (mx0, mx0 + 1, mx1 - 2, mx1 - 1):                              # the end rings
        for y in range(18, 74):
            s.set(x, y, 'panel', 3 if x < cx else 1)
    for x in range(mx0, mx1):                                              # the livery band
        for y in range(44, 49):
            s.set(x, y, sib('berry', noise2(x // 9, 0, 102), 0.2), 4 if y == 44 else 3 if y < 48 else 2)
    for (px_, lit) in ((mx0 + 12, True), (mx0 + 40, True), (mx1 - 34, False), (mx1 - 20, False)):   # portholes, lamp-lit
        for y in range(24, 34):
            for x in range(px_ - 1, px_ + 9):
                d = (x - px_ - 3.5) ** 2 + (y - 28.5) ** 2
                if d <= 12:
                    s.set(x, y, 'lamp', 2 if y < 28 else 3 if y < 30 else 4)
                elif d <= 20:
                    s.set(x, y, 'iron', 3 if (x < px_ + 3 and y < 29) else 1)
        s.set(px_ + 2, 26, 'lamp', 5)
    hatch(s, cx - 30, 52, 9, 12)
    hatch(s, cx + 22, 52, 9, 12, lit=False)
    hatch(s, mx0 + 26, 58, 6, 6)
    hatch(s, mx1 - 30, 57, 6, 7, lit=False)
    hatch(s, cx - 4, 22, 8, 6)
    for (gx, lit) in ((mx0 + 6, True), (cx - 14, True), (cx + 6, False), (mx1 - 16, False)):   # vent grilles
        for k in range(3):
            s.hline(gx, 56 + k * 2, 6, 'iron', 1 if lit else 0)
            s.hline(gx, 57 + k * 2, 6, 'hull', 3 if lit else 2)
    rail(s, mx0 + 10, mx0 + 40, 68)
    rail(s, mx1 - 44, mx1 - 12, 68)
    for x in range(mx0 + 2, mx1 - 2):                                      # a thin signal-blue stripe
        s.set(x, 50, 'sky', 3 if x < cx else 2)
    for k, x in enumerate(range(mx0 + 9, mx1 - 6, 17)):                    # bolts along the band, placards
        s.set(x, 46, 'iron', 4); s.set(x, 47, 'berry', 1)
        if k % 2 == 0:
            s.rect(x + 3, 34, 4, 3, 'snow', 4); s.hline(x + 3, 37, 4, 'snow', 1)
            s.set(x + 4, 35, 'iron', 1); s.set(x + 5, 35, 'iron', 1)
    for (lx, g) in ((mx0 + 8, 'glowflora'), (cx - 20, 'neon_cyan'), (cx + 34, 'glowflora'), (mx1 - 9, 'neon_pink')):
        s.set(lx, 51, g, 4); s.set(lx, 52, g, 2)                              # status lamps
    for (dx, dy, kind) in ((-62, 22, 'tag'), (-24, 30, 'strip'), (30, 24, 'stencil'), (34, 24, 'stencil'),
                           (58, 30, 'warn'), (-40, 60, 'tag')):
        decal(s, cx + dx, dy, kind)
    rail(s, mx0 + 6, mx0 + 34, 37)
    rail(s, mx1 - 46, mx1 - 8, 37)
    for (dx, kind) in ((-50, 'stencil'), (-45, 'stencil'), (-8, 'warn'), (14, 'tag'), (36, 'strip'), (52, 'tag')):
        decal(s, cx + dx, 66 if kind != 'warn' else 64, kind)
    for y in range(4, 18):                                                 # an antenna mast and its dish
        s.set(mx0 + 18, y, 'iron', 3); s.set(mx0 + 19, y, 'iron', 1)
    for (x, y, t) in ((mx0 + 14, 5, 4), (mx0 + 15, 4, 4), (mx0 + 16, 3, 4), (mx0 + 17, 3, 3), (mx0 + 18, 3, 3),
                      (mx0 + 19, 3, 2), (mx0 + 20, 4, 2), (mx0 + 21, 5, 1), (mx0 + 17, 4, 2), (mx0 + 18, 4, 2)):
        s.set(x, y, 'hull', t)
    s.set(mx0 + 18, 2, 'neon_cyan', 5)
    s.rect(mx1 - 30, 12, 10, 6, 'panel', 3)                                # a sensor pod on the top
    s.hline(mx1 - 30, 12, 10, 'panel', 4); s.hline(mx1 - 30, 17, 10, 'panel', 1)
    s.set(mx1 - 27, 14, 'glowflora', 4); s.set(mx1 - 24, 14, 'neon_pink', 3)
    # the docking port, hanging under the module's middle
    for y in range(74, 96):
        half = 16 if y < 80 else 12
        for x in range(cx - half, cx + half):
            tone = cyl_tone(x, cx, half)
            name = 'hull_cool'
            if y in range(80, 86):
                name = 'brass' if ((x + y) // 3) % 2 else 'iron'           # hazard chevrons on the collar
            s.set(x, y, name, tone)
    for x in range(cx - 12, cx + 12, 3):
        s.set(x, 92, 'neon_cyan', 4)                                         # the ring of status lamps
    s.hline(cx - 12, 95, 24, 'iron', 1)
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
    """The lander (Lumen's shuttle, the same craft drawn anew): a white cabin shaped like a
    cut cone with two lamp-lit windows and its hatch, on an eight-sided descent stage with a
    hazard-ochre band and rescue-red RCS quads, a dark engine bell, and four splayed legs
    with round footpads. legs 0 extended (in flight), 1 touching, 2 compressed, 3 settled."""
    w, h = 76, 72
    s = Spr(w, h)
    cx = w // 2
    # the legs behind first (the far pair, darker)
    extend = {0: 0, 1: 0, 2: -3, 3: -2}[legs]
    for (x0, y0, x1, y1) in ((26, 44, 14, 66 + extend), (50, 44, 62, 66 + extend)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            s.set(x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n, 'panel', 1)
    # the engine bell, sooted
    for k in range(9):
        half = 4 + k // 2
        for x in range(cx - half, cx + half + 1):
            s.set(x, 50 + k, 'iron', 3 if x < cx - half + 2 else 1 if x > cx + half - 2 else 2)
        s.set(cx - half, 50 + k, 'brass', 1)
    # the descent stage: an octagon in crinkled gold foil (brass siblings in 2 x 2 crinkles, each
    # facet lit by its side), a hazard-ochre band of stencilled panels, its rim lit
    for y in range(32, 52):
        inset = max(0, 3 - (y - 32)) + max(0, (y - 48))
        for x in range(8 + inset, w - 8 - inset):
            facet = 0 if x < cx - 14 else 1 if x < cx + 14 else 2
            base = (4, 3, 2)[facet]
            n = noise2(x // 2, y // 2, 121)
            t = base + (1 if n > 0.82 else -1 if n < 0.18 else 0)
            if noise2(x // 3, y, 126) > 0.93:
                t = max(0, base - 2)                                        # a crease in the foil
            name = sib('brass', noise2(x // 2 + 3, y // 2, 124), 0.34)
            if y in (32, 33):
                name, t = sib('hull', noise2(x // 6, 0, 125), 0.3), (5, 4, 3)[facet] if y == 32 else (4, 3, 2)[facet]
            if x in (cx - 14, cx + 14):
                t = max(0, base - 2)
            if y in (40, 41, 42):
                name = sib('hull', noise2(x // 5, 0, 122), 0.25)            # the panel band
                t = (4, 3, 2)[facet] if y != 42 else 1
            if y == 51:
                name, t = 'iron', 1
            s.set(x, y, name, max(0, min(5, t)))
    for (dx, kind) in ((-24, 'stencil'), (-20, 'stencil'), (-6, 'warn'), (8, 'tag'), (18, 'strip')):
        decal(s, cx + dx, 40 if kind != 'warn' else 39, kind)
    hatch(s, 12, 44, 6, 5)
    hatch(s, w - 18, 44, 6, 5, lit=False)
    for (x0_, lit) in ((cx - 22, True), (cx + 16, False)):                  # vent grilles on the stage
        for k in range(3):
            s.hline(x0_, 35 + k * 2, 5, 'iron', 1 if lit else 0)
    for (qx, lit) in ((4, True), (w - 9, False)):                           # rescue-red RCS quads
        s.rect(qx, 36, 5, 5, 'berry', 3 if lit else 2)
        s.hline(qx, 36, 5, 'berry', 4 if lit else 3)
        s.set(qx + (0 if lit else 4), 38, 'iron', 0)
    # the cabin: a cut cone of machined plates, lit on its left third, rails and an antenna
    def cone(x, y):
        return 4 <= y < 32 and abs(x - cx + 0.5) < 12 + (y - 4) * 8 // 28
    plates(s, cx - 20, 4, 40, 28, 'hull', 123, pw=8, ph=7, round_x=(cx, 17), other='panel', other_share=0.12, mask=cone)
    rail(s, cx - 15, cx - 5, 18, 'brass')
    rail(s, cx + 6, cx + 15, 18, 'brass')
    for x in range(cx - 18, cx + 18):                                       # the cabin's rescue-red livery
        if cone(x, 28):
            s.set(x, 28, sib('berry', noise2(x // 5, 0, 127), 0.2), 4 if x < cx - 6 else 3 if x < cx + 8 else 2)
            s.set(x, 29, 'berry', 2 if x < cx + 8 else 1)
    for (lx, g) in ((cx - 9, 'glowflora'), (cx + 12, 'neon_cyan')):
        s.set(lx, 24, g, 4); s.set(lx, 25, g, 2)                               # status lamps
    for y in range(-2, 5):
        s.set(cx + 9, y + 2, 'iron', 3)
    s.set(cx + 9, 1, 'neon_pink', 4)
    s.rect(cx - 4, 0, 8, 4, 'iron', 2)                                       # the docking ring on top
    s.hline(cx - 4, 0, 8, 'iron', 4)
    s.set(cx - 2, 1, 'neon_cyan', 4); s.set(cx + 1, 1, 'neon_cyan', 4)
    for (wx, lit) in ((cx - 10, True), (cx + 3, False)):                     # two lamp-lit windows
        for y in range(10, 16):
            for x in range(wx, wx + 7):
                edge = x in (wx, wx + 6) or y in (10, 15)
                s.set(x, y, 'iron' if edge else 'lamp', (3 if lit else 1) if edge else (3 if y > 12 else 2))
        s.set(wx + 1, 11, 'lamp', 5)
    s.rect(cx - 3, 20, 7, 11, 'hull_cool', 2)                               # the hatch and its frame
    s.vline(cx - 3, 20, 11, 'brass', 3); s.vline(cx + 3, 20, 11, 'brass', 1)
    s.hline(cx - 3, 20, 7, 'brass', 4)
    s.set(cx + 1, 25, 'iron', 3)
    for y in range(31, 50, 3):                                               # its ladder down the stage
        s.hline(cx - 2, y, 5, 'iron', 3 if y < 40 else 2)
    # the near legs, in front
    for (x0, y0, x1, y1, lit) in ((16, 48, 4, 68 + extend, True), (60, 48, 72, 68 + extend, False)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            x, y = x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n
            s.set(x, y, 'panel', 4 if lit else 2)
            s.set(x + (1 if lit else -1), y, 'panel', 2 if lit else 1)
        for d in range(-3, 4):                                               # the round footpad
            s.set(x1 + d, y1, 'panel', 4 if d < 0 else 2)
            s.set(x1 + d, y1 + 1, 'panel', 1)
        # the shock strut, shorter when compressed
        top_y = y0 - 6 if legs < 2 else y0 - 4
        for y in range(top_y, y0):
            s.set(x0 + (2 if lit else -2), y, 'iron', 3 if lit else 1)
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
