"""A zone's deck drawn from its walk (docs/vision/two-level-walk.md, "Drawing order").

A zone function returns its deck as the pixels of the ground it stands over (its foot),
its height and its connectors. This draws two transparent pictures the size of the zone:

- deck.png: the deck raised by its height, lit from the upper left. The surface (timber
  planks or steel grating), a railing along its back and front edges (open where a stair
  or lift lands), the front face (the deck's thickness) and the posts down to the street.
  The renderer sorts it by the deck's front foot among the street's props, so anything on
  the street behind it is covered and the companion's outline shows there.
- deck-shadow.png: the street under the deck one step darker and the deck's hard shadow
  falling down and to the right of it, drawn on the ground under every prop.

Claude A owns this file. Zones choose the material with deck['material'].
"""
from __future__ import annotations

from materials import INK, MATERIALS
from pixel import Canvas

WOOD = MATERIALS['wood']      # dark .. light
SLATE = MATERIALS['slate']
IRON = MATERIALS['iron']

FACE = 4            # the deck's thickness on screen, px
RAIL = 5            # a railing's height above the surface, px
POST_EVERY = 24     # posts under the front edge, px apart
RAIL_POST_EVERY = 6
OPEN_NEAR = 6       # railing left open this far round a connector's top, px
UNDER = (16, 14, 24, 70)      # the street under the deck (one step darker)
SHADOW = (16, 14, 24, 110)    # the deck's cast shadow (down and to the right)
SHADOW_OFFSET = (3, 3)


def _ramps(material: str):
    if material == 'steel':
        return {'surface': SLATE, 'frame': IRON}
    return {'surface': WOOD, 'frame': WOOD}


def _surface_px(material: str, x: int, y: int, ramp) -> str:
    """The deck's floor at foot point (x, y): planks running along x with staggered
    joints for timber; a grating of small dark holes for steel."""
    if material == 'steel':
        if x % 3 == 1 and y % 3 == 1:
            return ramp[0]
        return ramp[1] if (x // 3 + y // 3) % 2 else ramp[2]
    row = y // 3
    if y % 3 == 2:
        return ramp[2]                       # the gap between planks
    joint = (row * 11) % 16
    if (x - joint) % 16 == 0:
        return ramp[1]                       # a plank's end
    return ramp[4] if (row * 7 + (x - joint) // 16) % 5 == 0 else ramp[3]


def paint(deck: dict, w: int, h: int) -> tuple[Canvas, Canvas]:
    """The deck and its shadow, each a w x h transparent canvas in the zone's pixels."""
    foot = set(deck['walk'])
    height = int(deck['height'])
    material = deck.get('material', 'timber')
    ramps = _ramps(material)
    sr, fr = ramps['surface'], ramps['frame']
    tops = [tuple(c['top']) for c in deck.get('connectors', [])]

    def open_at(x: int, y: int) -> bool:
        return any(abs(x - tx) <= OPEN_NEAR and abs(y - ty) <= OPEN_NEAR for tx, ty in tops)

    shadow = Canvas(w, h)
    for (x, y) in foot:
        if 0 <= x < w and 0 <= y < h:
            shadow.set(x, y, UNDER[:3], UNDER[3])
    for (x, y) in foot:
        sx, sy = x + SHADOW_OFFSET[0], y + SHADOW_OFFSET[1]
        if (sx, sy) not in foot and 0 <= sx < w and 0 <= sy < h:
            shadow.set(sx, sy, SHADOW[:3], SHADOW[3])

    cv = Canvas(w, h)

    def put(x: int, y: int, c: str):
        if 0 <= x < w and 0 <= y < h:
            cv.set(x, y, c)

    # the posts first (behind the face), from under the front edge down to the street
    front = sorted((x, y) for (x, y) in foot if (x, y + 1) not in foot)
    ends = {min(x for x, _ in front), max(x for x, _ in front)} if front else set()
    for (x, y) in front:
        if x % POST_EVERY not in (0, 1, 2) and not any(abs(x - e) <= 1 for e in ends):
            continue
        for yy in range(y - height + FACE + 1, y + 1):
            put(x, yy, fr[1] if x % POST_EVERY == 0 or x == min(ends) else fr[0])
        put(x, y + 1, INK)
    # the surface, raised
    for (x, y) in foot:
        put(x, y - height, _surface_px(material, x, y, sr))
    # light from the upper left: the back and left edges catch it, the right edge falls off
    lit, dim = (sr[3], sr[1]) if material == 'steel' else (sr[4], sr[2])
    for (x, y) in foot:
        if (x, y - 1) not in foot or (x - 1, y) not in foot:
            put(x, y - height, lit)
        elif (x + 1, y) not in foot:
            put(x, y - height, dim)
    # the front face: the deck's thickness under its front edge, dark below
    for (x, y) in front:
        for k in range(1, FACE + 1):
            put(x, y - height + k, fr[2] if k == 1 else fr[1] if k < FACE else fr[0])
        put(x, y - height + FACE + 1, INK)
    # the outline round the raised silhouette
    for (x, y) in foot:
        for (dx, dy) in ((0, -1), (-1, 0), (1, 0)):
            if (x + dx, y + dy) not in foot:
                px, py = x + dx, y + dy - height
                if 0 <= px < w and 0 <= py < h and cv.get(px, py)[3] == 0:
                    put(px, py, INK)
    # railings along the back and the front edges, open where a stair or lift lands
    back = sorted((x, y) for (x, y) in foot if (x, y - 1) not in foot)
    for edge, light in ((back, fr[2]), (front, fr[3])):
        for (x, y) in edge:
            if open_at(x, y):
                continue
            top = y - height - RAIL
            put(x, top, light)
            put(x, top - 1, INK)
            if x % RAIL_POST_EVERY == 0:
                for yy in range(top + 1, y - height):
                    put(x, yy, fr[1])
    return cv, shadow
