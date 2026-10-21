"""Read the game's own sprites for the fight mock: pets and visitors from lib/pet-sprites.ts,
residents and zone props from their PNGs (saved at 4x, read back at 1x)."""
import os
import re

from PIL import Image

WT = (os.environ.get('NAPATTACK_REPO') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..')))
SRC = open(os.path.join(WT, 'lib/pet-sprites.ts')).read()
INDEX = re.search(r"PET_INDEX =\s*'([^']+)'", SRC).group(1)
PALETTE = re.findall(r"'(#[0-9A-Fa-f]{6})'", SRC[SRC.index('petPalette'):SRC.index('export type SpriteState')])


def _rows(block: str, state: str):
    m = re.search(state + r": \[\n((?:\s+'[^']*',\n)+)", block)
    return re.findall(r"'([^']*)'", m.group(1))


def _paint(rows):
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            col = PALETTE[INDEX.index(ch)]
            im.putpixel((x, y), tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im


def pet(species: str, stage: int, state: str = 'open', facing: str = 'right'):
    start = SRC.index(f'  {species}: {{', SRC.index('export const petSprites'))
    block = SRC[SRC.index(f"'{stage}': {{", start):]
    block = block[:block.index('hat:')]
    im = _paint(_rows(block, state))
    # the sprites are drawn facing right (the battle mirrors them for the left side)
    return im if facing == 'right' else im.transpose(Image.FLIP_LEFT_RIGHT)


def visitor(name: str, state: str = 'open', facing: str = 'right'):
    start = SRC.index(f'  {name}: {{', SRC.index('export const visitorSprites'))
    block = SRC[start:]
    block = block[:block.index('hat:')]
    im = _paint(_rows(block, state))
    return im if facing == 'right' else im.transpose(Image.FLIP_LEFT_RIGHT)


def png(path: str, s: int = 4):
    im = Image.open(os.path.join(WT, path)).convert('RGBA')
    return im.resize((im.width // s, im.height // s), Image.NEAREST)


def resident(name: str, view: str = '', frame: int = 0):
    """view: '' (front), 'east', 'west' or 'back'."""
    return png(f"assets/residents/{name}{'-' + view if view else ''}-{frame}.png")


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mock')
    sheet = Image.new('RGBA', (32 * 8, 32), (120, 160, 90, 255))
    for i, im in enumerate([pet('BLOB', 1), pet('BLOB', 2), pet('BLOB', 3), pet('RAT', 2), pet('CUBE', 2),
                            visitor('dave'), visitor('dave', facing='left'), pet('BLOB', 2, 'closed')]):
        sheet.alpha_composite(im, (i * 32, 0))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(out, 'pets.png'))


ICON_SRC = open(os.path.join(WT, 'lib/icon-art.ts')).read()
ICON_KEYS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
ICON_PAL = re.findall(r"'(#[0-9A-Fa-f]{6})'", ICON_SRC[:ICON_SRC.index('] as const')])


def icon(name: str):
    start = ICON_SRC.index(f'  {name}: [')
    rows = re.findall(r"'([^']{16})'", ICON_SRC[start:ICON_SRC.index('],', start)])
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            col = ICON_PAL[ICON_KEYS.index(ch)]
            im.putpixel((x, y), tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im


def icon_names():
    return re.findall(r"\n  ([a-zA-Z]+): \[", ICON_SRC)
