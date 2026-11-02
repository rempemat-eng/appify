"""One Crossroads grain-weighing candidate, in two purely visual work states.

SOURCE ONLY until exact-source review and a separate bounded drawing allocation.
Later command: python3 -B -m scripts.art.kit.crossroads_grain_scale --out RUN/first
Reproduction uses a SECOND fresh directory, never an overwrite of earlier evidence.
This module never writes a piece index, scene, zone, palette or other painter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.art.kit.settlement_props import Pixel


DENSITY = 3
SIZE = (168, 144)
FOOT = (84, 132)
FILENAMES = ('crossroads_grain_scale_ready.png', 'crossroads_grain_scale_loaded.png')


def _legs_and_frame(p):
    # Rear legs precede the front frame. All four feet lie inside the SAME
    # authored rectangular blocker; openings are not new walk-under passages.
    for x, top, bottom in ((43, 84, 118), (113, 84, 118), (53, 96, 131), (125, 96, 131)):
        p.poly([(x - 3, top), (x + 5, top), (x + 4, bottom), (x - 3, bottom)], 'timber', 0)
        p.poly([(x - 2, top + 1), (x + 2, top + 1), (x + 1, bottom - 1),
                (x - 2, bottom - 1)], 'timber', 3)
        p.line([(x - 2, top + 3), (x - 2, bottom - 3)], 'timber', 4)
        p.box((x + 2, top + 2, x + 4, bottom - 1), 'timber_cool', 1)
        # Foot wear follows actual floor contact, not random speckling.
        p.line([(x - 3, bottom), (x + 4, bottom)], 'timber_cool', 0, 2)
        p.line([(x - 1, bottom - 3), (x + 2, bottom - 3)], 'timber', 2)
    # Rear and front ties carry the uprights. Braces visibly meet rails/posts.
    p.poly([(45, 109), (116, 109), (119, 113), (46, 113)], 'timber', 0)
    p.line([(48, 110), (114, 110)], 'timber', 3, 3)
    p.poly([(55, 119), (128, 119), (128, 125), (55, 125)], 'timber', 0)
    p.box((57, 120, 126, 122), 'timber', 3)
    p.line([(58, 120), (124, 120)], 'timber', 4)
    for start, end in (((59, 118), (81, 101)), ((124, 118), (108, 101))):
        p.line([start, end], 'timber', 0, 7)
        p.line([(start[0], start[1] - 1), (end[0], end[1] - 1)], 'timber', 3, 4)
        p.line([(start[0] - 1, start[1] - 2), (end[0] - 1, end[1] - 2)], 'timber', 4)
    for x, y in ((58, 120), (126, 120), (80, 103), (109, 103)):
        p.box((x - 1, y - 1, x + 1, y + 1), 'iron', 0)
        p.box((x - 1, y - 1, x, y), 'iron', 4)


def _table(p):
    # One shallow projected top, its left thickness, front apron and dark
    # underside. Plank seams follow this plane instead of becoming a flat grid.
    p.poly([(33, 77), (117, 77), (139, 93), (139, 101), (49, 101), (33, 85)], 'timber', 0)
    p.poly([(34, 78), (116, 78), (137, 93), (50, 93)], 'timber', 3)
    p.poly([(35, 79), (116, 79), (122, 83), (40, 83)], 'timber', 4)
    p.poly([(35, 83), (50, 94), (50, 98), (35, 87)], 'timber', 2)
    p.poly([(51, 94), (137, 94), (137, 99), (51, 99)], 'timber_cool', 2)
    p.line([(51, 100), (137, 100)], 'timber_cool', 0, 2)
    for x in (55, 78, 100):
        p.line([(x, 79), (x + 19, 92)], 'timber', 1)
        p.line([(x + 2, 80), (x + 19, 91)], 'timber', 4)
    # Sparse connected grain, one knot and handling marks at the loading lip.
    # No seeded noise, stipple fill or identical marks on every plank.
    p.line([(43, 82), (48, 82), (57, 87)], 'timber', 2)
    p.line([(81, 83), (87, 84), (93, 88), (100, 89)], 'timber', 2)
    p.oval((66, 85, 72, 89), 'timber', 1)
    p.line([(66, 86), (69, 85), (72, 87)], 'timber', 4)
    p.line([(103, 92), (113, 92), (118, 90)], 'timber', 5)
    p.line([(123, 91), (129, 92)], 'timber', 4)
    # Forged corner straps bind the APRON to its supports, not floating trim.
    for x in (55, 128):
        p.box((x - 2, 94, x + 2, 103), 'iron', 0)
        p.box((x - 1, 94, x + 1, 101), 'iron', 2)
        p.box((x - 1, 95, x, 96), 'iron', 4)


def _balance_support(p):
    # Bolted base and triangular gusset explain how the narrow mast can carry
    # the crossbeam. The bright edge stays upper-left; the east face stays cool.
    p.poly([(76, 83), (91, 83), (98, 88), (80, 90), (73, 86)], 'iron', 0)
    p.poly([(77, 83), (90, 83), (94, 86), (80, 88), (76, 86)], 'iron', 3)
    p.line([(78, 84), (88, 84)], 'iron', 4)
    p.poly([(81, 82), (81, 47), (84, 39), (89, 41), (90, 86), (85, 88)], 'iron', 0)
    p.box((83, 48, 86, 84), 'iron', 3)
    p.line([(83, 49), (83, 81)], 'iron', 4)
    p.box((87, 48, 88, 85), 'iron', 1)
    p.poly([(79, 84), (82, 73), (85, 85)], 'iron', 1)
    p.line([(79, 83), (82, 75)], 'iron', 4)
    for x, y in ((78, 86), (92, 86)):
        p.box((x - 1, y - 1, x + 1, y + 1), 'iron', 0)
        p.box((x - 1, y - 1, x, y), 'iron', 5)


def _pan(p, x, rim_y, suspension_y, grain=False, weight=False):
    # Two hanging stays terminate at opposite points on the rim. Neither state
    # changes the foot/collider or introduces an interaction or weight economy.
    for dx in (-13, 13):
        p.line([(x, suspension_y), (x + dx, rim_y + 1)], 'iron', 0, 3)
        p.line([(x, suspension_y), (x + dx, rim_y)], 'iron', 3)
    p.oval((x - 17, rim_y, x + 17, rim_y + 11), 'iron', 0)
    p.poly([(x - 14, rim_y + 4), (x + 14, rim_y + 4),
            (x + 9, rim_y + 9), (x - 8, rim_y + 9)], 'iron', 1)
    p.oval((x - 15, rim_y, x + 15, rim_y + 6), 'iron', 3)
    p.oval((x - 12, rim_y + 1, x + 12, rim_y + 4), 'iron', 1)
    p.line([(x - 13, rim_y + 1), (x - 7, rim_y), (x + 5, rim_y)], 'iron', 5)
    p.line([(x - 7, rim_y + 8), (x + 7, rim_y + 8)], 'iron', 2)
    if grain:
        p.poly([(x - 11, rim_y + 2), (x - 8, rim_y - 3), (x - 3, rim_y - 6),
                (x + 3, rim_y - 5), (x + 8, rim_y - 1), (x + 12, rim_y + 3),
                (x + 4, rim_y + 5), (x - 6, rim_y + 4)], 'clay', 2)
        p.poly([(x - 9, rim_y + 1), (x - 5, rim_y - 3), (x - 1, rim_y - 5),
                (x + 4, rim_y - 3), (x + 8, rim_y), (x + 2, rim_y + 2)], 'clay', 4)
        for dx, dy in ((-7, 0), (-3, -2), (2, -1), (6, 2)):
            p.line([(x + dx, rim_y + dy), (x + dx + 2, rim_y + dy - 1)], 'clay', 5, 2)
        p.line([(x - 6, rim_y + 4), (x + 3, rim_y + 5), (x + 9, rim_y + 3)], 'clay', 1)
    if weight:
        _weight(p, x, rim_y + 3)


def _weight(p, x, y):
    p.poly([(x - 4, y), (x - 3, y - 5), (x + 2, y - 6),
            (x + 4, y - 1), (x + 3, y + 2), (x - 3, y + 2)], 'iron', 0)
    p.poly([(x - 2, y - 4), (x + 1, y - 5), (x + 2, y), (x - 2, y)], 'iron', 3)
    p.line([(x - 2, y - 3), (x - 2, y - 1)], 'iron', 5)


def grain_scale(loaded=False):
    """Fixed S-facing 168x144 art canvas; common foot (84,132), density3.

    Ready = level beam/empty pans, weights resting on the tabletop. Loaded =
    a lower grain pan and raised counterweight pan. These are ordinary visual
    illustrations, never named story stages, payment, stock or gameplay states.
    """
    p = Pixel(*SIZE)
    _legs_and_frame(p)
    _table(p)
    _balance_support(p)
    # Equal arms around (85,45); the loaded beam tilts as ONE rigid member.
    left_y, right_y = (51, 39) if loaded else (45, 45)
    p.line([(49, left_y + 1), (121, right_y + 1)], 'iron', 0, 6)
    p.line([(49, left_y), (121, right_y)], 'iron', 3, 3)
    p.line([(49, left_y - 1), (121, right_y - 1)], 'iron', 4)
    p.oval((81, 40, 89, 48), 'iron', 0)
    p.oval((82, 40, 87, 45), 'iron', 3)
    p.box((83, 41, 84, 42), 'iron', 5)
    _pan(p, 49, 73 if loaded else 66, left_y + 2, grain=loaded)
    _pan(p, 121, 62 if loaded else 66, right_y + 2, weight=loaded)
    if not loaded:
        _weight(p, 104, 89)
        _weight(p, 117, 91)
    # One local handling scuff at the pivot and a dark attachment below it.
    p.line([(83, 52), (84, 54)], 'iron', 5)
    p.line([(87, 58), (88, 66)], 'iron', 1)
    return p.image


def sprites():
    return {FILENAMES[0]: grain_scale(), FILENAMES[1]: grain_scale(True)}


def write(out):
    """Only the two declared files, into a fresh/empty caller-owned directory.

    Generation itself is NOT allocated by committing this function. Earlier
    evidence and shared art are never overwritten to obtain a reproduction pass.
    """
    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('use a fresh/empty owned output directory; existing evidence is retained')
    out.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, image in sprites().items():
        path = out / name
        image.save(path, optimize=False)
        data = path.read_bytes()
        result[name] = {'size_px': list(image.size), 'foot_art': list(FOOT),
                        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='fresh owned directory; no implicit shared-art writes')
    args = parser.parse_args(argv)
    print(json.dumps(write(args.out), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
