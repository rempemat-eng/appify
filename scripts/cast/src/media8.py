"""Contract v2 media for Matt (written to the scratchpad review folder, never committed).

  python3 media8.py sheets   -> review/v2/<id>_<clip>_8.png: every drawing of idle, walk and the
                                primary in all eight facings at 4x (rows S SE E NE N NW W SW)
  python3 media8.py video    -> review/v2/bramble_v2.mp4: 1920x1080, 60 fps, Bramble walks a full
                                circle (the facing follows the movement), idles into a fidget,
                                then shoots in all eight directions; arrows leave from each
                                facing's release_anchor and fly along the facing, with a ground
                                shadow under each.
Reads out/<id>/manifest.json and the exported PNGs, so it shows exactly the exported drawings
with the manifest's timings.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import anim
import scene
from scene import up2, blit, MUL

ROOT = anim.ROOT
OUT = os.path.join(ROOT, 'review', 'v2')
GX, GY = anim.PIVOT
FPS = 60
F8 = anim.FACINGS8
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
SFONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)


def load(cid):
    od = os.path.join(ROOT, 'out', cid)
    man = json.load(open(os.path.join(od, 'manifest.json')))
    cache = {}

    def spr(file):
        if file not in cache:
            cache[file] = np.array(Image.open(os.path.join(od, file)).convert('RGBA'))
        return cache[file]
    return man, spr


# ------------------------------------------------------------------------------------ sheets
def sheets(cid, clips=('idle', 'walk', 'primary'), z=4, out=None):
    """4x sheets: one row per facing the manifest has, then the turn in-betweens (V2.9)."""
    man, spr = load(cid)
    out = out or OUT
    os.makedirs(out, exist_ok=True)
    paths = []
    for clip in clips:
        ce = man['clips'][clip]
        rows = [(fc, ce['facings'][fc]) for fc in man['directions']] + [('%s turn' % d, te) for d, te in ce.get('turns', {}).items()]
        boxes = [fr['packed_bounds'] for _, fe in rows for fr in fe['frames']]
        x0 = max(0, min(b[0] for b in boxes) - 3)
        x1 = min(anim.CELL[0], max(b[2] for b in boxes) + 3)
        y0 = max(0, min(b[1] for b in boxes) - 3)
        y1 = GY + 5
        w, h = (x1 - x0) * z, (y1 - y0) * z
        n = ce['frame_count']
        lw, top = 60, 56
        lw = 150
        S = Image.new('RGB', (lw + n * (w + 6), top + len(rows) * (h + 6) + 30), (40, 42, 46))
        d = ImageDraw.Draw(S)
        rel = ce.get('release_frame')
        d.text((8, 10), '%s  %s  (%d drawings, %.3f s%s)  4x' % (man['name'], clip, n, ce['duration'],
                                                                 ', release %d at %.3f s' % (rel, ce['release_time']) if rel is not None else ''),
               font=FONT, fill=(236, 230, 214))
        for i, dur in enumerate(ce['durations']):
            d.text((lw + i * (w + 6) + 4, top - 22), '%d  %dms%s' % (i, round(dur * 1000), '  REL' if rel == i else ''), font=SFONT,
                   fill=(255, 210, 120) if rel == i else (200, 196, 186))
        for r, (fc, fe) in enumerate(rows):
            Y = top + r * (h + 6)
            d.text((10, Y + h // 2 - 10), fc, font=FONT, fill=(236, 230, 214))
            for i, fr in enumerate(fe['frames']):
                cell = Image.new('RGBA', (x1 - x0, y1 - y0), (126, 159, 80, 255))
                cell.alpha_composite(Image.fromarray(spr(fr['file'])).crop((x0, y0, x1, y1)))
                X = lw + i * (w + 6)
                S.paste(cell.resize((w, h), Image.NEAREST).convert('RGB'), (X, Y))
                d.line([(X, Y + (GY - y0) * z), (X + w, Y + (GY - y0) * z)], fill=(70, 96, 50))
                an = fe.get('release_anchor_name')
                if an and rel is not None and i in (rel, rel - 1) and fr['anchors'].get(an):
                    ax, ay = fr['anchors'][an]
                    px, py = X + (GX + ax - x0) * z, Y + (GY + ay - y0) * z
                    d.ellipse([px - 5, py - 5, px + 5, py + 5], outline=(255, 80, 200), width=2)
        p = os.path.join(out, '%s_%s.png' % (cid, clip))
        S.save(p)
        paths.append(p)
    return paths


# ------------------------------------------------------------------------------------ video
def shadow(canvas, x, y, rx, ry):
    x0, x1 = int(x - rx - 4), int(x + rx + 6)
    y0, y1 = int(y - ry - 3), int(y + ry + 4)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = ((xx + 0.5 - x - 2) / rx) ** 2 + ((yy + 0.5 - y - 0.5) / ry) ** 2 <= 1
    sub = canvas[y0:y1, x0:x1]
    sub[m] = (sub[m] * MUL).astype(np.uint8)


def nearest(v, cur=None, hyst=math.radians(10)):
    a = math.atan2(v[1], v[0])
    vec = {k: anim.FACING_VEC[k] for k in F8}

    def diff(fc):
        b = math.atan2(vec[fc][1], vec[fc][0])
        return abs((a - b + math.pi) % (2 * math.pi) - math.pi)
    if cur and diff(cur) <= math.pi / 8 + hyst:
        return cur
    return min(F8, key=diff)


def frame_at(man, clip, fc, t, loop=None):
    e = man['clips'][clip]
    d = e['durations']
    T = sum(d)
    if loop if loop is not None else e['loop']:
        t = t % T
    acc = 0.0
    for i, x in enumerate(d):
        if t < acc + x:
            return e['facings'][fc]['frames'][i], i
        acc += x
    return e['facings'][fc]['frames'][-1], len(d) - 1


ARROW_COL = dict(shaft=(222, 158, 78), head=(154, 162, 176), headl=(214, 218, 224), fl=(228, 224, 218), ink=(30, 25, 23))


def draw_arrow(c, x, y, dx, dy, gy):
    """A flying arrow: 1 px shaft, steel head, fletching, outlined; its shadow on the ground at gy."""
    L = 20
    pts = []
    for i in range(L + 1):
        pts.append((int(round(x - dx * i)), int(round(y - dy * i))))
    # ground shadow
    for i in range(0, L, 1):
        sx, sy = int(round(x - dx * i)), int(round(gy - dy * i * 0.0))
        if 0 <= sy < c.shape[0] and 0 <= sx < c.shape[1]:
            c[sy, sx] = (c[sy, sx] * MUL).astype(np.uint8)
    for (px, py) in pts:                         # outline first
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= py + oy < c.shape[0] and 0 <= px + ox < c.shape[1]:
                c[py + oy, px + ox] = ARROW_COL['ink']
    for i, (px, py) in enumerate(pts):
        if 0 <= py < c.shape[0] and 0 <= px < c.shape[1]:
            c[py, px] = ARROW_COL['head'] if i < 3 else (ARROW_COL['fl'] if i > L - 4 else ARROW_COL['shaft'])
    hx, hy = pts[0]
    if 0 <= hy < c.shape[0] and 0 <= hx < c.shape[1]:
        c[hy, hx] = ARROW_COL['headl']


def video(cid='bramble'):
    man, spr = load(cid)
    os.makedirs(OUT, exist_ok=True)
    ws = man['walk_speed']
    world = scene.world()[:, 200:1160].copy()
    cx, cy, R = 470.0, 388.0, 95.0              # an open stretch of the woodland: no props on the circle
    circ = 2 * math.pi * R / ws
    tl = []                                       # (t0, length, kind, data)
    t = 0.0
    tl.append((t, 0.8, 'idle', dict(fc='N', x=cx + R, y=cy)))       # facing the way he will walk
    t += 0.8
    tl.append((t, circ, 'circle', {}))
    t += circ
    end = (cx + R, cy)
    tl.append((t, 0.6, 'idle', dict(fc='N', x=end[0], y=end[1])))     # stops facing the way he walked ...
    t += 0.6
    tl.append((t, 3.4, 'idle', dict(fc='S', x=end[0], y=end[1])))     # ... then faces the camera (4 s of idle in all)
    t += 3.4
    fid = man['idle_fidgets']['clips'][0]
    L = man['clips'][fid]['duration']
    tl.append((t, L, 'fidget', dict(fc='S', x=end[0], y=end[1], clip=fid)))
    t += L
    tl.append((t, 0.8, 'idle', dict(fc='S', x=end[0], y=end[1])))
    t += 0.8
    shots = []
    for fc in F8:
        e = man['clips']['primary']
        tl.append((t, e['duration'], 'shot', dict(fc=fc, x=end[0], y=end[1])))
        ra = e['facings'][fc]['release_anchor']
        shots.append((t + e['release_time'], end[0] + ra[0], end[1] + ra[1], -ra[1], anim.FACING_VEC[fc]))
        t += e['duration']
        tl.append((t, 0.3, 'idle', dict(fc=fc, x=end[0], y=end[1])))
        t += 0.3
    tl.append((t, 1.2, 'idle', dict(fc='SW', x=end[0], y=end[1])))
    t += 1.2
    total = t
    state = dict(fc='E')

    def fn(tt):
        c = world.copy()
        seg = [s for s in tl if s[0] <= tt][-1]
        t0, L, kind, d = seg
        lt = tt - t0
        label = ''
        if kind == 'circle':
            ang = lt / circ * 2 * math.pi            # counter-clockwise on screen, from the east point
            x, y = cx + R * math.cos(-ang), cy + R * math.sin(-ang)
            v = (-math.sin(ang), -math.cos(ang))      # d(x, y)/d(ang)
            state['fc'] = nearest(v, state['fc'])
            fr, _ = frame_at(man, 'walk', state['fc'], tt - tl[1][0])
            label = 'walk  %s  (%.1f px/s)' % (state['fc'], ws)
        elif kind == 'idle':
            x, y = d['x'], d['y']
            fr, _ = frame_at(man, 'idle', d['fc'], lt)
            label = 'idle  %s' % d['fc']
        elif kind == 'fidget':
            x, y = d['x'], d['y']
            fr, _ = frame_at(man, d['clip'], d['fc'], lt, loop=False)
            label = '%s  %s  (after 4 s of idle)' % (d['clip'], d['fc'])
        else:
            x, y = d['x'], d['y']
            fr, _ = frame_at(man, 'primary', d['fc'], lt, loop=False)
            label = 'primary  %s' % d['fc']
        shadow(c, x, y, 13, 4.2)
        blit(c, spr(fr['file']), int(round(x)) - GX, int(round(y)) - GY)
        for (tf, ax, ay, h, (vx, vy)) in shots:
            if tt >= tf:
                s = (tt - tf) * 700.0
                px, py = ax + vx * s, ay + vy * s
                if -30 < px < 990 and -30 < py < 570:
                    draw_arrow(c, px, py, vx, vy, py + h)
        return c, label

    if os.environ.get('CROPS'):          # review aid: every 2nd frame cropped round him, tiled
        tiles = []
        for i in range(0, int(total * FPS), 2):
            tt = i / FPS
            c, text = fn(tt)
            seg = [s_ for s_ in tl if s_[0] <= tt][-1]
            if seg[2] == 'circle':
                ang = (tt - seg[0]) / circ * 2 * math.pi
                x, y = cx + R * math.cos(ang), cy - R * math.sin(ang)
            else:
                x, y = seg[3]['x'], seg[3]['y']
            x0, y0 = int(x) - 60, int(y) - 100
            crop = Image.fromarray(c[max(0, y0):y0 + 120, max(0, x0):x0 + 120]).resize((240, 240), Image.NEAREST)
            dd = ImageDraw.Draw(crop)
            dd.text((3, 2), '%d %s' % (i, text[:22]), font=SFONT, fill=(255, 255, 255))
            tiles.append(crop)
        for k in range(0, len(tiles), 96):
            sh = Image.new('RGB', (240 * 16, 240 * 6))
            for j, t_ in enumerate(tiles[k:k + 96]):
                sh.paste(t_, (240 * (j % 16), 240 * (j // 16)))
            sh.save(os.path.join(OUT, 'frames_%02d.png' % (k // 96)))
        return None, total
    path = os.path.join(OUT, '%s_v2.mp4' % cid)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        c, text = fn(i / FPS)
        big = up2(c)
        im = Image.fromarray(big)
        dr = ImageDraw.Draw(im)
        dr.rectangle((24, 20, 40 + 17 * len(text), 66), fill=(30, 28, 26))
        dr.text((34, 24), text, font=FONT, fill=(240, 232, 210))
        p.stdin.write(np.array(im).tobytes())
    p.stdin.close()
    p.wait()
    return path, total


if __name__ == '__main__':
    what = sys.argv[1:] or ['sheets', 'video']
    if 'sheets' in what:
        for cid in ('bramble', 'velvet'):
            print(sheets(cid))
    if 'video' in what:
        print(video('bramble'))


# ------------------------------------------------------------------------------------ aims (26 Oct)
F4 = ('S', 'E', 'N', 'W')


def pick(v):
    """The runtime's choice: nearest body facing (a tie goes to S or N), then the nearest aim."""
    a = math.degrees(math.atan2(v[1], v[0]))
    best, bd = 'S', 1e9
    for fc in ('S', 'N', 'E', 'W'):
        fx, fy = anim.FACING_VEC[fc]
        d = abs((a - math.degrees(math.atan2(fy, fx)) + 180) % 360 - 180)
        if d < bd - 1e-6:
            best, bd = fc, d
    fx, fy = anim.FACING_VEC[best]
    rel = (a - math.degrees(math.atan2(fy, fx)) + 180) % 360 - 180
    deg = min(anim.AIM_DEGS, key=lambda d: abs(d - rel))
    return best, anim.AIM_TAG[deg]


def aim_sheet(cid, clip='primary', idx=None, z=4, label='full draw', suffix=''):
    """4x: rows = the four body facings, columns = the five aims, at the full draw (and the
    release anchor marked); then one strip per facing with every drawing of every aim."""
    man, spr = load(cid)
    ce = man['clips'][clip]
    rel = ce['release_frame']
    idx = rel - 1 if idx is None else idx
    tags = [anim.AIM_TAG[d] for d in anim.AIM_DEGS]
    x0, y0, x1, y1 = 30, 22, 130, GY + 5
    w, h = (x1 - x0) * z, (y1 - y0) * z
    S = Image.new('RGB', (70 + 5 * (w + 8), 60 + 4 * (h + 30)), (40, 42, 46))
    d = ImageDraw.Draw(S)
    an = ce['facings']['E'].get('release_anchor_name')
    ai = rel if an and an in ce['facings']['E']['frames'][rel]['anchors'] else rel - 1      # the drawing the release anchor is on
    d.text((8, 10), '%s  %s  %s (drawing %d) in 4 body facings x 5 aims = 16 directions  4x%s' % (
        man['name'], clip, label, idx, '   release anchor (pink) on this drawing' if idx == ai else '   (aim line from the release anchor of drawing %d)' % ai),
        font=FONT, fill=(236, 230, 214))
    for r, fc in enumerate(F4):
        Y = 56 + r * (h + 30)
        d.text((12, Y + h // 2), fc, font=FONT, fill=(236, 230, 214))
        for c, tag in enumerate(tags):
            ae = ce['facings'][fc]['aims'][tag]
            fr = ae['frames'][idx]
            cell = Image.new('RGBA', (x1 - x0, y1 - y0), (126, 159, 80, 255))
            cell.alpha_composite(Image.fromarray(spr(fr['file'])).crop((x0, y0, x1, y1)))
            X = 70 + c * (w + 8)
            S.paste(cell.resize((w, h), Image.NEAREST).convert('RGB'), (X, Y))
            ax, ay = ae['release_anchor']
            px, py = X + (GX + ax - x0) * z, Y + (GY + ay - y0) * z
            sx, sy = ae['screen']
            d.line([(px, py), (px + sx * 90, py + sy * 90)], fill=(255, 80, 200), width=3)
            if idx == ai:
                d.ellipse([px - 6, py - 6, px + 6, py + 6], outline=(255, 80, 200), width=3)
            d.text((X + 6, Y + h + 4), '%s  %+.1f deg' % (tag, ae['deg']), font=SFONT, fill=(220, 214, 200))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, '%s_%s_aims%s.png' % (cid, clip, suffix))
    S.save(p)
    paths = [p]
    for fc in F4:                       # every drawing of every aim, one sheet per facing
        n = ce['frame_count']
        T = Image.new('RGB', (60 + n * (w // 2 + 4), 50 + 5 * (h // 2 + 6)), (40, 42, 46))
        dd = ImageDraw.Draw(T)
        dd.text((8, 8), '%s %s %s: every drawing in every aim (2x)' % (man['name'], clip, fc), font=FONT, fill=(236, 230, 214))
        for r, tag in enumerate(tags):
            for i, fr in enumerate(ce['facings'][fc]['aims'][tag]['frames']):
                cell = Image.new('RGBA', (x1 - x0, y1 - y0), (126, 159, 80, 255))
                cell.alpha_composite(Image.fromarray(spr(fr['file'])).crop((x0, y0, x1, y1)))
                T.paste(cell.resize((w // 2, h // 2), Image.NEAREST).convert('RGB'), (60 + i * (w // 2 + 4), 46 + r * (h // 2 + 6)))
            dd.text((6, 46 + r * (h // 2 + 6) + h // 4), tag, font=SFONT, fill=(236, 230, 214))
        q = os.path.join(OUT, '%s_%s_aims_%s.png' % (cid, clip, fc))
        T.save(q)
        paths.append(q)
    return paths


def aim_video(cid='bramble'):
    """1080p: Bramble shoots in 16 directions (every 22.5 degrees, clockwise from east); each shot
    picks the body facing and the aim as the runtime does; the arrow leaves the aim's release
    anchor and flies along the exact direction, with its ground shadow."""
    man, spr = load(cid)
    world = scene.world()[:, 200:1160].copy()
    x, y = 470.0, 388.0
    e = man['clips']['primary']
    tl, t = [], 0.0
    shots = []
    tl.append((t, 0.8, 'idle', 'E', None))
    t += 0.8
    for k in range(16):
        a = math.radians(22.5 * k)
        v = (math.cos(a), math.sin(a))
        fc, tag = pick(v)
        tl.append((t, e['duration'], 'shot', fc, tag))
        ae = e['facings'][fc]['aims'][tag]
        ra = ae['release_anchor']
        shots.append((t + e['release_time'], x + ra[0], y + ra[1], -ra[1], v))
        t += e['duration']
        tl.append((t, 0.35, 'idle', fc, None))
        t += 0.35
    total = t + 0.6

    def fn(tt):
        c = world.copy()
        seg = [s for s in tl if s[0] <= tt][-1]
        t0, L, kind, fc, tag = seg
        lt = tt - t0
        if kind == 'idle':
            fr, _ = frame_at(man, 'idle', fc, lt)
            label = 'idle  %s' % fc
        else:
            frs = e['facings'][fc]['aims'][tag]['frames']
            acc, fr = 0.0, frs[-1]
            for i, du in enumerate(e['durations']):
                if lt < acc + du:
                    fr = frs[i]
                    break
                acc += du
            label = 'primary  %s  aim %s (%+.1f deg)' % (fc, tag, e['facings'][fc]['aims'][tag]['deg'])
        shadow(c, x, y, 13, 4.2)
        blit(c, spr(fr['file']), int(x) - GX, int(y) - GY)
        for (tf, ax, ay, h, (vx, vy)) in shots:
            if tt >= tf:
                s_ = (tt - tf) * 700.0
                px, py = ax + vx * s_, ay + vy * s_
                if -30 < px < 990 and -30 < py < 570:
                    draw_arrow(c, px, py, vx, vy, py + h)
        return c, label
    path = os.path.join(OUT, '%s_aim.mp4' % cid)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(total * FPS)
    crops = []
    for i in range(n):
        c, text = fn(min(i / FPS, t))
        if i % 2 == 0:
            cr = Image.fromarray(c[int(y) - 110:int(y) + 20, int(x) - 80:int(x) + 80]).resize((320, 260), Image.NEAREST)
            ImageDraw.Draw(cr).text((3, 2), '%d %s' % (i, text[:30]), font=SFONT, fill=(255, 255, 255))
            crops.append(cr)
        big = up2(c)
        im = Image.fromarray(big)
        dr = ImageDraw.Draw(im)
        dr.rectangle((24, 20, 40 + 17 * len(text), 66), fill=(30, 28, 26))
        dr.text((34, 24), text, font=FONT, fill=(240, 232, 210))
        p.stdin.write(np.array(im).tobytes())
    p.stdin.close()
    p.wait()
    for k in range(0, len(crops), 72):
        sh = Image.new('RGB', (320 * 12, 260 * 6))
        for j, cr in enumerate(crops[k:k + 72]):
            sh.paste(cr, (320 * (j % 12), 260 * (j // 12)))
        sh.save(os.path.join(OUT, 'aim_frames_%02d.png' % (k // 72)))
    return path, total


# ------------------------------------------------------------------------------------ turns (26 Oct)
def facing4(v, cur=None, hyst=math.radians(10)):
    """CastSprite.facing_for: nearest of S N E W (a tie to S or N), kept within its quarter + 10 deg."""
    a = math.atan2(v[1], v[0])

    def diff(fc):
        fx, fy = anim.FACING_VEC[fc]
        return abs((a - math.atan2(fy, fx) + math.pi) % (2 * math.pi) - math.pi)
    if cur in ('S', 'N', 'E', 'W') and diff(cur) <= math.pi / 4 + hyst:
        return cur
    return min(('S', 'N', 'E', 'W'), key=lambda f: (round(diff(f), 6), f not in ('S', 'N')))


def turn_steps(a_fc, b_fc, hint=(0.0, 0.0)):
    """CastSprite.turn_steps (the same rule, for the media)."""
    if a_fc == b_fc:
        return []
    a, b = np.array(anim.FACING_VEC[a_fc], float), np.array(anim.FACING_VEC[b_fc], float)

    def near(v, opts):
        ang = math.atan2(v[1], v[0])
        return min(opts, key=lambda f: abs((ang - math.atan2(anim.FACING_VEC[f][1], anim.FACING_VEC[f][0]) + math.pi) % (2 * math.pi) - math.pi))
    if abs(a.dot(b)) < 0.5:
        return [near(a + b, F8)]
    cr = a[0] * hint[1] - a[1] * hint[0]
    s = float(np.sign(cr)) if math.hypot(*hint) > 0.01 else 0.0
    if s == 0.0:
        s = float(np.sign(a[0] * 1.0 - a[1] * 0.0)) if a_fc in ('E', 'W') else (1.0 if a_fc == 'N' else -1.0)
    c, sn = math.cos(s * math.pi / 2), math.sin(s * math.pi / 2)
    mid = np.array([a[0] * c - a[1] * sn, a[0] * sn + a[1] * c])
    return [near(a + mid, F8), near(mid, ('S', 'N', 'E', 'W')), near(mid + b, F8)]


def turn_video(cid='bramble'):
    """Side by side, the same walk and the same turns: left the old snap between the four facings,
    right the turn in-betweens (V2.9).  1920x1080, 60 fps."""
    man, spr = load(cid)
    ti = man['turn_inbetweens']
    ws = man['walk_speed']
    full = scene.world()[:, 200:1160]
    world = full[:, 230:710].copy()             # 480 x 540 per panel
    cx, cy, R = 240.0, 388.0, 95.0
    circ = 2 * math.pi * R / ws
    # timeline of (t0, length, kind, data): idle facing a way, the circle, then turns on the spot
    tl, t = [], 0.0
    tl.append((t, 0.8, 'idle', dict(fc='N'))); t += 0.8
    tl.append((t, circ, 'circle', {})); t += circ
    spot = ['N', 'W', 'S', 'E', 'N', 'E', 'W', 'E', 'S', 'N', 'S']
    for fc in spot:
        tl.append((t, 0.75, 'idle', dict(fc=fc))); t += 0.75
    tl.append((t, 0.8, 'idle', dict(fc='S'))); t += 0.8
    total = t
    end = (cx + R, cy)

    def target(tt):
        seg = [s for s in tl if s[0] <= tt][-1]
        t0, L, kind, d = seg
        if kind == 'circle':
            ang = (tt - t0) / circ * 2 * math.pi
            return 'walk', (cx + R * math.cos(-ang), cy + R * math.sin(-ang)), (-math.sin(ang), -math.cos(ang)), tt - t0
        i = tl.index(seg)
        prev = tl[i - 1][3].get('fc') if i > 0 else None
        hint = anim.FACING_VEC[d['fc']]
        if prev is not None:                    # a turn on the spot toward the new way: the input swings from the side
            pv = np.array(anim.FACING_VEC[prev], float)
            nv = np.array(anim.FACING_VEC[d['fc']], float)
            if pv.dot(nv) < -0.5:               # a reversal: the stick sweeps round clockwise, then counter-clockwise
                k = sum(1 for s in tl[:i] if s[2] == 'idle')
                rot = 1 if k % 2 else -1
                hint = tuple(nv * 0.9 + np.array([-pv[1], pv[0]]) * 0.3 * rot)
        return 'idle', end, hint, tt - t0, d['fc']

    st_snap = dict(fc='N')
    st = dict(fc='N', path=[], hold=0.0, clip='idle', ct=0.0)
    n = int(total * FPS)
    path = os.path.join(OUT, '%s_turns.mp4' % cid)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    tiles = []
    dt = 1.0 / FPS
    for i in range(n):
        tt = i / FPS
        tg = target(tt)
        clip, (x, y) = tg[0], tg[1]
        if clip == 'walk':
            want = facing4(tg[2], st['fc'])
            want_snap = facing4(tg[2], st_snap['fc'])
        else:
            want = want_snap = tg[4]
        hint = tg[2]
        # the turn rule (V2.9), as CastSprite does it
        if clip != st['clip']:
            st['clip'], st['ct'] = clip, 0.0
        if want != st['fc']:
            st['path'] = turn_steps(st['fc'], want, hint)
            st['step'] = ti['hold_180'] if len(st['path']) > 1 else ti['hold']
            st['hold'] = st['step']
            st['fc'] = want
        else:
            if st['path']:
                st['hold'] -= dt
                while st['hold'] <= 0 and st['path']:
                    st['path'].pop(0)
                    st['hold'] += st['step']
        st_snap['fc'] = want_snap
        ct = tg[3]
        e = man['clips'][clip]
        _, idx = frame_at(man, clip, 'S', ct)
        shown = st['path'][0] if st['path'] else st['fc']
        fr_new = (e['turns'][shown] if shown in e.get('turns', {}) else e['facings'][shown])['frames'][idx]
        fr_old = e['facings'][st_snap['fc']]['frames'][idx]
        panels = []
        for fr, lab, fc in ((fr_old, 'before: snaps between 4 facings', st_snap['fc']), (fr_new, 'now: turn in-betweens', shown)):
            c = world.copy()
            shadow(c, x, y, 13, 4.2)
            blit(c, spr(fr['file']), int(round(x)) - GX, int(round(y)) - GY)
            im = Image.fromarray(up2(c))
            dr = ImageDraw.Draw(im)
            text = '%s   %s %s' % (lab, clip, fc)
            dr.rectangle((16, 16, 30 + 15 * len(text), 58), fill=(30, 28, 26))
            dr.text((26, 20), text, font=SFONT if False else FONT.font_variant(size=26), fill=(240, 232, 210))
            panels.append(np.array(im))
        frame = np.concatenate(panels, axis=1)
        frame[:, 958:962] = (30, 28, 26)
        proc.stdin.write(frame.tobytes())
        if i % 3 == 0:
            x0, y0 = int(x) - 50, int(y) - 95
            crop = np.concatenate([p_[2 * max(0, y0):2 * (y0 + 110), 2 * max(0, x0) + o:2 * (x0 + 100) + o] for p_, o in ((frame, 0), (frame, 960))], axis=1)
            ti_ = Image.fromarray(crop).resize((200, 110), Image.NEAREST)
            ImageDraw.Draw(ti_).text((2, 1), '%d %s>%s' % (i, st_snap['fc'], shown), font=SFONT, fill=(255, 255, 255))
            tiles.append(ti_)
    proc.stdin.close()
    proc.wait()
    for k in range(0, len(tiles), 120):
        sh = Image.new('RGB', (200 * 12, 110 * 10))
        for j, t_ in enumerate(tiles[k:k + 120]):
            sh.paste(t_, (200 * (j % 12), 110 * (j // 12)))
        sh.save(os.path.join(OUT, 'turn_frames_%02d.png' % (k // 120)))
    return path, total


# ------------------------------------------------------------------------------------ polish (26 Oct)
def polish_video(cid='bramble', before_dir=None):
    """Side by side at 1080p: left the drawings and timing before the polish pass, right after.
    The same sequence on both: a walk across and back (with the turn), the shot east and north-east
    (aim p22... as the facing allows), the billhook, the hit and the dodge, then the shot again at
    half speed."""
    import json as _j
    man_a, spr_a = load(cid)
    od_b = before_dir
    man_b = _j.load(open(os.path.join(od_b, 'manifest.json')))
    cache = {}

    def spr_b(file):
        if file not in cache:
            cache[file] = np.array(Image.open(os.path.join(od_b, file)).convert('RGBA'))
        return cache[file]
    full = scene.world()[:, 200:1160]
    world = full[:, 230:710].copy()
    seq = [('idle', 'E', 1.2, 1.0), ('walk', 'E', 2.0, 1.0), ('walk', 'W', 2.0, 1.0), ('idle', 'S', 1.0, 1.0),
           ('primary', 'E', None, 1.0), ('idle', 'E', 0.4, 1.0), ('secondary', 'E', None, 1.0), ('idle', 'E', 0.4, 1.0),
           ('hit', 'E', None, 1.0), ('dodge', 'E', None, 1.0), ('idle', 'E', 0.5, 1.0),
           ('primary', 'E', None, 0.5), ('idle', 'E', 0.6, 1.0), ('secondary', 'E', None, 0.5), ('idle', 'E', 0.8, 1.0)]
    tl, t = [], 0.0
    for clip, fc, L, sp in seq:
        L = L if L is not None else man_a['clips'][clip]['duration'] / sp
        tl.append((t, L, clip, fc, sp))
        t += L
    total = t
    x0 = 240.0
    path = os.path.join(OUT, '%s_polish.mp4' % cid)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ws_a, ws_b = man_a['walk_speed'], man_b['walk_speed']
    tiles = []
    for i in range(int(total * FPS)):
        tt = i / FPS
        t0, L, clip, fc, sp = [s for s in tl if s[0] <= tt][-1]
        lt = (tt - t0) * sp
        panels = []
        for man, spr, ws, lab in ((man_b, spr_b, ws_b, 'before polish'), (man_a, spr_a, ws_a, 'after polish')):
            x = x0
            if clip == 'walk':                       # across and back from the centre
                d = ws * lt * (1 if fc == 'E' else -1)
                x = x0 - ws * 1.0 + d if fc == 'E' else x0 + ws * 1.0 + d
            fr, idx = frame_at(man, clip, fc, lt, loop=man['clips'][clip]['loop'])
            c = world.copy()
            shadow(c, x, 388, 13, 4.2)
            blit(c, spr(fr['file']), int(round(x)) - GX, 388 - GY)
            im = Image.fromarray(up2(c))
            dr = ImageDraw.Draw(im)
            text = '%s   %s %s #%d%s' % (lab, clip, fc, idx, '  (half speed)' if sp < 1 else '')
            dr.rectangle((16, 16, 30 + 15 * len(text), 58), fill=(30, 28, 26))
            dr.text((26, 20), text, font=FONT.font_variant(size=26), fill=(240, 232, 210))
            panels.append(np.array(im))
        frame = np.concatenate(panels, axis=1)
        frame[:, 958:962] = (30, 28, 26)
        proc.stdin.write(frame.tobytes())
        if i % 4 == 0:
            tiles.append(Image.fromarray(frame).resize((480, 270), Image.NEAREST))
    proc.stdin.close()
    proc.wait()
    for k in range(0, len(tiles), 40):
        sh = Image.new('RGB', (480 * 5, 270 * 8))
        for j, t_ in enumerate(tiles[k:k + 40]):
            sh.paste(t_, (480 * (j % 5), 270 * (j // 5)))
        sh.save(os.path.join(OUT, 'polish_frames_%02d.png' % (k // 40)))
    return path, total


# ------------------------------------------------------------------------------------ batch video
def batch_video(cids, name, out_dir):
    """1080p: the characters side by side (one panel each), each walking a square with the turn
    in-betweens (V2.9), idling into each fidget, then its action clip (primary, or work for the
    folk) in two facings, the weapon clips at three aims.  Timing from each manifest."""
    mans = {c: load(c) for c in cids}
    full = scene.world()[:, 200:1160]
    pw = 960 // len(cids)                          # art px per panel (x2 on screen)
    t_seq = {}
    for c in cids:
        man = mans[c][0]
        ws = man['walk_speed']
        side = 60.0
        seq = [('idle', 'S', 1.0, None)]
        for fc, v in (('E', (1, 0)), ('N', (0, -1)), ('W', (-1, 0)), ('S', (0, 1))):
            seq.append(('walk', fc, side / ws, v))
        seq.append(('idle', 'S', 0.8, None))
        for fid in man.get('idle_fidgets', {}).get('clips', []):
            seq.append((fid, 'S', man['clips'][fid]['duration'], None))
            seq.append(('idle', 'S', 0.4, None))
        act = 'primary' if 'primary' in man['clips'] else 'work'
        for fc in ('E', 'S'):
            n = 1 if act == 'primary' else 2
            for tag in ((['m45', '0', 'p45'] if fc == 'E' else ['0']) if man['clips'][act]['facings'][fc].get('aims') else [None]):
                seq.append((act, fc, man['clips'][act]['duration'] * n, tag))
                seq.append(('idle', fc, 0.35, None))
        t_seq[c] = seq
    total = max(sum(s[2] for s in seq) for seq in t_seq.values()) + 0.5
    path = os.path.join(out_dir, '%s.mp4' % name)
    os.makedirs(out_dir, exist_ok=True)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-tune', 'animation', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    state = {c: dict(fc='S', path=[], hold=0.0, step=0.07) for c in cids}
    tiles = []
    for i in range(int(total * FPS)):
        tt = i / FPS
        panels = []
        for k, c in enumerate(cids):
            man, spr = mans[c]
            ti = man.get('turn_inbetweens', {})
            seq = t_seq[c]
            acc, cur = 0.0, seq[-1]
            x, y = pw / 2 - 30, 300.0
            for s in seq:
                if tt < acc + s[2]:
                    cur = s
                    break
                if s[0] == 'walk':
                    x += s[3][0] * 60.0
                    y += s[3][1] * 60.0
                acc += s[2]
            else:
                acc = sum(s[2] for s in seq) - seq[-1][2]
            clip, fc, L, extra = cur
            lt = tt - acc
            if clip == 'walk':
                x += extra[0] * man['walk_speed'] * lt
                y += extra[1] * man['walk_speed'] * lt
            st = state[c]
            if fc != st['fc']:
                st['path'] = turn_steps(st['fc'], fc, (0.0, 0.0)) if man['clips'][clip].get('turns') else []
                st['step'] = ti.get('hold_180', 0.055) if len(st['path']) > 1 else ti.get('hold', 0.07)
                st['hold'] = st['step']
                st['fc'] = fc
            elif st['path']:
                st['hold'] -= 1.0 / FPS
                while st['hold'] <= 0 and st['path']:
                    st['path'].pop(0)
                    st['hold'] += st['step']
            e = man['clips'][clip]
            loop = e['loop']
            d = e['durations']
            tl = lt % sum(d) if loop else min(lt, sum(d) - 1e-6)
            idx, a = len(d) - 1, 0.0
            for j, dd in enumerate(d):
                if tl < a + dd:
                    idx = j
                    break
                a += dd
            if st['path'] and e.get('turns', {}).get(st['path'][0]):
                fr = e['turns'][st['path'][0]]['frames'][idx]
                shown = st['path'][0]
            elif clip in ('primary', 'powered_primary') and extra:
                fr = e['facings'][fc]['aims'][extra]['frames'][idx]
                shown = '%s %s' % (fc, extra)
            else:
                fr = e['facings'][fc]['frames'][idx]
                shown = fc
            c0 = int(k * pw + 0)
            bx = max(0, min(300, full.shape[1] - pw))           # one wide panel: start further left so the slice keeps its width
            bg = full[:, bx:bx + pw].copy()
            shadow(bg, x, y, 12, 4.0)
            blit(bg, spr(fr['file']), int(round(x)) - GX, int(round(y)) - GY)
            im = Image.fromarray(up2(bg))
            dr = ImageDraw.Draw(im)
            text = '%s  %s %s' % (man['name'], clip, shown)
            dr.rectangle((10, 10, 22 + 12 * len(text), 44), fill=(30, 28, 26))
            dr.text((18, 14), text, font=FONT.font_variant(size=20), fill=(240, 232, 210))
            panels.append(np.array(im))
        frame = np.concatenate(panels, axis=1)
        for k in range(1, len(cids)):
            frame[:, k * pw * 2 - 2:k * pw * 2 + 2] = (30, 28, 26)
        proc.stdin.write(frame[:1080, :1920].tobytes())
        if i % 6 == 0:
            tiles.append(Image.fromarray(frame).resize((480, 270), Image.NEAREST))
    proc.stdin.close()
    proc.wait()
    for k in range(0, len(tiles), 48):
        sh = Image.new('RGB', (480 * 6, 270 * 8))
        for j, t_ in enumerate(tiles[k:k + 48]):
            sh.paste(t_, (480 * (j % 6), 270 * (j // 6)))
        sh.save(os.path.join(out_dir, '%s_frames_%02d.png' % (name, k // 48)))
    return path, total
