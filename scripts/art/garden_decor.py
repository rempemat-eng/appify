"""Small garden props drawn at native pixel resolution.

The main garden generator owns placement, collisions and exported assets.
These functions only return transparent canvases and have no file side effects.
"""
from __future__ import annotations

from pixel import Canvas, oval


WOOD = ['#4A3122', '#6E4A30', '#93673F', '#B98A57', '#D9AE78']
NAP = ['#3E3466', '#5C4E8F', '#7D6BB5', '#A797D6', '#CFC4EC']
CREAM = ['#8C7A5E', '#C9B48E', '#E9DCBC', '#FBF4E4']
LEAF = ['#1F4B2E', '#2F6A3A', '#47894A', '#66A85A', '#93C978']
RED = ['#5E2A22', '#8E3F31', '#B95A45', '#DB8366', '#F2B79B']
TEAL = ['#284C5E', '#39738A', '#62A3B1', '#A1CFD0', '#E0EFDF']
INK = '#2A2421'


def reading_nook() -> Canvas:
    """A low bench, folded lilac cushion, open book and a flowering side pot."""
    cv = Canvas(28, 24)

    # Bench posts, a low back and a braced pair of legs. Light falls from above-left.
    cv.rect(3, 9, 2, 12, WOOD[1])
    cv.rect(20, 9, 2, 12, WOOD[1])
    cv.hline(4, 9, 17, WOOD[4])
    cv.rect(4, 10, 17, 3, WOOD[3])
    cv.hline(4, 12, 17, WOOD[2])
    cv.set(7, 11, WOOD[2])
    cv.set(8, 10, WOOD[4])
    cv.hline(5, 19, 15, WOOD[2])
    cv.set(5, 20, WOOD[0])
    cv.set(19, 20, WOOD[0])
    # A rail knot and small brass screws make the bench built, rather than flat.
    cv.set(5, 10, CREAM[1])
    cv.set(20, 10, CREAM[1])
    cv.hline(15, 11, 3, WOOD[1])
    cv.rect(3, 15, 19, 3, WOOD[2])
    cv.hline(3, 15, 19, WOOD[4])
    cv.hline(3, 17, 19, WOOD[1])
    cv.hline(8, 16, 3, WOOD[3])
    cv.vline(21, 15, 3, WOOD[1])

    # Folded cushion: a lit top, darker folded front and two small stitches.
    cv.rect(5, 12, 8, 3, NAP[3])
    cv.hline(6, 11, 6, NAP[4])
    cv.hline(5, 14, 8, NAP[2])
    cv.rect(6, 15, 6, 1, NAP[1])
    cv.vline(11, 12, 2, NAP[4])
    cv.set(6, 13, CREAM[2])
    cv.set(9, 13, NAP[4])
    cv.set(7, 12, NAP[2])
    cv.set(8, 12, CREAM[2])  # embroidered little leaf on the cushion

    # Open book in shallow perspective; separate page planes meet at a dark crease.
    cv.hline(15, 10, 5, WOOD[0])
    cv.hline(13, 11, 8, WOOD[0])
    cv.rect(13, 12, 9, 4, WOOD[0])
    cv.hline(14, 16, 7, WOOD[1])
    cv.hline(14, 11, 3, CREAM[3])
    cv.rect(14, 12, 3, 3, CREAM[2])
    cv.set(13, 13, CREAM[2])
    cv.hline(18, 11, 2, CREAM[2])
    cv.rect(18, 12, 3, 3, CREAM[3])
    cv.set(21, 14, CREAM[2])
    cv.vline(17, 12, 3, CREAM[0])
    cv.hline(14, 13, 2, CREAM[0])
    cv.hline(19, 13, 2, CREAM[1])
    cv.set(18, 15, NAP[2])  # a little ribbon bookmark over the page edge
    cv.set(18, 16, NAP[3])

    # Terracotta pot behind the right arm, with a leaf and a single lilac flower.
    cv.rect(23, 13, 3, 4, RED[2])
    cv.hline(22, 12, 5, RED[1])
    cv.hline(23, 12, 3, RED[4])
    cv.vline(23, 14, 2, RED[3])
    cv.hline(24, 17, 2, RED[1])
    cv.vline(24, 7, 5, LEAF[1])
    cv.set(23, 9, LEAF[3])
    cv.set(22, 8, LEAF[4])
    cv.set(25, 10, LEAF[2])
    cv.set(26, 9, LEAF[3])
    for x, y in ((24, 4), (23, 5), (25, 5), (24, 6)):
        cv.set(x, y, NAP[3] if x > 24 else NAP[4])
    cv.set(24, 5, '#F2D16B')

    # A mug on a tiny shelf, with its loop handle open to the background.
    cv.hline(2, 7, 5, WOOD[2])
    cv.rect(3, 4, 3, 3, TEAL[2])
    cv.hline(3, 4, 3, TEAL[4])
    cv.set(6, 5, TEAL[1]); cv.set(6, 6, TEAL[1])
    cv.set(3, 6, TEAL[1])

    cv.outline(INK)
    cv.shadow(13, 22, 10, 1, alpha=55)
    return cv


def watering_can() -> Canvas:
    """A teal can with an open loop handle, raised spout and glazed highlights."""
    cv = Canvas(14, 12)

    # The handle is drawn as a ring, preserving the transparent hole at this scale.
    cv.hline(1, 3, 4, TEAL[0])
    cv.vline(0, 4, 3, TEAL[0])
    cv.hline(1, 7, 4, TEAL[0])
    cv.vline(4, 4, 3, TEAL[0])
    cv.hline(1, 4, 3, TEAL[3])
    cv.vline(1, 5, 2, TEAL[2])
    cv.hline(2, 7, 2, TEAL[1])

    # A rising spout with a broad perforated rose at its tip.
    for y, x, length in ((2, 11, 3), (3, 11, 3), (4, 10, 3), (5, 10, 2), (6, 9, 3)):
        cv.hline(x, y, length, TEAL[0])
    for x, y in ((12, 2), (12, 3), (11, 4), (10, 5), (10, 6)):
        cv.set(x, y, TEAL[2])
    cv.hline(11, 1, 3, TEAL[1])
    cv.set(12, 1, TEAL[4])
    cv.set(13, 2, TEAL[0])

    # Rounded metal body, a darker right face and a visible top opening.
    for x, y in oval(7.5, 7, 3.7, 3.5):
        cv.set(x, y, TEAL[0])
    for x, y in oval(7.5, 7, 2.7, 2.5):
        cv.set(x, y, TEAL[1] if x >= 9 or y >= 8 else TEAL[2])
    cv.hline(5, 4, 4, TEAL[0])
    cv.hline(6, 4, 2, TEAL[1])
    cv.hline(5, 5, 3, TEAL[3])
    cv.set(5, 6, TEAL[4])
    cv.vline(5, 7, 2, TEAL[3])
    cv.set(9, 8, CREAM[1])  # one small brass rivet
    cv.set(7, 6, TEAL[3])
    cv.set(7, 7, TEAL[1]); cv.set(8, 6, TEAL[1])  # stamped leaf emblem
    cv.hline(5, 10, 5, TEAL[0])
    cv.shadow(8, 11, 4, 1, alpha=60)
    return cv


def frog() -> Canvas:
    """A tiny pond keeper: bright brow, gold eyes and broad webbed feet.

    The app places this sprite over a lily pad after an ordinary pond visit.
    Twelve native pixels wide keeps its detail in scale with the garden props.
    """
    cv = Canvas(12, 10)
    # Broad feet establish a stable silhouette on the pad.
    cv.hline(1, 8, 4, LEAF[1]); cv.hline(8, 8, 3, LEAF[0])
    cv.set(1, 7, LEAF[3]); cv.set(10, 7, LEAF[2])
    cv.rect(3, 4, 6, 4, LEAF[2])
    cv.hline(3, 4, 6, LEAF[3]); cv.hline(4, 7, 4, LEAF[1])
    cv.rect(3, 2, 7, 4, LEAF[3])
    cv.hline(4, 1, 5, LEAF[3]); cv.hline(3, 3, 5, LEAF[4])
    # Separate raised eyes, with the left brow catching the upper-left light.
    cv.rect(3, 1, 2, 3, LEAF[4]); cv.rect(8, 1, 2, 3, LEAF[3])
    cv.set(3, 2, '#E9D58B'); cv.set(8, 2, '#D1B866')
    cv.set(4, 2, INK); cv.set(9, 2, INK)
    cv.hline(5, 5, 3, LEAF[1]); cv.set(8, 4, LEAF[1])
    cv.hline(5, 6, 3, CREAM[2])
    cv.set(4, 4, RED[4]); cv.set(9, 4, RED[3])
    cv.outline(LEAF[0])
    return cv
