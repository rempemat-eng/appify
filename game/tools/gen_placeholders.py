"""Placeholder sprites until the redrawn cast lands: game/art/placeholder/{player,mossling,sign}.png.

    python3 game/tools/gen_placeholders.py

Each sheet is one row of four facings (S, E, N, W), drawn on the density-3 texel grid with a dark outline
and upper-left light, so scale and readability can be judged in the scene. They are stand-ins: swap the
texture and frame size in actors/*.tscn when the cast's sheets arrive.
"""
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'art', 'placeholder')
INK = (40, 30, 38, 255)


def blob(d, box, fill, light):
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=INK)
    d.ellipse((x0 + 2, y0 + 2, x1 - 2, y1 - 2), fill=fill)
    d.ellipse((x0 + 5, y0 + 4, x0 + (x1 - x0) // 2, y0 + (y1 - y0) // 2), fill=light)


def sheet(name, w, h, body, light, accent, tall):
    im = Image.new('RGBA', (w * 4, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, face in enumerate('SENW'):
        ox = i * w
        d.ellipse((ox + 6, h - 7, ox + w - 6, h - 1), fill=(20, 30, 20, 90))  # contact shadow
        if tall:
            blob(d, (ox + 9, h - 30, ox + w - 9, h - 3), body, light)  # body
            blob(d, (ox + 7, 2, ox + w - 7, 26), (236, 200, 160, 255), (250, 226, 196, 255))  # head
            eyes = {'S': [(-5, 0), (3, 0)], 'E': [(5, 0)], 'W': [(-7, 0)], 'N': []}[face]
            for ex, ey in eyes:
                d.rectangle((ox + w // 2 + ex, 14 + ey, ox + w // 2 + ex + 2, 17 + ey), fill=INK)
            d.rectangle((ox + 12, 1, ox + w - 12, 6), fill=accent)  # cap brim marks the top
        else:
            blob(d, (ox + 3, 4, ox + w - 3, h - 3), body, light)
            eyes = {'S': [(-6, 0), (4, 0)], 'E': [(6, 0)], 'W': [(-8, 0)], 'N': []}[face]
            for ex, ey in eyes:
                d.rectangle((ox + w // 2 + ex, 13 + ey, ox + w // 2 + ex + 2, 16 + ey), fill=accent)
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, f'{name}.png'), optimize=True)


def signpost():
    im = Image.new('RGBA', (33, 42), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 36, 27, 41), fill=(20, 30, 20, 90))
    d.rectangle((14, 14, 19, 39), fill=INK)
    d.rectangle((15, 15, 18, 38), fill=(120, 80, 50, 255))
    d.rectangle((1, 2, 31, 21), fill=INK)
    d.rectangle((2, 3, 30, 20), fill=(170, 120, 72, 255))
    d.rectangle((2, 3, 30, 5), fill=(204, 156, 100, 255))
    for y in (9, 13, 17):
        d.rectangle((6, y, 26 - (y % 3) * 2, y), fill=(110, 70, 44, 255))
    im.save(os.path.join(OUT, 'sign.png'), optimize=True)


if __name__ == '__main__':
    sheet('player', 36, 54, (70, 110, 170, 255), (110, 150, 205, 255), (200, 80, 60, 255), tall=True)
    sheet('mossling', 36, 30, (96, 140, 70, 255), (140, 180, 96, 255), (250, 230, 120, 255), tall=False)
    signpost()
    print('wrote', OUT)
