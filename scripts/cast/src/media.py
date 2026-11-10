"""1920x1080 MP4s of Bramble's exported clips in the density-3 woodland (scene.world(), the 960x540
grid scaled exactly 2x, nearest).  Reads out/bramble/*.png and manifest.json, so the videos show
exactly the exported drawings with the manifest's timings.

  python3 media.py actions   -> bramble_actions.mp4  (one Bramble acting out every clip, E and W)
  python3 media.py facings   -> bramble_facings.mp4  (S N E W side by side, every clip in turn)
  python3 media.py still     -> review/bramble_scene.png
"""
import json
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import anim
import scene
from scene import up2, blit, MUL


def shadow(canvas, x, y, rx, ry):
    """House-style hard shadow (scene.shadow), computed in a small window for speed."""
    x0, x1 = int(x - rx - 4), int(x + rx + 6)
    y0, y1 = int(y - ry - 3), int(y + ry + 4)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = ((xx + 0.5 - x - 2) / rx) ** 2 + ((yy + 0.5 - y - 0.5) / ry) ** 2 <= 1
    sub = canvas[y0:y1, x0:x1]
    sub[m] = (sub[m] * MUL).astype(np.uint8)
from ew import Fig
from parts import Rig
import bramble

ROOT = anim.ROOT
OD = os.path.join(ROOT, 'out', 'bramble')
MAN = json.load(open(os.path.join(OD, 'manifest.json')))
FPS = 60
CAM = 200
GX, GY = anim.PIVOT
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
_img = {}


def spr(file):
    if file not in _img:
        _img[file] = np.array(Image.open(os.path.join(OD, file)).convert('RGBA'))
    return _img[file]


def frame_at(clip, fc, t, hold_last=True):
    e = MAN['clips'][clip]
    d = e['durations']
    T = sum(d)
    if e['loop']:
        t = t % T
    acc = 0.0
    for i, x in enumerate(d):
        if t < acc + x:
            return e['facings'][fc]['frames'][i], i
        acc += x
    return e['facings'][fc]['frames'][-1], len(d) - 1


def arrow_sprite():
    f = Fig(40, 16, gx=6, gy=8)
    R = Rig(f, 'E')
    bramble.arrow3(f, R, (0, 0, 0), (1, 0, 0), 1)
    return f.render()


ARROW = None


def put(canvas, fr, x, y):
    blit(canvas, spr(fr['file']), int(x) - GX, int(y) - GY)


def encode(path, fn, n, label=None):
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        c, text = fn(i / FPS)
        big = up2(c)
        if text:
            im = Image.fromarray(big)
            d = ImageDraw.Draw(im)
            d.rectangle((24, 20, 34 + 18 * len(text), 66), fill=(30, 28, 26))
            d.text((34, 24), text, font=FONT, fill=(240, 232, 210))
            big = np.array(im)
        p.stdin.write(big.tobytes())
    p.stdin.close()
    p.wait()


def world():
    return scene.world()[:, CAM:CAM + 960].copy()


# ------------------------------------------------------------------------------- actions
def actions():
    """A timeline of (clip, facing, start time, length, x0, dx per second, extra)."""
    tl = []
    t = 0.0
    x = 250.0
    y = 352.0
    ws = MAN['walk_speed']

    def add(clip, fc, length=None, move=0.0, hold=None):
        nonlocal t, x
        e = MAN['clips'][clip]
        L = length if length is not None else sum(e['durations'])
        tl.append(dict(clip=clip, fc=fc, t0=t, L=L, x0=x, v=move, hold=hold))
        t += L
        x += move * L
    add('idle', 'E', 1.2)
    add('walk', 'E', 2.24, ws)
    add('idle', 'E', 0.5)
    add('idle', 'W', 0.6)
    add('walk', 'W', 2.24, -ws)
    add('idle', 'E', 0.6)
    add('primary', 'E')
    add('idle', 'E', 0.6)
    add('secondary', 'E')
    add('idle', 'E', 0.5)
    add('guard', 'E', 1.3, hold=0.6)
    add('idle', 'E', 0.5)
    add('special', 'E')
    add('powered_idle', 'E', 1.0)
    add('powered_primary', 'E')
    add('powered_idle', 'E', 0.5)
    add('powered_exit', 'E')
    add('idle', 'E', 0.5)
    add('hit', 'E')
    add('idle', 'E', 0.4)
    add('jump', 'E')
    add('idle', 'E', 0.4)
    add('dodge', 'E', None, 150.0)
    add('idle', 'E', 0.5)
    add('defeat', 'E')
    add('defeat', 'E', 1.2)
    total = t
    global ARROW
    ARROW = arrow_sprite()
    shots = []
    for s in tl:
        if s['clip'] in ('primary', 'powered_primary'):
            e = MAN['clips'][s['clip']]
            ra = e['facings']['E']['release_anchor']
            shots.append((s['t0'] + e['release_time'], s['x0'] + ra[0], y + ra[1]))
    trunk = 1000                # the arrows fly on out of frame (the oak stands above his line of fire)

    def fn(tt):
        c = world()
        seg = [s for s in tl if s['t0'] <= tt] [-1]
        lt = tt - seg['t0']
        x = seg['x0'] + seg['v'] * lt
        clip = seg['clip']
        e = MAN['clips'][clip]
        if seg['hold'] is not None:          # guard: raise, hold the brace, then lower
            d = e['durations']
            rise = sum(d[:4])
            if lt < rise:
                fr, _ = frame_at(clip, seg['fc'], lt)
            elif lt < rise + seg['hold']:
                fr = e['facings'][seg['fc']]['frames'][4]
            else:
                fr, _ = frame_at(clip, seg['fc'], lt - seg['hold'])
        elif clip == 'defeat' and lt >= sum(e['durations']) - 1e-6:
            fr = e['facings'][seg['fc']]['frames'][-1]
        else:
            fr, i = frame_at(clip, seg['fc'], lt)
        lift = 0
        if clip == 'jump':                     # the runtime lifts the body during drawings 2 to 4
            d = e['durations']
            a, b = sum(d[:2]), sum(d[:5])
            if a <= lt < b:
                u = (lt - a) / (b - a)
                lift = int(round(30 * 4 * u * (1 - u)))
        shadow(c, x, y, 13 - lift * 0.1, 4.2)
        put(c, fr, x, y - lift)
        for (tf, ax, ay) in shots:
            if tt >= tf:
                ex = min(ax + (tt - tf) * 760.0, trunk)
                blit(c, ARROW, int(ex) - 6 - 20, int(ay) - 8)
        return c, '%s  %s' % (clip, 'west' if seg['fc'] == 'W' else 'east')
    return fn, int(total * FPS)


# ------------------------------------------------------------------------------- facings
def facings():
    order = ['idle', 'walk', 'primary', 'secondary', 'special', 'powered_idle', 'powered_walk', 'powered_primary',
             'powered_guard', 'powered_exit', 'guard', 'hit', 'jump', 'stair_up', 'stair_down', 'dodge', 'defeat']
    tl = []
    t = 0.0
    for c in order:
        e = MAN['clips'][c]
        L = sum(e['durations']) * (2 if e['loop'] else 1) + 0.45
        tl.append((c, t, L))
        t += L
    xs = {'S': 190, 'N': 380, 'E': 570, 'W': 760}
    y = 360

    def fn(tt):
        c = world()
        clip, t0, L = [s for s in tl if s[1] <= tt][-1]
        lt = tt - t0
        e = MAN['clips'][clip]
        T = sum(e['durations'])
        for fc, x in xs.items():
            if not e['loop'] and lt > T:
                fr = e['facings'][fc]['frames'][-1 if clip == 'defeat' else 0] if clip == 'defeat' else MAN['clips']['idle']['facings'][fc]['frames'][0]
            else:
                fr, _ = frame_at(clip, fc, lt)
            shadow(c, x, y, 13, 4.2)
            put(c, fr, x, y)
        return c, '%s   (S  N  E  W)' % clip
    return fn, int(t * FPS)


def still():
    c = world()
    poses = [('primary', 'E', 6, 250), ('guard', 'S', 4, 400), ('secondary', 'W', 5, 560), ('special', 'N', 4, 700)]
    for clip, fc, i, x in poses:
        fr = MAN['clips'][clip]['facings'][fc]['frames'][i]
        shadow(c, x, 360, 13, 4.2)
        put(c, fr, x, 360)
    Image.fromarray(up2(c)).save(os.path.join(ROOT, 'review', 'bramble_scene.png'))


if __name__ == '__main__':
    what = sys.argv[1:] or ['still', 'actions', 'facings']
    if 'still' in what:
        still()
    if 'actions' in what:
        fn, n = actions()
        encode(os.path.join(ROOT, 'review', 'bramble_actions.mp4'), fn, n)
    if 'facings' in what:
        fn, n = facings()
        encode(os.path.join(ROOT, 'review', 'bramble_facings.mp4'), fn, n)
    print('done')
