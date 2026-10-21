"""The Static Storm: a knot of Glares wound tight round one big screen. Same palette, outline and
upper-left light as glare.py; drawn for this prototype (first pass, not ledger-checked)."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
import glare as gl
from PIL import Image

CORE = [
    "..........W..........",
    ".........WC..........",
    "....W....CWC.....W...",
    "...WC...CWCB....CW...",
    "...CWC.CWWCBD..CWCD..",
    "..CWCBDCWCCCBBDCWCBD.",
    ".CBNNNNNNNNNNNNNNNBD.",
    ".BNWWSSSSSSSSSSSSSNDN",
    ".BNWmSSSSSSSSSSSmSNDN",
    ".BNSSmmSSSSSSSmmSSNDN",
    ".BNSSSSmSSSSSmSSSSNDN",
    ".BNSSSSSSSSSSSSSSSNDN",
    ".BNSSSeeSSSSSeeSSSNDN",
    ".BNSSSeeSSSSSeeSSSNDN",
    ".BNSSSSSSSSSSSSSSSNDN",
    ".BNSSSSSSmmmSSSSSSNDN",
    ".BNSSSSSmSSSmSSSSSNDN",
    ".BNSSSSSSSSSSSSSSSNDN",
    ".CBNNNNNNNNNNNNNNNBDN",
    "..DBBBBBBBBBBBBBBBDN.",
    "...NDBBBBBBBBBBDDNN..",
    "....NNDBBBBBBDDNN....",
    "......NNDBBBDNN......",
    ".......NDBBBDN.......",
    "........NDBDN........",
    ".........NDN.........",
]
FACE_WIND = {  # eyes wide and bright, mouth a small o
    8: ".BNWSSSSSSSSSSSSSSNDN",
    9: ".BNSSSSSSSSSSSSSSSNDN",
    10: ".BNSSSeeeSSSeeeSSSNDN",
    11: ".BNSSSeWeSSSeWeSSSNDN",
    12: ".BNSSSeeeSSSeeeSSSNDN",
    13: ".BNSSSSSSSSSSSSSSSNDN",
    14: ".BNSSSSSSSmSSSSSSSNDN",
    15: ".BNSSSSSSmSmSSSSSSNDN",
    16: ".BNSSSSSSSmSSSSSSSNDN",
}
FACE_CALM = {
    8: ".BDWSSSSSSSSSSSSSSDDN",
    9: ".BDSSSSSSSSSSSSSSSDDN",
    10: ".BDSSSSSSSSSSSSSSSDDN",
    11: ".BDSSmSSSmSmSSSmSSDDN",
    12: ".BDSSSmmmSSSmmmSSSDDN",
    13: ".BDSSSSSSSSSSSSSSSDDN",
    14: ".BDSSSSSSSSSSSSSSSDDN",
    15: ".BDSSSSSSmmmSSSSSSDDN",
    16: ".BDSSSSSSSSSSSSSSSDDN",
}


def rows_for(mood, frame):
    rows = list(CORE)
    if frame == 1:  # flame tips lean
        rows[0] = "...........W........."
        rows[1] = "....W.....CW......W.."
        rows[2] = "...WC....CWC.....CW.."
        rows[3] = "...CW...CWCB....CWC.."
    if mood == 'windup':
        for k, v in FACE_WIND.items():
            rows[k] = v
    if mood == 'calm':
        for k, v in FACE_CALM.items():
            rows[k] = v
        rows = [r.replace('N', 'D') if 6 <= i <= 18 else r for i, r in enumerate(rows)]
    for r in rows:
        assert len(r) == 21, (len(r), r)
    return rows


def storm(mood='cross', frame=0, flash=0.0, minis=True):
    """The whole knot: two small glares wound in behind the core, static crackles between."""
    W, H = 41, 34
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = 'calm' if mood == 'calm' else ('windup' if mood == 'windup' else 'cross')
    if minis:
        a = gl.glare(frame, m if m != 'windup' else 'cross')
        b = gl.glare(1 - frame, m if m != 'windup' else 'cross').transpose(Image.FLIP_LEFT_RIGHT)
        im.alpha_composite(a, (0, 6 + frame))
        im.alpha_composite(b, (W - b.width, 7 - frame))
    pal = gl.WARM if mood == 'calm' else gl.COOL
    core = gl._paint(rows_for(mood, frame), pal, gl.OUT_WARM if mood == 'calm' else gl.OUT_COOL)
    im.alpha_composite(core, ((W - core.width) // 2, H - core.height))
    if mood != 'calm':  # static crackles: little pink and white zigzags in the gaps
        px = im.load()
        zig = [(9, 3), (10, 2), (11, 3), (12, 2)] if frame == 0 else [(8, 2), (9, 3), (10, 2), (11, 1)]
        for (x, y) in zig:
            px[x, y] = gl.hexc('#F59AD8')
            px[W - 1 - x, y + 1] = gl.hexc('#FFFFFF')
    if mood == 'windup':
        im = gl._tint(im, 0.2)
    if flash:
        im = gl._tint(im, flash)
    return im


def fold(step):
    """Calmed, folding: step 0 smaller warm core only, 1 a warm bud."""
    if step == 0:
        return storm('calm', 0, minis=False)
    rows = [
        ".....W.....",
        "....CWC....",
        "...CWWCB...",
        "..BCSSSCB..",
        ".BSSmSmSSD.",
        ".BSSSSSSSD.",
        ".BSSSmSSSD.",
        "..DBBBBBD..",
        "...NDBDN...",
        "....NDN....",
    ]
    return gl._paint(rows, gl.WARM, gl.OUT_WARM)


if __name__ == '__main__':
    ims = [storm(), storm(frame=1), storm('windup'), storm(flash=0.6), storm('cross', minis=False), storm('calm'), fold(0), fold(1)]
    sheet = Image.new('RGBA', (44 * len(ims), 36), (96, 140, 78, 255))
    for i, im in enumerate(ims):
        sheet.alpha_composite(im, (i * 44 + 1, 1))
    sheet.resize((sheet.width * 5, sheet.height * 5), Image.NEAREST).save('storm_sheet.png')
