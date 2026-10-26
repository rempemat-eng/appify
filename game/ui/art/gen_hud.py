"""The desktop HUD's pictures (Claude M, 25 Oct): hearts, roll charges, the Glint mark, the
panel the quest tracker and pause menu sit on, and the key cap for prompts.

Drawn on the 960 x 540 art grid at one image pixel per texel, the same grid as the world and
the cast (docs/godot.md), so the HUD is pixel-crisp at 2x on 1080p and 4x on 4K. Colours come
from art/materials.json through scripts/art/materials.py; light from the upper left; a dark
outline in each material's own darkest tone, the ink outline only around the panel.

Run from the repository root: python3 game/ui/art/gen_hud.py (writes game/ui/art/*.png; the
same bytes every run). Re-import the Godot project after changing it.
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts' / 'art'))
from materials import CREAM, GOLD, INK, RED, STONE, WOOD, WTR  # noqa: E402

OUT = Path(__file__).resolve().parent


def rgba(hex_colour, alpha=255):
    h = hex_colour.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def picture(rows, key):
    """rows: strings of key letters, '.' transparent."""
    h, w = len(rows), len(rows[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        assert len(row) == w, (row, w)
        for x, ch in enumerate(row):
            if ch != '.':
                im.putpixel((x, y), key[ch] if isinstance(key[ch], tuple) else rgba(key[ch]))
    return im


# o outline, d shade, m body, l lit, h highlight
HEART = [
    '..ooo.ooo..',
    '.ommmommmo.',
    'omhlmmmmmdo',
    'omlmmmmmmdo',
    'ommmmmmmmdo',
    '.ommmmmmdo.',
    '..ommmmdo..',
    '...ommdo...',
    '....odo....',
    '.....o.....',
]
HEART_FULL = {'o': RED[0], 'd': RED[1], 'm': RED[2], 'l': RED[3], 'h': RED[4]}
# an empty heart is its socket: the outline kept, the body sunk in stone shade
HEART_EMPTY = {'o': STONE[0], 'd': STONE[0], 'm': STONE[1], 'l': STONE[2], 'h': STONE[2]}

# a roll charge: a round token with a swept arc, the roll's path
ROLL = [
    '..ooooo..',
    '.ommmmmo.',
    'omllhhmdo',
    'omhmmmhdo',
    'ommmmmhdo',
    'omhmmmmdo',
    'omdhhhddo',
    '.odddddo.',
    '..ooooo..',
]
ROLL_FULL = {'o': WTR[0], 'd': WTR[1], 'm': WTR[2], 'l': WTR[3], 'h': WTR[4]}
ROLL_EMPTY = {'o': STONE[0], 'd': STONE[0], 'm': STONE[1], 'l': STONE[1], 'h': STONE[2]}

# the Glint mark: a four-point shard of light, gold with a cream core
GLINT = [
    '....o....',
    '...olo...',
    '...ohd...',
    '..ohmmo..',
    'oolhcmddo',
    'ohccccmdo',
    'oodmcmddo',
    '..ommdo..',
    '...omd...',
    '...odo...',
    '....o....',
]
GLINT_KEY = {'o': GOLD[0], 'd': GOLD[1], 'm': GOLD[2], 'l': GOLD[3], 'h': GOLD[4], 'c': CREAM[3]}

# the panel: a 9-slice (4 px margins) of dark wood, lit top and left, ink outline, the body a
# little see-through so the world reads behind the quest tracker
PANEL = [
    '.oooooooooo.',
    'ollllllllldo',
    'olmmmmmmmmdo',
    'olmffffffmdo',
    'olmffffffmdo',
    'olmffffffmdo',
    'olmffffffmdo',
    'olmffffffmdo',
    'olmffffffmdo',
    'olmmmmmmmmdo',
    'oddddddddddo',
    '.oooooooooo.',
]
PANEL_KEY = {'o': INK, 'l': WOOD[3], 'm': WOOD[2], 'd': WOOD[1], 'f': rgba(WOOD[0], 224)}

# a key cap for prompts (9-slice, 3 px margins): stone, lit top, its front face below
KEY = [
    '.ooooooo.',
    'ohhhhhhlo',
    'ohmmmmmlo',
    'ohmmmmmlo',
    'ohmmmmmlo',
    'ohmmmmmlo',
    'olllllllo',
    'odddddddo',
    '.ooooooo.',
]
KEY_KEY = {'o': INK, 'h': STONE[4], 'l': STONE[3], 'm': STONE[3], 'd': STONE[1]}

PICTURES = {
    'heart_full': (HEART, HEART_FULL),
    'heart_empty': (HEART, HEART_EMPTY),
    'roll_full': (ROLL, ROLL_FULL),
    'roll_empty': (ROLL, ROLL_EMPTY),
    'glint': (GLINT, GLINT_KEY),
    'panel': (PANEL, PANEL_KEY),
    'key': (KEY, KEY_KEY),
}


def main():
    for name, (rows, key) in PICTURES.items():
        picture(rows, key).save(OUT / f'{name}.png', optimize=False)
    print(f'hud art: {len(PICTURES)} pictures in game/ui/art')


if __name__ == '__main__':
    main()
