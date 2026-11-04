"""The v56 overview's small secrets (PROPOSALS, docs/vision/map-secrets.md): things that reward looking and may later become
places to find in the game. Drawing only: no label, no quest or gameplay data. Each is tiny (most read at 3840, a few barely
at 1920); two sit where the north cloud and the east fog thin. Positions are world px (the grown frame's y can be negative,
x can pass 12544)."""
import math

# (number, key, x, y, kind)   the table in docs/vision/map-secrets.md follows these numbers
SECRETS = [
    (1, 'the heart tarn', 3900, 380, 'heart'),
    (2, 'the Old Watcher', 5780, 1852, 'face'),
    (3, 'Bramble on the lip', 6300, 1900, 'figure'),
    (4, "the hermit's tower", 7055, 1720, 'tower'),
    (5, 'the sky stair', 3010, -470, 'stair'),
    (6, 'the lost pit', 7650, 1650, 'headframe'),
    (7, 'the old coal line', 7844, 1916, 'arches'),
    (8, 'the giant\'s chair', 10300, 1500, 'chair'),
    (9, 'the caught balloon', 12150, 1250, 'balloon'),
    (10, 'the drowned crater', 11452, 1900, 'craterlake'),
    (11, 'the first tree', 13360, 1520, 'bigtree'),
    (12, 'the Brackens ring', 4976, 3150, 'ring'),
    (13, 'the hedge maze', 7050, 4150, 'maze'),
    (14, 'the shard in the barley', 7900, 4750, 'cropshard'),
    (15, 'the bell in the oxbow', 9716, 4164, 'glint'),
    (16, 'the sea that was', 1350, 2650, 'whale'),
    (17, 'the lone palm', 592, 2900, 'palm'),
    (18, 'the sleeper in the canyon', 2484, 3172, 'fossil'),
    (19, 'the roofs under the salt', 1884, 3596, 'roofs'),
    (20, 'the steam cave', 2524, 4350, 'vent'),
    (21, 'the wreck on the Shell Bar', 7000, 6050, 'wreck'),
    (22, 'the drowned circle', 6452, 6740, 'subring'),
    (23, 'the sea cave', 8956, 6948, 'seacave'),
    (24, "the keeper's door", 11108, 5736, 'door'),
    (25, 'the pine on the stack', None, None, 'stackpine'),
    (26, 'the first rocket', 12068, 6516, 'rocket'),
]
CLOUD_GAPS = [3010]          # world x where the north bank thins (the sky stair)
FOG_GAPS = [(1350, 1700)]    # world y ranges where the east fog thins (the first tree)


def resolve(Sx):
    """The positions that come from the drawing (the pine on the first stack off Neon's headland)."""
    out = []
    for n, key, x, y, kind in SECRETS:
        if kind == 'stackpine':
            st = Sx.get('stacks') or []
            if not st:
                continue
            x, y = st[0]
        out.append((n, key, x, y, kind))
    return out


def draw(d, Sx, P, R, ink, k, s, after=False):
    """Each secret drawn small, in the map's own marks (k: canvas px per world px). The sky stair is drawn after the edge
    weather (after=True), climbing into the cloud where the bank thins; everything else before it."""
    u = max(1.0, 0.9 * s)
    stone = R['stone']; snow = R['snow']; wat = R['water_warm']; leaf = R['leaf']; sand = R['sand']; iron = R['iron']
    for n, key, x, y, kind in resolve(Sx):
        if (kind == 'stair') != after:
            continue
        X, Y = P(x, y)
        if kind == 'heart':                                         # a small tarn in the shape of a heart
            r = max(1.6, 15 * k)
            d.ellipse([X - r * 1.05, Y - r * 0.9, X + 0.05 * r, Y + 0.15 * r], fill=wat[3])
            d.ellipse([X - 0.05 * r, Y - r * 0.9, X + r * 1.05, Y + 0.15 * r], fill=wat[3])
            d.polygon([(X - r * 1.0, Y - r * 0.25), (X + r * 1.0, Y - r * 0.25), (X, Y + r * 1.05)], fill=wat[3])
            d.point([(X - r * 0.5, Y - r * 0.55)], fill=snow[5])
        elif kind == 'face':                                       # a face in the crag: a brow, two eyes and a mouth in shadow
            r = max(2.0, 14 * k)
            d.ellipse([X - r, Y - r * 1.2, X + r, Y + r * 1.2], fill=stone[3], outline=stone[1])
            for ex in (-0.4, 0.4):
                d.rectangle([X + ex * r - 0.5 * u, Y - 0.3 * r, X + ex * r + 0.5 * u, Y - 0.3 * r + u], fill=ink)
            d.line([(X - 0.35 * r, Y + 0.45 * r), (X + 0.35 * r, Y + 0.45 * r)], fill=ink, width=max(1, int(u)))
        elif kind == 'figure':                                     # Bramble: a fox-folk forester in a sky-blue cape, looking down the valley
            h = max(2.0, 9 * k)
            d.line([(X, Y), (X, Y - h)], fill=R['sky'][4], width=max(1, int(1.4 * u)))
            d.point([(X, Y - h - u)], fill=R['clay_warm'][4])
        elif kind == 'tower':                                      # a round ruined tower beside the tarn
            r = max(1.6, 9 * k)
            d.rectangle([X - r, Y - 2.6 * r, X + r, Y + r * 0.4], fill=stone[2], outline=ink)
            d.rectangle([X - r, Y - 2.6 * r, X, Y + r * 0.4], fill=stone[4])
            d.polygon([(X - r, Y - 2.6 * r), (X - r * 0.2, Y - 3.3 * r), (X + r, Y - 2.6 * r)], fill=stone[1])
        elif kind == 'stair':                                      # pale steps climbing into the cloud, a gate at the top
            st = max(1.5, 9 * k)
            for i in range(7):
                d.rectangle([X - 3 * st + i * 0.3 * st, Y - i * st * 1.4, X + 3 * st - i * 0.3 * st, Y - i * st * 1.4 + st * 0.7], fill=snow[4], outline=stone[2])
            gx, gy = X, Y - 7 * st * 1.4
            d.line([(gx - 2.5 * st, gy), (gx - 2.5 * st, gy - 4 * st)], fill=stone[1], width=max(1, int(u)))
            d.line([(gx + 2.5 * st, gy), (gx + 2.5 * st, gy - 4 * st)], fill=stone[1], width=max(1, int(u)))
            d.line([(gx - 3.2 * st, gy - 4 * st), (gx + 3.2 * st, gy - 4 * st)], fill=stone[1], width=max(1, int(u)))
        elif kind == 'headframe':                                  # a winding wheel on a timber frame in a clearing
            r = max(2.0, 10 * k)
            d.ellipse([X - 1.6 * r, Y - 0.6 * r, X + 1.6 * r, Y + 0.9 * r], fill=R['earth'][3] if 'earth' in R else sand[2])
            d.line([(X - r, Y + 0.5 * r), (X, Y - 1.4 * r), (X + r, Y + 0.5 * r)], fill=R['timber'][1], width=max(1, int(u)))
            d.ellipse([X - 0.5 * r, Y - 1.9 * r, X + 0.5 * r, Y - 0.9 * r], outline=iron[1], width=max(1, int(u)))
        elif kind == 'arches':                                     # three broken arches standing in the river, the deck gone
            a = max(1.5, 8 * k)
            for i in (-1, 0, 1):
                cx = X + i * 2.6 * a
                d.rectangle([cx - 0.5 * a, Y - 1.4 * a, cx + 0.5 * a, Y + 0.6 * a], fill=stone[3], outline=ink)
            d.line([(X - 3.1 * a, Y - 1.4 * a), (X - 1.8 * a, Y - 1.4 * a)], fill=stone[3], width=max(1, int(u)))
        elif kind == 'chair':                                      # a rock shaped like a great chair in the trees
            r = max(2.0, 12 * k)
            d.rectangle([X - r, Y - 0.2 * r, X + r, Y + 0.6 * r], fill=stone[3], outline=ink)
            d.rectangle([X - r, Y - 1.6 * r, X - 0.4 * r, Y + 0.6 * r], fill=stone[2], outline=ink)
            d.rectangle([X + 0.4 * r, Y - 0.9 * r, X + r, Y - 0.2 * r], fill=stone[4], outline=ink)
        elif kind == 'balloon':                                    # a red and white envelope snagged in the canopy, its basket hanging
            r = max(1.6, 9 * k)
            d.ellipse([X - r, Y - 2.2 * r, X + r, Y - 0.2 * r], fill=R['berry'][4], outline=ink)
            d.line([(X, Y - 2.2 * r), (X, Y - 0.2 * r)], fill=snow[5], width=max(1, int(u)))
            d.rectangle([X - 0.35 * r, Y + 0.1 * r, X + 0.35 * r, Y + 0.6 * r], fill=R['timber'][2])
        elif kind == 'craterlake':                                 # a small round lake in a rim of bare rock: a shard's crater, flooded
            r = max(2.0, 26 * k)
            d.ellipse([X - r * 1.25, Y - r * 1.25, X + r * 1.25, Y + r * 1.25], fill=stone[3])
            d.ellipse([X - r, Y - r, X + r, Y + r], fill=wat[2])
            d.arc([X - r, Y - r, X + r, Y + r], 200, 290, fill=snow[5])
            d.point([(X + 0.2 * r, Y + 0.1 * r)], fill=(170, 250, 255))
        elif kind == 'bigtree':                                    # a tree taller than the forest, its crown a dark shape in the fog
            r = max(3.0, 40 * k)
            col = (60, 96, 82)
            d.line([(X, Y + r), (X, Y - 0.5 * r)], fill=(70, 70, 70), width=max(1, int(2 * u)))
            d.ellipse([X - r, Y - 1.8 * r, X + r, Y - 0.2 * r], fill=col)
            d.ellipse([X - 1.3 * r, Y - 1.2 * r, X - 0.1 * r, Y + 0.0 * r], fill=col)
            d.ellipse([X + 0.1 * r, Y - 1.3 * r, X + 1.3 * r, Y - 0.1 * r], fill=col)
        elif kind == 'ring':                                       # a small ring of standing stones on the heath
            r = max(2.0, 14 * k)
            for i in range(7):
                a = 2 * math.pi * i / 7
                px, py = X + r * math.cos(a), Y + r * 0.7 * math.sin(a)
                d.rectangle([px - 0.5 * u, py - 1.2 * u, px + 0.5 * u, py + 0.4 * u], fill=stone[4], outline=ink)
        elif kind == 'maze':                                       # a square hedge maze behind the farm
            r = max(3.0, 26 * k)
            d.rectangle([X - r, Y - r, X + r, Y + r], fill=R['grass'][4])
            w = max(1, int(u))
            for i in range(4):
                q = r * (1 - i * 0.25)
                gap = (i % 2) * 2 - 1
                d.rectangle([X - q, Y - q, X + q, Y + q], outline=leaf[1], width=w)
                d.line([(X + gap * q * 0.3, Y - q), (X + gap * q * 0.3 + 1.5 * u, Y - q)], fill=R['grass'][4], width=w)
        elif kind == 'cropshard':                                  # a shard-shaped figure mown into a field of barley
            r = max(3.0, 30 * k)
            pts = [(X, Y - r), (X + 0.3 * r, Y - 0.1 * r), (X + 0.6 * r, Y + 0.1 * r), (X + 0.15 * r, Y + 0.25 * r), (X, Y + r),
                   (X - 0.2 * r, Y + 0.2 * r), (X - 0.6 * r, Y + 0.05 * r), (X - 0.25 * r, Y - 0.15 * r)]
            d.polygon(pts, fill=(236, 214, 150), outline=(170, 140, 80))
        elif kind == 'glint':                                      # something gold under the water
            r = max(1.0, 4 * k)
            d.ellipse([X - r, Y - r, X + r, Y + r], fill=R['brass'][5])
            d.point([(X - r, Y - r)], fill=snow[5])
        elif kind == 'whale':                                      # a long spine and ribs half buried in the dunes
            L = max(6.0, 90 * k)
            d.line([(X - L / 2, Y), (X + L / 2, Y - 0.12 * L)], fill=R['bleached'][5] if 'bleached' in R else snow[5], width=max(1, int(u)))
            for i in range(1, 8):
                t = i / 8; px, py = X - L / 2 + L * t, Y - 0.12 * L * t; rl = L * 0.12 * math.sin(math.pi * t) + u
                d.line([(px, py - rl), (px, py + rl)], fill=snow[5], width=max(1, int(u * 0.8)))
            d.ellipse([X + L / 2 - 0.08 * L, Y - 0.2 * L, X + L / 2 + 0.06 * L, Y - 0.04 * L], fill=snow[5])
        elif kind == 'palm':                                       # one palm alone in the dunes
            r = max(1.6, 9 * k)
            d.line([(X, Y), (X + 0.3 * r, Y - 1.6 * r)], fill=R['timber'][2], width=max(1, int(u)))
            for a in (-2.4, -1.6, -0.8, -0.1):
                d.line([(X + 0.3 * r, Y - 1.6 * r), (X + 0.3 * r + r * math.cos(a), Y - 1.6 * r + r * 0.7 * math.sin(a) + 0.4 * r)], fill=leaf[3], width=max(1, int(u)))
        elif kind == 'fossil':                                     # a coiled spine in the canyon wall
            r = max(2.0, 14 * k)
            for i in range(10):
                a = i * 0.7; rr = r * (1 - i / 14)
                d.point([(X + rr * math.cos(a), Y + rr * math.sin(a) * 0.7)], fill=snow[5])
        elif kind == 'roofs':                                      # a grid of roof ridges showing faintly through the salt crust
            r = max(2.0, 12 * k)
            for i in range(-1, 2):
                for j in range(-1, 1):
                    d.rectangle([X + i * 1.4 * r, Y + j * 1.2 * r, X + i * 1.4 * r + r, Y + j * 1.2 * r + 0.6 * r], outline=(196, 196, 200), width=1)
        elif kind == 'vent':                                       # a dark mouth in the slope, a curl of steam
            r = max(1.6, 8 * k)
            d.ellipse([X - r, Y - 0.6 * r, X + r, Y + 0.6 * r], fill=R['basalt'][0])
            d.arc([X - 0.6 * r, Y - 2.4 * r, X + 0.8 * r, Y - 0.6 * r], 120, 330, fill=snow[4], width=max(1, int(u)))
        elif kind == 'wreck':                                      # a hull on its side on the bar, ribs showing
            L = max(4.0, 44 * k)
            d.polygon([(X - L / 2, Y), (X + L / 2, Y - 0.15 * L), (X + L * 0.35, Y + 0.12 * L), (X - L * 0.4, Y + 0.16 * L)], fill=R['timber'][1], outline=ink)
            for i in range(1, 4):
                px = X - L / 2 + L * i / 4
                d.line([(px, Y - 0.2 * L + 0.05 * L * i), (px, Y - 0.02 * L)], fill=R['timber'][3], width=1)
        elif kind == 'subring':                                    # a ring of stones under clear water
            r = max(2.0, 20 * k)
            for i in range(9):
                a = 2 * math.pi * i / 9
                px, py = X + r * math.cos(a), Y + r * 0.8 * math.sin(a)
                d.ellipse([px - 0.7 * u, py - 0.6 * u, px + 0.7 * u, py + 0.6 * u], fill=wat[4])
        elif kind == 'seacave':                                    # a dark arch in the isle's south shore
            r = max(1.6, 9 * k)
            d.pieslice([X - r, Y - r * 0.4, X + r, Y + r * 1.4], 180, 360, fill=R['basalt'][1])
        elif kind == 'door':                                       # a small red door at the foot of the lighthouse
            r = max(1.0, 4 * k)
            d.rectangle([X - r * 0.6, Y + r * 2.2, X + r * 0.6, Y + r * 3.6], fill=R['berry'][3])
        elif kind == 'stackpine':                                  # one wind-bent pine on the sea stack
            r = max(1.6, 8 * k)
            d.polygon([(X + 0.6 * r, Y - 1.8 * r), (X + r, Y), (X - 0.6 * r, Y)], fill=leaf[2], outline=ink)
        elif kind == 'rocket':                                     # an older rocket lying broken on the reef
            L = max(4.0, 46 * k)
            d.polygon([(X - L / 2, Y), (X + L * 0.4, Y - 0.2 * L), (X + L / 2, Y - 0.12 * L), (X + L * 0.42, Y - 0.05 * L), (X - L / 2, Y + 0.1 * L)],
                      fill=snow[4], outline=ink)
            d.line([(X - L * 0.2, Y - 0.04 * L), (X - L * 0.2, Y + 0.06 * L)], fill=R['berry'][4], width=max(1, int(u)))


def overlay(img, Sx, P, R, ink, k, s, font):
    """The secrets version: each secret circled and numbered, matching docs/vision/map-secrets.md."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img, 'RGBA')
    for n, key, x, y, kind in resolve(Sx):
        X, Y = P(x, y); r = 16 * s
        d.ellipse([X - r, Y - r, X + r, Y + r], outline=(236, 72, 196, 255), width=max(2, int(1.5 * s)))
        tx, ty = X + r * 0.75, Y - r * 0.75
        d.ellipse([tx - 7 * s, ty - 7 * s, tx + 7 * s, ty + 7 * s], fill=(236, 72, 196, 255), outline=ink)
        d.text((tx, ty), str(n), font=font, fill=(255, 255, 255), anchor='mm')
    return img
