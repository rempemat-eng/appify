"""The people who live in the world's zones (world-atlas.md, "A world that feels
alive", L6): one or two residents per place, each dressed for it, drawn in the shared
rules (light from the upper left, material shading, a tinted outline) at the scale of
the zone props. Two walking frames each facing the viewer, and a walk pair each for
east, west and away (B7), so a route can turn someone to their work when they pause;
the atlas moves them along short routes.

Writes assets/residents/<id>-<frame>.png and <id>-<east|west|back>-<frame>.png, lib/resident-sprites.ts (data) and
lib/resident-assets.ts (images).
Run: python3 scripts/art/residents.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, oval  # noqa: E402
import style  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCALE = 4
W, H, PAD = 20, 28, 3


class Shifted:
    """Draws onto a canvas one pixel in from its top-left, leaving room for the outline."""

    def __init__(self, cv: Canvas, dx: int = 1, dy: int = 1):
        self.cv, self.dx, self.dy = cv, dx, dy

    def set(self, x, y, c):
        self.cv.set(x + self.dx, y + self.dy, c)

    def hline(self, x, y, w, c):
        self.cv.hline(x + self.dx, y + self.dy, w, c)

    def vline(self, x, y, h, c):
        self.cv.vline(x + self.dx, y + self.dy, h, c)

SKIN = {
    'a': ('#F2C9A0', '#D9A77E'), 'b': ('#D9A070', '#B87E52'), 'c': ('#A86E48', '#8A5434'),
    'd': ('#7A4E32', '#5E3A24'), 'e': ('#E8B890', '#C8946C'),
}
HAIR = {'dark': '#2A1E18', 'brown': '#5E3A24', 'red': '#A8482A', 'grey': '#B8B4AE', 'black': '#141016',
        'blond': '#E2BC5E'}


def shade(c: str, k: float) -> str:
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    f = (lambda v: max(0, min(255, int(v * k)))) if k < 1 else (lambda v: min(255, int(v + (255 - v) * (k - 1))))
    return '#%02X%02X%02X' % (f(r), f(g), f(b))


def person(look: dict, frame: int) -> Canvas:
    """A resident, 20 x 28 (drawn one pixel in), facing the viewer three-quarters to the right: legs in
    trousers or a skirt, a torso in their working clothes with an apron or a trim, arms
    swinging with the step, a head with a face and hair or a hat."""
    canvas = Canvas(W, H, pad=PAD)
    cv = Shifted(canvas)
    skin, skin_dark = SKIN[look.get('skin', 'a')]
    top = look['top']
    legs = look.get('legs', '#3E3A50')
    cx = 8
    # legs: apart on frame 0, together on frame 1
    stride = 2 if frame == 0 else 0
    for (lx, front) in ((cx - 2 - stride // 2, False), (cx + 1 + stride // 2, True)):
        for y in range(18, 24):
            cv.set(lx, y, legs if front else shade(legs, 0.75)); cv.set(lx + 1, y, shade(legs, 0.75))
        cv.hline(lx, 24, 2, look.get('shoes', '#2A2026'))
    if look.get('skirt'):
        for y in range(16, 21):
            hw = 3 + (y - 16) // 2
            for x in range(cx - hw, cx + hw):
                cv.set(x, y, look['skirt'] if x < cx + 1 else shade(look['skirt'], 0.8))
    # the torso
    for y in range(10, 18):
        for x in range(cx - 4, cx + 4):
            c = shade(top, 1.15) if x < cx - 2 else top if x < cx + 2 else shade(top, 0.78)
            cv.set(x, y, c)
    if look.get('apron'):
        for y in range(12, 19):
            for x in range(cx - 2, cx + 3):
                cv.set(x, y, look['apron'] if x < cx + 2 else shade(look['apron'], 0.85))
    if look.get('trim'):
        cv.hline(cx - 4, 17, 8, look['trim']); cv.vline(cx, 10, 7, look['trim'])
    # arms swing opposite the legs
    sw = 1 if frame == 0 else -1
    for (ax, d) in ((cx - 5, sw), (cx + 4, -sw)):
        for y in range(11, 16):
            cv.set(ax, y + (d if y > 13 else 0), shade(top, 0.9) if ax < cx else shade(top, 0.7))
        cv.set(ax, 16 + d, skin)
    if look.get('carry'):
        kind, col = look['carry']
        if kind == 'basket':
            for (x, y) in oval(cx + 6, 16, 2.5, 2):
                cv.set(x, y, col)
        elif kind == 'plant':
            cv.set(cx + 5, 15, '#8A5A3A'); cv.set(cx + 6, 15, '#8A5A3A')
            for (x, y) in disc(cx + 5.5, 13, 1.8):
                cv.set(x, y, col)
        elif kind == 'lantern':
            cv.set(cx + 5, 17, '#2A2026'); cv.set(cx + 5, 18, col); cv.set(cx + 6, 18, shade(col, 0.8))
        elif kind == 'tray':
            cv.hline(cx + 3, 14, 5, col)
        elif kind == 'broom':  # a street broom held across the body, its head on the ground
            for t in range(13):
                cv.set(cx + 6 - t // 4, 12 + t, '#8A6A44' if t < 10 else col)
            cv.hline(cx + 1, 25, 5, col)
        elif kind == 'board':  # a clipboard
            for y in range(13, 17):
                cv.hline(cx + 4, y, 3, col if y > 13 else '#8A6A44')
    # the head
    for (x, y) in disc(cx, 6, 3.6):
        cv.set(x, y, skin if x < cx + 2 else skin_dark)
    cv.set(cx + 1, 6, '#2A1E18'); cv.set(cx + 3, 6, '#2A1E18')  # eyes, looking right
    cv.set(cx + 2, 8, shade(skin_dark, 0.85))
    hair = HAIR[look.get('hair', 'dark')]
    for (x, y) in disc(cx - 1, 4, 3.2):
        if y <= 4 or x < cx - 2:
            cv.set(x, y, hair)
    hat = look.get('hat')
    if hat:
        kind, col = hat
        if kind == 'straw':
            cv.hline(cx - 5, 3, 11, col); cv.hline(cx - 3, 1, 6, col); cv.hline(cx - 3, 2, 6, shade(col, 0.85))
        elif kind == 'cap':
            cv.hline(cx - 3, 2, 6, col); cv.hline(cx - 3, 3, 8, shade(col, 0.8))
        elif kind == 'wide':
            cv.hline(cx - 6, 3, 13, shade(col, 0.8)); cv.hline(cx - 3, 0, 6, col); cv.hline(cx - 3, 1, 6, col)
            cv.hline(cx - 3, 2, 6, col)
        elif kind == 'goggles':
            cv.hline(cx - 3, 3, 7, '#5E3D2E'); cv.set(cx + 1, 3, '#C99A3C'); cv.set(cx + 3, 3, '#C99A3C')
        elif kind == 'wrap':
            for (x, y) in disc(cx - 1, 4, 3.6):
                if y <= 5:
                    cv.set(x, y, col if x < cx else shade(col, 0.8))
            cv.vline(cx - 4, 5, 6, shade(col, 0.8))
        elif kind == 'hood':
            for (x, y) in disc(cx - 1, 5, 4.2):
                if not ((x - cx) ** 2 + (y - 6) ** 2 < 7 and x > cx - 2):
                    cv.set(x, y, col if x < cx else shade(col, 0.75))
        elif kind == 'bowler':
            cv.hline(cx - 4, 3, 9, col); cv.hline(cx - 2, 1, 5, col); cv.hline(cx - 2, 2, 5, shade(col, 0.8))
        elif kind == 'helmet':
            for (x, y) in disc(cx, 5, 4.6):
                if (x - cx) ** 2 + (y - 6) ** 2 >= 8 or y < 3:
                    cv.set(x, y, '#DCE2EC' if x < cx else '#B8C0D2')
    return canvas


def _lit(c: str, x: int, mid: float) -> str:
    """Light from the upper left: the left of a form is lit, the right in shade."""
    return shade(c, 1.15) if x <= mid - 2 else c if x <= mid + 1 else shade(c, 0.78)


def _carried(cv, kind: str, col: str, hx: int, hy: int, d: int):
    """What a resident carries, at the hand (hx, hy), the far side toward d."""
    if kind == 'basket':
        # wicker body with woven rows, a lit rim and a handle arching over the hand
        for (x, y) in oval(hx + d * 1 + 0.5, hy + 2, 2.6, 1.9):
            c = col if (x + y) % 2 else shade(col, 0.82)
            cv.set(x, y, shade(c, 1.12) if x <= hx else shade(c, 0.85))
        cv.hline(min(hx - 1, hx + d * 3), hy + 1, 4, shade(col, 1.2))
        cv.set(hx, hy, shade(col, 0.7)); cv.set(hx + d * 2, hy, shade(col, 0.7)); cv.set(hx + d, hy - 1, shade(col, 0.7))
        if col.upper() == '#C89C6A':
            cv.set(hx + d, hy + 1, '#C2453A'); cv.set(hx + d * 2, hy + 1, '#7EA05A')  # something picked
    elif kind == 'plant':
        cv.set(hx, hy + 1, '#A8683E'); cv.set(hx + d, hy + 1, '#8A5434'); cv.set(hx, hy + 2, '#8A5434'); cv.set(hx + d, hy + 2, '#6E4026')
        for (x, y) in disc(hx + d * 0.5 + 0.5, hy - 1, 1.9):
            cv.set(x, y, shade(col, 1.18) if x <= hx and y <= hy - 1 else shade(col, 0.82) if y >= hy else col)
    elif kind == 'lantern':
        cv.set(hx, hy + 1, '#2A2026')
        cv.set(hx, hy + 2, col); cv.set(hx + d, hy + 2, shade(col, 0.82))
        cv.set(hx, hy + 3, shade(col, 0.9)); cv.set(hx + d, hy + 3, shade(col, 0.75))
        cv.hline(min(hx, hx + d), hy + 4, 2, '#3E3238')
    elif kind == 'tray':
        cv.hline(min(hx - d, hx + d * 3), hy, 5, col)
        cv.hline(min(hx - d, hx + d * 3), hy + 1, 5, shade(col, 0.72))
        cv.set(hx + d, hy - 1, shade(col, 1.15)); cv.set(hx + d * 2, hy - 1, shade(col, 0.95))
    elif kind == 'broom':  # a street broom, its handle in the hand, its head on the ground ahead
        for t in range(10):
            cv.set(hx + d * (t // 3), hy - 3 + t, '#8A6A44' if t < 8 else col)
        cv.hline(min(hx + d * 2, hx + d * 5), hy + 7, 4, col)
    elif kind == 'board':  # a clipboard held flat
        for y in range(hy - 1, hy + 3):
            cv.hline(min(hx, hx + d * 2), y, 3, col if y > hy - 1 else '#8A6A44')


def person_side(look: dict, frame: int, d: int) -> Canvas:
    """A resident seen from the side, walking toward d (+1 east, -1 west), in the same
    20 x 28 box, scale and light as the front frames: the near leg forward on frame 0
    and passing on frame 1, the near arm swinging against it, the face in profile
    (eye, nose, ear) under hair or a hat seen from the side. The left of every form is
    lit whichever way they walk, so the west frames are drawn, not mirrored."""
    canvas = Canvas(W, H, pad=PAD)
    cv = Shifted(canvas)
    skin, skin_dark = SKIN[look.get('skin', 'a')]
    top = look['top']
    legs = look.get('legs', '#3E3A50')
    shoes = look.get('shoes', '#2A2026')
    bx = 9 if d > 0 else 8
    F = lambda o: bx + d * o  # noqa: E731  a column o pixels ahead of the body's centre
    tone = lambda c, x: _lit(c, x, bx)  # noqa: E731

    def leg(foot: int, lift: int, far: bool):
        for y in range(18, 24 - lift):
            o = round(foot * (y - 17) / 6)
            for k in (0, 1):
                x = F(o) + k - (1 if d < 0 else 0)
                c = tone(legs, x)
                cv.set(x, y, shade(c, 0.72) if far else c)
        o = foot
        toe = F(o + 1)
        heel = F(o) - (1 if d < 0 else 0)
        y = 24 - lift
        for x in range(min(heel, toe), max(heel, toe) + 1):
            cv.set(x, y, shade(shoes, 0.8) if far else shoes)
        cv.set(toe, y - 1, shade(shoes, 1.4) if not far else shoes)

    # the far leg behind, then the near leg in front
    if frame == 0:
        leg(-2, 0, True); leg(2, 0, False)
    else:
        leg(0, 1, True); leg(0, 0, False)
    if look.get('skirt'):
        sk = look['skirt']
        for y in range(16, 21):
            hw = 2 + (y - 16) // 2
            for x in range(bx - hw - (1 if y >= 18 else 0), bx + hw + 1):
                cv.set(x, y, tone(sk, x))
        cv.hline(bx - 4, 20, 8, shade(sk, 0.7))
    # the far arm swings forward on frame 0, its hand just ahead of the chest
    if frame == 0 and not look.get('carry'):
        cv.set(F(3), 14, shade(top, 0.6)); cv.set(F(3), 15, skin_dark)
    # the torso: back straight, chest a pixel forward
    for y in range(10, 18):
        for x in range(bx - 2, bx + 3):
            cv.set(x, y, tone(top, x))
    for y in (12, 13):
        cv.set(F(3), y, tone(top, F(3)))
    cv.set(F(-2), 10, shade(tone(top, F(-2)), 0.92))
    if look.get('apron'):
        ap = look['apron']
        for y in range(12, 19):
            for o in (1, 2, 3) if y >= 13 else (1, 2):
                cv.set(F(o), y, tone(ap, F(o)))
        cv.set(F(-3), 13, shade(ap, 0.8)); cv.set(F(-3), 14, shade(ap, 0.8))  # the bow at the back
        cv.set(F(0), 11, shade(ap, 0.85))  # the neck strap
    if look.get('trim'):
        tr = look['trim']
        cv.hline(bx - 2, 17, 5, tr); cv.vline(F(2), 10, 7, tr)
    # the near arm: sleeve from the shoulder, swinging against the near leg
    carry = look.get('carry')
    reach = (1 if carry else (-2 if frame == 0 else 0))
    hand = None
    for y in range(11, 17):
        o = round(reach * (y - 11) / 5)
        x = F(o)
        if y < 16:
            cv.set(x, y, shade(tone(top, x), 0.84))
        else:
            cv.set(x, y, skin)
            hand = (x, y)
    cv.set(F(-1 if reach <= 0 else 0), 11, shade(tone(top, bx), 0.92))  # the shoulder's roundness
    if carry:
        kind, col = carry
        hx, hy = hand
        if kind == 'tray':
            # carried level in front, both hands under it
            _carried(cv, kind, col, F(3), 14, d)
            cv.set(F(3), 15, skin)
        elif kind == 'plant':
            _carried(cv, kind, col, F(2), 13, d)
        else:
            _carried(cv, kind, col, hx, hy, d)
    # the head in profile
    hx = bx + d * 0.6 + 0.5
    for (x, y) in disc(hx, 6, 3.5):
        cv.set(x, y, skin if x <= bx else skin_dark)
    cv.set(F(4), 7, skin if d < 0 else skin_dark)  # the nose
    cv.set(F(2), 6, '#2A1E18')  # the eye
    cv.set(F(3), 8, shade(skin_dark, 0.82))  # the mouth
    cv.set(bx, 9, skin_dark); cv.set(bx - d, 9, shade(skin_dark, 0.9))  # the neck
    hair = HAIR[look.get('hair', 'dark')]
    for (x, y) in disc(hx - d * 0.8, 4.6, 3.3):
        if y <= 3 or (x - bx) * d <= -1:
            cv.set(x, y, hair if x <= bx else shade(hair, 0.8))
    cv.set(F(-3), 8, shade(hair, 0.8))  # the nape
    cv.set(F(0), 6, shade(skin_dark, 0.9)); cv.set(F(0), 7, skin_dark)  # the ear
    hat = look.get('hat')
    if hat:
        kind, col = hat
        lo = lambda o: min(F(o), F(-o))  # noqa: E731
        if kind == 'straw':
            cv.hline(bx - 5, 3, 11, col); cv.hline(lo(2) if d > 0 else F(2), 1, 6, col)
            cv.hline(bx - 2, 2, 5, shade(col, 0.85)); cv.hline(bx - 2, 2, 2, shade(col, 1.1))
            cv.set(F(-2), 2, '#8A5A3A'); cv.set(F(-1), 2, '#8A5A3A')  # the band
            cv.set(bx - 5, 3, shade(col, 1.12)); cv.set(bx + 5, 3, shade(col, 0.8))
        elif kind == 'cap':
            for x in range(bx - 3, bx + 3):
                cv.set(x, 2, tone(col, x)); cv.set(x, 3, tone(col, x))
            cv.set(F(-3), 3, shade(col, 0.85))
            cv.hline(min(F(3), F(5)), 4, 3, shade(col, 0.7))  # the peak, forward
        elif kind == 'wide':
            cv.hline(bx - 6, 3, 13, shade(col, 0.8)); cv.hline(bx - 6, 3, 3, col)
            for y in (0, 1, 2):
                for x in range(bx - 3, bx + 3):
                    cv.set(x, y, tone(col, x))
            cv.hline(bx - 3, 2, 6, shade(col, 0.62))  # the band
        elif kind == 'goggles':
            cv.hline(bx - 3, 3, 7, '#5E3D2E')
            cv.set(F(2), 3, '#C99A3C'); cv.set(F(3), 3, '#C99A3C'); cv.set(F(2), 2, '#F2D88A')
        elif kind == 'wrap':
            for (x, y) in disc(hx - d * 0.8, 4.4, 3.7):
                if y <= 4 or ((x - bx) * d <= -1 and y <= 7):
                    cv.set(x, y, tone(col, x))
            cv.vline(F(-4), 5, 6, shade(col, 0.78)); cv.vline(F(-3), 8, 3, shade(col, 0.9))
        elif kind == 'hood':
            for (x, y) in disc(hx - d * 0.5, 5.4, 4.3):
                if (x - bx) * d <= 1 or y <= 2:
                    cv.set(x, y, col if x <= bx else shade(col, 0.75))
            cv.vline(F(2), 3, 6, shade(col, 0.62))  # the hood's opening round the face
        elif kind == 'bowler':
            cv.hline(bx - 4, 3, 9, col)
            for y in (1, 2):
                for x in range(bx - 2, bx + 3):
                    cv.set(x, y, tone(col, x))
            cv.set(bx - 2, 1, shade(col, 1.6))
        elif kind == 'helmet':
            for (x, y) in disc(hx, 4.8, 4.4):
                if y <= 4:
                    cv.set(x, y, '#DCE2EC' if x <= bx else '#B8C0D2')
            cv.hline(min(F(2), F(5)), 5, 4, '#B8C0D2')  # the brim, forward
            cv.set(bx - 2, 1, '#F7F9FC')
    return canvas


def person_back(look: dict, frame: int) -> Canvas:
    """A resident seen from behind, walking away, in the same box, scale and light as the
    front frames: legs and heels with the step, the back of the clothes (apron strings
    tied at the waist, a collar), arms swinging, the back of the head under its hair or
    hat. What they carry shows at their side."""
    canvas = Canvas(W, H, pad=PAD)
    cv = Shifted(canvas)
    skin, skin_dark = SKIN[look.get('skin', 'a')]
    top = look['top']
    legs = look.get('legs', '#3E3A50')
    shoes = look.get('shoes', '#2A2026')
    cx = 8
    tone = lambda c, x: _lit(c, x, cx - 1)  # noqa: E731
    stride = 2 if frame == 0 else 0
    # on frame 0 the right leg is the one stepping away (heel lifted), on frame 1 they pass
    for (lx, lift) in ((cx - 2 - stride // 2, 0), (cx + 1 + stride // 2, 1 if frame == 0 else 0)):
        for y in range(18, 24 - lift):
            cv.set(lx, y, tone(legs, lx)); cv.set(lx + 1, y, shade(legs, 0.75))
        cv.hline(lx, 24 - lift, 2, shoes)
        cv.set(lx, 24 - lift, shade(shoes, 1.35))  # the heel catching the light
    if look.get('skirt'):
        sk = look['skirt']
        for y in range(16, 21):
            hw = 3 + (y - 16) // 2
            for x in range(cx - hw, cx + hw):
                cv.set(x, y, tone(sk, x))
        cv.set(cx - 1, 18, shade(sk, 0.8)); cv.set(cx - 1, 19, shade(sk, 0.8))  # a fold
    carry = look.get('carry')
    if carry and carry[0] == 'tray':
        # held out in front: its ends show either side of the body
        cv.hline(cx - 6, 13, 13, carry[1]); cv.hline(cx - 6, 14, 13, shade(carry[1], 0.72))
    for y in range(10, 18):
        for x in range(cx - 4, cx + 4):
            cv.set(x, y, tone(top, x))
    cv.vline(cx - 1, 11, 6, shade(tone(top, cx - 1), 0.9))  # the back seam
    cv.hline(cx - 2, 10, 4, shade(top, 0.8))  # the collar
    if look.get('apron'):
        ap = look['apron']
        cv.hline(cx - 4, 14, 8, ap)
        cv.set(cx - 2, 15, ap); cv.set(cx, 15, shade(ap, 0.85)); cv.set(cx - 1, 15, shade(ap, 0.7))  # the bow
        cv.set(cx - 2, 16, shade(ap, 0.9)); cv.set(cx, 16, shade(ap, 0.8))
        cv.set(cx - 3, 10, ap); cv.set(cx + 2, 10, shade(ap, 0.85))  # the straps
        cv.set(cx - 3, 11, ap); cv.set(cx + 2, 11, shade(ap, 0.85))
    if look.get('trim'):
        cv.hline(cx - 4, 17, 8, look['trim'])
    sw = 1 if frame == 0 else -1
    for (ax, dd) in ((cx - 5, -sw), (cx + 4, sw)):
        for y in range(11, 16):
            cv.set(ax, y + (dd if y > 13 else 0), shade(top, 0.9) if ax < cx else shade(top, 0.7))
        cv.set(ax, 16 + dd, skin if ax < cx else skin_dark)
    if carry:
        kind, col = carry
        if kind == 'basket':
            _carried(cv, kind, col, cx + 5, 15 + sw, 1)
        elif kind == 'lantern':
            _carried(cv, kind, col, cx + 4, 16 + sw, 1)
        elif kind == 'plant':
            # cradled in front: the leaves show over the right shoulder
            for (x, y) in disc(cx + 3.5, 9.5, 1.8):
                cv.set(x, y, shade(col, 0.85) if x > cx + 3 else col)
    # the back of the head: hair over almost all of it, ears and the nape below
    hair = HAIR[look.get('hair', 'dark')]
    for (x, y) in disc(cx, 6, 3.6):
        cv.set(x, y, skin if x < cx else skin_dark)
    for (x, y) in disc(cx, 5.6, 3.6):
        if y <= 7:
            cv.set(x, y, hair if x < cx - 1 else shade(hair, 0.82))
    cv.set(cx - 2, 4, shade(hair, 1.25)); cv.set(cx - 1, 3, shade(hair, 1.25))  # the light on the crown
    cv.set(cx - 4, 6, skin); cv.set(cx + 3, 6, skin_dark)  # the ears
    cv.set(cx - 1, 9, skin_dark); cv.set(cx, 9, skin_dark)
    hat = look.get('hat')
    if hat:
        kind, col = hat
        if kind == 'straw':
            cv.hline(cx - 5, 3, 11, col); cv.hline(cx - 3, 1, 6, col); cv.hline(cx - 3, 2, 6, shade(col, 0.85))
            cv.hline(cx - 3, 2, 6, '#8A5A3A'); cv.set(cx - 5, 3, shade(col, 1.12))
        elif kind == 'cap':
            cv.hline(cx - 3, 2, 6, col); cv.hline(cx - 3, 3, 7, shade(col, 0.8))
            cv.set(cx - 1, 4, shade(col, 0.6)); cv.set(cx, 4, shade(col, 0.6))  # the strap at the back
        elif kind == 'wide':
            cv.hline(cx - 6, 3, 13, shade(col, 0.8)); cv.hline(cx - 3, 0, 6, col); cv.hline(cx - 3, 1, 6, col)
            cv.hline(cx - 3, 2, 6, shade(col, 0.62))
        elif kind == 'goggles':
            cv.hline(cx - 4, 4, 8, '#5E3D2E'); cv.set(cx - 1, 4, '#C99A3C')  # the buckle on the strap
        elif kind == 'wrap':
            for (x, y) in disc(cx - 0.5, 4.6, 3.8):
                if y <= 6:
                    cv.set(x, y, tone(col, x))
            cv.vline(cx - 1, 6, 5, shade(col, 0.78)); cv.vline(cx, 7, 3, shade(col, 0.68))  # the tail
        elif kind == 'hood':
            for (x, y) in disc(cx - 0.5, 5.4, 4.3):
                cv.set(x, y, col if x < cx - 1 else shade(col, 0.75))
            cv.vline(cx - 1, 3, 6, shade(col, 0.85))  # the seam
        elif kind == 'bowler':
            cv.hline(cx - 4, 3, 9, col); cv.hline(cx - 2, 1, 5, col); cv.hline(cx - 2, 2, 5, shade(col, 0.8))
        elif kind == 'helmet':
            for (x, y) in disc(cx, 5, 4.6):
                if y <= 5:
                    cv.set(x, y, '#DCE2EC' if x < cx else '#B8C0D2')
            cv.hline(cx - 3, 5, 6, '#9AA2B6')  # the harness at the back
    return canvas


FACINGS = {'east': lambda look, f: person_side(look, f, 1), 'west': lambda look, f: person_side(look, f, -1),
           'back': person_back}


# Who lives where, and what they wear (zone ids from scripts/art/zones.py).
RESIDENTS = {
    'gardener': {'zone': 'town', 'skin': 'b', 'top': '#5E8A62', 'apron': '#C8A06A', 'hat': ('straw', '#E2BC5E'),
                 'carry': ('basket', '#C89C6A')},
    'baker': {'zone': 'town', 'skin': 'a', 'top': '#E8DCC8', 'apron': '#F7F2E8', 'hair': 'red', 'legs': '#5E4A3A',
              'carry': ('tray', '#C8803A')},
    'fisher': {'zone': 'harbour', 'skin': 'c', 'top': '#E8C04A', 'legs': '#3E5468', 'hat': ('cap', '#3E5468')},
    'keeper': {'zone': 'harbour', 'skin': 'a', 'top': '#3E4A6A', 'hair': 'grey', 'trim': '#E8D8B8',
               'carry': ('lantern', '#FFC766')},
    'steward': {'zone': 'hearthold', 'skin': 'd', 'top': '#6A4A8A', 'trim': '#E6BC5C', 'hair': 'black'},
    'tinkerer': {'zone': 'junction', 'skin': 'e', 'top': '#6E4A2E', 'apron': '#3E2A1E', 'hat': ('goggles', ''),
                 'hair': 'brown'},
    'boatwoman': {'zone': 'canal', 'skin': 'b', 'top': '#2C5A44', 'skirt': '#6E2C24', 'hat': ('cap', '#1E3E30'),
                  'legs': '#2A2026'},
    'cowhand': {'zone': 'gulch', 'skin': 'c', 'top': '#A8482A', 'legs': '#3E4A6A', 'hat': ('wide', '#8A6040'),
                'trim': '#C99466'},
    'saloon': {'zone': 'gulch', 'skin': 'a', 'top': '#E8DCC8', 'trim': '#5E3A24', 'hat': ('bowler', '#2A2026'),
               'legs': '#2A2026'},
    'trader': {'zone': 'oasis', 'skin': 'd', 'top': '#E2D2B0', 'skirt': '#C8B48A', 'hat': ('wrap', '#3E6A8A')},
    # the prospector by the old mine's landing, a lamp in hand for the drift (S5)
    'prospector': {'zone': 'gulch', 'skin': 'b', 'top': '#7A5A3A', 'legs': '#3E4A6A', 'hat': ('wide', '#6A5040'),
                   'carry': ('lantern', '#FFC766')},
    'smith': {'zone': 'caldera', 'skin': 'c', 'top': '#3E3A44', 'apron': '#6E4A2E', 'hair': 'black'},
    'attendant': {'zone': 'springs', 'skin': 'a', 'top': '#E8E2D8', 'trim': '#C2621E', 'hair': 'dark',
                  'carry': ('tray', '#F2EEE6')},
    'vendor': {'zone': 'neon', 'skin': 'e', 'top': '#2A2640', 'trim': '#E8429A', 'hat': ('hood', '#3B3657')},
    'courier': {'zone': 'neon', 'skin': 'd', 'top': '#1FB5D0', 'legs': '#1C192B', 'hat': ('cap', '#1C192B')},
    'porter': {'zone': 'skyport', 'skin': 'b', 'top': '#DCE2EC', 'trim': '#1FB5D0', 'legs': '#5C6680',
               'hat': ('cap', '#5C6680')},
    # the city's new quarters (N1, 19 Oct)
    'seller': {'zone': 'market', 'skin': 'c', 'top': '#C8463A', 'apron': '#F2ECDE', 'hat': ('wrap', '#2A2640'),
               'carry': ('tray', '#FFC766')},
    # the city at work (N3, 19 Oct): a stallholder in the gap by her stall, the plaza's
    # sweeper, the car park's attendant, the noodle cook by his stall
    'stallholder': {'zone': 'market', 'skin': 'b', 'top': '#2E5A40', 'apron': '#E8E2D2', 'hair': 'black',
                    'carry': ('basket', '#C89C6A')},
    'sweeper': {'zone': 'plaza', 'skin': 'd', 'top': '#E8962A', 'trim': '#F2ECDE', 'legs': '#2C3E4C',
                'hat': ('cap', '#2C3E4C'), 'carry': ('broom', '#C8B48A')},
    'parker': {'zone': 'waterfront', 'skin': 'a', 'top': '#2A4068', 'trim': '#FFC766', 'legs': '#1C192B',
               'hat': ('cap', '#FFC766'), 'carry': ('board', '#E8ECF4')},
    'cook': {'zone': 'neon', 'skin': 'c', 'top': '#F2EEE6', 'apron': '#C8463A', 'legs': '#2A2640',
             'hat': ('wrap', '#F2EEE6'), 'carry': ('tray', '#C8803A')},
    'docker': {'zone': 'docks', 'skin': 'd', 'top': '#E8962A', 'legs': '#2C3E4C', 'hat': ('helmet', '#F2ECDE')},
    'stroller': {'zone': 'waterfront', 'skin': 'a', 'top': '#3E566A', 'trim': '#6FE6F2', 'hair': 'grey',
                 'legs': '#1C192B'},
    'farmer': {'zone': 'halt', 'skin': 'c', 'top': '#4A6A8A', 'apron': '#3E5468', 'hat': ('straw', '#E2BC5E'),
               'legs': '#5E4A3A'},
    'hiker': {'zone': 'ridge', 'skin': 'a', 'top': '#C2453A', 'legs': '#3E3A50', 'hat': ('cap', '#2E5A40'),
              'trim': '#E8D8B8'},
    'forager': {'zone': 'woodland', 'skin': 'd', 'top': '#6A7A3A', 'skirt': '#5E3D2E', 'hair': 'black',
                'carry': ('basket', '#A5764C')},
    'picnicker': {'zone': 'park', 'skin': 'e', 'top': '#E8A0BC', 'skirt': '#F2EEE6', 'hair': 'blond',
                  'carry': ('basket', '#C89C6A')},
    'miller': {'zone': 'riverside', 'skin': 'd', 'top': '#8A7A5E', 'apron': '#F2EEE6', 'legs': '#5E4A3A',
               'hat': ('cap', '#D8D0BE')},
    'angler': {'zone': 'riverside', 'skin': 'b', 'top': '#5A7A4A', 'legs': '#3E4A3A', 'hat': ('wide', '#7A6A4A')},
    'botanist': {'zone': 'station', 'skin': 'a', 'top': '#B8C2D6', 'trim': '#22B5A0', 'hair': 'blond',
                 'carry': ('plant', '#557A45')},
    # in Halcyon's lounge, under the long windows (Lumen's walkable rooms are all roofed
    # now, so nobody walks in the open there; review 19 Oct 14:20)
    'stargazer': {'zone': 'station', 'skin': 'e', 'top': '#3E3A6A', 'trim': '#9AD2FF', 'legs': '#2A2838',
                  'hair': 'black'},
    # the Frostline Highlands and the Tidebloom Isles (18 Oct)
    'warden': {'zone': 'saddle', 'skin': 'b', 'top': '#B83A32', 'legs': '#3E3A50', 'hat': ('cap', '#E8DCC8'),
               'carry': ('lantern', '#FFC766')},
    'skater': {'zone': 'snowmelt', 'skin': 'a', 'top': '#3E6AA8', 'trim': '#F7F2E8', 'legs': '#2A2838',
               'hat': ('hood', '#F7F2E8')},
    'ferryman': {'zone': 'landing', 'skin': 'c', 'top': '#F2EEE6', 'trim': '#3E6AA8', 'legs': '#3E5468',
                 'hat': ('cap', '#3E6AA8')},
    'naturalist': {'zone': 'rainforest', 'skin': 'd', 'top': '#7A8A4A', 'legs': '#5E4A3A', 'hat': ('wide', '#C8B48A'),
                   'carry': ('plant', '#4A8A44')},
    'beachcomber': {'zone': 'cove', 'skin': 'e', 'top': '#E8A0BC', 'skirt': '#F2EEE6', 'hair': 'dark',
                    'carry': ('basket', '#C89C6A')},
}


def main():
    out = os.path.join(ROOT, 'assets', 'residents')
    os.makedirs(out, exist_ok=True)
    for old in os.listdir(out):
        os.remove(os.path.join(out, old))
    entries, facing_entries, imports, sizes = [], [], [], {}
    ident = lambda s: ''.join(p.capitalize() for p in s.replace('-', '_').split('_'))  # noqa: E731
    for rid, look in RESIDENTS.items():
        frames = []
        for f in (0, 1):
            sp = style.finalize(person(look, f), keep_size=True, name=f'{rid}-{f}')
            sp.save(os.path.join(out, f'{rid}-{f}.png'), SCALE)
            name = f'resident{ident(rid)}{f}'
            imports.append(f"import {name} from '@/assets/residents/{rid}-{f}.png';")
            frames.append(name)
        entries.append(f"  {rid}: [{', '.join(frames)}],")
        sizes[rid] = (sp.w, sp.h)
        sides = []
        for facing, draw in FACINGS.items():
            names = []
            for f in (0, 1):
                fp = style.finalize(draw(look, f), keep_size=True, name=f'{rid}-{facing}-{f}')
                assert (fp.w, fp.h) == sizes[rid], f'{rid}-{facing}-{f}: box differs from the front frames'
                fp.save(os.path.join(out, f'{rid}-{facing}-{f}.png'), SCALE)
                name = f'resident{ident(rid)}{facing.capitalize()}{f}'
                imports.append(f"import {name} from '@/assets/residents/{rid}-{facing}-{f}.png';")
                names.append(name)
            sides.append(f"{facing}: [{', '.join(names)}]")
        facing_entries.append(f"  {rid}: {{ {', '.join(sides)} }},")
    data = [
        '// Generated by scripts/art/residents.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ZoneId } from './zone-maps';",
        '',
        '/** The residents of each zone and their sprite size in art pixels (images: resident-assets.ts). */',
        'export const residentSprites: Record<string, { zone: ZoneId; w: number; h: number }> = {',
        *[f"  {rid}: {{ zone: {json.dumps(look['zone'])}, w: {sizes[rid][0]}, h: {sizes[rid][1]} }}," for rid, look in RESIDENTS.items()],
        '};',
        '',
    ]
    images = [
        '// Generated by scripts/art/residents.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        *imports,
        '',
        '/** Two walking frames for each resident. */',
        'export const residentFrames: Record<string, readonly ImageSourcePropType[]> = {',
        *entries,
        '};',
        '',
        '/**',
        ' * Walk pairs for the other three ways a resident can face: east and west in profile',
        ' * (each drawn, not mirrored, so the light stays upper left) and back, walking away.',
        ' * Same box and anchor as the front frames, so a route can swap them freely.',
        ' */',
        'export const residentFacingFrames: Record<',
        '  string,',
        '  { east: readonly ImageSourcePropType[]; west: readonly ImageSourcePropType[]; back: readonly ImageSourcePropType[] }',
        '> = {',
        *facing_entries,
        '};',
        '',
    ]
    paths = [os.path.join(ROOT, 'lib', 'resident-sprites.ts'), os.path.join(ROOT, 'lib', 'resident-assets.ts')]
    for path, body in zip(paths, (data, images)):
        with open(path, 'w') as f:
            f.write('\n'.join(body))
    subprocess.run(['npx', 'oxfmt', '--write', *paths], cwd=ROOT, check=True, capture_output=True)
    if os.environ.get('ZONE_PREVIEW'):
        from PIL import Image
        keys = ['0', '1'] + [f'{k}-{f}' for k in FACINGS for f in (0, 1)]
        ims = [Image.open(os.path.join(out, f'{rid}-{k}.png')) for rid in RESIDENTS for k in keys]
        sheet = Image.new('RGBA', (sum(i.width + 8 for i in ims), max(i.height for i in ims)), (200, 190, 170, 255))
        x = 0
        for i in ims:
            sheet.alpha_composite(i, (x, 0)); x += i.width + 8
        sheet.save(os.path.join(os.environ['ZONE_PREVIEW'], 'residents.png'))
    print('ok residents', len(RESIDENTS))


if __name__ == '__main__':
    main()
