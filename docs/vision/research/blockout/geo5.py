"""World plan v5: a window onto a larger continent.

The sea is only along the south. Land runs off the north (the high massif and its glaciers), the west
(the dune sea) and the east (the moss fens and the old forest). Each place is put where people would
live, and the terrain is shaped to give it what it needs. The paths come first: footpaths, drove roads,
mule tracks, a canyon trail, a pass, towpaths; the ground is then fitted round them.

Geology in one line: an ocean plate dives under the continent along the south coast. That raises a
volcanic arc parallel to the coast (the Ember range; Mount Ember is the one cone still alive, and the
Tidebloom Isles are its drowned eastern end), and the arc casts a rain shadow over an interior basin,
which the northern massif closes off on the other side (after the Cascades and the Oregon High Desert,
with the Tarim Basin's oasis rivers along the mountain foot).

In the repository this file is the library geo52.py builds on: run geo52.py (see README.md). Run on its own,
python3 -I geo5.py writes the v5 images and stats next to this file; do not commit them."""
import heapq, json, math, os, zlib
import numpy as np
from scipy import ndimage as ndi
from skimage.graph import MCP_Geometric
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = 8
WPX, HPX = 11264, 6912
W, H = WPX // CELL, HPX // CELL
SPEED = 40.0
F = lambda n, b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed%s.ttf' % ('-Bold' if b else ''), n)
FONT, FONTB, FONTT = F(13), F(15, True), F(20, True)
yy, xx = np.mgrid[0:H, 0:W]
PX = xx * CELL + CELL / 2.0
PY = yy * CELL + CELL / 2.0
NOISE_CACHE = {}


# ------------------------------------------------------------------------------------------ helpers
def stable_name_seed(name, modulus):
    """Prospective map seeds: the existing geo55 UTF-8 CRC32 convention."""
    return zlib.crc32(name.encode('utf-8')) % modulus


def noise(scale_px, seed, octaves=4):
    key = (scale_px, seed, octaves)
    if key in NOISE_CACHE:
        return NOISE_CACHE[key]
    r = np.random.default_rng(seed)
    out = np.zeros((H, W)); amp = 1.0; tot = 0.0; s = scale_px
    for _ in range(octaves):
        gh, gw = max(2, int(HPX / s) + 2), max(2, int(WPX / s) + 2)
        g = r.uniform(-1, 1, (gh, gw))
        out += amp * ndi.zoom(g, (H / (gh - 1), W / (gw - 1)), order=3)[:H, :W]
        tot += amp; amp *= 0.5; s /= 2
    NOISE_CACHE[key] = out / tot
    return NOISE_CACHE[key]


def band(a, b, soft):
    return 1 / (1 + np.exp(-(PY - a) / soft)) / (1 + np.exp((PY - b) / soft))


def ridged(scale_px, seed):
    return 1 - np.abs(noise(scale_px, seed, 5))


def chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            out += [(0.75 * ax + 0.25 * bx, 0.75 * ay + 0.25 * by), (0.25 * ax + 0.75 * bx, 0.25 * ay + 0.75 * by)]
        out.append(pts[-1]); pts = out
    return pts


def meander(pts, amp, seed, step=120):
    r = np.random.default_rng(seed); res = [pts[0]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) // step))
        res += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(1, n + 1)]
    if amp <= 0 or len(res) < 3:
        return chaikin(res, 2)
    off = ndi.gaussian_filter1d(r.uniform(-1, 1, len(res)), 1.6) * amp * 2.4
    out = []
    for i, (x, y) in enumerate(res):
        j, k = min(i + 1, len(res) - 1), max(i - 1, 0)
        tx, ty = res[j][0] - res[k][0], res[j][1] - res[k][1]; L = math.hypot(tx, ty) or 1
        o = off[i] if 0 < i < len(res) - 1 else 0
        out.append((x - ty / L * o, y + tx / L * o))
    return chaikin(out, 2)


def densify(pts, step=4.0):
    xs, ys, al = [], [], []; acc = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, int(L // step))
        t = np.arange(n) / n
        xs.append(ax + (bx - ax) * t); ys.append(ay + (by - ay) * t); al.append(acc + L * t); acc += L
    xs.append(np.array([pts[-1][0]])); ys.append(np.array([pts[-1][1]])); al.append(np.array([acc]))
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(al), acc


def raster(pts):
    """Distance (px) to a polyline, and the distance along it of the nearest point."""
    x, y, a, tot = densify(pts)
    cx, cy = (x // CELL).astype(int), (y // CELL).astype(int)
    ok = (cx >= 0) & (cx < W) & (cy >= 0) & (cy < H)
    seed = np.zeros((H, W), bool); al = np.zeros((H, W))
    seed[cy[ok], cx[ok]] = True; al[cy[ok], cx[ok]] = a[ok]
    if not seed.any():
        return np.full((H, W), 1e9), np.zeros((H, W)), tot
    d, (iy, ix) = ndi.distance_transform_edt(~seed, return_indices=True)
    return d * CELL, al[iy, ix], tot


def disk(r):
    a = np.arange(-r, r + 1); return (a[:, None] ** 2 + a[None, :] ** 2) <= r * r + r


def line_mask(pts, width):
    x, y, _, _ = densify(pts, 3)
    m = np.zeros((H, W), bool)
    cx, cy = (x // CELL).astype(int), (y // CELL).astype(int)
    ok = (cx >= 0) & (cx < W) & (cy >= 0) & (cy < H); m[cy[ok], cx[ok]] = True
    r = max(0, int(round(width / CELL / 2 - 0.5)))
    if r:
        m = ndi.binary_dilation(m, structure=disk(r))
    return m


WARP = None


def warped(Fd):
    return ndi.map_coordinates(Fd, [np.clip(WARP[1] / CELL - 0.5, 0, H - 1), np.clip(WARP[0] / CELL - 0.5, 0, W - 1)], order=1)


def shape(cx, cy, rx, ry, seed, rough=0.45, rot=0.0):
    """An organic shape: an oval only as a starting point, pushed about by two scales of noise."""
    c, s = math.cos(rot), math.sin(rot)
    u, v = (PX - cx) * c + (PY - cy) * s, -(PX - cx) * s + (PY - cy) * c
    e = np.hypot(u / rx, v / ry)
    return e + rough * noise(max(rx, ry) * 0.9, seed) + rough * 0.45 * noise(max(rx, ry) * 0.3, seed + 1, 3) < 1.0


def capsule(pts, w0, w1, seed=None, rough=0.0):
    d, al, tot = raster(pts)
    w = w0 + (w1 - w0) * np.clip(al / tot, 0, 1)
    if seed is not None:
        w = w * (1 + rough * noise(max(w0, w1) * 2, seed))
    return d < w


# ------------------------------------------------------------------------------------------ design
HOME = (6300, 3420)
VOLCANO = (2450, 4480)
COAST = [(0, 5450), (700, 5600), (1400, 5720), (2000, 5800), (2500, 5880), (3000, 5820), (3400, 5650), (3800, 5420), (4250, 5330),
         (4700, 5250), (5200, 5150), (5800, 5100), (6200, 5150), (6600, 5230), (7000, 5230), (7500, 5180), (8000, 5250), (8400, 5300),
         (9000, 5350), (9500, 5380), (10000, 5420), (10500, 5380), (11000, 5300), (11264, 5280)]
FRONT = [(0, 1650), (800, 1500), (1700, 1350), (2600, 1300), (3400, 1380), (4300, 1250), (5200, 1450), (5800, 1800), (6000, 2250),
         (6200, 2450), (6450, 2250), (6800, 1950), (7300, 1700), (8000, 1550), (8700, 1450), (9400, 1350), (10200, 1250), (11264, 1150)]
SPURS = {  # lobes of the massif reaching into the lowland: narrow, so they come out lower (hills, not peaks)
    'the Brackens': ([(5050, 1400), (5000, 2200), (5050, 2800), (5000, 3250)], 520, 160),
    'the coal hills': ([(7600, 1500), (7900, 2100), (8400, 2500), (9000, 2500), (9500, 2300)], 700, 420),
    'the Fern hills': ([(7300, 1700), (7200, 2500), (7000, 3200), (6950, 3700)], 420, 150),
    'the Lode spur': ([(3000, 1300), (3050, 1800)], 350, 200),
}
CHAIN = [(0, 4950), (700, 4900), (1400, 4880), (2000, 4720), (2450, 4480), (3000, 4700), (3600, 4800), (4100, 4950)]  # the arc

RIVERS = {  # name: (points, width at source px, width at mouth px, meander px, barrier?)
    'the Lull': ([(8650, 420), (8700, 800), (8820, 1150), (8960, 1500), (9050, 1700), (9000, 1950), (9070, 2200), (8990, 2450), (9040, 2700),
                  (8950, 2950), (8850, 3150), (8960, 3330), (9180, 3420), (9330, 3600), (9190, 3790), (8930, 3830), (8820, 3990), (8930, 4150),
                  (8960, 4300), (8960, 4480), (9060, 4780), (9150, 5080), (9220, 5500)], 36, 200, 25, True),
    'the Sorrel': ([(10300, 300), (10000, 800), (9600, 1300), (9300, 1550), (9060, 1690)], 18, 40, 30, True),
    'the Cog': ([(7500, 200), (7550, 900), (7700, 1600), (7800, 2200), (7860, 2500), (8150, 2850), (8500, 3050), (8860, 3160)], 16, 40, 22, True),
    'the Rift': ([(4550, -50), (4400, 700), (4520, 1300), (4300, 1900), (4390, 2500), (4220, 3000), (4300, 3420), (4200, 3900), (4330, 4500),
                  (4260, 5450)], 22, 34, 30, True),
    'the Sleepwater': ([(6200, 1880), (6230, 2400), (6170, 2800), (6250, 3150), (6370, 3480), (6290, 3900), (6400, 4300), (6360, 4700),
                        (6460, 5100)], 12, 30, 40, False),
    'the Amber': ([(2750, 300), (2850, 900), (2760, 1500), (2820, 2000), (2700, 2450), (2640, 2800), (2560, 3100), (2450, 3350), (2150, 3620)], 14, 8, 45, False),
    'the Willow Run': ([(3650, 1100), (3560, 1600), (3640, 2100), (3480, 2700), (3350, 3050)], 10, 5, 40, False),
    'the Glint': ([(11300, 3250), (10950, 3600), (10600, 3950), (10300, 4150), (10200, 4240)], 30, 50, 40, False),
}
DELTA = {'west arm': [(8960, 4480), (8820, 4700), (8700, 4850), (8560, 5050), (8540, 5250), (8420, 5500)],
         'middle arm': [(8960, 4480), (8930, 4780), (8980, 4950), (8870, 5150), (8900, 5480)],
         'creek': [(8700, 4850), (8780, 5050), (8720, 5300), (8680, 5520)]}
OXBOWS = [[(9330, 3700), (9480, 3780), (9520, 3930), (9420, 4050), (9280, 4030)], [(9350, 3330), (9480, 3310), (9560, 3410), (9520, 3520)]]
GLINT_ARMS = [[(10200, 4240), (10110, 4330), (10075, 4470)], [(10200, 4240), (10260, 4350), (10245, 4475)]]
BAY = [(10160, 4545), (10170, 4650), (10120, 4850), (10150, 5050), (10100, 5250), (10080, 5650)]  # a ria: the Glint's old valley, drowned
BAY_W = [90, 130, 250, 320, 300, 420]

SETTLE = {  # name: (x, y, radius px, kind)
    'Home valley': (6300, 3480, 560, 'village'), 'Driftwood': (6420, 4960, 230, 'harbour'), 'Fernhollow': (7150, 3080, 170, 'hamlet'),
    'Cogsworth': (7980, 2450, 330, 'town'), 'Lullford': (8700, 4300, 240, 'town'), 'Gullwick': (7950, 5130, 170, 'harbour'),
    'Neon Harbour': (10450, 4520, 700, 'city'), 'Launch Cape': (10980, 5560, 170, 'cape'),
    'Palm Spring': (3480, 2800, 170, 'oasis'), 'Dust Gulch': (2760, 2420, 270, 'frontier'), 'the Lode': (3060, 1650, 120, 'mine'),
    'Hearthold': (2480, 5120, 200, 'castle'), 'Ember forge': (2460, 4860, 110, 'forge'), 'Cinder Springs': (2200, 5420, 130, 'springs'),
    'Cinderwick': (2760, 5640, 150, 'hamlet'), 'Lagoon Landing': (6560, 6200, 150, 'hamlet'), 'the Frostline': (6220, 1800, 150, 'cirque'),
}
WHY = {
    'Home valley': 'a sheltered basin where the Sleepwater leaves the uplands: water, a mill head, flat ground, hills on three sides',
    'the Frostline': "a glacier's cirque above the valley: the Sleepwater's source, a tarn, snow late into summer",
    'Driftwood': "the cove at the Sleepwater's mouth, sheltered by the Headland: the valley's landing place",
    'Fernhollow': "timber in the wet woods of the Fern hills, the valley's east wall",
    'Cogsworth': 'coal and iron in the coal hills, the fast Cog for power (the Millrace), and the valley floor for a railway out',
    'Lullford': 'the lowest place the Lull can be bridged: gravel terraces narrow the floodplain and an island takes the piers',
    'Gullwick': 'a cove on the open coast west of the delta: fish, and a beach to haul boats',
    'Neon Harbour': "a deep, sheltered ria clear of the Lull's silt; the falls gave the first crossing, the head of navigation and mill power",
    'Launch Cape': 'an exposed headland past the city: rockets go up over open sea, away from people',
    'Palm Spring': 'the Willow Run sinks into the gravel and comes up again here: the first water in the dry country',
    'Dust Gulch': 'where the Amber leaves the mountains: water, the mine above, the railhead',
    'the Lode': 'iron and copper in the massif foothills, reached by a mule track',
    'Hearthold': "a rock between two lava flows below the crater: the only defensible ground on the volcano's seaward side",
    'Ember forge': "the crater's heat at the caldera lip; ore comes down from the Lode by cart",
    'Cinder Springs': "hot springs where the sea seeps into the volcano's warm flank",
    'Cinderwick': 'a black-sand cove between the flows: charcoal and fish',
    'Lagoon Landing': "the main isle's lagoon: a drowned crater of the old arc, sheltered water",
}

ROUTES = {  # name: (points, kind, features). The paths come first; the terrain is fitted to them.
    'Col Path': ([(6280, 2960), (6250, 2650), (6240, 2350), (6215, 2050), (6210, 1890)], 'path', ['switchbacks:0.3-0.78', 'hut:Col hut@0.55']),
    'High Fells': ([(6300, 1760), (6450, 1690), (6800, 1650), (7150, 1650), (7450, 1820), (7650, 2050), (7790, 2280), (7920, 2390)], 'path', []),
    'Foothill Road': ([(6760, 3400), (6950, 3250), (7150, 3110), (7400, 2950), (7600, 2760), (7760, 2580), (7900, 2480)], 'road', ['woodland:0-0.6']),
    'Towpath': ([(8040, 2560), (8250, 2800), (8450, 2930), (8560, 3000), (8620, 3150), (8600, 3450), (8560, 3700), (8580, 3950), (8650, 4200)],
                'path', []),
    'Lull Road': ([(6760, 3760), (7300, 3900), (7900, 3970), (8350, 4120), (8640, 4300), (8960, 4310), (9200, 4300), (9450, 4360),
                   (9750, 4400), (9980, 4360)], 'road', ['watermeadows:0.55-0.75']),
    'Coast Path': ([(6660, 4930), (6870, 5100), (7300, 5070), (7950, 5050), (8150, 4930), (8380, 4700), (8560, 4450), (8640, 4330)], 'path',
                   ['dunes:0.3-0.6']),
    'Headland Lane': ([(6900, 5110), (6975, 5250), (7020, 5420), (7060, 5620)], 'path', []),
    'Shell Bar': ([(7060, 5640), (6960, 5800), (6870, 5920), (6700, 6080)], 'bar', []),
    "Drover's Road": ([(5800, 4060), (5400, 3880), (5000, 3620), (4700, 3500), (4300, 3420), (3950, 3150), (3700, 2950), (3480, 2830),
                       (3150, 2620), (2860, 2470)], 'road', ['folds', 'well:0.25']),
    'Lode Track': ([(2830, 2330), (2900, 2100), (2980, 1880), (3040, 1700)], 'path', ['switchbacks:0.1-0.9']),
    'Canyon Road': ([(2800, 2560), (2780, 2850), (2690, 3150), (2560, 3420), (2380, 3720), (2150, 4000), (1950, 4320), (1900, 4620),
                     (2050, 4860), (2260, 4980), (2440, 5080)], 'path', []),
    'Forge Stair': ([(2470, 5040), (2465, 4900)], 'path', []),
    'Ember Way': ([(2470, 5120), (2300, 5280), (2210, 5400), (2400, 5560), (2700, 5620)], 'path', []),
    'Ash Coast': ([(5800, 4150), (5450, 4500), (5000, 4850), (4600, 5080), (4380, 5200), (4150, 5250), (3850, 5320), (3500, 5480),
                   (3200, 5600), (2900, 5650), (2780, 5650)], 'path', ['deadwood:0.68-0.85']),
    'Delta Road': ([(9150, 4320), (9300, 4600), (9450, 4820), (9650, 4930), (9800, 4985)], 'path', []),
    'Harbour Bridge': ([(9800, 4985), (10130, 4985), (10470, 4990)], 'bridge', []),
    'Old Bridges': ([(9980, 4360), (10170, 4320), (10340, 4390)], 'road', []),
    'Quay Street': ([(10340, 4400), (10430, 4650), (10470, 4900), (10480, 5150), (10450, 5320)], 'road', []),
    'Beacon Causeway': ([(10450, 5320), (10260, 5420), (10100, 5440)], 'bridge', []),
    'Cape Road': ([(10600, 4950), (10800, 5150), (10930, 5350), (10980, 5520)], 'road', []),
    'Valley lane east': ([(6300, 3450), (6550, 3480), (6760, 3400)], 'path', []),
    'Valley lane south': ([(6300, 3450), (6280, 3900), (6300, 4400), (6380, 4800), (6500, 4950), (6660, 4930)], 'path', []),
    'Valley lane west': ([(6300, 3450), (6050, 3700), (5850, 3950), (5800, 4100)], 'path', []),
    'Valley lane to the Lull Road': ([(6300, 3450), (6550, 3650), (6760, 3760)], 'path', []),
    'Valley lane north': ([(6300, 3450), (6290, 3200), (6280, 2960)], 'path', []),
}
CROSS = {('Col Path', 'rim'): 'W2', ('High Fells', 'rim'): 'W2', ('High Fells', 'the Cog'): 'W3', ('Foothill Road', 'the Cog'): 'W3',
         ('Towpath', 'the Cog'): 'W3', ("Drover's Road", 'the Rift'): 'W5', ('Ash Coast', 'the Rift'): 'W5',
         ('Canyon Road', 'fire'): 'W6', ('Ash Coast', 'fire'): 'W6', ('Lull Road', 'the Lull'): 'W7', ('Headland Lane', 'wall'): 'W1',
         ('Shell Bar', 'sea'): 'W4', ('Harbour Bridge', 'sea'): 'open', ('Beacon Causeway', 'sea'): 'open', ('Old Bridges', 'sea'): 'open',
         ('Ember Way', 'sea'): 'open', ('Forge Stair', 'fire'): 'open'}
WAY_NAMES = {'W1': 'the Headland stile', 'W2': 'the ridge col (rim crossings)', 'W3': 'the Millrace landslip (the Cog crossings)',
             'W4': 'the Shell Bar and the ferry', 'W5': "the Rift: Drover's bridge, the mouth ferry, the desert line viaduct",
             'W6': 'the chasm bridge and the crust crossing', 'W7': "Lullford's swing bridge and the maglev", 'W8': 'the rocket', 'W9': 'the lander'}
BRIDGES = {  # the great river's landmark bridges
    'Lullford Bridge': (8960, 4310, 'old stone arches resting on a river island, with an iron swing span for the barges (W7)'),
    'Narrows Viaduct': (9030, 2330, 'the railway (now the maglev) on tall piers over the gorge'),
    'Harbour Bridge': (10300, 4990, "two high arches across the ria, resting on Chapel Islet; tall enough for masts"),
}
STATIONS = {'valley halt': (5850, 4050), 'Cogsworth platform': (8060, 2330), 'Cogsworth terminus': (8350, 2560), 'Dust Gulch platform': (2900, 2330),
            'Neon terminus': (10650, 4450), 'Driftwood pier': (6520, 5080), 'Lagoon pier': (6480, 6150), 'the Lode mine mouth': (3040, 1700),
            'the forge cart bay': (2470, 4900), 'Neon steamer pier': (10420, 4950)}
SHORTCUTS = [('valley train', 'valley halt', 'Cogsworth platform', 4, 'W3', [(6400, 4250), (7400, 3800), (7700, 3000)]),
             ('desert line (Rift viaduct)', 'valley halt', 'Dust Gulch platform', 4, 'W5', [(4900, 3900), (4280, 3700), (3600, 3100)]),
             ('maglev (Narrows Viaduct)', 'Cogsworth terminus', 'Neon terminus', 4, 'W7', [(9030, 2330), (9900, 3300), (10400, 4100)]),
             ('ferry', 'Driftwood pier', 'Lagoon pier', 4, 'W4', [(6350, 5700)]),
             ('mine cart (S1)', 'the Lode mine mouth', 'the forge cart bay', 3, 'W6', [(2950, 2900), (2850, 3900)]),
             ('coastal steamer (S3)', 'Neon steamer pier', 'Driftwood pier', 4, 'W7', [(9900, 5650), (8200, 5700), (7200, 5600)])]
EGGS = {'stone ring on the Brackens': (5000, 3150), 'wreck on the Shell Bar': (6930, 5870), 'bell in the oxbow': (9450, 3900),
        'fossil in the Amber canyon': (2560, 3200), "hermit's tarn": (7050, 1720), 'lone palm in the dune sea': (1050, 2900),
        'steam cave on Ember': (2800, 4300), "lighthouse keeper's door": (10050, 5440)}
WAYS = {'W8': [(10980, 5560, 40)]}
ORDER = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7']
BEHIND = {'W1': [(7050, 5600)], 'W2': [(6220, 1820)], 'W3': ['Cogsworth'], 'W4': ['Lagoon Landing'], 'W5': ['Dust Gulch', 'Palm Spring', 'the Lode'],
          'W6': ['Hearthold', 'Cinder Springs', 'Cinderwick', 'Ember forge'], 'W7': ['Neon Harbour', 'Launch Cape', (9750, 4900), (10500, 5250), (10170, 4340), (10130, 4985), (10080, 5440)]}
START = ['Driftwood', 'Fernhollow', 'Lullford', 'Gullwick', 'valley halt']


# ------------------------------------------------------------------------------------------ terrain
def build():
    global WARP
    T = {}
    wx = 240 * noise(1500, 1) + 80 * noise(380, 2)
    wy = 240 * noise(1500, 3) + 80 * noise(380, 4)
    WARP = (PX + wx, PY + wy); WX, WY = WARP

    # ---- the sea, along the south only
    cy_ = np.interp(PX, [p[0] for p in COAST], [p[1] for p in COAST])
    pot = (cy_ - PY) / 230 + 0.6 * noise(800, 101) + 0.32 * noise(260, 102) + 0.16 * noise(90, 103, 2)
    land = pot > 0
    land |= capsule([(8960, 4480), (8880, 5000), (8860, 5500)], 380, 520, 104, 0.3) & (PY < 5560 + 60 * noise(200, 105))   # the delta's lobe
    land |= capsule([(10500, 5100), (10800, 5350), (10990, 5680)], 280, 190, 106, 0.25)    # the Launch Cape
    land |= capsule([(9500, 4900), (9750, 5250), (9850, 5520)], 300, 200, 107, 0.25)       # the Heights headland, west of the ria
    d_b, al_b, tot_b = raster(chaikin(BAY, 2))
    bw = np.interp(al_b, np.linspace(0, tot_b, len(BAY_W)), BAY_W) * (1 + 0.22 * noise(300, 108))
    land &= ~(d_b < bw)                                                                     # the ria
    land &= ~shape(9930, 4700, 120, 80, 114, 0.3)                                           # the canal basin's cove under the Heights
    land |= shape(10080, 5440, 95, 65, 113, 0.3)                                            # Beacon Isle
    land |= shape(10130, 4985, 75, 55, 115, 0.25)                                           # Chapel Islet
    land &= ~shape(6470, 5130, 230, 130, 109, 0.3)                                          # Driftwood's cove
    land &= ~shape(7950, 5300, 170, 110, 110, 0.3)                                          # Gullwick's cove
    land &= ~shape(2780, 5800, 150, 110, 111, 0.3)                                          # Cinderwick's black-sand cove
    # the Headland: a body on a narrow neck; a field wall across the neck
    neck = capsule([(6940, 5120), (6985, 5380)], 62, 70, 116, 0.2)
    body = shape(7050, 5560, 165, 190, 112, 0.38, 0.2) | shape(7120, 5480, 90, 70, 117, 0.4)
    land &= ~(capsule([(6940, 5120), (6990, 5320), (7040, 5500), (7080, 5700)], 400, 400) & (PY > 5235))
    land |= neck | body
    # the isles: the old arc's drowned eastern end; the main isle's lagoon is a flooded crater
    isles = np.zeros((H, W), bool)
    for i, (cx, cy, rx, ry) in enumerate([(6650, 6380, 560, 330), (6880, 5900, 90, 60), (5250, 6250, 280, 170), (4050, 6120, 220, 150),
                                          (7850, 6450, 250, 160), (8700, 6650, 170, 110), (4650, 6650, 160, 110), (9600, 6500, 140, 90)]):
        isles |= shape(cx, cy, rx, ry, 120 + i, 0.55 if i != 1 else 0.3)
    lagoon = shape(6700, 6450, 230, 140, 130, 0.35) | capsule([(6720, 6500), (6800, 6620), (6830, 6800)], 45, 60)  # breached on the south
    land = (land & (PY < 5900)) | (isles & ~lagoon)
    lab, n = ndi.label(land)
    sizes = ndi.sum(land, lab, range(1, n + 1)); land &= np.isin(lab, 1 + np.nonzero(sizes >= 40)[0])
    sea = ~land
    dsea = ndi.distance_transform_edt(land) * CELL
    T['land'], T['isles'], T['coast_y'] = land, isles & land, cy_

    # ---- height
    front = np.interp(WX, [p[0] for p in FRONT], [p[1] for p in FRONT])
    M = WY < front
    for nm, (pts, w0, w1) in SPURS.items():
        d, al, tot = raster(pts)
        M |= warped(d) < w0 + (w1 - w0) * np.clip(warped(al) / tot, 0, 1)
    d_in = ndi.distance_transform_edt(M) * CELL; d_out = ndi.distance_transform_edt(~M) * CELL
    var = 0.78 + 0.38 * noise(2600, 5)
    hm = np.where(M, 0.30 + (1 - np.exp(-d_in / 1000)) * 0.9 * var * (0.62 + 0.5 * ridged(700, 6)), 0.30 * np.exp(-d_out / 420))
    base = 0.09 + 0.10 * np.clip((cy_ - PY) / 3200, 0, 1) + 0.035 * noise(600, 7)
    plateau = 0.14 / (1 + np.exp((WX - 4300) / 260))                        # the basin floor stands higher than the plains
    plateau -= 0.07 * np.exp(-(((PX - 1950) / 650) ** 2 + ((PY - 3700) / 380) ** 2))   # the salt lake's hollow
    uplands = 0.15 / (1 + np.exp(-(WX - 9650) / 260)) * np.clip((cy_ - PY - 150) / 450, 0, 1)  # the eastern uplands, a scarp to the sea
    heights = 0.2 * np.exp(-(((PX - 9720) / 300) ** 2 + ((PY - 5000) / 330) ** 2))       # the Heights headland
    dch, alch, totch = raster(CHAIN); dch = warped(dch)
    taper = np.interp(alch, [0, totch * 0.45, totch * 0.62, totch], [0.85, 1.0, 0.75, 0.35])
    hcr = 0.62 * taper * np.exp(-(dch / 430) ** 2) * (0.68 + 0.5 * ridged(450, 8))
    dv = np.hypot(PX - VOLCANO[0] + 0.6 * wx, PY - VOLCANO[1] + 0.6 * wy)
    dvc = np.hypot(PX - VOLCANO[0], PY - VOLCANO[1])                      # the summit itself stays put
    gullies = 0.05 * ridged(260, 10) * np.clip(1 - dv / 1450, 0, 1)        # erosion gullies run down the cone
    cone = 1.22 * np.clip(1 - dv / 1450, 0, 1) ** 1.7 - gullies
    cone = np.where(dvc < 150, 0.95 + 0.03 * noise(80, 9, 2), cone)         # the crater floor below the rim
    for (cx, cy, r, hh) in [(1900, 4150, 260, 0.42), (3150, 4250, 230, 0.38), (2950, 5200, 180, 0.3)]:  # parasitic cones
        cone = np.maximum(cone, hh * np.clip(1 - np.hypot(PX - cx, PY - cy) / r, 0, 1) ** 1.3)
    h = np.maximum.reduce([base + plateau + uplands + heights, hm, hcr, cone])
    vb = np.exp(-(((WX - 6300) / 760) ** 2 + ((WY - 3600) / 980) ** 2))   # the valley: a basin worn into the hills' foot
    h = h - 0.3 * vb * np.clip(h - 0.13, 0, None)
    cq_shape = shape(6215, 1810, 310, 220, 30, 0.42, 0.25)
    h = np.where(cq_shape, np.minimum(h, 0.74 + 0.025 * noise(100, 31)), h)
    h = np.where(cq_shape, h, np.maximum(h, 0.86 * ndi.binary_dilation(cq_shape, iterations=8)))  # the headwall above it

    # ---- rivers and their valleys. The great river's lower course is tens of cells wide.
    water = np.zeros((H, W), bool); T['river_masks'] = {}; T['river_px'] = {}; vcut = np.zeros((H, W))
    NAR = band(1850, 2900, 60)
    for i, (name, (pts, w0, w1, amp, bar)) in enumerate(RIVERS.items()):
        mp = meander(pts, amp, 40 + i, 100)
        d, al, tot = raster(mp)
        width = w0 + (w1 - w0) * (al / tot) ** 1.3
        if name == 'the Lull':  # narrow in the Narrows, braided and wide below the Cog, narrowed again at Lullford
            width = width * (1 - NAR) + 44 * NAR
            width = width * (1 + 0.7 * band(2950, 3450, 60))
            width = np.minimum(width, 130 + 400 * (1 - band(4220, 4400, 40)))
        m = d < width / 2
        if name in ('the Amber', 'the Willow Run'):
            m &= al < tot - 60
        m &= land | (PY < 5800)
        water |= m; T['river_masks'][name] = m; T['river_px'][name] = mp
        if name == 'the Rift':
            vcut = np.maximum(vcut, 0.75 * np.exp(-(d / 160) ** 2))
        elif name == 'the Lull':
            vcut = np.maximum(vcut, NAR * 0.75 * np.exp(-(d / 170) ** 2) + (1 - NAR) * 0.45 * np.exp(-(d / 700) ** 2))
        elif name == 'the Amber':
            cw = band(2550, 3450, 80)
            vcut = np.maximum(vcut, cw * 0.6 * np.exp(-(d / 170) ** 2) + (1 - cw) * 0.3 * np.exp(-(d / 330) ** 2))
        else:
            vcut = np.maximum(vcut, 0.32 * np.exp(-(d / 360) ** 2))
    h = h - vcut * np.clip(h - 0.07, 0, None)
    lull = T['river_masks']['the Lull']
    for nm, pts in DELTA.items():
        mp = meander(pts, 45, 77 + len(nm), 90); d, al, tot = raster(mp)
        m = (d < ((60 + 50 * al / tot) if nm != 'creek' else 34) / 2) & (PY < 5800); lull |= m; water |= m; T['river_px']['the Lull, ' + nm] = mp
    deltamarsh = land & (PY > 4800) & (np.abs(PX - 8750) < 450) & (noise(160, 78) > 0.0)
    shoals = (shape(9000, 3260, 110, 50, 140, 0.4, 0.5) | shape(9150, 3360, 90, 40, 141, 0.4, 0.3) | shape(8960, 4310, 60, 34, 142, 0.2)) & lull
    oxbow = np.zeros((H, W), bool)
    for ob in OXBOWS:
        oxbow |= raster(chaikin(ob, 3))[0] < 45
    T['shoals'], T['oxbow'] = shoals, oxbow & ~lull
    lake_ff = shape(6200, 1790, 120, 70, 33, 0.3)
    salt_lake = shape(1950, 3700, 430, 240, 32, 0.45) & land
    rapids = lull & (NAR > 0.5)

    # ---- wetness: the wind comes off the southern sea; whatever it climbs first takes the rain
    hl = np.where(land, h, 0)
    run = np.maximum.accumulate(hl[::-1, :], axis=0)[::-1, :]
    shadow = np.clip(run - h, 0, None)
    # far from open sea the continent dries westward over some 6 km (dune sea, desert, scrub, steppe, meadow);
    # behind the arc the rain shadow takes a further share; the arc's own seaward slope stays green
    ramp = 0.03 + 0.85 * np.clip((WX - 500) / 8000, 0, 1)
    wet = ramp * np.exp(-shadow * 1.2) * (0.8 + 0.2 * np.exp(-np.clip(cy_ - PY, 0, None) / 3000))
    wet += 0.28 * np.exp(-np.clip(cy_ - PY, 0, None) / 500) * (WX < 4300)                      # the arc's windward coastal shelf
    wet += 0.25 * np.exp(-np.clip(front - WY, 0, None) / 650) * np.clip((WX - 3600) / 2600, 0, 1)  # rain on the massif's windward face
    wet = ndi.gaussian_filter(wet, 40)                                           # transitions run for kilometres, not along a line
    wet = ndi.map_coordinates(wet, [np.clip((PY + 2.2 * wy) / CELL, 0, H - 1), np.clip((PX + 2.2 * wx) / CELL, 0, W - 1)], order=1)
    for (ax, ay) in [(2790, 1450), (3600, 1450), (1500, 1550)]:              # alluvial fans where snowmelt streams leave the massif
        rr_ = np.hypot(PX - ax, (PY - ay) * 1.3); wet += 0.14 * np.exp(-(rr_ / 420) ** 2) / (1 + np.exp(-(PY - ay + 50) / 160))
    near_r = np.zeros((H, W))
    for name, mp in list(T['river_px'].items()):
        d = raster(mp)[0]
        reach = 170 if name in ('the Amber', 'the Willow Run') else (650 if name.startswith('the Lull') else 240)
        near_r = np.maximum(near_r, np.exp(-(d / reach) ** 2))
    wet = wet + 0.42 * near_r + 0.07 * noise(900, 33) + 0.05 * noise(300, 34) + 0.03 * noise(70, 35, 2)
    wet = np.where(shape(3480, 2800, 300, 220, 36, 0.4), np.maximum(wet, 0.85), wet)  # Palm Spring
    wet = np.where(shape(2760, 2420, 330, 260, 37, 0.4), np.maximum(wet, 0.7), wet)   # Dust Gulch's fields

    # ---- ground
    gy_, gx_ = np.gradient(h)
    slope = np.hypot(gx_, gy_)
    snowline = 0.80 - 0.06 * np.tanh(gy_ * 90) + 0.035 * noise(220, 37)   # lower on north faces (gy > 0: ground rises southward)
    treeline = 0.64 - 0.04 * np.tanh(gy_ * 90) + 0.035 * noise(220, 38)
    hh = h + 0.03 * noise(70, 39, 2)
    L = land
    K = np.full((H, W), 'sea', dtype=object)
    K[L] = 'meadow'
    K[L & (wet < 0.56)] = 'steppe'
    K[L & (wet < 0.40)] = 'scrub'
    K[L & (wet < 0.25)] = 'desert'
    K[L & (wet < 0.1)] = 'erg'
    forestable = L & (wet >= 0.52) & (hh < treeline)
    fn = noise(420, 40) + 0.35 * noise(120, 41, 2)
    K[forestable & (hh > 0.26) & (fn > -0.35)] = 'broadleaf'
    K[forestable & (hh > 0.44)] = 'conifer'
    K[forestable & (hh <= 0.26) & (fn > 0.38)] = 'broadleaf'
    hi = L & (hh >= treeline) & (hh < snowline)
    K[hi] = np.where(wet[hi] > 0.33, 'alpine', 'barren')
    K[L & (hh >= snowline)] = 'snow'
    K[L & (hh >= snowline + 0.13)] = 'glacier'
    K[L & (hh >= snowline + 0.05) & (slope > 0.022)] = 'crag'
    # the Lull's floodplain: water meadows, willows, an old oxbow or two
    d_lull = raster(T['river_px']['the Lull'])[0]
    fp = L & (d_lull < 520 + 220 * noise(300, 79)) & (h < 0.25) & (PY > 2950)
    K[fp & ~np.isin(K, ['broadleaf'])] = 'watermeadow'
    # dry country: badlands where the rivers cut down, mesas left standing between them
    dry = L & (wet < 0.45) & (WX < 4600)
    near_cut = np.exp(-(np.minimum(raster(T['river_px']['the Amber'])[0], raster(T['river_px']['the Rift'])[0]) / 520) ** 2)
    near_cut *= 1 / (1 + np.exp(-(PY - 1700) / 150))                              # where the rivers have left the mountains
    K[dry & (near_cut > 0.3) & (near_r < 0.6) & (ridged(170, 42) > 0.72 - 0.15 * near_cut)] = 'badland'
    mesa = dry & (noise(380, 43) + 0.45 * near_cut > 0.72) & (near_r < 0.35) & (h > 0.2) & (h < 0.55) & (np.hypot(PX - 2760, PY - 2420) > 500)
    h = np.where(mesa, h + 0.07, h)
    K[mesa] = 'mesa'
    K[salt_lake] = 'saltpan'
    # Mount Ember and the land round it, by height, wind and the age of each flow; no ring
    ashfall = np.exp(-(((PX - VOLCANO[0] - 150) / 650) ** 2 + ((PY - VOLCANO[1] + 500) / 950) ** 2))  # blown north by the sea wind
    nz = noise(300, 44) + 0.4 * noise(90, 45, 2)
    dither = np.random.default_rng(44).random((H, W))
    p_ash = np.clip(1.5 * ashfall - 0.25 + 0.3 * nz, 0, 1)                       # thins out into a dusting, then scrub
    K[L & (p_ash > dither) & ~np.isin(K, ['glacier', 'crag', 'saltpan', 'erg', 'river'])] = 'ash'
    T['old_flows'] = []
    r_ = np.random.default_rng(12)
    for i, (ang, rad0) in enumerate([(-2.3, 380), (-0.9, 520), (0.35, 300), (1.25, 620), (2.6, 450)]):   # old flows from flank vents
        L1 = r_.uniform(500, 1100)
        pts = [(VOLCANO[0] + rad0 * math.cos(ang), VOLCANO[1] + rad0 * math.sin(ang))]
        a_ = ang
        for k_ in range(5):
            a_ += r_.uniform(-0.3, 0.3); pts.append((pts[-1][0] + L1 / 5 * math.cos(a_), pts[-1][1] + L1 / 5 * math.sin(a_)))
        mp = meander(pts, 40, 300 + i, 80); d, al, tot = raster(mp); T['old_flows'].append(mp)
        tongue = L & (d < (30 + 90 * al / tot) * (1 + 0.5 * noise(120, 310 + i))) & (al < tot * 0.97) & (dither > 0.08 + 0.5 * al / tot)
        tt = tongue & ~np.isin(K, ['glacier', 'crag', 'saltpan', 'river'])
        K[tt] = np.where(wet[tt] > 0.55, 'fireweed', 'lavastone')
    upper = L & (h > 0.62) & (dv < 1100)
    K[upper & (nz > -0.25)] = 'ash'                                              # scree and cinders high on the cone
    K[L & (dvc < 420) & (nz > 0.05)] = 'basalt'
    fire = np.zeros((H, W), bool)
    T['flows'] = []
    for i, lp in enumerate([[(2410, 4540), (2330, 4680), (2200, 4850), (2120, 5050), (2010, 5250), (1980, 5500), (1900, 5950)],
                            [(2500, 4540), (2610, 4700), (2800, 4880), (2930, 5100), (3150, 5300), (3240, 5560), (3300, 5950)]]):
        mp = meander(lp, 45, 50 + i, 80); d, al, tot = raster(mp); T['flows'].append(mp)
        wdt = (36 + 80 * (al / tot) ** 1.4) * (1 + 0.45 * noise(160, 51 + i) + 0.25 * noise(50, 61 + i, 2))
        fire |= (d < wdt) & L
        for j, frac in enumerate((0.45, 0.7)):  # side lobes where the flow spilled over
            x_, y_, a2, t2 = densify(mp, 8); q = int(frac * (len(x_) - 1))
            fire |= shape(x_[q] + (1 if i else -1) * 90, y_[q] + 40, 120, 70, 70 + 4 * i + j, 0.5, 0.6 if i else -0.6) & L
    rim = (dvc >= 150) & (dvc < 205 + 22 * noise(70, 47)) & L
    fire |= rim | ((dvc < 150) & L)
    K[fire] = 'lava'; K[rim] = 'crag'; K[L & (dvc < 150)] = 'basalt'; K[L & shape(VOLCANO[0], VOLCANO[1] + 10, 70, 55, 48, 0.3)] = 'crater'
    fire |= (dvc < 150) & L
    # a fumarole field and a dead forest where the east flow passed through the coastal woods
    for (fx, fy) in [(2780, 4300), (2950, 4420), (2230, 4330)]:
        K[shape(fx, fy, 60, 40, int(fx), 0.4) & L & ~fire] = 'channel'
    dead = L & (noise(300, 48) + 0.5 * np.exp(-(raster(T['flows'][1])[0] / 500) ** 2) > 0.35) & (np.hypot(PX - 3450, PY - 5200) < 750) \
        & np.isin(K, ['broadleaf', 'meadow', 'steppe', 'fireweed', 'lavastone', 'conifer'])
    K[dead] = 'deadwood'
    # the Frostline: a cirque, a tarn, and a rim of crags with a lip to the south
    rim_ff = ndi.binary_dilation(cq_shape, iterations=6) & ~cq_shape
    K[cq_shape] = np.where(noise(90, 49)[cq_shape] > -0.1, 'snow', 'alpine'); K[lake_ff] = 'tarn'; K[rim_ff & L] = 'crag'
    # the eastern border: moss fens on the uplands, the old forest beyond them
    fscore = 1 / (1 + np.exp(-(WX - 10350) / 220)) / (1 + np.exp(-(WY - 2500) / 220)) / (1 + np.exp((WY - 4250) / 220))
    fens = L & (fscore + 0.35 * noise(400, 52) > 0.55)
    K[fens] = 'bog'; K[fens & (noise(110, 53, 2) > 0.45)] = 'mere'
    K[L & (WX > 9800) & (WY < 2600) & np.isin(K, ['broadleaf', 'conifer', 'meadow'])] = 'conifer'
    forest = np.isin(K, ['broadleaf', 'conifer'])
    K[ndi.binary_erosion(forest, iterations=10) & (noise(260, 54) > -0.2)] = 'wild'
    # coasts
    shore = L & (dsea < 32 + 22 * (noise(200, 55) + 1))
    sh = shore & ~np.isin(K, ['lava', 'crag', 'crater'])
    K[sh] = np.where(dv[sh] < 2300, 'blacksand', 'sand')
    K[shore & ((h > 0.33) | (hcr > 0.3))] = 'cliff'
    K[L & (slope > 0.017) & ~np.isin(K, ['lava', 'glacier', 'snow', 'crag', 'crater', 'tarn'])] = 'cliff'
    K[deltamarsh & np.isin(K, ['meadow', 'watermeadow', 'steppe', 'sand', 'broadleaf'])] = 'bog'
    K[water & L] = 'river'; K[rapids & L] = 'rapids'; K[T['oxbow'] & L] = 'oxbow'; K[shoals & L] = 'shoal'
    # creeks and tarns from the drainage of the height field (priority flood); they are fordable, not barriers
    cre, tarn = drainage(h, wet, land)
    K[cre & L & np.isin(K, ['meadow', 'steppe', 'broadleaf', 'conifer', 'alpine', 'barren', 'watermeadow', 'fireweed', 'scrub', 'snow', 'bog', 'deadwood'])] = 'creek'
    K[tarn & L & np.isin(K, ['alpine', 'barren', 'snow', 'conifer'])] = 'tarn'
    wall = capsule([(6820, 5300), (7120, 5300)], 12, 12) & L & (PY > 5250)
    K[wall] = 'wall'
    T.update(K=K, h=h, wet=wet, dv=dv, sea=sea, fire=fire, rim=rim_ff, slope=slope)
    T['barriers'] = {'rim': rim_ff & L, 'fire': fire, 'sea': sea, 'the Cog': T['river_masks']['the Cog'], 'the Lull': lull | T['river_masks']['the Sorrel'],
                     'the Rift': T['river_masks']['the Rift'], 'wall': wall}
    T['K0'] = K.copy()
    return T


def drainage(h, wet, land):
    S = 4; hs = ndi.gaussian_filter(h, 6)[::S, ::S] + 0.004 * noise(400, 90)[::S, ::S]; ls = land[::S, ::S]; ws = wet[::S, ::S]; hh_, ww_ = hs.shape
    done = np.zeros(hs.shape, bool); fill = hs.copy(); rec = -np.ones(hs.size, int); order = []
    pq = []
    border = ~ls.copy(); border[0, :] = True; border[:, 0] = True; border[:, -1] = True
    for y, x in zip(*np.nonzero(border)):
        heapq.heappush(pq, (hs[y, x], y * ww_ + x)); done[y, x] = True
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while pq:
        v, i = heapq.heappop(pq); y, x = divmod(i, ww_); order.append(i)
        for dy, dx in nb:
            ny, nx = y + dy, x + dx
            if 0 <= ny < hh_ and 0 <= nx < ww_ and not done[ny, nx]:
                done[ny, nx] = True; fill[ny, nx] = max(hs[ny, nx], v + 1e-6); rec[ny * ww_ + nx] = i
                heapq.heappush(pq, (fill[ny, nx], ny * ww_ + nx))
    rain = (np.clip(ws, 0, 1.2) ** 2 + 0.6 * (hs > 0.7)).ravel()
    acc = rain.copy()
    for i in reversed(order):
        r = rec[i]
        if r >= 0:
            acc[r] += acc[i]
    acc = acc.reshape(hs.shape)
    cr = (acc > 110) & ls & (ws > 0.45)
    flat = cr.ravel()
    donor = np.zeros(hs.size, bool)
    for i in np.nonzero(flat)[0]:
        if rec[i] >= 0:
            donor[rec[i]] = True
    full = np.zeros((H, W), bool); seen = np.zeros(hs.size, bool); chains = []
    for i0 in np.nonzero(flat & ~donor)[0]:  # each creek from its head down to where it joins water or another creek
        pts = []; i = i0
        while i >= 0 and flat[i]:
            y, x = divmod(i, ww_); pts.append(((x * S + 2) * CELL, (y * S + 2) * CELL))
            if seen[i]:
                break
            seen[i] = True; i = rec[i]
        if i >= 0 and not flat[i]:
            y, x = divmod(i, ww_); pts.append(((x * S + 2) * CELL, (y * S + 2) * CELL))
        if len(pts) >= 7:
            chains.append(pts)
    for k_, pts in enumerate(chains):
        sm = meander(pts[::3] + [pts[-1]], 22, 900 + k_, 70)
        x_, y_, _, _ = densify(sm, 3); cx_, cy_ = (x_ // CELL).astype(int), (y_ // CELL).astype(int)
        ok = (cx_ >= 0) & (cx_ < W) & (cy_ >= 0) & (cy_ < H); full[cy_[ok], cx_[ok]] = True
    tarn = np.kron(((fill - hs) > 0.012) & (hs > 0.5) & ls, np.ones((S, S), bool))[:H, :W]
    return full, tarn


WALK = {'meadow', 'watermeadow', 'steppe', 'scrub', 'desert', 'broadleaf', 'conifer', 'deadwood', 'alpine', 'barren', 'snow', 'ash', 'lavastone',
        'fireweed', 'basalt', 'sand', 'blacksand', 'bog', 'saltpan', 'badland', 'mesa', 'creek', 'channel', 'shoal', 'path', 'road', 'bridge',
        'yard', 'field', 'field2', 'orchard', 'plaza', 'dock', 'pier', 'bar', 'stair', 'garden', 'pad', 'hedge'}
COL = {'sea': '#2B557F', 'meadow': '#8DB05C', 'watermeadow': '#7FB466', 'steppe': '#B5B36C', 'scrub': '#C8AE72', 'desert': '#E2C385',
       'erg': '#ECC97F', 'broadleaf': '#5E8A45', 'conifer': '#3F6B48', 'wild': '#2A4A33', 'deadwood': '#857A68', 'alpine': '#A3B489',
       'barren': '#A89C86', 'snow': '#EEF2F6', 'glacier': '#D3E4F1', 'crag': '#5E5A64', 'badland': '#B0663E', 'mesa': '#BF7444',
       'saltpan': '#EEE8DC', 'ash': '#86807A', 'lavastone': '#5D5658', 'fireweed': '#8C6E78', 'basalt': '#3A353C', 'lava': '#E0612A',
       'crater': '#FFB347', 'sand': '#E8D39C', 'blacksand': '#4A4448', 'cliff': '#7A726B', 'river': '#3E78B5', 'rapids': '#9CC7E8',
       'oxbow': '#4C83B0', 'shoal': '#D9CBA0', 'creek': '#5E95C4', 'tarn': '#4F86B8', 'mere': '#4C7FA6', 'bog': '#7D8F62', 'canal': '#3E70A8',
       'channel': '#6FA5CF', 'path': '#E2C68C', 'road': '#D7C29B', 'bridge': '#9C7448', 'bar': '#E5D5A6', 'yard': '#C2A574', 'field': '#CDB458',
       'field2': '#A9B65A', 'orchard': '#6E9A4A', 'hedge': '#4F7A3E', 'plaza': '#DDD3BC', 'dock': '#8F7356', 'pier': '#A88A62',
       'building': '#A4553E', 'warehouse': '#8C5A44', 'tower': '#6A5A90', 'neon': '#D04FA6', 'castlewall': '#8A8590', 'wall': '#6E5E4E',
       'stair': '#EADFC2', 'viaduct': '#6B5E55', 'garden': '#77A257', 'pad': '#C9C6C0', 'hut': '#7A4A30', 'falls': '#E8F4FF'}


# ------------------------------------------------------------------------------------------ paths
def switchback(pts, a0, a1, amp=70, n=7):
    x, y, al, tot = densify(pts, 6)
    out = []; leg = (a1 - a0) * tot / n
    for i in range(len(x)):
        a = al[i]
        if a0 * tot < a < a1 * tot:
            j, k = min(i + 1, len(x) - 1), max(i - 1, 0); tx, ty = x[j] - x[k], y[j] - y[k]; L = math.hypot(tx, ty) or 1
            ph = ((a - a0 * tot) / leg) % 2; tri = (ph if ph < 1 else 2 - ph) * 2 - 1
            env = math.sin(math.pi * (a - a0 * tot) / ((a1 - a0) * tot))
            out.append((x[i] - ty / L * tri * amp * env, y[i] + tx / L * tri * amp * env))
        else:
            out.append((x[i], y[i]))
    return out[::3] + [out[-1]]


def routes(T):
    K = T['K']; crossings = []; T['route_px'] = {}; T['huts'] = []
    used = np.zeros((H, W), bool)
    for name, (pts, kind, feats) in ROUTES.items():
        sm = meander(pts, 0 if kind == 'bridge' or len(pts) < 3 else 18, stable_name_seed(name, 1000), 140)
        for f in feats:
            if f.startswith('switchbacks'):
                a0, a1 = map(float, f.split(':')[1].split('-')); sm = switchback(sm, a0, a1)
        T['route_px'][name] = sm
        width = {'road': 40, 'path': 24, 'bar': 40, 'bridge': 40}[kind]
        rmask = line_mask(sm, width)
        d, al, tot = raster(sm)
        for f in feats:  # fit the ground to the path
            nm, _, rng = f.partition(':')
            a0, a1 = (map(float, rng.split('-')) if '-' in rng else (0, 1))
            seg = (al > a0 * tot) & (al < a1 * tot)
            if nm == 'woodland':  # the road winds through woods; the trees close in on both sides
                K[seg & (d < 380) & (d > width) & np.isin(K, ['meadow', 'steppe', 'watermeadow'])] = 'broadleaf'
            if nm == 'watermeadows':
                K[seg & (d < 300) & (d > width) & np.isin(K, ['meadow', 'steppe'])] = 'watermeadow'
            if nm == 'dunes':
                K[seg & (d < 160) & (d > width) & np.isin(K, ['meadow', 'steppe', 'scrub'])] = 'sand'
            if nm == 'deadwood':
                K[seg & (d < 420) & (d > width) & np.isin(K, ['broadleaf', 'meadow', 'fireweed', 'steppe', 'lavastone'])] = 'deadwood'
            if nm == 'hut':
                lab_, at = rng.split('@'); x, y, _, _ = densify(sm, 6); i = int(float(at) * (len(x) - 1))
                T['huts'].append((lab_, x[i] + 48, y[i])); hx, hy = int((x[i] + 48) // CELL), int(y[i] // CELL); K[hy - 2:hy + 2, hx - 2:hx + 3] = 'hut'
            if nm == 'well':
                x, y, _, _ = densify(sm, 6); i = int(float(rng) * (len(x) - 1)); T['huts'].append(('well', x[i], y[i] + 30))
            if nm == 'folds':
                x, y, _, _ = densify(sm, 6)
                for j in range(len(x) // 5, len(x), len(x) // 4):
                    fx, fy = int((x[j] + 50) // CELL), int((y[j] - 45) // CELL)
                    if np.isin(K[fy - 3:fy + 3, fx - 4:fx + 4], ['steppe', 'scrub', 'meadow', 'desert']).all():
                        K[fy - 3:fy + 3, fx - 4:fx + 4] = 'hedge'; K[fy - 2:fy + 2, fx - 3:fx + 3] = 'steppe'
        water = rmask & np.isin(K, ['river', 'rapids', 'lava', 'sea', 'creek', 'canal', 'oxbow', 'tarn', 'mere', 'crater', 'wall', 'crag'])
        if kind == 'bar':
            K[rmask & (K == 'sea')] = 'bar'
        K[water & (K != 'bar')] = np.where(np.isin(K[water & (K != 'bar')], ['wall', 'crag']), 'stair', 'bridge')
        K[rmask & ~water & ~np.isin(K, ['bridge', 'bar', 'stair'])] = 'stair' if name in ('Col Path', 'Lode Track') else (kind if kind != 'bridge' else 'road')
        used |= rmask
        for bname, bm in T['barriers'].items():
            hit = rmask & bm
            if not hit.any():
                continue
            lab, n = ndi.label(ndi.binary_dilation(hit, iterations=2))
            for i in range(1, n + 1):
                ys, xs = np.nonzero(lab == i)
                way = CROSS.get((name, bname)); x, y = xs.mean() * CELL + 4, ys.mean() * CELL + 4
                rr = max(np.ptp(xs), np.ptp(ys)) * CELL / 2 + 48
                crossings.append({'route': name, 'barrier': bname, 'way': way, 'x': round(float(x)), 'y': round(float(y))})
                if way and way != 'open':
                    WAYS.setdefault(way, []).append((float(x), float(y), float(rr)))
    T['crossings'] = crossings; T['used_routes'] = used


OK = ['meadow', 'watermeadow', 'steppe', 'scrub', 'desert', 'broadleaf', 'conifer', 'sand', 'alpine', 'barren', 'ash', 'blacksand',
      'yard', 'lavastone', 'fireweed', 'basalt', 'deadwood', 'creek', 'garden', 'badland']


def settle(T):
    K, h = T['K'], T['h']; used = T['used_routes'].copy()
    r = np.random.default_rng(5)

    def put(x0, y0, w, h_, kind, need=OK, ring=None):
        a, b = int(y0 // CELL), int(x0 // CELL); c, d = a + max(1, int(h_ // CELL)), b + max(1, int(w // CELL))
        if a < 1 or b < 1 or c >= H - 1 or d >= W - 1:
            return False
        blk = K[a:c, b:d]
        if not np.isin(blk, need).all():
            return False
        if ring:
            rg = K[a - 1:c + 1, b - 1:d + 1]; m = np.isin(rg, OK); rg[m] = ring
        K[a:c, b:d] = kind; used[a - 1:c + 1, b - 1:d + 1] = True; return True

    for name, (cx, cy, rad, kind) in SETTLE.items():
        if kind in ('cirque', 'city'):
            continue
        dn = np.hypot(PX - cx, PY - cy) / rad + 0.35 * noise(rad * 1.3, stable_name_seed(name, 997))
        core = dn < 1
        K[core & np.isin(K, ['broadleaf', 'conifer'])] = 'garden'   # cleared for houses and gardens
        used |= core & np.isin(K, list(WALK))
        if kind in ('village', 'town', 'hamlet', 'harbour', 'frontier', 'oasis'):
            patch(T, cx, cy, rad, kind, used)
        hw = {'village': 64, 'town': 56, 'frontier': 48, 'castle': 40}.get(kind, 40)
        for rn, sm in T['route_px'].items():  # houses go along the streets that pass through
            x, y, al, tot = densify(sm, 8)
            for i in range(0, len(x), 14):
                yi, xi = min(H - 1, int(y[i] // CELL)), min(W - 1, int(x[i] // CELL))
                if not core[yi, xi]:
                    continue
                j = min(i + 1, len(x) - 1); k_ = max(i - 1, 0); tx, ty = x[j] - x[k_], y[j] - y[k_]; L = math.hypot(tx, ty) or 1
                for side in (-1, 1):
                    bx, by = x[i] - ty / L * hw * side, y[i] + tx / L * hw * side
                    bw, bh = (48, 40) if kind != 'frontier' else (56, 32)
                    if r.uniform() < 0.85:
                        put(bx - bw / 2, by - bh / 2, bw, bh, 'building', ring='yard')
        if kind == 'village':  # the square
            put(cx - 120, cy - 70, 240, 136, 'plaza', need=OK + ['creek', 'field', 'field2', 'hedge'])
        if kind == 'castle':  # Hearthold: walls round the rock's top, a keep, the gate where the road comes in
            a, b = int((cy - 200) // CELL), int((cx - 200) // CELL); blk = K[a:a + 50, b:b + 50]
            rd = np.isin(blk, ['path', 'road', 'bridge', 'stair'])
            ok = np.isin(blk, OK)
            blk[ok & ~rd] = 'yard'
            ring_ = np.zeros(blk.shape, bool); ring_[[0, 1, -2, -1], :] = True; ring_[:, [0, 1, -2, -1]] = True
            blk[ring_ & ok & ~rd] = 'castlewall'
            keep = blk[18:30, 18:32]; keep[~np.isin(keep, ['path', 'road'])] = 'building'
        if kind == 'springs':
            for (sx, sy) in [(cx - 60, cy + 40), (cx + 50, cy + 70), (cx - 10, cy - 60)]:
                put(sx, sy, 48, 32, 'channel')
        if kind in ('mine', 'forge', 'cape'):
            put(cx - 32, cy - 24, 64, 48, 'building' if kind != 'cape' else 'tower', need=OK + ['path', 'road'])
    # Cogsworth's Millrace: a leat off the Cog through the mills
    mill = line_mask(chaikin([(7835, 2300), (7930, 2380), (8000, 2470), (8050, 2560), (8000, 2650), (7930, 2700)], 2), 16)
    K[mill & ~np.isin(K, ['road', 'path', 'bridge', 'river', 'stair'])] = 'canal'
    # irrigation from the oases: narrow channels, stepped over
    for (sx, sy, ex, ey) in [(3480, 2800, 3300, 3000), (3480, 2800, 3650, 2950), (2730, 2450, 2600, 2700), (2730, 2450, 2950, 2600)]:
        m = line_mask(meander([(sx, sy), ((sx + ex) / 2, (sy + ey) / 2), (ex, ey)], 15, int(sx + ey), 60), 8)
        K[m & np.isin(K, OK + ['field', 'field2', 'orchard'])] = 'channel'
    city(T, used)
    T['used'] = used


def patch(T, cx, cy, rad, kind, used):
    """Fields in a patchwork round a settlement, on the flat ground near water; hedges between them."""
    K = T['K']; r = np.random.default_rng(int(cx + cy))
    dry = kind in ('frontier', 'oasis')
    y = cy - rad * 1.5
    while y < cy + rad * 1.5:
        x = cx - rad * 1.6; rh = int(r.integers(64, 136))
        while x < cx + rad * 1.6:
            rw = int(r.integers(72, 168))
            d = math.hypot(x + rw / 2 - cx, y + rh / 2 - cy) / rad
            if 0.55 < d < 1.25 + 0.35 * r.uniform() and r.uniform() < 0.8:
                a, b = int(y // CELL), int(x // CELL); c, e = a + rh // CELL, b + rw // CELL
                if 1 < a and c < H - 1 and 1 < b and e < W - 1:
                    blk = K[a:c, b:e]
                    land_ = ['meadow', 'steppe', 'watermeadow', 'scrub', 'garden'] + (['desert'] if dry else [])
                    ok = np.isin(blk, land_).mean()
                    flat = T['slope'][a:c, b:e].max() < 0.012
                    if ok > 0.9 and flat and (not dry or T['wet'][a:c, b:e].mean() > 0.5):
                        m = np.isin(blk, land_)
                        blk[m] = 'orchard' if dry else r.choice(['field', 'field2'])
                        edge = np.zeros(blk.shape, bool); edge[[0, -1], :] = True; edge[:, [0, -1]] = True
                        blk[edge & m] = 'hedge'; used[a:c, b:e] = True
            x += rw
        y += rh


def city(T, used):
    """Neon Harbour round the ria. Districts: the Falls Rock (the old town between the two falls), the market at
    the old bridges' foot, the docks and warehouses on the deep east side, the Heights' terraces on the west
    headland, the Gull Strand fishing quarter at the mouth, Chapel Islet and Beacon Isle, the neon new town and
    the Skyport on the eastern flats, the canal basin where the Lull Cut comes in."""
    K, h = T['K'], T['h']; r = np.random.default_rng(9)
    C = lambda x, y: (int(y // CELL), int(x // CELL))
    LAND = ['meadow', 'watermeadow', 'steppe', 'broadleaf', 'conifer', 'sand', 'scrub', 'garden', 'yard', 'creek', 'wild', 'bog', 'cliff', 'mere']

    def district(x0, y0, x1, y1, mode, shape_seed=None):
        a, b = C(x0, y0); c, d = C(x1, y1); sub = K[a:c, b:d]; ok = np.isin(sub, LAND); hh = h[a:c, b:d]
        if mode == 'grid':  # the new town has grown out from the terminus; its far edges are ragged, unfinished
            fx = (PX[a:c, b:d] - x0) / (x1 - x0) + 0.22 * noise(260, 68)[a:c, b:d]
            fy = (PY[a:c, b:d] - y0) / (y1 - y0) + 0.22 * noise(260, 69)[a:c, b:d]
            ok &= (fx < 0.95) & (fy > 0.05)
        elif shape_seed is not None:  # districts end where the ground does, not on a ruler line
            e = np.hypot((PX[a:c, b:d] - (x0 + x1) / 2) / ((x1 - x0) / 2), (PY[a:c, b:d] - (y0 + y1) / 2) / ((y1 - y0) / 2))
            ok &= (np.maximum(e, 0) ** 4 + 0.35 * noise(300, shape_seed)[a:c, b:d]) < 1.0
        gy, gx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
        if mode == 'grid':  # planned blocks 208 x 272 with 96 px streets; towers round each block's edge, a court inside
            bx, by = (gx * CELL) % 304, (gy * CELL) % 368
            blk = (bx < 208) & (by < 272); edge = blk & ((bx < 56) | (bx >= 152) | (by < 56) | (by >= 216))
            sub[ok & ~blk] = 'road'; sub[ok & blk] = 'plaza'; sub[ok & edge] = 'tower'
            sub[ok & edge & (r.uniform(size=sub.shape) < 0.07)] = 'neon'
        elif mode == 'terraces':  # houses in rows along the contours, gardens between, stairs straight up the slope
            band = ((hh + 0.012 * noise(220, 63)[a:c, b:d] + 0.004 * noise(60, 64, 2)[a:c, b:d]) * 60) % 1.0
            row = band < 0.38
            house = row & (((gx + (band * 40).astype(int)) % 7) < 5)
            sub[ok] = 'garden'; sub[ok & row] = 'path'; sub[ok & house] = 'building'
        elif mode == 'old':  # the old town: dense houses, wandering lanes, a square at the top
            n = noise(120, 61)[a:c, b:d] + 0.5 * noise(40, 62, 2)[a:c, b:d]
            sub[ok] = 'building'; sub[ok & (np.abs(n) <= 0.08)] = 'road'
            sub[ok & (((gy % 6) == 0) | ((gx % 7) == 0)) & (np.abs(n) < 0.25)] = 'road'
        elif mode == 'warehouses':
            m = ((gy % 12) < 9) & ((gx % 9) < 7); sub[ok & m] = 'warehouse'; sub[ok & ~m] = 'plaza'
        elif mode == 'fishing':  # a strip along the beach, boats hauled up in front
            ok &= ndi.distance_transform_edt(~T['sea'])[a:c, b:d] * CELL < 170
            m = ((gy % 7) < 3) & ((gx % 6) < 4) & (r.uniform(size=sub.shape) < 0.98); sub[ok] = 'sand'; sub[ok & m] = 'building'
        elif mode in ('plaza', 'pad'):
            sub[ok] = mode
        used[a:c, b:d] |= ok

    district(9520, 4560, 10000, 5330, 'terraces', 64)      # the Heights: the rich quarter, views and breeze, away from the docks
    district(10100, 4250, 10250, 4460, 'old')              # the Falls Rock: the old town, defensible, the first crossing
    district(10330, 4380, 10690, 4620, 'plaza')            # the market at the old bridges' foot (352 x 248)
    district(10500, 4660, 10700, 5080, 'warehouses')       # warehouses behind the docks
    district(10720, 4220, 11220, 4930, 'grid')         # the neon new town, round the maglev terminus
    district(10480, 5120, 10800, 5420, 'fishing')      # the Gull Strand: boats on the beach at the ria's mouth
    district(10760, 4960, 11160, 5220, 'pad')              # the Skyport: a flat field, open to the sea wind
    for (mx, my) in [(10840, 5040), (10980, 5060), (11080, 5110)]:
        a, b = C(mx, my); K[a:a + 3, b:b + 3] = 'tower'    # mooring masts
    # docks along the deep east side of the ria, piers out into the lee water
    bay = T['sea'] & (PX > 9800) & (PX < 10500) & (PY > 4450) & (PY < 5150)
    bank = ndi.binary_dilation(bay, iterations=4) & ~bay & (PX > 10230) & T['land']
    K[bank & ~np.isin(K, ['road', 'bridge'])] = 'dock'; used |= bank
    for py in range(4600, 5120, 90):
        a, b = C(10520, py)
        js = [j for j in range(b - 50, b + 1) if K[a, j] == 'sea']
        for j in js[-14:]:
            K[a:a + 2, j] = 'pier'
    # the Lull Cut from Lullford's east bank to the canal basin under the Heights, with its towpath
    cut = chaikin([(9020, 4400), (9350, 4490), (9600, 4560), (9800, 4640), (9900, 4690)], 3)
    cm = line_mask(cut, 24); K[cm & ~np.isin(K, ['road', 'bridge', 'river', 'sea'])] = 'canal'
    tp = line_mask([(x, y - 30) for (x, y) in cut], 16); K[tp & np.isin(K, LAND + ['building', 'garden', 'stair'])] = 'path'; used |= tp
    a, b = C(10080, 5440); K[a - 3:a + 3, b - 3:b + 3] = 'tower'   # the old lighthouse on Beacon Isle
    via = line_mask([(8760, 2380), (9030, 2330), (9300, 2300)], 16)      # the Narrows Viaduct: rail only, not a footway
    K[via & ~np.isin(K, ['road', 'path', 'bridge'])] = 'viaduct'
    a, b = C(10130, 4985); K[a - 3:a + 3, b - 5:b - 1] = 'building'  # the chapel on its islet, beside the bridge
    for arm in GLINT_ARMS:  # the Glint's two arms drop off the scarp into the head of the ria
        m = line_mask(chaikin(arm, 2), 34); K[m & ~np.isin(K, ['road', 'bridge'])] = 'river'
        x, y = arm[-1]; a, b = C(x, y - 16); K[a - 3:a + 2, b - 3:b + 3] = 'falls'


FRAME_PX = 470
FRAME = None


def walk_mask(K):
    m = np.isin(K, list(WALK))
    return m & ~FRAME if FRAME is not None else m


def way_mask(labels):
    m = np.zeros((H, W), bool)
    for lab in labels:
        for (x, y, r) in WAYS.get(lab, []):
            m |= np.hypot(PX - x, PY - y) < r
    return m


def pt(p):
    if isinstance(p, str):
        return STATIONS[p] if p in STATIONS else SETTLE[p][:2]
    return p


def nearest_walk(Wm, x, y):
    cy, cx = int(y // CELL), int(x // CELL)
    for r in range(0, 90):
        y0, x0 = max(0, cy - r), max(0, cx - r)
        ys, xs = np.nonzero(Wm[y0:cy + r + 1, x0:cx + r + 1])
        if len(ys):
            k = np.argmin((ys + y0 - cy) ** 2 + (xs + x0 - cx) ** 2)
            return y0 + ys[k], x0 + xs[k]
    raise ValueError((x, y))


def gate_check(K, crossings):
    Wm = walk_mask(K); out = {}
    for n in range(len(ORDER) + 1):
        closed = way_mask(ORDER[n:])
        lab, _ = ndi.label(Wm & ~closed)
        hy, hx = nearest_walk(Wm & ~closed, *HOME); home = lab[hy, hx]
        leaks, missing = [], []
        for w in ORDER:
            for tgt in BEHIND[w]:
                ty, tx = nearest_walk(Wm & ~closed, *pt(tgt)); reach = lab[ty, tx] == home
                if reach and w in ORDER[n:]:
                    leaks.append(f'{tgt} reachable with {w} closed')
                if not reach and w not in ORDER[n:]:
                    missing.append(f'{tgt} not reached with {w} open')
        if n == 0:
            for tgt in START:
                ty, tx = nearest_walk(Wm & ~closed, *pt(tgt))
                if lab[ty, tx] != home:
                    missing.append(f'{tgt} not reached from home at the start')
        out['open: ' + (','.join(ORDER[:n]) or 'none')] = {'leaks': leaks, 'missing': missing}
    out['crossings without a way'] = [c for c in crossings if not c['way']]
    out['crossings'] = crossings
    return out


def times(K):
    Wm = walk_mask(K); cost = np.where(Wm, 1.0, np.inf)

    def from_(p):
        y, x = nearest_walk(Wm, *pt(p)); d, _ = MCP_Geometric(cost).find_costs([(y, x)]); return d * CELL / SPEED

    def at(dm, p):
        y, x = nearest_walk(Wm, *pt(p)); v = dm[y, x]; return float(v) if np.isfinite(v) else math.inf
    nodes = ['home'] + list(STATIONS); D = {'home': from_(HOME)}
    for s in STATIONS:
        D[s] = from_(s)
    dist = {n: math.inf for n in nodes}; dist['home'] = 0; done = set()
    while len(done) < len(nodes):
        n = min((v, k) for k, v in dist.items() if k not in done)[1]; done.add(n)
        for o in STATIONS:
            c = at(D[n], o)
            for sc in SHORTCUTS:
                if {sc[1], sc[2]} == {n, o}:
                    c = min(c, sc[3])
            dist[o] = min(dist[o], dist[n] + c)
    res = {}
    for nm in SETTLE:
        f = at(D['home'], nm); b = min(dist[k] + at(D[k], nm) for k in nodes)
        res[nm] = {'on_foot_s': round(f, 1) if f < math.inf else None, 'with_shortcuts_s': round(b, 1) if b < math.inf else None}
    rl = {}
    for rn, (pts, kind, feats) in ROUTES.items():
        if rn.startswith('Valley lane') or kind == 'bridge':
            continue
        v = at(from_(pts[0]), pts[-1]); rl[rn] = round(v, 1) if v < math.inf else None
    return res, rl, int(Wm.sum())


# ------------------------------------------------------------------------------------------ drawing
def hexc(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def shade(h):
    gy_, gx_ = np.gradient(ndi.gaussian_filter(h, 1.2))
    return np.clip(1.0 - (gx_ + gy_) * 30.0, 0.5, 1.4)


class Labels:
    def __init__(self, draw):
        self.d = draw; self.boxes = []

    def free(self, b):
        return all(b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3] for o in self.boxes)

    def put(self, xy, text, font, fill='white', stroke='black', prefer=((0, -16), (0, 16), (60, 0), (-60, 0), (0, -32), (0, 32), (90, -20), (-90, 20))):
        for dx, dy in prefer:
            x, y = xy[0] + dx, xy[1] + dy
            b = self.d.textbbox((x, y), text, font=font, anchor='mm', stroke_width=2)
            b = (b[0] - 3, b[1] - 2, b[2] + 3, b[3] + 2)
            if self.free(b):
                self.boxes.append(b); self.d.text((x, y), text, font=font, fill=fill, stroke_width=2, stroke_fill=stroke, anchor='mm'); return True
        return False


SHADE = {}


def colour(T, K, physical=False):
    rgb = np.zeros((H, W, 3))
    for k, c in COL.items():
        rgb[K == k] = hexc(c)
    if 'shade' not in SHADE:
        SHADE['shade'] = shade(T['h']); dsea = ndi.distance_transform_edt(T['sea']) * CELL; SHADE['deep'] = np.clip(dsea / 900, 0, 1)[..., None]
        rnd = np.random.default_rng(3).random((H, W))
        dunes = np.sin((PX * 0.8 + PY * 0.6) / 34 + 5 * noise(500, 80)) > 0.55
        SHADE['tex'] = (rnd, dunes)
    rnd, dunes = SHADE['tex']
    tex = np.ones((H, W))
    tex[np.isin(K, ['broadleaf', 'conifer', 'wild', 'orchard']) & (rnd < 0.28)] = 0.82      # canopy
    tex[np.isin(K, ['erg', 'desert']) & dunes] = 1.07                                     # dune crests
    tex[np.isin(K, ['scrub', 'steppe', 'lavastone', 'fireweed', 'deadwood']) & (rnd < 0.1)] = 0.85   # bushes, boulders, snags
    tex[np.isin(K, ['bog', 'watermeadow']) & (rnd < 0.08)] = 0.8
    rgb = rgb * tex[..., None]
    rgb = rgb * (0.8 + 0.32 * np.clip(T['h'], 0, 1.1))[..., None] if physical else rgb * (0.9 + 0.15 * np.clip(T['h'], 0, 1.1))[..., None]
    rgb = np.where(T['land'][..., None], rgb * SHADE['shade'][..., None], rgb)
    deep = SHADE['deep']
    rgb = np.where((K == 'sea')[..., None], np.array(hexc('#3C78A6')) * (1 - deep) + np.array(hexc('#23466E')) * deep, rgb)
    return rgb


def render(T, out, scale=1, annotate=True, crop=None, physical=False, title=None):
    K = T['K0'] if physical else T['K']
    rgb = colour(T, K, physical)
    if FRAME is not None and not physical:  # land drawn but not walked: a little hazier
        rgb = np.where((FRAME & T['land'])[..., None], rgb * 0.9 + np.array([40, 44, 52]) * 0.1, rgb)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    x0 = y0 = 0
    if crop:
        x0, y0, x1, y1 = crop; img = img.crop((x0 // CELL, y0 // CELL, x1 // CELL, y1 // CELL))
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(img); k = scale / CELL; P = lambda x, y: ((x - x0) * k, (y - y0) * k)
    Lb = Labels(d)
    if annotate:
        for lab, discs in WAYS.items():
            for (x, y, r) in discs:
                X, Y = P(x, y); d.rectangle([X - 13, Y - 9, X + 13, Y + 9], fill='#D7263D', outline='white')
                d.text((X, Y), lab, font=FONT, fill='white', anchor='mm'); Lb.boxes.append((X - 14, Y - 10, X + 14, Y + 10))
        for sc in SHORTCUTS:
            pts = chaikin([P(*pt(sc[1]))] + [P(*v) for v in sc[5]] + [P(*pt(sc[2]))], 3)
            for i, (p, q) in enumerate(zip(pts, pts[1:])):
                if i % 2 == 0:
                    d.line([p, q], fill='#FFFFFF', width=2)
        for nm, (x, y) in EGGS.items():
            X, Y = P(x, y); d.ellipse([X - 4, Y - 4, X + 4, Y + 4], outline='#FFFFFF', width=1)
        for nm, (x, y, r, kind) in SETTLE.items():
            X, Y = P(x, y); d.rectangle([X - 5, Y - 5, X + 5, Y + 5], fill='#FFE14A', outline='black'); Lb.boxes.append((X - 6, Y - 6, X + 6, Y + 6))
        for nm, (x, y, r, kind) in SETTLE.items():
            Lb.put(P(x, y), nm, FONTB)
        for nm, (x, y, desc) in BRIDGES.items():
            X, Y = P(x, y); d.ellipse([X - 6, Y - 6, X + 6, Y + 6], fill='#F2E5C8', outline='black')
            Lb.put((X, Y), nm, FONT, fill='#F2E5C8', prefer=((80, -14), (-80, -14), (80, 14), (-80, 14), (0, -24), (0, 24)))
        for lab_, x, y in T['huts']:
            X, Y = P(x, y); d.rectangle([X - 4, Y - 4, X + 4, Y + 4], fill='#7A4A30', outline='white')
        for rn, (pts, kind, feats) in ROUTES.items():
            if rn.startswith('Valley lane') or kind == 'bridge' or rn in ('Old Bridges', 'Quay Street', 'Forge Stair'):
                continue
            sm = T['route_px'][rn]
            for frac in (0.5, 0.35, 0.65):
                mp = sm[int(len(sm) * frac)]
                if Lb.put(P(*mp), rn.upper(), FONT, fill='#FFE98A', prefer=((0, 0), (0, -18), (0, 18), (50, 0), (-50, 0))):
                    break
        for rn, mp in T['river_px'].items():
            if ',' in rn:
                continue
            for frac in (0.3, 0.55, 0.75):
                q = mp[int(len(mp) * frac)]
                if Lb.put(P(*q), rn, FONT, fill='#CFE6FF', stroke='#123', prefer=((0, 0), (46, 0), (-46, 0), (0, 22), (0, -22))):
                    break
        for sc in SHORTCUTS:
            q = sc[5][len(sc[5]) // 2] if sc[5] else pt(sc[1]); Lb.put(P(*q), sc[0], FONT, fill='#F2F2F2', prefer=((0, 14), (0, -14), (60, 0), (-60, 0)))
    if annotate or physical:
        for t, x, y in [('THE NORTHERN MASSIF: glaciers; the land goes on north', 5600, 330), ('THE BRACKENS', 5000, 2650),
                        ('THE COAL HILLS', 8500, 2050), ('THE FERN HILLS', 7200, 2350), ('THE SUNSTONE BASIN', 1700, 2450),
                        ('the dune sea: the basin goes on west', 600, 3150), ('THE EMBER RANGE (the arc)', 1000, 4600), ('MOUNT EMBER', 2450, 4250),
                        ('THE LULL PLAIN', 7800, 4500), ('THE NARROWS', 9250, 2250), ('THE LULL DELTA', 8700, 5150),
                        ('THE MOSS FENS: the land goes on east', 10850, 3500), ('THE OLD FOREST', 10500, 1700), ('THE SOUTHERN SEA', 4900, 5950),
                        ('TIDEBLOOM ISLES', 5500, 6700), ('salt lake', 1950, 3700), ('ash fields', 2900, 3700), ('dead forest', 3500, 5250)]:
            if not crop or (crop[0] <= x <= crop[2] and crop[1] <= y <= crop[3]):
                Lb.put(P(x, y), t, FONTT if scale >= 2 else FONTB, prefer=((0, 0), (0, -26), (0, 26), (90, 0), (-90, 0)))
    if title:
        d.rectangle([0, 0, img.width, 26], fill=(20, 20, 24)); d.text((8, 4), title, font=FONTB, fill='white')
    img.save(os.path.join(HERE, out))
    return img


def ingame_map(T):
    """The in-game map in the soft-grid style (Matt's example 2): tiers stepped at 32 px from the height, flat
    colours from the ground, a darker face on each tier's south edge, outlines, icons on the tiers."""
    S = 4
    h = ndi.uniform_filter(T['h'], 3)[::S, ::S]; K = T['K'][::S, ::S]; land = T['land'][::S, ::S]
    tier = ndi.median_filter(np.clip(np.floor(h / 0.15), 0, 7).astype(int), 5)
    pal = dict(COL)
    pal.update({'meadow': '#93B866', 'steppe': '#C3BC75', 'desert': '#E6CA8E', 'broadleaf': '#6F9B4E', 'conifer': '#4F7E52', 'wild': '#3C6745',
                'river': '#3E4FA8', 'rapids': '#6E8FD8', 'oxbow': '#3E4FA8', 'canal': '#3E4FA8', 'path': '#EFDCA4', 'road': '#EFDCA4', 'stair': '#EFDCA4'})
    big = np.zeros(K.shape + (3,))
    for k, c in pal.items():
        big[K == k] = hexc(c)
    big = ndi.median_filter(big, size=(3, 3, 1))
    for k in ('river', 'rapids', 'road', 'path', 'bridge', 'lava', 'canal', 'stair', 'bar'):
        big[K == k] = hexc(pal[k])
    big[~land] = hexc('#2B2733')
    face = land & (np.roll(tier, 1, axis=0) > tier); big[face] = big[face] * 0.6
    edge = land & ((np.roll(tier, -1, 0) != tier) | (np.roll(tier, 1, 1) != tier) | (np.roll(tier, -1, 1) != tier)); big[edge] = big[edge] * 0.85
    coastl = land & ~ndi.binary_erosion(land); big[coastl] = big[coastl] * 0.65
    if FRAME is not None:
        fr = FRAME[::S, ::S] & land; big[fr] = big[fr] * 0.72 + np.array([40, 38, 50]) * 0.28
    img = Image.fromarray(np.clip(big, 0, 255).astype(np.uint8)).resize((K.shape[1] * 6, K.shape[0] * 6), Image.NEAREST)
    d = ImageDraw.Draw(img); k = 6 / (CELL * S); Lb = Labels(d)
    for nm, (x, y, r, kind) in SETTLE.items():
        X, Y = x * k, y * k
        col = {'city': '#7C6B95', 'castle': '#A0A0A0', 'cape': '#E0E0E0', 'cirque': '#DDEBF5'}.get(kind, '#C4704F')
        d.rectangle([X - 9, Y - 6, X + 9, Y + 8], fill=col, outline='#1E1917', width=2)
        d.polygon([(X - 11, Y - 6), (X, Y - 14), (X + 11, Y - 6)], fill='#7A3B2E', outline='#1E1917')
        Lb.boxes.append((X - 12, Y - 15, X + 12, Y + 9))
    for nm, (x, y, r, kind) in SETTLE.items():
        Lb.put((x * k, y * k + 4), nm, FONT, fill='#F7F2E8', stroke='#1E1917', prefer=((0, 18), (0, -24), (50, 0), (-50, 0), (0, 34)))
    for lab, discs in WAYS.items():
        for (x, y, r) in discs[:1]:
            d.ellipse([x * k - 6, y * k - 6, x * k + 6, y * k + 6], fill='#D7263D', outline='#1E1917', width=2)
    d.text((20, img.height - 30), 'In-game map mock, soft-grid style: tiers stepped at 32 px from the height; land beyond the walkable world drawn hazier', font=FONTB, fill='#F7F2E8')
    img.save(os.path.join(HERE, 'ingame-map-mock.png'))


def thumbnails():
    """Three arrangements of the same places, as small sketch maps."""
    tw, th = 440, 270; img = Image.new('RGB', (tw * 3 + 60, th + 96), '#F3EFE6'); d = ImageDraw.Draw(img)
    rr = np.random.default_rng(1)

    def jag(poly, a=6):
        out = []
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            for t in np.linspace(0, 1, 7)[:-1]:
                out.append((x0 + (x1 - x0) * t + rr.uniform(-a, a), y0 + (y1 - y0) * t + rr.uniform(-a, a)))
        return out

    def frame(ox, title, sub):
        d.rectangle([ox, 34, ox + tw, 34 + th], fill='#8DB05C'); d.text((ox, 8), title, font=FONTB, fill='black')
        for i, s in enumerate(sub):
            d.text((ox, 40 + th + i * 16), s, font=F(12), fill='#333')
    C = dict(sea='#2B557F', mount='#9C978F', snow='#EEF2F6', dry='#E2C385', steppe='#C3BC75', river='#3A78B8', volc='#5D5658', lava='#E0612A',
             city='#6A5A90', bog='#7D8F62')
    Y = lambda v: 34 + v
    ox = 10; frame(ox, 'A (developed): the arc and its rain shadow', ['massif N; a volcanic arc along the SW coast; the dry basin behind it;',
                                                                    'valley centre; the great river E to a delta; the city in a ria E of it'])
    d.polygon(jag([(ox, Y(0)), (ox + tw, Y(0)), (ox + tw, Y(40)), (ox + 330, Y(48)), (ox + 300, Y(95)), (ox + 260, Y(60)), (ox + 200, Y(90)),
                   (ox + 170, Y(55)), (ox + 120, Y(55)), (ox, Y(65))]), fill=C['mount'])
    d.polygon(jag([(ox, Y(0)), (ox + tw, Y(0)), (ox + tw, Y(18)), (ox, Y(24))], 4), fill=C['snow'])
    d.polygon(jag([(ox, Y(70)), (ox + 110, Y(62)), (ox + 160, Y(80)), (ox + 165, Y(205)), (ox, Y(215))]), fill=C['dry'])
    d.polygon(jag([(ox + 120, Y(75)), (ox + 170, Y(85)), (ox + 190, Y(200)), (ox + 150, Y(205))]), fill=C['steppe'])
    d.polygon(jag([(ox, Y(205)), (ox + 170, Y(200)), (ox + 150, Y(240)), (ox, Y(232))]), fill=C['volc'])
    d.line([(ox + 80, Y(212)), (ox + 70, Y(245))], fill=C['lava'], width=3); d.line([(ox + 90, Y(212)), (ox + 110, Y(246))], fill=C['lava'], width=3)
    d.polygon(jag([(ox + 380, Y(80)), (ox + tw, Y(70)), (ox + tw, Y(170)), (ox + 390, Y(160))]), fill=C['bog'])
    d.polygon(jag([(ox, Y(240)), (ox + 330, Y(222)), (ox + 345, Y(240)), (ox + 360, Y(220)), (ox + tw, Y(222)), (ox + tw, Y(th)), (ox, Y(th))]), fill=C['sea'])
    d.line([(ox + 300, Y(10)), (ox + 310, Y(80)), (ox + 300, Y(130)), (ox + 330, Y(170)), (ox + 320, Y(230))], fill=C['river'], width=5)
    d.line([(ox + 255, Y(60)), (ox + 305, Y(120))], fill=C['river'], width=2); d.line([(ox + 205, Y(60)), (ox + 215, Y(225))], fill=C['river'], width=2)
    d.rectangle([ox + 355, Y(205), ox + 380, Y(222)], fill=C['city'])
    for (x, y) in [(ox + 220, Y(250)), (ox + 140, Y(252)), (ox + 280, Y(258))]:
        d.ellipse([x, y, x + 18, y + 9], fill='#8DB05C')
    ox = 30 + tw; frame(ox, 'B: the river down the middle, desert beyond the massif', ['the great river splits the land down the centre;',
                                                                                      'the desert lies north of a broad pass; the volcano is an offshore hotspot isle'])
    d.polygon(jag([(ox, Y(0)), (ox + 170, Y(0)), (ox + 160, Y(60)), (ox, Y(80))]), fill=C['dry'])
    d.polygon(jag([(ox + 170, Y(0)), (ox + tw, Y(0)), (ox + tw, Y(60)), (ox + 200, Y(110)), (ox, Y(120)), (ox, Y(85)), (ox + 160, Y(60))]), fill=C['mount'])
    d.polygon(jag([(ox, Y(225)), (ox + tw, Y(215)), (ox + tw, Y(th)), (ox, Y(th))]), fill=C['sea'])
    d.line([(ox + 220, Y(110)), (ox + 200, Y(160)), (ox + 230, Y(220))], fill=C['river'], width=6); d.ellipse([ox + 330, Y(235), ox + 380, Y(262)], fill=C['volc'])
    d.rectangle([ox + 222, Y(205), ox + 248, Y(222)], fill=C['city'])
    ox = 50 + tw * 2; frame(ox, 'C: dry east behind a coastal range', ['massif N; the dry basin E behind its own coast range;',
                                                                       "the city W at a river mouth; the volcano at the range's E end"])
    d.polygon(jag([(ox, Y(0)), (ox + tw, Y(0)), (ox + tw, Y(50)), (ox, Y(45))]), fill=C['mount'])
    d.polygon(jag([(ox + 260, Y(55)), (ox + tw, Y(55)), (ox + tw, Y(190)), (ox + 270, Y(190))]), fill=C['dry'])
    d.polygon(jag([(ox + 240, Y(55)), (ox + 265, Y(55)), (ox + 270, Y(190)), (ox + 245, Y(190))]), fill=C['steppe'])
    d.polygon(jag([(ox + 240, Y(190)), (ox + tw, Y(185)), (ox + tw, Y(222)), (ox + 245, Y(228))]), fill=C['volc'])
    d.polygon(jag([(ox, Y(230)), (ox + tw, Y(222)), (ox + tw, Y(th)), (ox, Y(th))]), fill=C['sea'])
    d.line([(ox + 80, Y(40)), (ox + 100, Y(130)), (ox + 90, Y(230))], fill=C['river'], width=5)
    d.rectangle([ox + 75, Y(210), ox + 100, Y(228)], fill=C['city'])
    img.save(os.path.join(HERE, 'thumbnails.png'))


CROPS = {'region-valley-and-frostline': (5300, 1700, 7300, 5400), 'region-cogsworth-and-the-narrows': (7200, 1500, 9700, 3600),
         'region-sunstone-basin': (300, 900, 4700, 4000), 'region-fire-country': (1200, 3500, 4000, 6000),
         'region-isles': (3600, 5400, 9000, 6912), 'river-and-bridges': (8000, 1500, 10400, 5700), 'harbour-city': (9400, 4100, 11200, 5750),
         'route-drovers-road': (2600, 2200, 6000, 4300), 'route-ash-coast': (2500, 4000, 6000, 5900), 'route-canyon-road': (1600, 2300, 3200, 5300),
         'route-lull-road-coast-path-towpath': (6600, 2400, 9400, 5400), 'route-high-fells-col-path-foothill-road': (5800, 1500, 8300, 3600),
         'route-shell-bar-headland': (6300, 4900, 7500, 6300), 'route-cape-road': (10300, 4800, 11264, 5900)}


def main(only=None):
    global FRAME
    T = build(); routes(T); settle(T)
    K = T['K']
    FRAME = ndi.distance_transform_edt(~T['used']) * CELL > (FRAME_PX + 200 * noise(500, 70))
    FRAME &= ~((PX > 9500) & (PY > 4200) & (PY < 5500) & (PX < 11200))   # the city is walkable throughout
    gates = gate_check(K, T['crossings'])
    res, rl, wc = times(K)
    stats = {'world_px': [WPX, HPX], 'walkable_zone_areas': round(wc / 2880, 1), 'routes_s': rl, 'home_to': res, 'why_here': WHY,
             'bridges': BRIDGES, 'easter_egg_spots_later': EGGS, 'ways': WAY_NAMES}
    json.dump(stats, open(os.path.join(HERE, 'stats.json'), 'w'), indent=1)
    json.dump(gates, open(os.path.join(HERE, 'gates.json'), 'w'), indent=1)
    render(T, 'continent-1x.png', 1, annotate=False)
    if os.environ.get('QUICK'):
        return
    render(T, 'continent-labelled.png', 2)
    render(T, 'physical-map.png', 1, annotate=False, physical=True)
    Image.open(os.path.join(HERE, 'continent-1x.png')).resize((WPX // 32, HPX // 32), Image.BOX).save(os.path.join(HERE, 'overview-32px.png'))
    ingame_map(T); thumbnails()
    for name, c in CROPS.items():
        render(T, f'{name}.png', 4 if (c[2] - c[0]) <= 2600 else 2, crop=c, title=name.replace('-', ' '))
    print(json.dumps({k: v for k, v in stats.items() if k in ('walkable_zone_areas', 'routes_s')}, indent=1))
    for k_, v in res.items():
        print(f'{k_:22s} {v}')
    print(json.dumps({k_: v for k_, v in gates.items() if k_ != 'crossings'}, indent=0)[:4000])


if __name__ == '__main__':
    main()
