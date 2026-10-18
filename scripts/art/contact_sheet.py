"""A contact sheet of every zone prop, grouped by region (coherence plan step 11: the
expansion library). Nothing in the game reads it; it is for reviewing the art.
Run: python3 scripts/art/contact_sheet.py out.png
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw  # noqa: E402
import zones  # noqa: E402

GROUPS = [
    ('Valley', None), ('Cogsworth', 'junction'), ('Dust Gulch and the oasis', 'gulch'),
    ('Ember Caldera and Cinder Springs', 'caldera'), ('Neon Harbour and the Skyport', 'neon'),
    ('Driftwood Harbour', 'harbour'), ('Hearthold Castle', 'castle'), ('Halcyon Station', 'station'),
    ('Lumen', 'lumen'), ('The hut', 'home'),
]


def main(out: str, scale: int = 3, width: int = 1400):
    sprites = zones.sprites()
    regional = set()
    for name in zones.REGION_PROPS:
        regional |= zones.region_keys(name)
    rows = []
    for title, zone in GROUPS:
        keys = sorted(zones.region_keys(zone)) if zone else sorted(k for k in sprites if k not in regional)
        keys = [k for k in keys if k in sprites and k not in zones.OVERHEAD]
        rows.append((title, keys))
    pad, label_h = 8, 18
    # measure the sheet: each group a title, then its sprites in wrapped rows
    y = 0
    for _title, keys in rows:
        y += label_h + pad
        x, line_h = pad, 0
        for k in keys:
            w, h = sprites[k].w * scale, sprites[k].h * scale
            if x + w > width - pad:
                x, y = pad, y + line_h + pad
                line_h = 0
            x += w + pad
            line_h = max(line_h, h)
        y += line_h + pad * 2
    sheet = Image.new('RGBA', (width, y + pad), (58, 66, 54, 255))
    draw = ImageDraw.Draw(sheet)
    # titles: written above the first sprite of each group
    y = 0
    for title, keys in rows:
        y_title = y
        draw.text((pad, y_title + 2), title, fill=(242, 236, 220, 255))
        y += label_h + pad
        x, line_h = pad, 0
        for k in keys:
            sp = sprites[k]
            w, h = sp.w * scale, sp.h * scale
            if x + w > width - pad:
                x, y = pad, y + line_h + pad
                line_h = 0
            sheet.alpha_composite(sp.img.resize((w, h), Image.NEAREST), (x, y))
            x += w + pad
            line_h = max(line_h, h)
        y += line_h + pad * 2
    sheet.save(out)
    print('contact sheet', sheet.size, sum(len(k) for _, k in rows), 'props')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/zone-props.png')
