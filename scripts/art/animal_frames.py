"""Animals that live (art-faults.md A9; Matt, 20 Oct: "animals lacking detail and not moving").

Every animal placed in a zone gets a small set of frames beside its still sprite, and a
kind that tells the renderer (components/atlas-animals.tsx) how it lives: a two to four
frame idle loop (a sheep lifts its head and chews, a heron preens, a cat washes and
flicks its tail) and, for the ones that move, a two-frame walk and a few spots near the
place the zone put it, where it wanders now and then (a sheep inside its fold, ducks on
their pond, the heron in the shallows, the cat on its corner). Decorative only: animals
never block the companion's walk more than their still sprite does, take no taps and
give nothing.

Frames are named `<sprite>_<role>` ('sheep_look', 'heron_preen', 'cat_w_step1'). An
animal facing the other way has its own drawn sprite with the same roles ('sheep_left'
for 'sheep'); where no one has drawn one, `relit_mirror` makes it: the shape mirrored,
the light kept on the upper left.

Claude A draws its own animals here and in their modules (the town cat in zones.py,
the ibex in frost_props.py, both from region masks shaded by `paint_mask`). The other
lanes' animals (Claude B's sheep, heron, duck and marmot; Claude C's crab; Claude D's
horse and camel) get frames *derived from their still* by moving parts of it (the head
dips, a leg steps, the tail swishes). A lane that draws a frame by hand under the same
name in its own module replaces the derived one: `frames()` only derives what is not
already drawn.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, hex_rgba  # noqa: E402

CELL = 4  # the walk grid's cell (zones.CELL)
SHADE_RGBA = (12, 16, 46, 80)  # an animal's own shadow, laid over the ground it stands on

# ---------------------------------------------------------------------------------------
# Painting from masks: a figure as rows of letters, one per material; each material is a
# five-tone ramp (dark .. highlight) or a fixed colour. Light comes from the upper left:
# a pixel whose upper or left neighbour lies outside the figure is lit, one whose lower or
# right neighbour lies outside is in shade, so a mirrored mask is lit the same way.


def paint_mask(cv: Canvas, rows: list[str], inks: dict, x0: int, y0: int, mirror: bool = False):
    """Paint `rows` onto `cv` with its top-left at (x0, y0). `inks` maps a letter to a
    five-tone ramp (shaded by the figure's edges) or to a single colour (drawn as is).
    With `mirror` the rows are flipped left to right first (the light stays upper left)."""
    w = max(len(r) for r in rows)
    grid = [(r.ljust(w, '.')[::-1] if mirror else r.ljust(w, '.')) for r in rows]

    def inside(x, y):
        return 0 <= y < len(grid) and 0 <= x < w and grid[y][x] != '.'

    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            ink = inks[ch]
            if isinstance(ink, str):
                cv.set(x0 + x, y0 + y, ink)
                continue
            lit = (not inside(x, y - 1)) + (not inside(x - 1, y))
            dark = (not inside(x, y + 1)) + (not inside(x + 1, y))
            # a little volume: the lower part of a run of rows sits a step darker
            deep = inside(x, y - 1) and inside(x, y - 2) and not inside(x, y + 2)
            tone = 2 + min(lit, 2) - min(dark, 1) - (1 if deep and not lit else 0)
            cv.set(x0 + x, y0 + y, ink[max(0, min(4, tone))])


# ---------------------------------------------------------------------------------------
# Working on another lane's still: its pixels as a dict, moved about and put back.

def pixels(cv: Canvas) -> dict:
    p = cv.pad
    out = {}
    for y in range(-p, cv.h + p):
        for x in range(-p, cv.w + p):
            c = cv.get(x, y)
            if c[3]:
                out[(x, y)] = c
    return out


def canvas_of(like: Canvas, pix: dict) -> Canvas:
    cv = Canvas(like.w, like.h, pad=like.pad)
    for (x, y), c in pix.items():
        cv.set(x, y, c)
    return cv


def move(pix: dict, sel, dx: int, dy: int, heal: bool = False) -> dict:
    """Move the pixels `sel` picks by (dx, dy), drawn over the rest. With `heal`, a
    pixel they leave inside what stays (the body they covered) takes its colour from its
    nearest neighbour that stayed, so no hole opens where a head was."""
    moved = {(x, y): c for (x, y), c in pix.items() if sel(x, y, c)}
    out = {k: c for k, c in pix.items() if k not in moved}
    if heal:
        for (x, y) in moved:
            if (x, y) in out:
                continue
            for (nx, ny) in ((x - 1, y), (x, y - 1), (x - 2, y), (x, y - 2), (x + 1, y)):
                if (nx, ny) in out and (nx, ny) not in moved:
                    left = any((x - k, y) in out for k in range(1, 6))
                    right = any((x + k, y) in out for k in range(1, 6))
                    up = any((x, y - k) in out for k in range(1, 6))
                    if left and right and up:
                        out[(x, y)] = out[(nx, ny)]
                    break
    for (x, y), c in moved.items():
        out[(x + dx, y + dy)] = c
    return out


def _bluish(c) -> bool:
    return c[2] > c[0] + 20 and c[2] >= c[1]


def _grassy(c) -> bool:
    return c[1] > c[0] + 15 and c[1] > c[2] + 15


def split_ground(pix: dict) -> tuple[dict, dict]:
    """A still as (the animal, what it stands on): its own contact shadow (the translucent
    pixels a lane draws under it), the water round a wader's feet (a bluish bottom row) and
    the grass at a grazing mouth stay where they are while the animal moves above them."""
    ground = {k: c for k, c in pix.items() if c[3] < 255 or _grassy(c)}
    body = {k: c for k, c in pix.items() if k not in ground}
    if body:
        bottom = max(y for (_x, y) in body)
        row = [k for k in body if k[1] == bottom]
        if all(_bluish(body[k]) for k in row):
            for k in row:
                ground[k] = body.pop(k)
    return body, ground


def on_ground(pix: dict, ground: dict) -> dict:
    """The animal drawn over what it stands on."""
    return {**ground, **pix}


def legs_of(pix: dict) -> tuple[int, list[list[int]]]:
    """The rows of a standing animal's legs and the columns of each leg: from the bottom
    up, the rows that are only thin separate runs (two pixels or less) are legs. A run two
    wide is a near and a far leg seen one behind the other (a sheep's pair, a heron's
    two), and the legs may all be in one such run."""
    ys = sorted({y for (_x, y) in pix})
    bottom = ys[-1]
    top = bottom + 1
    legs: list[list[int]] = []
    for y in range(bottom, ys[0] - 1, -1):
        xs = sorted(x for (x, yy) in pix if yy == y)
        runs, cur = [], [xs[0]] if xs else []
        for x in xs[1:]:
            if x == cur[-1] + 1:
                cur.append(x)
            else:
                runs.append(cur)
                cur = [x]
        if cur:
            runs.append(cur)
        if not runs or (len(runs) < 2 and len(runs[0]) < 2) or any(len(r) > 2 for r in runs):
            break
        top = y
        if y == bottom:
            legs = runs
    return top, legs


def step(pix: dict, forward: int, first: bool) -> dict:
    """A walking step: alternate legs (the first and third, or the second and fourth)
    swing a pixel forward and the others a pixel back, so the pairs open and close. Where
    each pair is a near and a far leg one behind the other (two wide), one pair strides
    on each step instead: the front pair on the first, the hind pair on the second, the
    leading leg's lower part a pixel forward and the other's a pixel back, the upper leg
    still under the body."""
    top, legs = legs_of(pix)
    if len(legs) < 2:
        return dict(pix)
    out = dict(pix)
    if all(len(leg) == 2 for leg in legs):
        legs = sorted(legs, key=lambda leg: leg[0] * forward)
        pair = legs[-1] if first else legs[0]
        bottom = max(y for (_x, y) in pix)
        lead, trail = (pair[1], pair[0]) if forward > 0 else (pair[0], pair[1])
        moved = {}
        for (x, y), c in pix.items():
            if y >= max(top + 1, bottom - 1) and x in pair:
                out.pop((x, y), None)
                moved[(x + (forward if x == lead else -forward), y)] = c
        out.update(moved)
        return out
    moved = {}
    for i, leg in enumerate(sorted(legs)):
        d = forward if (i % 2 == 0) == first else -forward
        for (x, y), c in pix.items():
            if y >= top and x in leg:
                out.pop((x, y), None)
                moved[(x + d, y)] = c
    out.update(moved)
    return out


def lift_leg(pix: dict, which: int, forward: int) -> dict:
    """A wading step: one leg lifted, its foot drawn up and a pixel forward."""
    top, legs = legs_of(pix)
    legs = sorted([x] for leg in legs for x in leg)  # each column a leg (a near and a far)
    if which >= len(legs):
        return dict(pix)
    bottom = max(y for (_x, y) in pix)
    out = dict(pix)
    leg = legs[which]
    for y in range(bottom - 2, bottom + 1):
        for x in leg:
            out.pop((x, y), None)
    colour = pix.get((leg[0], top)) or next(iter(pix.values()))
    out[(leg[0] + forward, bottom - 3)] = colour
    out[(leg[0] + 2 * forward, bottom - 3)] = colour
    return out


def _lum(c) -> float:
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def relit_mirror(cv: Canvas) -> Canvas:
    """The still turned to face the other way with its light kept on the upper left: the
    shape mirrored, and every pair of tones that meets as lit-left / shaded-right on the
    same material swapped back."""
    pix = pixels(cv)
    pairs: dict = {}
    for (x, y), c in pix.items():
        d = pix.get((x + 1, y))
        if not d or d == c:
            continue
        hue_c = tuple(v - min(c[:3]) for v in c[:3])
        hue_d = tuple(v - min(d[:3]) for v in d[:3])
        if max(abs(a - b) for a, b in zip(hue_c, hue_d)) > 24:
            continue  # a different material, not a lit and a shaded side
        if _lum(c) > _lum(d) + 12:
            pairs[(c, d)] = pairs.get((c, d), 0) + 1
    swap = {}
    for (a, b), n in sorted(pairs.items(), key=lambda kv: -kv[1]):
        if n >= 3 and a not in swap and b not in swap:
            swap[a], swap[b] = b, a
    w = cv.w
    out = {(w - 1 - x, y): swap.get(c, c) for (x, y), c in pix.items()}
    return canvas_of(cv, out)


# ---------------------------------------------------------------------------------------
# Frames derived from the other lanes' stills (each returns {role: canvas} for one still).

def _bbox(pix):
    xs = [x for (x, _y) in pix]
    ys = [y for (_x, y) in pix]
    return min(xs), min(ys), max(xs), max(ys)


def _head_of(pix: dict, facing: int, reach: int = 6):
    """The dark face of a pale-fleeced animal: the pixels at its front, above its legs,
    darker than any of the fleece behind them."""
    x0, _y0, x1, _y1 = _bbox(pix)
    top, _legs = legs_of(pix)
    front = (lambda x: x >= x1 - reach) if facing > 0 else (lambda x: x <= x0 + reach)
    # (the fleece behind the face, leaving out the dark legs under it)
    back = sorted(_lum(c) for (x, y), c in pix.items() if not front(x) and y < top)
    fleece = [v for v in back if back and v > back[len(back) // 2] / 2]
    dark = (min(fleece) if fleece else 255) - 4
    face = {k for k, c in pix.items() if front(k[0]) and k[1] < top and _lum(c) < dark}
    # and what only the face holds up (the tuft of wool on a lamb's poll), so nothing is
    # left floating where the head was
    for (x, y) in list(pix):
        near = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if (x, y) not in face and front(x) and any(n in face for n in near) and \
                all(n in face or n not in pix for n in near):
            face.add((x, y))
    return lambda x, y, c: (x, y) in face


def _sheep(cv: Canvas, facing: int) -> dict:
    """A grazing sheep (its still has the head down in the grass): look up (the grass
    bitten off), chew, and a stride of the front and then the hind legs. Its own contact
    shadow and the grass stay on the ground."""
    pix, ground = split_ground(pixels(cv))
    head = _head_of(pix, facing)
    if not any(head(x, y, c) for (x, y), c in pix.items()):
        return {}
    shadow = {k: c for k, c in ground.items() if c[3] < 255}
    return {
        'look': canvas_of(cv, on_ground(move(pix, head, facing, -3, heal=True), shadow)),
        'chew': canvas_of(cv, {**on_ground(move(pix, head, 0, 1, heal=True), shadow),
                               **{k: c for k, c in ground.items() if c[3] == 255}}),
        'step1': canvas_of(cv, on_ground(step(pix, facing, True), ground)),
        'step2': canvas_of(cv, on_ground(step(pix, facing, False), ground)),
    }


def _lying(cv: Canvas, facing: int) -> dict:
    """A sheep lying down with its head up, chewing the cud: the jaw (the lower half of
    the face) drops a pixel and comes up again; the body and its shadow stay."""
    pix, ground = split_ground(pixels(cv))
    _x0, y0, _x1, y1 = _bbox(pix)
    head = _head_of(pix, facing, reach=5)
    rows = sorted({y for (x, y), c in pix.items() if head(x, y, c)})
    if not rows:
        return {}
    mid = (rows[0] + rows[-1] + 1) // 2
    jaw = lambda x, y, c: head(x, y, c) and y >= mid  # noqa: E731
    return {'chew': canvas_of(cv, on_ground(move(pix, jaw, 0, 1, heal=True), ground))}


def _lamb(cv: Canvas, facing: int) -> dict:
    """A lamb standing with its head up: it dips to nibble and lifts again, chews, and
    trots on shorter legs."""
    pix, ground = split_ground(pixels(cv))
    head = _head_of(pix, facing, reach=4)
    if not any(head(x, y, c) for (x, y), c in pix.items()):
        return {}
    return {
        'dip': canvas_of(cv, on_ground(move(pix, head, facing, 2, heal=True), ground)),
        'chew': canvas_of(cv, on_ground(move(pix, head, 0, 1, heal=True), ground)),
        'step1': canvas_of(cv, on_ground(step(pix, facing, True), ground)),
        'step2': canvas_of(cv, on_ground(step(pix, facing, False), ground)),
    }


def _heron(cv: Canvas, facing: int) -> dict:
    """A heron standing in the shallows: preen (the head drawn down to the breast),
    strike (neck and bill thrust down and forward), and a wading step on each leg."""
    pix, ground = split_ground(pixels(cv))
    x0, y0, x1, y1 = _bbox(pix)
    # the body is the first wide row below the head (the bill makes the head's row wide
    # too); above it are the neck and head
    body = next(y for y in range(y0 + 3, y1 + 1) if sum(1 for (_x, yy) in pix if yy == y) >= 7)
    head = lambda x, y, c: y < y0 + (body - y0) // 2  # noqa: E731
    return {
        'preen': canvas_of(cv, on_ground(move(pix, head, -facing, 3), ground)),
        'strike': canvas_of(cv, on_ground(move(pix, head, facing * 2, 2), ground)),
        'step1': canvas_of(cv, on_ground(lift_leg(pix, 0, facing), ground)),
        'step2': canvas_of(cv, on_ground(lift_leg(pix, 1, facing), ground)),
    }


def _duck(cv: Canvas, facing: int) -> dict:
    """A duck afloat: dabble (head dipped to the water), preen (head turned back over its
    wing), and the slight rise and fall of paddling."""
    pix = pixels(cv)
    x0, y0, x1, y1 = _bbox(pix)
    mid = (y0 + y1) // 2
    front = (lambda x: x >= x1 - 5) if facing > 0 else (lambda x: x <= x0 + 5)
    head = lambda x, y, c: front(x) and y <= mid  # noqa: E731
    return {
        'dabble': canvas_of(cv, move(pix, head, facing, 3, heal=True)),
        'preen': canvas_of(cv, move(pix, head, -3 * facing, 1, heal=True)),
        'step1': canvas_of(cv, move(pix, lambda x, y, c: y < y1 - 1, 0, 1)),
        'step2': canvas_of(cv, dict(pix)),
    }


def _crab(cv: Canvas) -> dict:
    """A crab: claws lowered, and two scuttling steps (it goes sideways, so it faces no way)."""
    pix = pixels(cv)
    x0, y0, x1, y1 = _bbox(pix)
    claws = lambda x, y, c: y <= y0 + 1 and (x <= x0 + 2 or x >= x1 - 2)  # noqa: E731
    legs = lambda x, y, c: y >= y1 - 1  # noqa: E731
    return {
        'claws': canvas_of(cv, move(pix, claws, 0, 1)),
        'step1': canvas_of(cv, move(pix, lambda x, y, c: legs(x, y, c) and x < (x0 + x1) / 2, -1, 0)),
        'step2': canvas_of(cv, move(pix, lambda x, y, c: legs(x, y, c) and x > (x0 + x1) / 2, 1, 0)),
    }


def _tail_and_head(cv: Canvas, tail_side: int, head: str = 'high') -> dict:
    """A big animal at rest (a horse dozing, a camel lying down): its tail swishes and its
    head dips. The tail is the thin part at the back; the head is the top of the front
    (`head` 'high', a camel's) or the whole front end ('low', a horse dozing)."""
    pix = pixels(cv)
    x0, y0, x1, y1 = _bbox(pix)
    back = (lambda x: x <= x0 + 3) if tail_side < 0 else (lambda x: x >= x1 - 3)
    front = (lambda x: x >= x1 - (5 if head == 'low' else 7)) if tail_side < 0 else \
        (lambda x: x <= x0 + (5 if head == 'low' else 7))
    tail = lambda x, y, c: back(x) and y > (y0 + y1) // 2 - 4  # noqa: E731
    out = {'swish': canvas_of(cv, move(pix, tail, tail_side, -1))}
    if head:
        top = (lambda y: y < y1 - 6) if head == 'low' else (lambda y: y < y0 + 5)
        out['dip'] = canvas_of(cv, move(pix, lambda x, y, c: front(x) and top(y), 0, 1, heal=True))
    return out


def _marmot(cv: Canvas) -> dict:
    """The marmot on its rock: it ducks its head and looks up again."""
    pix = pixels(cv)
    x0, y0, x1, y1 = _bbox(pix)
    fur = lambda x, y, c: y < y0 + 6 and c[0] > c[2] + 20  # noqa: E731
    return {'dip': canvas_of(cv, move(pix, fur, 0, 1, heal=True))}


# ---------------------------------------------------------------------------------------
# The kinds. `east` and `west` name the still drawn facing each way (the placed sprite is
# one of them); `idle` the accents shown while it stands ([role, ms, times]: a frame held
# for ms, shown `times` over with the still between); `walk` its two step frames; `moves`
# where it may go ('ground', 'water', 'wade' in the shallows, or 'still': it stays put);
# `reach` how far from its home spot (px), `speed` px per second, `step_ms` a step.

KINDS: dict[str, dict] = {
    'sheep': dict(east='sheep', west='sheep_left', idle=[['look', 1600, 1], ['chew', 220, 3]],
                  walk=['step1', 'step2'], moves='ground', reach=12, speed=5, step_ms=260),
    'heron': dict(east='heron_e', west='heron', idle=[['preen', 1400, 1], ['strike', 420, 1]],
                  walk=['step1', 'step2'], moves='wade', reach=6, speed=3, step_ms=420),
    'duck': dict(east='duck', west='duck_w', idle=[['dabble', 1100, 1], ['preen', 900, 1]],
                 walk=['step1', 'step2'], moves='water', reach=12, speed=4, step_ms=400),
    'cat': dict(east='cat', west='cat_w', idle=[['flick', 240, 2], ['wash', 1800, 1], ['ear', 200, 2]],
                walk=['step1', 'step2'], moves='ground', reach=10, speed=12, step_ms=150),
    'ibex': dict(east='ibex', west='ibex', idle=[['graze', 2200, 1], ['flick', 180, 2], ['look', 1600, 1],
                                                  ['turn', 2600, 1]],
                 walk=[], moves='still', reach=0, speed=0, step_ms=0),
    'crab': dict(east='crab', west='crab', idle=[['claws', 300, 2]], walk=['step1', 'step2'],
                 moves='ground', reach=10, speed=10, step_ms=120),
    'horse': dict(east='horse', west='horse', idle=[['swish', 260, 2], ['dip', 1600, 1]], walk=[],
                  moves='still', reach=0, speed=0, step_ms=0),
    'camel': dict(east='camel', west='camel', idle=[['dip', 1400, 1], ['swish', 260, 2]], walk=[],
                  moves='still', reach=0, speed=0, step_ms=0),
    'camel_b': dict(east='camel_b', west='camel_b', idle=[['swish', 260, 2]], walk=[], moves='still',
                    reach=0, speed=0, step_ms=0),
    'marmot_rock': dict(east='marmot_rock', west='marmot_rock', idle=[['dip', 1400, 1]],
                        walk=[], moves='still', reach=0, speed=0, step_ms=0),
}
KINDS['sheep_left'] = KINDS['sheep']
# Claude B's lying sheep chews the cud where it lies; its lamb trots in shorter steps and
# keeps nearer home. The sheep and lambs draw their own contact shadow in the still
# (valley_props.sheep), which walks with them, so they take no derived shadow (`own_shadow`).
KINDS['sheep_lying'] = dict(east='sheep_lying', west='sheep_lying_left', idle=[['chew', 240, 4]], walk=[],
                            moves='still', reach=0, speed=0, step_ms=0)
KINDS['lamb'] = dict(east='lamb', west='lamb_left', idle=[['dip', 1300, 1], ['chew', 200, 3]],
                     walk=['step1', 'step2'], moves='ground', reach=7, speed=4, step_ms=180)
for _k in ('sheep', 'lamb'):
    KINDS[_k]['own_shadow'] = True
KINDS['sheep_lying_left'] = KINDS['sheep_lying']
KINDS['lamb_left'] = KINDS['lamb']


def roles(kind: dict) -> list[str]:
    return [r for (r, _ms, _n) in kind['idle']] + list(kind['walk'])


def bases(kind: dict) -> list[str]:
    return list(dict.fromkeys([kind['east'], kind['west']]))


def moving(key: str) -> bool:
    """An animal that walks or swims away from its home spot (its shadow goes with it,
    drawn in its still or derived by `shade`, so the zone does not paint one on the
    ground)."""
    return key in KINDS and KINDS[key]['moves'] != 'still'


def frames(items: dict) -> dict:
    """The frames every kind still needs, derived from the stills in `items` (raw,
    unfinalized canvases); frames already drawn by hand are kept."""
    out: dict = {}

    def put(base, made):
        for role, cv in made.items():
            key = f'{base}_{role}'
            if key not in items and key not in out:
                out[key] = cv

    if 'heron' in items and 'heron_e' not in items:
        out['heron_e'] = relit_mirror(items['heron'])
    if 'duck' in items and 'duck_w' not in items:
        out['duck_w'] = relit_mirror(items['duck'])
    have = {**items, **out}
    for base, fn in (('sheep', lambda c: _sheep(c, 1)), ('sheep_left', lambda c: _sheep(c, -1)),
                     ('sheep_lying', lambda c: _lying(c, 1)), ('sheep_lying_left', lambda c: _lying(c, -1)),
                     ('lamb', lambda c: _lamb(c, 1)), ('lamb_left', lambda c: _lamb(c, -1)),
                     ('heron', lambda c: _heron(c, -1)), ('heron_e', lambda c: _heron(c, 1)),
                     ('duck', lambda c: _duck(c, 1)), ('duck_w', lambda c: _duck(c, -1)),
                     ('crab', _crab), ('horse', lambda c: _tail_and_head(c, -1, 'low')),
                     ('camel', lambda c: _tail_and_head(c, -1)),
                     ('camel_b', lambda c: _tail_and_head(c, -1, '')), ('marmot_rock', _marmot)):
        if base in have:
            put(base, fn(have[base]))
    # a kind whose frames could not be derived from its still keeps only what it has
    return out


# ---------------------------------------------------------------------------------------
# Where each animal may go: a few spots near home, chosen so its feet (the band the walk
# grid blocks for it) never cross a prop, water (unless it swims), a wall or a cliff on
# the straight way there and back.

def foot_cells(key_w: int, key_h: int, x: int, y: int) -> set:
    """The walk cells under an animal's feet (zones.walk_grid's band for a small prop)."""
    return {(xx // CELL, yy // CELL) for yy in range(y + key_h - 6, y + key_h)
            for xx in range(x + 3, x + key_w - 3)}


def spots(objects, sprite_map, terrain: list[str], walk: list[str], grid_of) -> dict:
    """{object id: [[dx, dy], ...]} for every animal that moves in one zone. `grid_of`
    is zones.walk_grid for a list of objects (the cells their feet block); `walk` the
    zone's final walk rows (props reaching in from a neighbour, lava margins)."""
    out = {}
    rows, cols = len(terrain), len(terrain[0])
    for (oid, key, x, y) in objects:
        kind = KINDS.get(key)
        if not kind or kind['moves'] == 'still':
            continue
        sp = sprite_map[key]
        others = grid_of([o for o in objects if o[0] != oid])
        blocked = {(c, r) for r, row in enumerate(others) for c, ch in enumerate(row) if ch == '#'}
        home = foot_cells(sp.w, sp.h, x, y)
        if kind['moves'] in ('ground', 'wade'):  # (nothing else closed on dry ground: the final walk)
            blocked |= {(c, r) for r, row in enumerate(walk) for c, ch in enumerate(row)
                        if ch == '#' and (c, r) not in home and terrain[r][c] != '~'}
        want = {'ground': '.=', 'water': '~', 'wade': '~'}[kind['moves']]
        # wading birds keep to the terrain they stand in (shallows), never out onto a bank
        if kind['moves'] == 'wade':
            here = {terrain[r][c] for (c, r) in home if 0 <= r < rows and 0 <= c < cols}
            want = ''.join(sorted(here - set('^!'))) or '~'

        def ok(dx, dy):
            for (c, r) in foot_cells(sp.w, sp.h, x + dx, y + dy):
                if not (0 <= r < rows and 0 <= c < cols):
                    return False
                if (c, r) in blocked or terrain[r][c] not in want:
                    return False
            return True

        def way(dx, dy, fx=0, fy=0):
            """The straight way from (fx, fy) to (dx, dy) (rounded as the test and the
            renderer round it) is clear all along (home itself is where the zone put it)."""
            n = max(abs(dx - fx), abs(dy - fy))
            pts = {(round(fx + (dx - fx) * i / n), round(fy + (dy - fy) * i / n)) for i in range(n + 1)}
            return all(ok(*p) for p in pts - {(0, 0)})

        reach = kind['reach']
        cands = [(dx, dy) for dx in range(-reach, reach + 1) for dy in range(-reach // 2, reach // 2 + 1)
                 if (dx or dy) and dx * dx + 4 * dy * dy <= reach * reach and abs(dx) >= 3]
        cands = [c for c in cands if way(*c)]
        chosen: list = []
        # one spot each way along the ground, and one a little up or down
        for (ux, uy) in ((-1, 0.3), (1, -0.3), (0.6, 0.8), (-0.6, -0.8)):
            best = max(cands, key=lambda c: c[0] * ux + c[1] * uy * 1.5, default=None)
            if best and best not in chosen and all(math.dist(best, o) >= 4 for o in chosen):
                if best[0] * ux + best[1] * uy > reach * 0.4:
                    chosen.append(best)
            if len(chosen) == 3:
                break
        if not chosen:
            continue
        # the last walk home goes the way the placed still faces, so it rests as placed
        east = (kind['east'] == key)
        chosen.sort(key=lambda c: (c[0] < 0) if east else (c[0] > 0))
        # and it walks from spot to spot only where the way between them is clear too
        path: list = []
        for c in chosen:
            if way(*c, *(path[-1] if path else (0, 0))):
                path.append(c)
        if path:
            out[oid] = [list(c) for c in path]
    return out


# ---------------------------------------------------------------------------------------
# The export: the frames, each still's shadow, and the kinds table for the renderer.

def shade(sp: Canvas) -> Canvas | None:
    """The animal's own contact shadow (detail.silhouette_shadow's shape), as a picture
    that walks with it instead of being painted on the ground at its home."""
    import detail
    pts = detail.silhouette_shadow(sp, 0, 0)
    if not pts:
        return None
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    cv = Canvas(max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    for (x, y) in pts:
        cv.px[x - min(xs), y - min(ys)] = SHADE_RGBA
    cv.ox, cv.oy = min(xs), min(ys)
    return cv


def export(built: dict, sm: dict, used: dict, grid_of) -> list[str]:
    """Add every placed animal's frames and shadows to `used` and return the lines of
    lib/zone-maps.ts that describe them (zoneAnimals, zoneAnimalSpots)."""
    table = {}
    for key in sorted(k for k in list(used) if k in KINDS):
        kind = KINDS[key]
        base = sm[key]
        sets = {}
        for side in ('east', 'west'):
            name = kind[side]
            if name not in sm:
                name = key
            fl = []
            for role in [None, *roles(kind)]:
                fk = name if role is None else f'{name}_{role}'
                if fk not in sm:
                    fk = name  # (a frame no one could make: the still stands in)
                fr = sm[fk]
                used[fk] = fr
                fl.append([fk, fr.ox - base.ox, fr.oy - base.oy, fr.w, fr.h])
            sets[side] = fl
        entry = {
            'east': sets['east'], 'west': sets['west'],
            'faces': 'east' if kind['east'] == key else 'west',
            'idle': [[1 + i, ms, n] for i, (_r, ms, n) in enumerate(kind['idle'])],
            'walk': [1 + len(kind['idle']) + i for i in range(len(kind['walk']))],
            'moves': kind['moves'], 'speed': kind['speed'], 'stepMs': kind['step_ms'],
        }
        if kind['moves'] != 'still' and not kind.get('own_shadow'):
            sh = shade(base)
            if sh:
                sk = f'{key}_shade'
                used[sk] = sh
                entry['shade'] = [sk, sh.ox, sh.oy, sh.w, sh.h]
        table[key] = entry
    zone_spots = {}
    for z, b in built.items():
        found = spots(b['objects'], b['sprites'], b['terrain'], b['walk'], grid_of)
        if found:
            zone_spots[z] = found
    import json
    return [
        '/** Animals that live (scripts/art/animal_frames.py): per placed sprite, its frames facing each way',
        ' *  ([frame sprite, dx, dy, w, h] from the placed sprite\'s top-left; index 0 is the still), which way',
        ' *  the placed still faces, the idle accents ([frame index, ms, times]), the two walk frames, where it may',
        ' *  go, its pace (px per second) and step (ms), and its own shadow when it moves. */',
        'export type AnimalFrame = readonly [string, number, number, number, number];',
        'export type AnimalKind = {',
        '  east: readonly AnimalFrame[];',
        '  west: readonly AnimalFrame[];',
        "  faces: 'east' | 'west';",
        '  idle: readonly (readonly [number, number, number])[];',
        '  walk: readonly number[];',
        "  moves: 'ground' | 'water' | 'wade' | 'still';",
        '  speed: number;',
        '  stepMs: number;',
        '  shade?: AnimalFrame;',
        '};',
        f'export const zoneAnimals: Record<string, AnimalKind> = {json.dumps(table)};',
        '/** Where each animal that moves may wander: [dx, dy] from where the zone placed it (its home), in',
        ' *  zone px; checked against props, water, walls and cliffs on the straight way there and back. */',
        'export const zoneAnimalSpots: Partial<Record<ZoneId, Record<string, readonly (readonly [number, number])[]>>> = '
        f'{json.dumps(zone_spots)};',
    ]
