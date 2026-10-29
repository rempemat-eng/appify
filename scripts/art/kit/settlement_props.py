"""Four reusable waterfront candidates, drawn natively on the density-3 pixel grid.

    python3 -m scripts.art.kit.settlement_props --out game/kit/props/art

This deliberately does not write the shared piece index or generated Godot scenes.
The two authored piece JSONs carry the measured anchors and collision rectangles.
No production placement, interaction, animation or approval is implied by drawing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scripts.art.native.palette import rgb

ROOT = Path(__file__).resolve().parents[3]
DENSITY = 3
FILENAMES = (
    'industry_bollard_single.png', 'industry_bollard_rope.png',
    'industry_net_rack_working.png', 'industry_net_rack_repair.png',
)


def colour(family, tone):
    return (*rgb(family, tone), 255)


class Pixel:
    """Integer texels only; no smoothing, resampling, external palette or noise."""

    def __init__(self, width, height):
        self.image = Image.new('RGBA', (width, height))
        self.draw = ImageDraw.Draw(self.image)

    def poly(self, points, family, tone):
        self.draw.polygon(points, fill=colour(family, tone))

    def line(self, points, family, tone, width=2):
        self.draw.line(points, fill=colour(family, tone), width=width)

    def box(self, bounds, family, tone):
        self.draw.rectangle(bounds, fill=colour(family, tone))

    def oval(self, bounds, family, tone):
        self.draw.ellipse(bounds, fill=colour(family, tone))


def bollard(rope=False):
    """Iron mushroom head on a rectangular four-bolt plate; foot (48,60) art px.

    The iron has broad, upper-left-lit planes and a worn rope groove. The rope
    stays inside the same dry ground envelope, rather than crossing a route.
    The plate is the authored blocker; the optional loose coil is non-solid.
    """
    p = Pixel(96, 72)
    # A seated base with visible thickness and a quiet contact seam.
    p.poly([(27, 50), (60, 50), (69, 56), (65, 60), (29, 60), (23, 56)], 'iron', 0)
    p.poly([(28, 49), (60, 49), (67, 54), (63, 57), (29, 57), (25, 54)], 'iron', 2)
    p.line([(28, 50), (58, 50), (65, 54)], 'iron', 4)
    p.line([(30, 57), (62, 57), (66, 55)], 'iron', 1)
    for x, y in ((31, 52), (57, 52), (31, 55), (59, 55)):
        p.box((x - 1, y - 1, x + 1, y + 1), 'iron', 0)
        p.box((x - 1, y - 1, x, y), 'iron', 4)
    # Neck, flared foot and a cap with readable top/body/shadow planes.
    p.poly([(38, 31), (54, 31), (56, 47), (61, 51), (55, 54), (36, 53), (31, 50), (36, 46)], 'iron', 0)
    p.poly([(39, 31), (52, 31), (53, 47), (57, 50), (53, 52), (37, 51), (35, 49), (39, 46)], 'iron', 2)
    p.poly([(39, 32), (43, 32), (42, 47), (38, 49), (36, 48)], 'iron', 4)
    p.poly([(49, 32), (53, 32), (54, 47), (57, 50), (51, 51)], 'iron', 1)
    p.oval((29, 18, 62, 36), 'iron', 0)
    p.oval((30, 18, 61, 32), 'iron', 2)
    p.oval((31, 18, 60, 28), 'iron', 4)
    p.oval((35, 20, 56, 26), 'iron', 3)
    p.line([(32, 27), (37, 30), (51, 31), (58, 28)], 'iron', 1, 3)
    p.line([(33, 22), (37, 20), (45, 20)], 'iron', 5)
    p.line([(39, 35), (49, 36), (54, 34)], 'iron', 3)
    # Two broad scuffs, not random grain or isolated highlights.
    p.line([(38, 40), (40, 38)], 'iron', 3)
    p.line([(45, 47), (48, 47)], 'iron', 1)
    if rope:
        p.line([(39, 33), (43, 35), (52, 35), (57, 32)], 'timber', 0, 5)
        p.line([(39, 32), (44, 34), (52, 34), (57, 31)], 'timber', 4, 3)
        p.line([(40, 33), (31, 40), (20, 48), (18, 51)], 'timber', 0, 5)
        p.line([(40, 32), (30, 39), (19, 47), (17, 51)], 'timber', 3, 3)
        for bounds in ((7, 48, 29, 59), (10, 50, 26, 57), (13, 51, 23, 55)):
            p.draw.ellipse(bounds, outline=colour('timber', 0), width=4)
            p.draw.arc(bounds, 165, 340, fill=colour('timber', 4), width=2)
        p.line([(22, 57), (27, 59), (31, 58)], 'timber', 2, 3)
    return p.image


def net_rack(repair=False):
    """Drying/mending rack: 48-world-px post spacing, foot (96,120) art px.

    Twine has actual transparent diamond openings. The mending variant leaves
    a rolled area and a broad patched tear; it is an ordinary work state,
    unrelated to story restoration flags. A low timber tie joins the feet:
    the full authored rectangular base is intentionally a blocker.
    """
    p = Pixel(192, 132)
    # Two foot blocks and the low, route-blocking tie joining the posts.
    p.poly([(18, 113), (168, 113), (177, 118), (173, 120), (20, 120), (14, 117)], 'timber', 0)
    p.poly([(20, 112), (167, 112), (172, 116), (22, 116), (17, 114)], 'timber', 3)
    p.line([(23, 112), (165, 112)], 'timber', 4)
    p.box((27, 116, 165, 118), 'timber', 1)
    # Uprights: lit west arris, shaded east face, end grain and iron foot straps.
    for x in (24, 168):
        p.box((x - 5, 17, x + 5, 115), 'timber', 0)
        p.box((x - 4, 18, x + 3, 114), 'timber', 3)
        p.box((x - 4, 18, x - 2, 111), 'timber', 4)
        p.box((x + 2, 19, x + 4, 114), 'timber', 1)
        p.line([(x - 1, 40), (x, 53), (x - 1, 67)], 'timber', 2)
        p.line([(x + 1, 83), (x - 1, 91), (x, 101)], 'timber', 2)
        p.poly([(x - 5, 17), (x + 2, 15), (x + 6, 18), (x - 2, 21)], 'timber', 4)
        for y in (28, 103):
            p.box((x - 5, y, x + 5, y + 7), 'iron', 0)
            p.box((x - 4, y + 1, x + 3, y + 5), 'iron', 2)
            p.box((x - 3, y + 1, x - 1, y + 2), 'iron', 4)
    p.poly([(19, 22), (170, 22), (177, 26), (174, 34), (19, 34), (15, 30)], 'timber', 0)
    p.poly([(20, 23), (170, 23), (173, 26), (171, 30), (20, 30), (18, 28)], 'timber', 3)
    p.line([(22, 24), (168, 24)], 'timber', 4)
    p.line([(23, 31), (169, 31)], 'timber', 1)
    for x in (26, 164):
        p.line([(x - 2, 23), (x - 3, 34)], 'timber', 1, 4)
        p.line([(x, 23), (x - 1, 34)], 'timber', 4, 2)
    # Mesh laid on its own mask, so clipping cuts twine as well as its shadow.
    mesh = Pixel(192, 132)
    for start in range(-30, 184, 16):
        mesh.line([(start, 35), (start + 72, 107)], 'timber_cool', 1, 3)
        mesh.line([(start + 1, 35), (start + 73, 107)], 'timber_cool', 3, 2)
        mesh.line([(start + 72, 35), (start, 107)], 'timber_cool', 1, 3)
        mesh.line([(start + 73, 35), (start + 1, 107)], 'timber_cool', 3, 2)
    clip = Image.new('L', p.image.size)
    cd = ImageDraw.Draw(clip)
    cd.polygon([(33, 35), (159, 35), (155, 88), (137, 97), (98, 104), (59, 97), (36, 89)], fill=255)
    if repair:
        cd.polygon([(109, 35), (158, 35), (157, 81), (147, 76), (138, 80), (124, 65), (114, 58)], fill=0)
    mesh.image.putalpha(Image.fromarray(np.minimum(np.asarray(mesh.image.getchannel('A')), np.asarray(clip))))
    p.image.alpha_composite(mesh.image)
    p.line([(32, 35), (63, 40), (99, 43), (132, 40), (159, 35)], 'timber', 0, 4)
    p.line([(32, 34), (63, 39), (99, 42), (132, 39), (159, 34)], 'timber', 4, 2)
    if repair:
        # Rolled net at the right and a visible stitched patch left of the tear.
        for x in range(143, 161, 4):
            p.line([(x, 36), (x - 3, 70)], 'timber_cool', 1, 4)
            p.line([(x, 36), (x - 3, 68)], 'timber_cool', 3, 2)
        p.poly([(87, 62), (106, 64), (104, 84), (85, 82)], 'timber_cool', 1)
        p.poly([(89, 64), (104, 66), (102, 82), (87, 80)], 'timber_cool', 3)
        for y in (67, 73, 79):
            p.line([(85, y), (90, y + 1)], 'timber', 4)
            p.line([(102, y + 2), (107, y + 3)], 'timber', 4)
    else:
        p.line([(36, 89), (60, 98), (98, 105), (136, 98), (155, 89)], 'timber', 1, 3)
    # Cork floats and two weighted corners make its use readable at game scale.
    for x, y in ((46, 37), (75, 41), (117, 41), (147, 37)):
        p.oval((x - 3, y - 1, x + 3, y + 5), 'clay', 0)
        p.box((x - 2, y, x + 1, y + 3), 'clay', 3)
        p.line([(x - 1, y), (x + 1, y)], 'clay', 4)
    for x, y in ((39, 91), (151, 91)):
        p.line([(x, y - 4), (x, y + 3)], 'timber', 1)
        p.oval((x - 3, y + 1, x + 3, y + 8), 'iron', 0)
        p.line([(x - 1, y + 2), (x - 1, y + 5)], 'iron', 3)
    return p.image


def sprites():
    return dict(zip(FILENAMES, (bollard(), bollard(True), net_rack(), net_rack(True))))


def write(out):
    out.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, image in sprites().items():
        path = out / name
        image.save(path, optimize=False)
        result[name] = {'size_px': list(image.size), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'game/kit/props/art')
    args = parser.parse_args(argv)
    print(json.dumps(write(args.out), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
