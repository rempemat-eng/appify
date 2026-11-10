"""What the zone generators share about solids (docs/physics.md): the layers, the low rule and the kit
library's boxes. Used by gen_zone.py, gen_village.py and gen_undercroft.py; nothing here draws.

Layers (game/project.godot names 1 to 4): 1 walls, 2 player, 3 enemy, 4 interact, and 5 low. A solid
is a StaticBody2D on layer 1 with mask 0. A low solid is on layers 1 and 5: it stops feet like any wall,
and actors/arrow.gd lets an arrow fly over it.

Low rule: a solid is low when its picture stands less than LOW_RISE texels above its foot (the shoulder of
a 74 texel person; an arrow leaves the bow 21 to 70 texels up and is drawn flying over it). A kit piece may
say how high it stands itself (geometry.height_px) or that it never stops a shot (gameplay.blocks_shots
false); terrain is low where a zone's low.txt says so (water, a drop).

Y-sort: a sprite's origin is what the y-sort compares with an actor's feet, so it sits on the picture's
drawn feet (its lowest opaque row): feet_drop() says how far a picture is drawn below or above the origin
its zone gives it, and where that is more than 2 texels the generators move the origin there, keeping
every texel where it was.

Boxes: a picture's solid is its piece's in the kit library (game/kit/pieces/prop/*.json,
geometry.collision: a rectangle in world px from the foot). The woodland takes every object's box from
there. A drawn village keeps the boxes of its plan, except where the library holds a box reviewed against
the art (audit.overrides has "collision") or the object is an approved woodland picture: then the library's
box stands, so the playable zone and the kit never disagree about the same picture.
"""
import glob
import json
import os

GAME = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
WALL_LAYER = 1
LOW_LAYER = 1 | 16
LOW_RISE = 64          # texels
_PIECES = None


def pieces() -> dict:
    """Every prop piece of the kit library by id."""
    global _PIECES
    if _PIECES is None:
        _PIECES = {}
        for path in sorted(glob.glob(os.path.join(GAME, 'kit', 'pieces', 'prop', '*.json'))):
            piece = json.load(open(path))
            _PIECES[piece['id']] = piece
    return _PIECES


def box(piece: dict):
    """A piece's solid: (x, y, w, h) in world px from the foot, or None when it blocks nothing."""
    col = (piece.get('geometry') or {}).get('collision') or {}
    if col.get('shape') != 'rect' or not (piece.get('gameplay') or {}).get('blocks_move'):
        return None
    return tuple(col['rect'])


def reviewed(piece: dict) -> bool:
    """True when the piece's box was reviewed against the art and stands over its source zone's."""
    return 'collision' in (piece.get('audit') or {}).get('overrides', [])


def source_piece(zone: str, object_id: str):
    """The piece seeded from one object of a zone (audit.sources), or None."""
    for piece in pieces().values():
        for src in (piece.get('audit') or {}).get('sources', []):
            if src.get('zone') == zone and src.get('object') == object_id and src.get('part') == 'body':
                return piece
    return None


def rise(png: str, foot_y: float, frames: int = 1) -> int:
    """How far a picture stands above its foot, in texels: from its topmost opaque row down to `foot_y`
    (the foot's row in the picture). `frames` is the number of drawings side by side in a strip."""
    from PIL import Image
    im = Image.open(png).convert('RGBA')
    if frames > 1:
        im = im.crop((0, 0, im.width // frames, im.height))
    bbox = im.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
    return 0 if bbox is None else int(round(foot_y - bbox[1]))


def feet_drop(png: str, foot_y: float, frames: int = 1) -> int:
    """How many texels a picture's lowest opaque row lies below (+) or above (-) `foot_y`, the row its zone
    takes for its feet. 0 when the origin already sits on the drawn feet."""
    from PIL import Image
    im = Image.open(png).convert('RGBA')
    if frames > 1:
        im = im.crop((0, 0, im.width // frames, im.height))
    bbox = im.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
    return 0 if bbox is None else int(round(bbox[3] - foot_y))


SORT_SLACK = 2         # texels a y-sort origin may sit from the drawn feet


def on_feet(png: str, foot, offset, frames: int = 1, most: int = 6):
    """A sprite's origin moved onto its drawn feet: (foot, offset) with the same texels on screen. An
    origin within SORT_SLACK texels stays where the kit put it (so a sign still ties with its talk area and
    draws under its own "!"), and a drop of more than `most` is left alone (a thing hung or lifted on
    purpose)."""
    drop = feet_drop(png, -offset[1], frames)
    if abs(drop) <= SORT_SLACK or abs(drop) > most:
        return tuple(foot), tuple(offset)
    return (foot[0], foot[1] + drop), (offset[0], offset[1] - drop)


def drawn_base(png: str, foot, offset, depth: int = 12, density: int = 3):
    """The box under a picture that has none of its own: the texels drawn in its lowest `depth` rows, as
    [x, y, w, h] in world px (`foot` and `offset` in texels, as kit.json holds them)."""
    from PIL import Image
    a = Image.open(png).convert('RGBA').getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    bbox = a.getbbox()
    if bbox is None:
        return None
    low = a.crop((0, bbox[3] - depth, a.width, bbox[3])).getbbox()
    x0, y0 = foot[0] + offset[0] + low[0], foot[1] + offset[1] + bbox[3] - depth
    return [x0 / density, y0 / density, (low[2] - low[0]) / density, depth / density]


def is_low(stands: float, piece: dict | None = None) -> bool:
    """The low rule: the piece's own word if it has one, else the picture's rise."""
    if piece is not None:
        if (piece.get('gameplay') or {}).get('blocks_shots') is False:
            return True
        stands = (piece.get('geometry') or {}).get('height_px', stands)
    return stands < LOW_RISE
