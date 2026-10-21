"""Glares: wisps of screen light that drift in from the city. They are calmed, never killed.
Drawn at 1x art pixels, lit from the upper left, with the house's near-black outline tinted
cool (a light creature, but drawn, not a blur)."""
from PIL import Image, ImageDraw

OUT_COOL = (0x1C, 0x22, 0x3E, 255)
OUT_WARM = (0x3B, 0x2A, 0x14, 255)

COOL = dict(W='#F6FCFF', S='#DDF3FD', C='#A9E2F6', B='#62BCE6', D='#3B7CC2', N='#27508F',
            P='#F59AD8', eye='#1C223E')
WARM = dict(W='#FFFBEA', S='#FFF0C2', C='#F8DD8F', B='#E6BC5C', D='#BF8F36', N='#7F5B1E',
            P='#F0A688', eye='#3B2A14')

# The glare, 15 x 17: a cold flame on top, a small screen for a body (the face), a wisp tail.
# Letters: W white, S screen, C pale, B cyan, D deep, N darkest, P a neon pink fleck,
# e eye, m brow/mouth, '.' empty. The outline is added afterwards.
BODY = [
    "......W........",
    ".....WC........",
    ".....CWC.......",
    "....CWCB...P...",
    "...CWWCBD......",
    "..CWCCCBBD.....",
    ".CBNNNNNNNNBD..",
    ".BNWWSSSSSSNDN.",
    ".BNWmSSSSSmNDN.",
    ".BNSSmSSSmSNDN.",
    ".BNSSeSSSeSNDN.",
    ".BNSSSSSSSSNDN.",
    ".BNSSSmmmSSNDN.",
    ".CBNNNNNNNNBDN.",
    "..DBBBBBBBBDN..",
    "...NDBBBDDNN...",
    ".....NDBDN.....",
    "......NDN......",
]
# Calmed: the brow eases, the eyes close (down-curved), the screen goes warm.
CALM = [
    "...............",
    "...............",
    "......W........",
    ".....CWC.......",
    "...CWWCBD......",
    "..CWCCCBBD.....",
    ".CBDDDDDDDDBD..",
    ".BDWWSSSSSSDDN.",
    ".BDWSSSSSSSDDN.",
    ".BDSmSmSmSmDDN.",
    ".BDSSeSSSeSDDN.",
    ".BDSSSSSSSSDDN.",
    ".BDSSSSmSSSDDN.",
    ".CBDDDDDDDDBDN.",
    "..DBBBBBBBBDN..",
    "...NDBBBDDNN...",
    ".....NDBDN.....",
    "...............",
]


def hexc(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _paint(rows, pal, outline):
    h, w = len(rows), len(rows[0])
    im = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            key = {'e': 'eye', 'm': 'eye'}.get(ch, ch)
            im.putpixel((x + 1, y + 1), hexc(pal[key]))
    # outline: every empty pixel touching a filled one (4-neighbour)
    px = im.load()
    out = im.copy()
    po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < im.width and 0 <= yy < im.height and px[xx, yy][3]:
                    po[x, y] = outline
                    break
    return out


def glare(frame=0, mood='cross', flash=0.0):
    """frame 0/1 flicker (the flame tip leans); mood 'cross', 'windup' (bright, eyes wide),
    'calm' (warm, eyes closed)."""
    rows = [r for r in (CALM if mood == 'calm' else BODY)]
    if frame == 1 and mood != 'calm':
        rows = rows[:]
        rows[0] = ".......W......."
        rows[1] = "......CW......."
        rows[2] = ".....CWC.....P."
        rows[3] = "....CWCB......."
    if mood == 'windup':
        rows = rows[:]
        rows[7] = ".BNWWSSSSSSNDN."
        rows[8] = ".BNWSSSSSSSNDN."
        rows[9] = ".BNSeeSSSeeNDN."
        rows[10] = ".BNSeeSSSeeNDN."
        rows[11] = ".BNSSSSeSSSNDN."
        rows[12] = ".BNSSSSSSSSNDN."
    pal = WARM if mood == 'calm' else COOL
    im = _paint(rows, pal, OUT_WARM if mood == 'calm' else OUT_COOL)
    if mood == 'windup':  # charged: the rim whitens
        im = _tint(im, 0.25)
    if flash:
        im = _tint(im, flash)
    return im


def _tint(im, amount):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (int(r + (255 - r) * amount), int(g + (255 - g) * amount), int(b + (255 - b) * amount), a)
    return out


SPARK = [
    "..W..",
    ".WSW.",
    "WSWSW",
    ".WSW.",
    "..W..",
]


def spark(stage=0):
    """The calmed glare's harmless spark, a warm mote (5 x 5 plus outline), stage 0 bright, 1 dimmer."""
    pal = dict(W='#F8DD8F' if stage else '#FFF0C2', S='#FFFBEA' if not stage else '#F8DD8F')
    return _paint(SPARK, pal, OUT_WARM)


def shrink_calm(step):
    """Calming in three steps: 0 the warm glare, 1 the body folding into the flame, 2 the spark."""
    if step == 0:
        return glare(0, 'calm')
    if step == 1:
        rows = [
            "....W....",
            "...CWC...",
            "..CWWCB..",
            ".BCSSSCB.",
            ".BSmSmSD.",
            ".BSSSSSD.",
            "..DBBBD..",
            "...NDN...",
        ]
        return _paint(rows, WARM, OUT_WARM)
    return spark(0)


if __name__ == '__main__':
    import os
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ims = [glare(0), glare(1), glare(0, 'windup'), glare(0, flash=0.6), glare(0, 'calm'), shrink_calm(1), spark(0), spark(1)]
    sheet = Image.new('RGBA', (20 * len(ims), 23), (96, 140, 78, 255))
    for i, im in enumerate(ims):
        sheet.alpha_composite(im, (i * 20 + 1, 1))
    sheet.resize((sheet.width * 10, sheet.height * 10), Image.NEAREST).save(os.path.join(here, '_glare_sheet.png'))
