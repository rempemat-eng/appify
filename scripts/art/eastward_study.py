"""The Eastward edge study (docs/vision/eastward-edges.md): measuring official screenshots.

Matt, 21 Oct 09:23: "can you use only eastward as the example on how to draw edges and the
soft grid". The rules in eastward-edges.md were measured with these steps. The screenshots
stay out of the repository; SHOTS lists the official URL of each one used.

  python3 scripts/art/eastward_study.py scale SHOT.jpg ...          period per shot (FFT)
  python3 scripts/art/eastward_study.py native OUT_DIR SCALE SHOT.jpg ...
                                                                    downscale to native px
  python3 scripts/art/eastward_study.py crops NATIVE_DIR OUT_DIR   the evidence crops
  python3 scripts/art/eastward_study.py trace NATIVE.png down|right X0 Y0 X1 Y1 TEST [L]
                                                                    how an edge steps
  python3 scripts/art/eastward_study.py strip NATIVE.png X Y0 Y1 [W] [h]
                                                                    colours down a column, as runs

TEST for trace: green, notgreen, dark (luminance under L, default 75), light (over L).
"""
import os
import sys

import numpy as np
from PIL import Image

STEAM = 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/'
SHOTS = {   # index in the team's reference folder -> official URL and the scale measured here
    '01': (STEAM + '977880/ss_5d50545b49db3a8502666b4195d2fabd0e31a29d.1920x1080.jpg', 3),
    '12': (STEAM + '2305370/ss_c3e35bbd8e25af924b3b9cbf087f1f0c77dcf68a.1920x1080.jpg', 3),
    '13': (STEAM + '2305370/ss_f5788b1d4ade71e0cdb1e0110debfad3b32ca51c.1920x1080.jpg', 3),
    '15': (STEAM + '2305370/ss_c73bb91589b4ec73ba204ce2fbb402ce849cdc60.1920x1080.jpg', 3.3),
    '16': (STEAM + '2305370/ss_6251ef76241411ab5659482fc644a215ffe4ddcf.1920x1080.jpg', 3),
    '37': ('https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-7_Fishing.jpg', 3.3),
    '39': ('https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-9_Beach.jpg', 3),
}
ADULT_E = 54      # John, feet to crown, native px
ADULT = 25        # ours (size-guide.md)

CROPS = [  # evidence crops named in docs/vision/eastward-edges.md, made locally, never committed: name, shot, box in native px
    ('01-adult', '13', 300, 122, 342, 190),
    ('02-tile-kerb', '16', 196, 218, 332, 246),
    ('03-ledge', '13', 0, 216, 110, 264),
    ('04-diagonal', '13', 94, 220, 126, 254),
    ('05-round-corner', '39', 108, 96, 172, 140),
    ('06-cliff-plan', '12', 28, 0, 180, 84),
    ('07-cliff-face', '12', 36, 24, 132, 132),
    ('08-side', '12', 26, 52, 62, 124),
    ('09-foot', '13', 140, 240, 236, 292),
    ('10-grass-dirt', '12', 140, 242, 252, 300),
    ('11-grass-cobble', '13', 318, 20, 394, 92),
    ('12-bank', '13', 18, 294, 134, 342),
    ('13-pond', '37', 0, 52, 96, 132),
    ('14-stair-farm', '13', 238, 244, 332, 312),
    ('15-stair-city', '01', 280, 150, 380, 262),
    ('16-shadow', '39', 376, 228, 524, 332),
    ('17-plants', '13', 112, 222, 244, 302),
    ('18-dither', '15', 0, 56, 84, 172),
]


def rgb(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.int32)


def period(path):
    """The pixel period across and down: the strongest peak of the FFT of the edge profile."""
    a = np.asarray(Image.open(path).convert('L')).astype(float)
    out = []
    for axis in (1, 0):
        prof = np.abs(np.diff(a, axis=axis)).mean(axis=0 if axis == 1 else 1)
        prof = prof - prof.mean()
        n = len(prof)
        spec = np.abs(np.fft.rfft(prof, n * 8))
        freq = np.fft.rfftfreq(n * 8)
        m = (freq > 1 / 8.0) & (freq < 0.49)
        k = int(np.argmax(spec[m]))
        out.append((1 / freq[m][k], spec[m][k] / np.median(spec[m])))
    return out


def downscale(path, s):
    """Native pixels from a shot shown at scale s (integer or not): find the block phase that
    puts the most edge energy on block boundaries, then take each block's inner median."""
    a = rgb(path)

    def offset(prof):
        best = (-1.0, 0.0)
        for o in np.arange(0, s, 0.05):
            b = np.floor(o + s * np.arange(1, int(len(prof) / s) - 1)).astype(int) - 1
            b = b[(b >= 0) & (b < len(prof))]
            e = prof[b].mean() / prof.mean()
            best = max(best, (e, o))
        return best[1]

    ox = offset(np.abs(np.diff(a, axis=1)).sum(axis=2).sum(axis=0).astype(float))
    oy = offset(np.abs(np.diff(a, axis=0)).sum(axis=2).sum(axis=1).astype(float))
    w, h = int((a.shape[1] - ox) / s), int((a.shape[0] - oy) / s)
    out = np.zeros((h, w, 3), np.uint8)
    for j in range(h):
        y0 = int(np.ceil(oy + s * j))
        y1 = max(int(np.floor(oy + s * (j + 1))), y0 + 1)
        for i in range(w):
            x0 = int(np.ceil(ox + s * i))
            x1 = max(int(np.floor(ox + s * (i + 1))), x0 + 1)
            out[j, i] = np.median(a[y0:y1, x0:x1].reshape(-1, 3), axis=0)
    return Image.fromarray(out)


def trace(path, direction, box, test, level=None):
    """Follow a boundary column by column (or row by row) and say how it steps."""
    x0, y0, x1, y1 = box
    a = rgb(path)[y0:y1, x0:x1]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    green = (g > r + 6) & (g > b + 6)
    m = {'green': green, 'notgreen': ~green,
         'dark': lum < (level or 75), 'light': lum > (level or 200)}[test]
    if direction == 'right':
        m = m.T
    pos = np.array([np.argmax(col) for col in m.T if col.any()], float)
    k = np.arange(len(pos))
    res = pos - np.polyval(np.polyfit(k, pos, 1), k)
    runs, cur = [], 1
    for i in range(1, len(pos)):
        if pos[i] == pos[i - 1]:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    steps = np.abs(np.diff(pos))
    steps = steps[steps > 0].astype(int)
    rep = sorted(((np.mean(pos[p:] == pos[:-p]), p) for p in range(8, min(80, len(pos) // 2))), reverse=True)
    return {'n': len(pos), 'range': float(res.max() - res.min()), 'sd': float(res.std()),
            'run_median': float(np.median(runs)), 'run_mean': float(np.mean(runs)), 'run_max': int(max(runs)),
            'step_sizes': np.bincount(steps)[1:].tolist() if len(steps) else [],
            'repeats': [(p, round(float(s), 2)) for s, p in rep[:3]]}


def strip(path, x, y0, y1, w=2, horizontal=False):
    """The colours down a column (median of w px), as runs of one colour."""
    a = rgb(path)
    s = a[x:x + w, y0:y1].transpose(1, 0, 2) if horizontal else a[y0:y1, x:x + w]
    rows = np.median(s, axis=1).astype(int)
    out, start = [], 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or np.abs(rows[i] - rows[start]).sum() > 24:
            c = rows[start]
            lum = int(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
            out.append('%d-%d (%d px) #%02x%02x%02x L%d' % (y0 + start, y0 + i - 1, i - start, *c, lum))
            start = i
    return out


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == 'scale':
        for p in argv[1:]:
            (px, sx), (py, sy) = period(p)
            print('%s across %.3f (snr %.0f) down %.3f (snr %.0f)' % (os.path.basename(p), px, sx, py, sy))
    elif cmd == 'native':
        out, s = argv[1], float(argv[2])
        os.makedirs(out, exist_ok=True)
        for p in argv[3:]:
            name = os.path.splitext(os.path.basename(p))[0]
            downscale(p, s).save(os.path.join(out, name + '.png'))
    elif cmd == 'crops':
        src, out = argv[1], argv[2]
        os.makedirs(out, exist_ok=True)
        for name, shot, x0, y0, x1, y1 in CROPS:
            c = Image.open(os.path.join(src, shot + '.png')).convert('RGB').crop((x0, y0, x1, y1))
            c.save(os.path.join(out, name + '.png'))
            c.resize((c.width * 4, c.height * 4), Image.NEAREST).save(os.path.join(out, name + '-4x.png'))
    elif cmd == 'trace':
        level = float(argv[8]) if len(argv) > 8 else None
        print(trace(argv[1], argv[2], tuple(map(int, argv[3:7])), argv[7], level))
    elif cmd == 'strip':
        w = int(argv[5]) if len(argv) > 5 else 2
        print('\n'.join(strip(argv[1], *map(int, argv[2:5]), w=w, horizontal=len(argv) > 6 and argv[6] == 'h')))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
