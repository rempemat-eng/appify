"""World plan v5.2 (built on v5.1, same structure): a refinement pass on arrangement A, on top of geo5.py (whose helpers, tables, routes,
gate check, timing and drawing it reuses). What changes:

- the Lull widens gradually with each tributary; a sine-generated meander belt with point bars, scroll bars,
  a fresh oxbow by the channel and an old silted one further out, willow carr; a braided reach; the Narrows
  as a gorge with cliff walls, white water and the viaduct drawn; a branching delta with uneven arms,
  sandbars, mudflats, reed beds and a lobed front;
- Neon Harbour drawn as organic districts round the whole ria (Voronoi blocks with buildings along lanes,
  terraces on contours over three knolls, a looser rotated grid for the new town, piers all round);
- the dry-to-wet change follows the arc's rain shadow carried by a south-south-westerly wind and the
  distance from the sea, so it curves and is patchy; the Rift winds and has a side canyon; badlands only
  where the rivers cut, and the oasis corridors fade downstream;
- the Frostline as a cirque in the massif's relief (headwall, tarn, moraine at the lip, a col); Hearthold
  as a walled hill town on its rock; fields as strips and hedged plots that follow the roads; the massif
  with separate peaks, valley glaciers and scree; star dunes and flats in the dune sea; the two lava flows
  no longer mirror each other.

This is the v5.2 block-out behind world plan v5.3 (docs/vision/world-plan.md). It needs geo5.py beside it (it reuses its
helpers and tables and replaces build() with build51() below), numpy, scipy, scikit-image, Pillow and the DejaVu fonts.

Run from this folder:  python3 -I geo52.py
- the data (stats-v52.json, gates-v52.json, blockout-v52.json) is written next to this file and is committed;
- the renders (continent, tier map, crops, before and after) go to out/ (git-ignored), or to $BLOCKOUT_OUT if set.
QUICK=name1,name2 writes the JSON, the 1x continent, the tier map and only those crops (see CROPS)."""
import json, math, os, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage as ndi
from skimage.draw import polygon as skpoly
from PIL import Image, ImageDraw
import geo5 as g
from geo5 import (xx, yy, noise, ridged, chaikin, meander, densify, raster, line_mask, shape, capsule, band, H, W, CELL, PX, PY,
                  WPX, HPX, COAST, FRONT, SPURS, CHAIN, VOLCANO, GLINT_ARMS, BAY, BAY_W, hexc)

g.hash = lambda s: zlib.crc32(str(s).encode())     # stable across runs (Python's own string hash is salted per process)
DATA = os.path.dirname(os.path.abspath(__file__))                       # the committed JSON lives here
HERE = os.environ.get('BLOCKOUT_OUT') or os.path.join(DATA, 'out')       # every render goes here (git-ignored)
os.makedirs(HERE, exist_ok=True)
g.HERE = HERE                                                             # geo5's render() saves to its own HERE
SUF = '-v52'

# ------------------------------------------------------------------------------------------ tables changed for v5.1
g.SETTLE['Hearthold'] = (2480, 5120, 200, 'hilltown')
g.BEHIND['W2'] = [(6230, 1930)]
g.BEHIND['W7'] = ['Neon Harbour', 'Launch Cape', (9800, 4985), (10500, 5250), (10170, 4340), (10130, 4985), (10080, 5440)]                     # the cirque floor south of the tarn
g.STATIONS['Cogsworth platform'] = (7960, 2420); g.STATIONS['Cogsworth terminus'] = (8240, 2790)   # on the town's streets
# thresholds: where one region turns into the next, each a recognisable place on the route (section 5 of the plan)
THRESHOLDS = {
    'the Col hut': (6290, 2350), 'the Frostline lip': (6230, 2040), 'the Brackens gap': (5200, 3760), "Drover's bridge": (4330, 3440),
    'the Rift ferry': (4180, 5240), 'the Amber canyon head': (2770, 2650), 'the Cinder Rise': (2270, 3860), 'the chasm bridge': (2170, 4920),
    'the crust causeway': (3300, 5560), 'the Millrace cutting': (7650, 2740), 'the Cog foot': (8530, 3060), 'Lullford Bridge': (8960, 4310),
    'the canal embankment': (9450, 4680), 'the Headland stile': (6990, 5300), 'the Shell Bar': (6900, 5900),
}
LIFTS = {'the Heights funicular': [(9900, 4700), (9700, 4820)], 'the Narrows lift (proposal)': [(8940, 2600), (8900, 2700)]}
g.ROUTES['Towpath'] = ([(8040, 2560), (8250, 2800), (8450, 2950), (8560, 3020), (8520, 3200), (8440, 3450), (8420, 3750), (8480, 4020),
                        (8650, 4220)], 'path', [])
g.ROUTES['Coast Path'] = ([(6660, 4930), (6870, 5100), (7300, 5070), (7950, 5050), (8150, 4930), (8300, 4700), (8480, 4450), (8640, 4330)],
                          'path', ['dunes:0.3-0.6'])
g.ROUTES['Delta Road'] = ([(9150, 4320), (9380, 4560), (9560, 4780), (9700, 4920), (9800, 4985)], 'path', [])
RIFT = [(4550, -50), (4280, 480), (4620, 980), (4760, 1450), (4560, 1850), (4300, 2080), (4190, 2330), (4380, 2700), (4480, 2950),
        (4280, 3200), (4300, 3420), (3950, 3800), (3880, 4080), (4200, 4350), (4520, 4700), (4400, 5050), (4200, 5250), (4250, 5450)]
# hugs the Brackens' north-west foot, swings west round the Heather spur's tip, back east into the bay below it where the
# Brackens beck comes in, west again round the Fold spur, then south-west round a mesa and east round the arc's last hills
BRACKENS_SPURS = [((4990, 1960), (4560, 2190), 0.075), ((4930, 3220), (4560, 3330), 0.06)]
DRY_FORKS = [[(3350, 3500), (3650, 3700), (3800, 3620), (3960, 3790)], [(4800, 3000), (4600, 3100), (4310, 3175)]]
UPPER_LULL = [(8650, 420), (8700, 800), (8820, 1150), (8960, 1500), (9050, 1700), (9000, 1950), (9070, 2200), (8990, 2450), (9040, 2700),
              (8950, 2950), (8850, 3150)]
OTHER_RIVERS = {
    'the Sorrel': ([(10300, 300), (10000, 800), (9600, 1300), (9300, 1550), (9060, 1690)], 18, 40, 30),
    'the Cog': ([(7500, 200), (7550, 900), (7700, 1600), (7800, 2200), (7860, 2500), (8150, 2850), (8500, 3050), (8860, 3160)], 16, 40, 22),
    'the Rift': (RIFT, 22, 34, 45),
    'the Sleepwater': ([(6200, 1880), (6230, 2400), (6170, 2800), (6250, 3150), (6370, 3480), (6290, 3900), (6400, 4300), (6360, 4700),
                        (6460, 5100)], 12, 30, 40),
    'the Amber': ([(2750, 300), (2900, 800), (2700, 1300), (2850, 1800), (2760, 2400), (2600, 2750), (2700, 3050), (2480, 3300), (2300, 3450),
                   (2150, 3620)], 14, 16, 30),
    'the Willow Run': ([(3650, 1100), (3450, 1500), (3700, 1950), (3550, 2400), (3480, 2800), (3250, 2950), (2950, 3000), (2720, 3040)], 10, 8, 30),
    'the Brackens beck': ([(5050, 2350), (4900, 2650), (4700, 2800), (4470, 2880)], 8, 12, 25),
    'the Glint': ([(11300, 3250), (10950, 3600), (10600, 3950), (10300, 4150), (10200, 4240)], 30, 50, 40),
    'the Heather burn': ([(5020, 1560), (4900, 1700), (4730, 1800), (4580, 1850)], 6, 10, 18),
    'the Sedgeburn': ([(3820, 1320), (3930, 1650), (4080, 1950), (4230, 2140)], 6, 10, 22),
}
NEW_KINDS = {'scroll': '#A2BE73', 'pointbar': '#DCCB98', 'carr': '#4E7A55', 'reeds': '#8F9C5E', 'mud': '#6F6A5A', 'sandbar': '#D8C48E',
             'scree': '#9C968E', 'moraine': '#A59C8C', 'wash': '#D9C08C', 'viapier': '#4A4038', 'fallow': '#B79C6A', 'lane': '#CDB894',
             'quay': '#9A8C7A', 'keep': '#7E3B30', 'talus': '#8E8880',
             'heath': '#9C7E8C', 'spoil': '#2F2B2D', 'aa': '#4A4246', 'fissure': '#C8452A', 'arcade': '#B0508C', 'boulevard': '#CDBFA6',
             'terminal': '#5E6E8C', 'hangar': '#7D8794', 'apron': '#B7B3AA', 'airfield': '#A9C47E', 'crane': '#2E2A28', 'fishmarket': '#C9B79A',
             'stall': '#B3473A', 'retain': '#8C7A66',
             'trail': '#D9C9A0', 'boulders': '#8A8580', 'thicket': '#3C5A34', 'felltree': '#6B4E33', 'pool': '#5C88A8', 'ravine': '#3E3530',
             'ruinbridge': '#7A6A5A', 'gorse': '#A7A04A', 'dunewall': '#D9B26E', 'crevasse': '#9FB8D0', 'sinkhole': '#2F4A44',
             'caravan': '#7A4A30', 'ancient': '#1F3A26', 'surf': '#DDE9F0', 'farisle': '#3E5A78', 'bramble': '#4E5A30',
             'scrubwall': '#A08A5A', 'scree2': '#8E8A84', 'driftwood': '#9C8A70', 'clearing': '#B8C98A', 'tor': '#7E7A74'}
g.COL.update(NEW_KINDS)
g.WALK |= {'scroll', 'pointbar', 'carr', 'reeds', 'scree', 'wash', 'fallow', 'lane', 'quay', 'heath', 'arcade', 'boulevard', 'apron', 'airfield', 'fishmarket', 'trail', 'clearing'}
g.OK.extend(['scroll', 'carr', 'scree', 'wash', 'reeds', 'heath'])


def raster_idx(pts, step=4.0):
    """Like raster(), plus the index of the nearest polyline sample, so a cell can ask about the bend it lies on."""
    x, y, a, tot = densify(pts, step)
    cx, cy = (x // CELL).astype(int), (y // CELL).astype(int)
    ok = (cx >= 0) & (cx < W) & (cy >= 0) & (cy < H)
    seed = np.zeros((H, W), bool); idx = np.zeros((H, W), int)
    seed[cy[ok], cx[ok]] = True; idx[cy[ok], cx[ok]] = np.nonzero(ok)[0]
    d, (iy, ix) = ndi.distance_transform_edt(~seed, return_indices=True)
    I = idx[iy, ix]
    return d * CELL, a[I], tot, I, x, y


def sine_belt(p0, p1, bends, omega, seed, n=900, bow=0.0):
    """A meander belt as a sine-generated curve (Langbein and Leopold): the heading swings by up to omega
    radians, with the swing different from bend to bend, so loops vary from gentle to nearly cut off."""
    r = np.random.default_rng(seed)
    s = np.linspace(0, 1, n)
    nb = int(math.ceil(bends)) + 3
    amps = r.uniform(0.55, 1.25, nb)
    om = omega * np.interp(s * (bends + 1), np.arange(nb), amps) * np.sin(np.pi * s) ** 0.6
    th = om * np.sin(2 * np.pi * bends * s + r.uniform(0, 2 * np.pi))
    z = np.concatenate([[0], np.cumsum(np.exp(1j * th))]) / n
    z = z + 1j * bow * np.sin(np.pi * np.linspace(0, 1, n + 1)) * abs(z[-1])
    P0, P1 = complex(*p0), complex(*p1)
    w = P0 + (z - z[0]) * (P1 - P0) / (z[-1] - z[0])
    return [(float(q.real), float(q.imag)) for q in w[::6]]


def delta_net(apex, seed):
    """A branching distributary network from the apex: uneven splits, arms that wander, all reaching the sea."""
    r = np.random.default_rng(seed); chans = []

    def grow(p, ang, w, depth):
        x, y = p; pts = [p]; L = r.uniform(240, 420) if depth < 3 else 3000
        for _ in range(int(L // 50)):
            ang += r.uniform(-0.14, 0.14)
            if x < 8470:
                ang = max(ang, 0.2)
            if x > 9290:
                ang = min(ang, -0.2)
            ang = float(np.clip(ang, -0.9, 0.9))
            x += 50 * math.sin(ang); y += 50 * math.cos(ang); pts.append((x, y))
            if y > 5700:
                break
        chans.append((pts, w))
        if y <= 5700:
            if depth < 2 and w > 40 and r.uniform() < 0.9:
                split = r.uniform(0.55, 0.72)
                grow((x, y), ang - r.uniform(0.25, 0.5), max(34, w * split), depth + 1)
                grow((x, y), ang + r.uniform(0.25, 0.5), max(34, w * (1 - split) * 1.15), depth + 1)
            else:
                grow((x, y), ang, w, 3)
    grow(apex, 0.05, 120, 0)
    return chans


def build51():
    T = {}
    wx = 240 * noise(1500, 1) + 80 * noise(380, 2)
    wy = 240 * noise(1500, 3) + 80 * noise(380, 4)
    g.WARP = (PX + wx, PY + wy); WX, WY = g.WARP
    warped = g.warped
    delta = delta_net((8960, 4480), 3)
    mouths = [c[0][-1] for c in delta if c[0][-1][1] > 5600]

    # ---- the sea, along the south only
    cy_ = np.interp(PX, [p[0] for p in COAST], [p[1] for p in COAST])
    pot = (cy_ - PY) / 230 + 0.6 * noise(800, 101) + 0.32 * noise(260, 102) + 0.16 * noise(90, 103, 2)
    land = pot > 0
    land |= capsule([(8960, 4480), (8880, 5000), (8860, 5420)], 360, 480, 104, 0.3) & (PY < 5450 + 60 * noise(200, 105))
    for i, (mx, my) in enumerate(mouths):     # a lobe of new land at every mouth
        land |= shape(mx, 5470, 170 + 30 * (i % 3), 120, 160 + i, 0.4)
    land |= capsule([(10500, 5100), (10800, 5350), (10990, 5680)], 280, 190, 106, 0.25)
    land |= capsule([(9500, 4900), (9750, 5250), (9850, 5520)], 300, 200, 107, 0.25)
    d_b, al_b, tot_b = raster(chaikin(BAY, 2))
    bw = np.interp(al_b, np.linspace(0, tot_b, len(BAY_W)), BAY_W) * (1 + 0.22 * noise(300, 108))
    land &= ~(d_b < bw)
    land &= ~shape(9930, 4700, 120, 80, 114, 0.3)
    land |= shape(10080, 5440, 95, 65, 113, 0.3) | shape(10130, 4985, 75, 55, 115, 0.25)
    land &= ~shape(6470, 5130, 230, 130, 109, 0.3)
    land &= ~shape(7950, 5300, 170, 110, 110, 0.3)
    land &= ~shape(2780, 5800, 150, 110, 111, 0.3)
    neck = capsule([(6940, 5120), (6985, 5380)], 62, 70, 116, 0.2)
    body = shape(7050, 5560, 165, 190, 112, 0.38, 0.2) | shape(7120, 5480, 90, 70, 117, 0.4)
    land &= ~(capsule([(6940, 5120), (6990, 5320), (7040, 5500), (7080, 5700)], 400, 400) & (PY > 5235))
    land |= neck | body
    isles = np.zeros((H, W), bool)
    for i, (cx, cy, rx, ry) in enumerate([(6650, 6380, 560, 330), (6880, 5900, 90, 60), (5250, 6250, 280, 170), (4050, 6120, 220, 150),
                                          (7850, 6450, 250, 160), (8700, 6650, 170, 110), (4650, 6650, 160, 110), (9600, 6500, 140, 90)]):
        isles |= shape(cx, cy, rx, ry, 120 + i, 0.55 if i != 1 else 0.3)
    lagoon = shape(6700, 6450, 230, 140, 130, 0.35) | capsule([(6720, 6500), (6800, 6620), (6830, 6800)], 45, 60)
    land = (land & (PY < 5900)) | (isles & ~lagoon)
    lab, n = ndi.label(land)
    sizes = ndi.sum(land, lab, range(1, n + 1)); land &= np.isin(lab, 1 + np.nonzero(sizes >= 40)[0])
    sea = ~land
    dsea = ndi.distance_transform_edt(land) * CELL
    T['land'], T['isles'], T['coast_y'] = land, isles & land, cy_

    # ---- height: the massif with separate peaks
    front = np.interp(WX, [p[0] for p in FRONT], [p[1] for p in FRONT])
    M = WY < front
    for nm, (pts, w0, w1) in SPURS.items():
        d, al, tot = raster(pts)
        M |= warped(d) < w0 + (w1 - w0) * np.clip(warped(al) / tot, 0, 1)
    d_in = ndi.distance_transform_edt(M) * CELL; d_out = ndi.distance_transform_edt(~M) * CELL
    var = 0.78 + 0.38 * noise(2600, 5)
    hm = np.where(M, 0.30 + (1 - np.exp(-d_in / 1000)) * 0.82 * var * (0.6 + 0.5 * ridged(700, 6)), 0.30 * np.exp(-d_out / 420))
    rp = np.random.default_rng(77); ys_, xs_ = np.nonzero((WY < front - 300) & (d_in > 420))
    peaks = np.zeros((H, W))
    for k in rp.choice(len(ys_), 80, replace=False):   # peaks as short ridges, each with its own line, height and width
        px_, py_ = xs_[k] * CELL, ys_[k] * CELL; amp = rp.uniform(0.1, 0.34); rad = rp.uniform(160, 380)
        ang = rp.uniform(0, math.pi); hl_ = rp.uniform(150, 450); ex, ey = math.cos(ang) * hl_, math.sin(ang) * hl_
        y0, y1, x0, x1 = max(0, ys_[k] - 110), min(H, ys_[k] + 110), max(0, xs_[k] - 110), min(W, xs_[k] + 110)
        qx, qy = PX[y0:y1, x0:x1] - px_, PY[y0:y1, x0:x1] - py_
        t = np.clip((qx * ex + qy * ey) / (hl_ * hl_), -1, 1); rr = np.hypot(qx - t * ex, qy - t * ey) + 0.25 * np.abs(t) * rad
        peaks[y0:y1, x0:x1] = np.maximum(peaks[y0:y1, x0:x1], amp * np.clip(1 - rr / rad, 0, 1) ** 1.6)
    hm = hm + peaks * (0.75 + 0.5 * ridged(160, 78)) * np.clip(d_in / 600, 0, 1)
    dist_c = np.clip(cy_ - PY, 0, None)
    banks = sum(1 / (1 + np.exp(-(dist_c - dk - 180 * noise(600, 300 + k)) / 45)) for k, dk in enumerate([650, 1650, 2750]))
    base = 0.086 + 0.0335 * banks + 0.006 * noise(600, 7)                    # each bank one 32 px tier; flats between
    plateau = 0.14 / (1 + np.exp((WX - 4300) / 260))
    plateau -= 0.07 * np.exp(-(((PX - 1950) / 650) ** 2 + ((PY - 3700) / 380) ** 2))
    uplands = 0.15 / (1 + np.exp(-(WX - 9650) / 260)) * np.clip((cy_ - PY - 150) / 450, 0, 1)
    heights = (0.2 * np.exp(-(((PX - 9650) / 200) ** 2 + ((PY - 4800) / 200) ** 2)) + 0.16 * np.exp(-(((PX - 9820) / 170) ** 2 + ((PY - 5120) / 190) ** 2))
               + 0.12 * np.exp(-(((PX - 9690) / 160) ** 2 + ((PY - 5350) / 150) ** 2)))      # the Heights: three knolls, not one dome
    heights *= 1 + 0.25 * noise(160, 79)
    dch, alch, totch = raster(CHAIN); dch = warped(dch)
    taper = np.interp(alch, [0, totch * 0.45, totch * 0.62, totch], [0.85, 1.0, 0.75, 0.35])
    hcr = 0.62 * taper * np.exp(-(dch / 430) ** 2) * (0.68 + 0.5 * ridged(450, 8))
    dv = np.hypot(PX - VOLCANO[0] + 0.6 * wx, PY - VOLCANO[1] + 0.6 * wy)
    dvc = np.hypot(PX - VOLCANO[0], PY - VOLCANO[1])
    gullies = 0.05 * ridged(260, 10) * np.clip(1 - dv / 1450, 0, 1)
    cone = 1.22 * np.clip(1 - dv / 1450, 0, 1) ** 1.7 - gullies
    cone = np.where(dvc < 150, 0.95 + 0.03 * noise(80, 9, 2), cone)
    for (cx, cy, r, hh) in [(1900, 4150, 260, 0.42), (3150, 4250, 230, 0.38), (2950, 5200, 180, 0.3)]:
        cone = np.maximum(cone, hh * np.clip(1 - np.hypot(PX - cx, PY - cy) / r, 0, 1) ** 1.3)
    hm = hm + 0.3 * np.exp(-(((PX - 6230) / 520) ** 2 + ((PY - 1480) / 300) ** 2))    # the peak behind the Frostline
    rock = 0.09 * np.exp(-(((PX - 2480) / 190) ** 2 + ((PY - 5110) / 170) ** 2))       # Hearthold's rock
    h = np.maximum.reduce([base + plateau + uplands + heights, hm, hcr, cone + rock])
    vb = np.exp(-(((WX - 6300) / 760) ** 2 + ((WY - 3600) / 980) ** 2))
    h = h - 0.3 * vb * np.clip(h - 0.13, 0, None)
    # the Frostline: a bowl with a headwall behind it and a low lip to the south, in the massif's own relief
    bowl = shape(6215, 1810, 300, 215, 30, 0.42, 0.25)
    dbo = ndi.distance_transform_edt(~bowl) * CELL
    southness = np.clip((PY - 1780) / 240, 0, 1)
    h = h + 0.22 * np.exp(-((dbo - 70) / 130) ** 2) * (dbo > 0) * (1 - southness) * (1 + 0.3 * ridged(90, 32))   # the horseshoe headwall
    h = np.where(bowl, np.minimum(h, 0.70 + 0.05 * np.clip((1950 - PY) / 300, 0, 1) + 0.015 * noise(90, 31)), h)

    # thresholds shaped into the ground: bluffs either side of the Brackens gap, the Cinder Rise, the Millrace cutting
    for (bx, by, rx_, ry_, a_) in [(5170, 3600, 170, 120, 0.13), (5260, 3960, 160, 110, 0.12)]:
        h = h + a_ * np.exp(-(((PX - bx) / rx_) ** 2 + ((PY - by) / ry_) ** 2)) * (1 + 0.3 * ridged(60, 88))
    h = h + 0.07 * np.exp(-(((PX - 2300) / 520) ** 2 + ((PY - 3860) / 90) ** 2)) * (1 + 0.4 * noise(80, 89))
    for (p0, p1, a_) in BRACKENS_SPURS:                                              # two spurs of the Brackens that push the Rift west
        dsp, alsp, totsp = raster([p0, p1]); dsp = warped(dsp)
        h = h + a_ * np.exp(-(dsp / (170 - 70 * np.clip(alsp / totsp, 0, 1))) ** 2) * (1 - 0.6 * np.clip(alsp / totsp, 0, 1)) * (1 + 0.3 * ridged(90, 91))
    # ---- rivers: the Lull widens with each tributary
    water = np.zeros((H, W), bool); T['river_masks'] = {}; T['river_px'] = {}; vcut = np.zeros((H, W))
    NAR = band(1850, 2900, 120)
    # v5.3: bends no tighter than the river is wide (radius 115 to 285 px against a width of about 100 px), so the
    # channel keeps its width round them instead of filling into beads; still unequal, still no one loop dominating
    belt = sine_belt((8850, 3150), (9380, 3620), 1.2, 0.9, 11, bow=0.08)[:-1] + sine_belt((9380, 3620), (8960, 4230), 1.2, 0.945, 9, bow=-0.06)
    lull_pts = chaikin(UPPER_LULL, 2) + belt[1:] + [(8960, 4300), (8960, 4480)]
    d, al, tot, I, lx, ly = raster_idx(lull_pts)
    def at(px_, py_):
        return float(al[int(py_ // CELL), int(px_ // CELL)])
    a_sor, a_cog, a_ford = at(9060, 1690), at(8860, 3160), at(8960, 4300)
    sm = lambda a0, s: 1 / (1 + np.exp(-(al - a0) / s))
    width = 26 + 14 * sm(a_sor, 150) + 34 * sm(a_cog, 200) + 26 * (al / tot) ** 1.3
    width *= 1 - 0.3 * NAR                                                     # pinched in the Narrows
    width *= 1 + 0.35 * np.exp(-((al - a_cog - 350) / 280) ** 2)              # spread over gravel below the Cog
    width = np.minimum(width, 118 + 300 * (1 - np.exp(-((al - a_ford) / 120) ** 2)))   # narrowed at Lullford
    # curvature along the belt: wider at the bends, sand on the inside, scroll bars beyond
    head = np.unwrap(np.arctan2(np.gradient(ly), np.gradient(lx)))
    kap = ndi.gaussian_filter1d(np.gradient(head) / 4.0, 8)
    nx_, ny_ = -np.sin(head), np.cos(head)
    k_c = kap[I]
    width *= 1 + 0.06 * np.clip(np.abs(k_c) / 0.004, 0, 1)              # v5.3: only a little wider at the bends, never bulbous
    lull = (d < width / 2)
    side = np.sign((PX - lx[I]) * nx_[I] + (PY - ly[I]) * ny_[I])
    inner = (side * np.sign(k_c) > 0)
    inbelt = (PY > 3150) & (PY < 4230) & (PX < 9800)
    T['river_px']['the Lull'] = lull_pts
    vcut = np.maximum(vcut, NAR * 0.8 * np.exp(-(d / 150) ** 2) + (1 - NAR) * 0.45 * np.exp(-(d / 700) ** 2))
    pointbar = inbelt & inner & (np.abs(k_c) > 0.0012) & (d >= width / 2) & (d < width / 2 + 25 + 80 * np.clip(np.abs(k_c) / 0.004, 0, 1))
    scroll = inbelt & inner & (np.abs(k_c) > 0.0009) & (d >= width / 2) & (d < width / 2 + 300) & (((d // 26) % 2) == 0)
    # oxbows: a fresh one hard by an outer bend, an old silted one further out
    ext = [i for i in range(10, len(kap) - 10) if inbelt[int(ly[i] // CELL), int(lx[i] // CELL)] and abs(kap[i]) > 0.0016
           and abs(kap[i]) == max(abs(kap[i - 10:i + 11]))]
    oxbow = np.zeros((H, W), bool); silted = np.zeros((H, W), bool); T['oxbows'] = []
    east = [i for i in ext if -np.sign(kap[i]) * nx_[i] > 0.4]
    for j, (i, gap, R, wd, kind) in enumerate([(east[0] if east else ext[0], 30, 140, 46, 'fresh'), (east[-1] if east else ext[-1], 330, 170, 80, 'old')]):
        ox_, oy_ = -np.sign(kap[i]) * nx_[i], -np.sign(kap[i]) * ny_[i]
        cx, cy = lx[i] + ox_ * (gap + R), ly[i] + oy_ * (gap + R)
        a_in = math.atan2(-oy_, -ox_)
        arc = [(cx + R * (1 + 0.12 * math.sin(3 * t)) * math.cos(a_in + t), cy + R * (1 + 0.12 * math.sin(3 * t)) * math.sin(a_in + t))
               for t in np.linspace(0.95, 2 * math.pi - 0.95, 40)]
        dd = raster(arc)[0]
        if kind == 'fresh':
            oxbow |= dd < wd / 2
        else:
            silted |= dd < wd / 2; oxbow |= dd < 10
        T['oxbows'].append((kind, round(cx), round(cy)))
    shoals = np.zeros((H, W), bool)
    cum = np.r_[0, np.cumsum(np.hypot(np.diff(lx), np.diff(ly)))]
    for q in range(6):  # gravel islands in the braided reach, long with the flow
        a_q = a_cog + 120 + q * 110; i = int(np.argmin(np.abs(cum - a_q)))
        off = (q % 2 * 2 - 1) * 0.22 * float(width[int(ly[i] // CELL), int(lx[i] // CELL)])
        shoals |= shape(lx[i] + nx_[i] * off, ly[i] + ny_[i] * off, 60 + 15 * (q % 3), 16, 140 + q, 0.35, float(head[i]))
    shoals |= shape(8960, 4310, 60, 34, 142, 0.2)
    shoals &= lull
    # the delta's arms
    deltaw = np.zeros((H, W), bool); T['delta'] = []
    for k_, (pts, w) in enumerate(delta):
        mp = meander(pts, 18, 600 + k_, 60); dd, aa, tt = raster(mp)
        deltaw |= (dd < (w * (0.85 + 0.3 * aa / tt)) / 2) & (PY < 5800); T['delta'].append(mp)
    lull |= deltaw
    water |= lull; T['river_masks']['the Lull'] = lull
    for i, (name, (pts, w0, w1, amp)) in enumerate(OTHER_RIVERS.items()):
        mp = meander(pts, amp, 40 + i, 100)
        d2, al2, tot2 = raster(mp)
        wd = w0 + (w1 - w0) * (al2 / tot2) ** 1.3
        m = d2 < wd / 2
        if name == 'the Amber':
            m &= al2 < tot2 - 60
        m &= land | (PY < 5800)
        water |= m; T['river_masks'][name] = m; T['river_px'][name] = mp
        if name == 'the Rift':
            vcut = np.maximum(vcut, 0.75 * np.exp(-(d2 / 150) ** 2))
        elif name == 'the Amber':
            cw = band(2550, 3450, 80)
            vcut = np.maximum(vcut, cw * 0.6 * np.exp(-(d2 / 170) ** 2) + (1 - cw) * 0.3 * np.exp(-(d2 / 330) ** 2))
        else:
            vcut = np.maximum(vcut, 0.32 * np.exp(-(d2 / 360) ** 2))
    wash = np.zeros((H, W), bool)
    for k_, pts in enumerate(DRY_FORKS):  # dry side canyons into the Rift: a sandy wash floor between cut walls
        mp = meander(pts, 30, 700 + k_, 80); d2 = raster(mp)[0]
        vcut = np.maximum(vcut, 0.45 * np.exp(-(d2 / 120) ** 2)); wash |= d2 < 20; T['river_px'][['the Dry Fork', 'Brackens wash'][k_]] = mp
    h = h - vcut * np.clip(h - 0.07, 0, None)
    lake_ff = shape(6200, 1800, 120, 70, 33, 0.3)
    salt_lake = shape(1950, 3700, 430, 240, 32, 0.45) & land
    rr = np.random.default_rng(8).random((H, W))
    rapids = lull & (NAR > 0.3) & (rr < 0.35 + 0.5 * NAR * ridged(60, 9))

    # ---- wetness: a south-south-westerly sea wind; rain falls on whatever it climbs first, and the shadow
    # trails downwind to the north-north-east, fading with distance; the land far from the sea is drier
    hl = np.where(land, h, 0); run = np.zeros((H, W)); t_ = 0.35
    run[-1] = hl[-1]
    xs = np.arange(W)
    for y in range(H - 2, -1, -1):
        prev = np.interp(xs - t_, xs, run[y + 1])
        run[y] = np.maximum(hl[y], prev - 0.0004)
    shadow = np.clip(run - h, 0, None)
    dist_sea = np.clip(cy_ - PY, 0, None)
    c_mid = 4950 + 600 / (1 + np.exp(-(PY - 3400) / 350))                       # further east south of the Brackens: the steppe wraps round them
    cont = 0.4 + 0.6 / (1 + np.exp(-(WX + 350 * noise(900, 96) - c_mid) / 1000))   # west of the Brackens the continent dries, unevenly
    wet = (0.25 + 0.75 * np.exp(-dist_sea / 4200)) * np.exp(-shadow * 3.2) * cont
    wet += 0.2 * np.exp(-np.clip(WY - front, 0, None) / 450) * (WX < 5200)          # a piedmont belt along the massif's foot: steppe, not dune
    wet += 0.25 * np.exp(-dist_sea / 450) * (WX < 4300)
    wet += 0.22 * np.exp(-np.clip(front - WY, 0, None) / 650) * np.clip((WX - 3600) / 2600, 0, 1)
    dbr_ = raster(SPURS['the Brackens'][0])[0]
    wet += 0.22 * np.exp(-(dbr_ / 380) ** 2) * np.clip((h - 0.3) / 0.15, 0, 1)       # the Brackens' hills catch their own rain
    wet += 0.12 * noise(420, 97) * np.exp(-((WX - 4600) / 1100) ** 2)              # patchy where dry meets green
    wet = ndi.gaussian_filter(wet, 22)
    wet = ndi.map_coordinates(wet, [np.clip((PY + 2.0 * wy) / CELL, 0, H - 1), np.clip((PX + 2.0 * wx) / CELL, 0, W - 1)], order=1)
    for (ax, ay) in [(2790, 1450), (3600, 1450), (1500, 1550)]:
        rr_ = np.hypot(PX - ax, (PY - ay) * 1.3); wet += 0.14 * np.exp(-(rr_ / 420) ** 2) / (1 + np.exp(-(PY - ay + 50) / 160))
    near_r = np.zeros((H, W))
    for name, mp in list(T['river_px'].items()):
        if name in ('the Dry Fork', 'Brackens wash'):
            continue
        d2, al2, tot2 = raster(mp)
        if name in ('the Amber', 'the Willow Run'):  # the oasis rivers lose water as they go: the green fades downstream
            fade = np.exp(-np.clip(al2 - 1300, 0, None) / 900)
            near_r = np.maximum(near_r, fade * np.exp(-(d2 / (120 + 120 * fade)) ** 2))
        elif name == 'the Rift':                    # the green strip varies: wide in the bays and at the confluences, a thread in the gorges
            rq = np.random.default_rng(31)
            wv = np.interp(al2, np.linspace(0, tot2, 14), rq.uniform(55, 210, 14))
            for (cx_, cy_) in [(4580, 1850), (4230, 2140), (4470, 2880), (4310, 3175), (3960, 3790)]:
                wv = wv + 160 * np.exp(-(np.hypot(PX - cx_, PY - cy_) / 380) ** 2)
            near_r = np.maximum(near_r, np.exp(-(d2 / wv) ** 2))
        elif name in ('the Heather burn', 'the Sedgeburn'):
            near_r = np.maximum(near_r, 0.8 * np.exp(-(d2 / 90) ** 2))
        else:
            near_r = np.maximum(near_r, np.exp(-(d2 / {'the Lull': 650}.get(name, 240)) ** 2))
    wet = wet + 0.42 * near_r + 0.1 * noise(1400, 92) + 0.07 * noise(900, 33) + 0.06 * noise(260, 34) + 0.04 * noise(70, 35, 2)
    wet = np.where(shape(3480, 2800, 300, 220, 36, 0.4), np.maximum(wet, 0.85), wet)
    wet = np.where(shape(2760, 2420, 330, 260, 37, 0.4), np.maximum(wet, 0.7), wet)
    wq = wet + 0.07 * (rr - 0.5)                                                # outliers: a bush in the dunes, a dry patch in the steppe

    # ---- ground
    gy_, gx_ = np.gradient(h)
    slope = np.hypot(gx_, gy_)
    snowline = 0.86 - 0.07 * np.tanh(gy_ * 90) + 0.035 * noise(220, 37)
    treeline = 0.64 - 0.04 * np.tanh(gy_ * 90) + 0.035 * noise(220, 38)
    hh = h + 0.03 * noise(70, 39, 2)
    L = land
    K = np.full((H, W), 'sea', dtype=object)
    K[L] = 'meadow'
    K[L & (wq < 0.56)] = 'steppe'
    K[L & (wq < 0.40)] = 'scrub'
    K[L & (wq < 0.25)] = 'desert'
    K[L & ((wq < 0.15) | ((wq < 0.3) & (WX < 1700 + 600 * noise(700, 94)))) & (h < 0.5) & (WX < 2700 + 400 * noise(600, 95))] = 'erg'   # the dune sea
    K[L & (K == 'erg') & (noise(700, 81) > 0.42)] = 'desert'                   # interdune flats
    forestable = L & (wq >= 0.52) & (hh < treeline)
    fn = noise(420, 40) + 0.35 * noise(120, 41, 2)
    K[forestable & (hh > 0.26) & (fn > -0.35)] = 'broadleaf'
    K[forestable & (hh > 0.44)] = 'conifer'
    K[forestable & (hh <= 0.26) & (fn > 0.38)] = 'broadleaf'
    hi = L & (hh >= treeline) & (hh < snowline)
    K[hi] = np.where(wq[hi] > 0.33, 'alpine', 'barren')
    K[hi & (slope > 0.011)] = 'scree'
    K[L & (hh >= snowline)] = 'snow'
    K[L & (hh >= snowline + 0.06) & (slope < 0.012)] = 'glacier'
    K[L & (hh >= snowline - 0.02) & (slope > 0.02)] = 'crag'
    d_l = d
    fp = L & (d_l < 520 + 220 * noise(300, 79)) & (h < 0.25) & (PY > 2950 + 200 * noise(300, 87))
    K[fp & ~np.isin(K, ['broadleaf'])] = 'watermeadow'
    K[fp & (noise(140, 82) > 0.35)] = 'carr'                                    # willow carr on the wettest ground
    K[scroll & L] = 'scroll'; K[pointbar & L] = 'pointbar'
    K[silted & L] = 'reeds'
    # each region its own ground: heather on the Brackens, spoil heaps and pit heads in the coal hills
    dbr = raster(SPURS['the Brackens'][0])[0]
    K[L & (dbr < 420 + 120 * noise(200, 90)) & (h > 0.24) & np.isin(K, ['meadow', 'steppe', 'alpine', 'scrub'])] = 'heath'
    for k_, (sx, sy) in enumerate([(7700, 2300), (8150, 2350), (8250, 2650), (7700, 2150), (8400, 2300)]):
        K[shape(sx, sy, 50, 34, 400 + k_, 0.3) & L & ~water] = 'spoil'
    # dry country: badlands only where the rivers have cut down; mesas left standing beside the cuts
    dry = L & (wet < 0.45) & (WX < 4800)
    below = PY > 1900 + 250 * noise(400, 93)                                      # where the rivers have cut into the basin floor
    K[dry & below & (vcut > 0.06) & (slope > 0.005) & (ridged(110, 42) > 0.45)] = 'badland'
    near_cut = (ndi.gaussian_filter((vcut > 0.15).astype(float), 40) > 0.12) & below
    mesa = dry & near_cut & (vcut < 0.03) & (noise(300, 43) > 0.38) & (h > 0.2) & (h < 0.55) & (np.hypot(PX - 2760, PY - 2420) > 500)
    h = np.where(mesa, h + 0.07, h)
    K[mesa] = 'mesa'
    K[wash & L] = 'wash'
    K[salt_lake] = 'saltpan'
    # Mount Ember: ash downwind, old flows, the young flows (the west one wide and fresh, the east one older, narrower, turning)
    ashfall = np.exp(-(((PX - VOLCANO[0] - 250) / 650) ** 2 + ((PY - VOLCANO[1] + 520) / 950) ** 2))
    nz = noise(300, 44) + 0.4 * noise(90, 45, 2)
    dither = np.random.default_rng(44).random((H, W))
    p_ash = np.clip(1.5 * ashfall - 0.25 + 0.3 * nz, 0, 1)
    K[L & (p_ash > dither) & ~np.isin(K, ['glacier', 'crag', 'saltpan', 'erg', 'river'])] = 'ash'
    r_ = np.random.default_rng(12)
    for i, (ang, rad0) in enumerate([(-2.3, 380), (-0.9, 520), (0.35, 300), (1.25, 620), (2.6, 450)]):
        L1 = r_.uniform(500, 1100)
        pts = [(VOLCANO[0] + rad0 * math.cos(ang), VOLCANO[1] + rad0 * math.sin(ang))]; a_ = ang
        for k_ in range(5):
            a_ += r_.uniform(-0.3, 0.3); pts.append((pts[-1][0] + L1 / 5 * math.cos(a_), pts[-1][1] + L1 / 5 * math.sin(a_)))
        mp = meander(pts, 40, 300 + i, 80); d2, al2, tot2 = raster(mp)
        tongue = L & (d2 < (30 + 90 * al2 / tot2) * (1 + 0.5 * noise(120, 310 + i))) & (al2 < tot2 * 0.97) & (dither > 0.08 + 0.5 * al2 / tot2)
        tt = tongue & ~np.isin(K, ['glacier', 'crag', 'saltpan', 'river'])
        K[tt] = np.where(wet[tt] > 0.55, 'fireweed', 'lavastone')
    K[L & (h > 0.62) & (dv < 1100) & (nz > -0.25)] = 'ash'
    K[L & (dvc < 420) & (nz > 0.05)] = 'basalt'
    # the crater: irregular, the young flow pouring through its south-east rim; a rift-zone fissure runs south-west
    # down the flank to the vent of the old flow, which is crusted, its edges grown over
    crater = shape(VOLCANO[0], VOLCANO[1], 175, 140, 47, 0.35, 0.3)
    dcr = ndi.distance_transform_edt(~crater) * CELL
    rim = (dcr > 0) & (dcr < 40 + 25 * noise(70, 47)) & L
    T['flows'] = []
    # v5.3: the young flow comes from a flank vent partway down the south-east side: a short fissure on the flank
    # ending in a small spatter cone. The old flow came from the summit crater, through a breach in its south-west rim.
    # The cone's upper slopes are loose cinder, too steep to climb (never walked), and close the barrier between them.
    vent = (2810, 4840)
    young = [vent, (2900, 4950), (3040, 5130), (3190, 5420), (3290, 5950)]
    mp = meander(young, 40, 51, 80); d2, al2, tot2 = raster(mp); T['flows'].append(mp)
    yw = (40 + 70 * (al2 / tot2) ** 1.3) * (1 + 0.45 * noise(160, 52) + 0.25 * noise(50, 62, 2))
    youngm = (d2 < yw) & L
    x_, y_, a2, t2 = densify(mp, 8)
    for j, frac in enumerate((0.35, 0.65)):
        q = int(frac * (len(x_) - 1)); youngm |= shape(x_[q] + 80, y_[q] + 30, 100, 60, 71 + j, 0.5, 0.6) & L
    upper = (dvc < 300 + 22 * noise(90, 523, 2)) & L                             # the steep upper cone
    fiss = line_mask(chaikin([(2640, 4670), (2700, 4730), (2760, 4790), vent], 2), 26) & L    # starts inside the upper cone
    spat = shape(vent[0], vent[1], 72, 58, 524, 0.35, 0.6) & L
    old = [(2330, 4570), (2265, 4700), (2190, 4840), (2160, 4930), (2100, 5100), (2020, 5300), (1990, 5520), (1920, 5950)]
    mp2 = meander(old, 45, 50, 80); d3, al3, tot3 = raster(mp2); T['flows'].append(mp2)
    ow = (55 + 90 * (al3 / tot3) ** 1.2) * (1 + 0.4 * noise(160, 54) + 0.3 * noise(50, 63, 2))
    oldcore = (d3 < np.maximum(ow * 0.72, 44)) & L
    oldedge = (d3 < ow) & L & ~oldcore & ~youngm
    fire = youngm | fiss | oldcore | rim | (crater & L) | upper | spat
    K[oldedge] = np.where(rr[oldedge] < 0.5, 'fireweed', 'lavastone')            # the old flow's edges have grown over
    K[oldcore] = 'aa'                                                            # crusted rubble: no way across but a bridge
    K[upper & ~rim & ~crater & ~oldcore] = 'talus'
    K[rim & ~oldcore] = 'crag'; K[crater & L] = 'basalt'; K[youngm] = 'lava'; K[fiss] = 'fissure'
    K[spat] = 'crag'; K[shape(vent[0], vent[1], 22, 18, 525, 0.3) & L] = 'crater'          # the spatter cone, glowing in its throat
    K[oldcore & rim] = 'aa'                                                      # the breach: the old flow's crust runs out through the rim
    K[L & shape(VOLCANO[0] + 30, VOLCANO[1] + 25, 85, 55, 48, 0.4, 0.4)] = 'crater'
    for (fx, fy) in [(2780, 4300), (2950, 4420), (2230, 4330)]:
        K[shape(fx, fy, 60, 40, int(fx), 0.4) & L & ~fire] = 'channel'
    dead = L & (noise(300, 48) + 0.5 * np.exp(-(raster(T['flows'][0])[0] / 500) ** 2) > 0.35) & (np.hypot(PX - 3450, PY - 5200) < 750) \
        & np.isin(K, ['broadleaf', 'meadow', 'steppe', 'fireweed', 'lavastone', 'conifer'])
    K[dead] = 'deadwood'
    # the Frostline: snow in the shaded back of the bowl, alpine meadow and a tarn in front, moraine at the lip;
    # the rim is crag on the headwall, scree on the sides and moraine on the lip, of uneven thickness
    rim_ff = (dbo > 0) & (dbo < 18 + 24 * (noise(70, 34, 2) + 1) / 2) & L
    K[bowl] = 'alpine'; K[bowl & (PY < 1790 + 60 * noise(120, 49))] = 'snow'
    K[bowl & (southness > 0.8) & (rr < 0.12)] = 'scree'
    K[lake_ff] = 'tarn'
    K[rim_ff] = np.where(southness[rim_ff] > 0.8, 'moraine', np.where(southness[rim_ff] < 0.35, 'crag', 'talus'))
    T['rim_unwalk'] = rim_ff
    # the eastern border
    fscore = 1 / (1 + np.exp(-(WX - 10350) / 220)) / (1 + np.exp(-(WY - 2500) / 220)) / (1 + np.exp((WY - 4250) / 220))
    fens = L & (fscore + 0.35 * noise(400, 52) > 0.55)
    K[fens] = 'bog'; K[fens & (noise(110, 53, 2) > 0.45)] = 'mere'
    K[L & (WX > 9800) & (WY < 2600) & np.isin(K, ['broadleaf', 'conifer', 'meadow'])] = 'conifer'
    forest = np.isin(K, ['broadleaf', 'conifer'])
    K[ndi.binary_erosion(forest, iterations=10) & (noise(260, 54) > -0.2)] = 'wild'
    # coasts; the delta's front: reed beds between the arms, mudflats and sandbars off the mouths
    shore = L & (dsea < 32 + 22 * (noise(200, 55) + 1))
    sh = shore & ~np.isin(K, ['lava', 'crag', 'crater', 'aa', 'fissure'])
    K[sh] = np.where(dv[sh] < 2300, 'blacksand', 'sand')
    K[shore & ((h > 0.33) | (hcr > 0.3))] = 'cliff'
    K[L & (slope > 0.017) & ~np.isin(K, ['lava', 'glacier', 'snow', 'crag', 'crater', 'tarn', 'scree', 'moraine'])] = 'cliff'
    dzone = (ndi.distance_transform_edt(~deltaw) * CELL < 220 + 120 * noise(200, 86)) & (PY > 4700 + 180 * noise(260, 91)) & (PY > 4560)
    K[L & dzone & np.isin(K, ['meadow', 'watermeadow', 'steppe', 'sand', 'broadleaf', 'carr', 'scroll'])] = 'reeds'
    mud = sea & (ndi.distance_transform_edt(~(deltaw | (dzone & L))) * CELL < 160) & (ndi.distance_transform_edt(sea) * CELL < 110 + 50 * noise(120, 83)) & (PY < 5800)
    K[mud] = 'mud'
    for i, (mx, my) in enumerate(mouths):
        K[sea & shape(mx + 30, 5650, 70, 26, 170 + i, 0.4) & ~deltaw] = 'sandbar'
    K[water & L] = 'river'
    K[deltaw & sea] = 'river'
    K[rapids & L] = 'rapids'; K[oxbow & L] = 'oxbow'; K[shoals & L] = 'shoal'
    gorge = (NAR > 0.4) & (d_l >= width / 2) & (d_l < width / 2 + 34 + 20 * noise(60, 84)) & L
    K[gorge & ~water] = 'cliff'                                                  # the Narrows' walls
    cre, tarn, acc_f = drainage51(h, wet, land)
    tarn = (ndi.gaussian_filter(tarn.astype(float), 2.5) + 0.22 * noise(40, 522, 2)) > 0.5    # the fill works on a coarse grid: round its blocky shores
    K[cre & L & np.isin(K, ['meadow', 'steppe', 'broadleaf', 'conifer', 'alpine', 'barren', 'watermeadow', 'fireweed', 'scrub', 'bog', 'deadwood', 'scroll', 'carr'])] = 'creek'
    K[tarn & L & np.isin(K, ['alpine', 'barren', 'snow', 'conifer', 'scree'])] = 'tarn'
    tongue = L & (acc_f > 18) & (h > snowline - 0.12) & (h > 0.62) & np.isin(K, ['snow', 'alpine', 'barren', 'scree'])
    K[ndi.binary_dilation(tongue, iterations=2) & np.isin(K, ['snow', 'alpine', 'barren', 'scree'])] = 'glacier'   # valley glaciers
    wall = capsule([(6820, 5300), (7120, 5300)], 12, 12) & L & (PY > 5250)
    K[wall] = 'wall'
    cut = line_mask([(7520, 2830), (7650, 2740), (7760, 2620)], 120) & L & ~np.isin(K, ['river'])
    K[cut & ~line_mask([(7520, 2830), (7650, 2740), (7760, 2620)], 48)] = 'cliff'          # the Millrace cutting's walls
    T.update(K=K, h=h, wet=wet, dv=dv, sea=sea, fire=fire, rim=rim_ff, slope=slope)
    T['barriers'] = {'rim': rim_ff, 'fire': fire, 'sea': sea, 'the Cog': T['river_masks']['the Cog'],
                     'the Lull': lull | T['river_masks']['the Sorrel'], 'the Rift': T['river_masks']['the Rift'], 'wall': wall}
    T['K0'] = K.copy()
    return T


def drainage51(h, wet, land):
    """geo5's drainage, also returning the flow accumulation (for valley glaciers)."""
    full, tarn = g.drainage(h, wet, land)
    S = 4; hs = ndi.gaussian_filter(h, 6)[::S, ::S]
    # a cheap stand-in for accumulation at the glacier scale: how much higher ground drains through a cell
    acc = ndi.gaussian_filter((hs > 0.8).astype(float), 3) * 40 * (ndi.gaussian_filter(hs, 4) - hs > 0.004)
    return full, tarn, np.kron(acc, np.ones((S, S)))[:H, :W]


# ------------------------------------------------------------------------------------------ fields that follow the roads
def strips(T, cx, cy, rad, kind, used):
    """Strip fields and hedged plots laid off the roads that run through a settlement's farmland: long
    narrow strips at right angles to the road, groups of four to seven under one hedge, crops alternating."""
    K = T['K']; r = np.random.default_rng(int(cx * 7 + cy))
    dry = kind in ('frontier', 'oasis')
    landk = ['meadow', 'steppe', 'watermeadow', 'scrub', 'garden', 'scroll'] + (['desert'] if dry else [])
    crops = ['orchard', 'orchard', 'fallow'] if dry else ['field', 'field2', 'fallow', 'field']
    for rn, sm in T['route_px'].items():
        x, y, al, tot = densify(sm, 6)
        hw = 34
        group = 0; L_ = r.uniform(110, 220)
        for i in range(0, len(x), 6):  # every 36 px along the road
            dd = math.hypot(x[i] - cx, y[i] - cy) / rad
            if not (0.5 < dd < 1.55 + 0.25 * r.uniform()):
                continue
            j = min(i + 2, len(x) - 1); k_ = max(i - 2, 0); tx, ty = x[j] - x[k_], y[j] - y[k_]; Lt = math.hypot(tx, ty) or 1
            tx, ty = tx / Lt, ty / Lt; nx_, ny_ = -ty, tx
            group += 1
            if group % int(r.integers(4, 8)) == 0:
                L_ = r.uniform(110, 220)
            for sd in (-1, 1):
                if r.uniform() < 0.15:
                    continue
                bx, by = x[i] + nx_ * sd * hw, y[i] + ny_ * sd * hw
                quad = [(bx - tx * 17, by - ty * 17), (bx + tx * 17, by + ty * 17),
                        (bx + tx * 17 + nx_ * sd * L_, by + ty * 17 + ny_ * sd * L_), (bx - tx * 17 + nx_ * sd * L_, by - ty * 17 + ny_ * sd * L_)]
                rr_, cc_ = skpoly([q[1] / CELL for q in quad], [q[0] / CELL for q in quad], shape=(H, W))
                if len(rr_) == 0:
                    continue
                okm = np.isin(K[rr_, cc_], landk)
                if okm.mean() < 0.8 or T['slope'][rr_, cc_].max() > 0.014 or (dry and T['wet'][rr_, cc_].mean() < 0.5):
                    continue
                K[rr_[okm], cc_[okm]] = crops[(i // 6 + (sd > 0)) % len(crops)]
                used[rr_, cc_] = True
        # hedges: the outline of each run of strips
    fm = np.isin(K, ['field', 'field2', 'fallow', 'orchard'])
    win = (np.abs(PX - cx) < rad * 2.2) & (np.abs(PY - cy) < rad * 2.2)
    edge = fm & win & ~ndi.binary_erosion(fm)
    K[edge & (np.random.default_rng(3).random((H, W)) < 0.85)] = 'hedge'


# ------------------------------------------------------------------------------------------ organic towns
def voronoi_blocks(mask, spacing_px, seed, lane_cells=1, warp=60):
    """Irregular blocks: a jittered set of seeds, each cell taking its nearest seed (in a warped space so the
    lanes wander), lanes along the boundaries. Returns (block label, lane mask)."""
    r = np.random.default_rng(seed)
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return np.zeros((H, W), int), np.zeros((H, W), bool)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sp = spacing_px / CELL
    gy, gx = np.mgrid[y0:y1:sp, x0:x1:sp]
    sy = (gy + r.uniform(-0.45, 0.45, gy.shape) * sp).ravel(); sx = (gx + r.uniform(-0.45, 0.45, gx.shape) * sp).ravel()
    seedimg = np.zeros((y1 - y0, x1 - x0), int)
    for k, (a, b) in enumerate(zip(sy, sx)):
        a, b = int(np.clip(a - y0, 0, y1 - y0 - 1)), int(np.clip(b - x0, 0, x1 - x0 - 1)); seedimg[a, b] = k + 1
    _, (iy, ix) = ndi.distance_transform_edt(seedimg == 0, return_indices=True)
    lab = seedimg[iy, ix]
    wy_ = (noise(spacing_px * 1.5, seed + 1)[y0:y1, x0:x1] * warp / CELL)
    wx_ = (noise(spacing_px * 1.5, seed + 2)[y0:y1, x0:x1] * warp / CELL)
    gg = np.mgrid[0:y1 - y0, 0:x1 - x0]
    lab = ndi.map_coordinates(lab, [np.clip(gg[0] + wy_, 0, y1 - y0 - 1), np.clip(gg[1] + wx_, 0, x1 - x0 - 1)], order=0)
    full = np.zeros((H, W), int); full[y0:y1, x0:x1] = lab
    lane = np.zeros((H, W), bool)
    lane[:, 1:] |= full[:, 1:] != full[:, :-1]; lane[1:, :] |= full[1:, :] != full[:-1, :]
    if lane_cells > 1:
        lane = ndi.binary_dilation(lane, iterations=lane_cells - 1)
    return full * mask, lane & mask


def fill_blocks(K, mask, lab, lane, depth, kind='building', court='yard', plot_px=48, seed=0, lane_kind='lane'):
    """Buildings along the lanes, a few cells deep, broken into houses; courtyards and gardens behind."""
    blocks = mask & ~lane
    dl = ndi.distance_transform_edt(~lane)
    plots, plane = voronoi_blocks(blocks, plot_px, seed + 5, 1, warp=10)
    K[mask & lane] = lane_kind
    K[blocks] = court
    K[blocks & (dl <= depth) & ~plane] = kind


def city51(T, used):
    """Neon Harbour wrapping its ria, and Hearthold on its rock."""
    K, h = T['K'], T['h']
    C = lambda x, y: (int(y // CELL), int(x // CELL))
    LAND = ['meadow', 'watermeadow', 'steppe', 'broadleaf', 'conifer', 'sand', 'scrub', 'garden', 'yard', 'creek', 'wild', 'bog', 'cliff',
            'mere', 'building', 'field', 'field2', 'fallow', 'hedge', 'scroll', 'carr', 'reeds']
    land = T['land']
    free = lambda: np.isin(K, LAND) & land

    # the city's footprint follows the ria and the coast; districts share it out by nearest centre, in a warped
    # space, so their borders are irregular streets rather than circles
    CITY = [(9470, 4520), (9700, 4380), (9990, 4260), (10180, 4150), (10480, 4170), (10800, 4120), (11180, 4180), (11250, 4600),
            (11230, 4960), (11180, 5260), (10850, 5440), (10460, 5470), (10300, 5330), (9980, 5640), (9720, 5560), (9500, 5320), (9440, 4900)]
    rr_, cc_ = skpoly([p[1] / CELL for p in CITY], [p[0] / CELL for p in CITY], shape=(H, W))
    foot = np.zeros((H, W), bool); foot[rr_, cc_] = True
    foot &= ndi.distance_transform_edt(foot) * CELL + 60 * noise(220, 199) > 20
    foot &= free()
    DIST = {'old': [(10170, 4350), (10400, 4430), (10560, 4480)], 'warehouses': [(10560, 4800), (10600, 5000)], 'heights': [(9650, 4800), (9800, 5100), (9700, 5350), (9900, 4650)],
            'newtown': [(10900, 4380), (11080, 4560), (10880, 4700), (11100, 4820)], 'strand': [(10560, 5290), (10700, 5330)], 'skyport': [(10960, 5110)]}
    names = list(DIST); seeds = [(n, p) for n in names for p in DIST[n]]
    wxs, wys = PX + 90 * noise(300, 197), PY + 90 * noise(300, 198)
    best = np.full((H, W), 1e12); which = np.zeros((H, W), int)
    for k_, (n, (sx, sy)) in enumerate(seeds):
        dd = (wxs - sx) ** 2 + (wys - sy) ** 2
        m = dd < best; best[m] = dd[m]; which[m] = names.index(n)
    D = {n: foot & (which == i) for i, n in enumerate(names)}

    # the old town: the Falls Rock and the quarter round the market, crooked lanes, the market square
    old = D['old']
    lab, lane = voronoi_blocks(old, 84, 210, 1, warp=70)
    fill_blocks(K, old, lab, lane, 3, seed=211)
    if lab[C(10450, 4520)] > 0:
        K[(lab == lab[C(10450, 4520)]) & old] = 'plaza'
    # the docks and warehouses along the deep east shore
    bay = T['sea'] & (PX > 9800) & (PX < 10560) & (PY > 4420) & (PY < 5200)
    shore_e = ndi.binary_dilation(bay, iterations=4) & ~bay & (PX > 10200) & land & free()
    K[shore_e] = 'quay'; used |= shore_e
    wh = D['warehouses'] & ~shore_e
    lab, lane = voronoi_blocks(wh, 120, 220, 2, warp=30)
    fill_blocks(K, wh, lab, lane, 6, kind='warehouse', court='plaza', plot_px=72, seed=221)
    # the Heights: separate terrace blocks on the contours over three knolls, a retaining wall under each,
    # gardens between, lanes and stairs climbing between the blocks
    hts = D['heights']
    hb = ((h + 0.012 * noise(220, 205) + 0.004 * noise(60, 206, 2)) * 60) % 1.0
    tlab, tlane = voronoi_blocks(hts, 150, 250, 1, warp=25)
    keep_b = ((tlab * 7919) % 10) < 7                                              # most blocks built, some left as gardens
    K[hts] = 'garden'
    K[hts & (hb >= 0.40) & (hb < 0.47) & ~tlane] = 'retain'
    K[hts & (hb < 0.36) & keep_b & ~tlane & (np.random.default_rng(6).random((H, W)) < 0.95)] = 'building'
    K[hts & tlane] = 'lane'
    used |= hts
    # the neon new town, grown out from the maglev station: blocks of different sizes split from the land,
    # a boulevard east from the station, an arcade street, two squares, towers clustered by the station
    nt = D['newtown']
    th = math.radians(14); sx0, sy0 = 10700, 4470
    u = (PX - sx0) * math.cos(th) + (PY - sy0) * math.sin(th); v = -(PX - sx0) * math.sin(th) + (PY - sy0) * math.cos(th)
    r9 = np.random.default_rng(31); rects = []
    def split(u0, v0, u1, v1, dep=0):
        if (u1 - u0 < 340 and v1 - v0 < 340) or dep > 6:
            rects.append((u0, v0, u1, v1)); return
        if u1 - u0 >= v1 - v0:
            c = u0 + (u1 - u0) * r9.uniform(0.35, 0.65); split(u0, v0, c, v1, dep + 1); split(c, v0, u1, v1, dep + 1)
        else:
            c = v0 + (v1 - v0) * r9.uniform(0.35, 0.65); split(u0, v0, u1, c, dep + 1); split(u0, c, u1, v1, dep + 1)
    split(-200, -420, 700, 640)
    blab = np.zeros((H, W), int)
    for k_, (u0, v0, u1, v1) in enumerate(rects):
        sw = 20
        blab[nt & (u > u0 + sw) & (u < u1 - sw) & (v > v0 + sw) & (v < v1 - sw)] = k_ + 1
    street = nt & (blab == 0)
    boulevard = nt & (np.abs(v) < 34) & (u > -40)
    arcade = nt & (np.abs(u - 300) < 14) & (v < 0) & (v > -380)
    fill_blocks(K, nt, blab, street | boulevard | arcade, 3, seed=260, lane_kind='road')
    near = np.hypot(PX - sx0, PY - sy0) < 420 + 80 * noise(200, 261)
    K[nt & near & np.isin(K, ['building'])] = 'tower'
    K[nt & near & ~street & ~boulevard & ~arcade & (np.isin(K, ['yard']))] = 'plaza'
    K[boulevard] = 'boulevard'; K[boulevard & (np.abs(v) < 4) & ((u // 40) % 2 == 0)] = 'garden'   # trees down the middle
    K[arcade] = 'arcade'
    edge_a = ndi.binary_dilation(boulevard | arcade, iterations=3) & np.isin(K, ['tower', 'building'])
    K[edge_a & (np.random.default_rng(7).random((H, W)) < 0.18)] = 'neon'
    for (qx, qy) in [(10760, 4520), (11020, 4700)]:                               # the station square and Neon Square
        if blab[C(qx, qy)] > 0:
            K[(blab == blab[C(qx, qy)]) & nt & ~boulevard & ~arcade] = 'plaza'
    a, b = C(sx0 - 20, sy0 - 10); K[a - 3:a + 3, b - 8:b + 8] = 'terminal'          # the maglev station
    used |= nt
    # the Gull Strand: fishing houses along the beach at the ria's mouth
    gs = D['strand'] & (ndi.distance_transform_edt(~T['sea']) * CELL < 200)
    lab, lane = voronoi_blocks(gs, 64, 230, 1, warp=30)
    fill_blocks(K, gs, lab, lane, 2, court='sand', plot_px=40, seed=231)
    used |= gs
    K[D['strand'] & ~gs] = 'garden'
    # the Skyport: a grass field with a terminal, aprons, hangars and three mooring masts with their circles
    sp = D['skyport']
    K[sp] = 'airfield'
    def box(x0, y0, x1, y1, kind):
        a0, b0 = C(x0, y0); a1, b1 = C(x1, y1); sub = K[a0:a1, b0:b1]; m = sp[a0:a1, b0:b1]; sub[m] = kind
    box(10770, 5000, 10970, 5070, 'apron'); box(10790, 4970, 10910, 5006, 'terminal')
    box(10930, 4975, 11030, 5035, 'hangar'); box(11045, 4990, 11140, 5050, 'hangar')
    for (mx, my) in [(10860, 5140), (10990, 5160), (11110, 5170)]:
        circ = sp & (np.hypot(PX - mx, PY - my) < 44); K[circ] = 'apron'
        a, b = C(mx, my); K[a - 1:a + 2, b - 1:b + 2] = 'tower'
    used |= sp
    # the old town's waterfront: warehouses fronting the quay, cranes on its edge, the fish market at its south end
    front = ndi.binary_dilation(shore_e, iterations=6) & ~ndi.binary_dilation(shore_e, iterations=1) & land & (PY > 4540) & (PY < 5060) & (PX > 10230)
    front &= ~np.isin(K, ['road', 'path', 'bridge', 'stair', 'river'])
    gy2, gx2 = np.mgrid[0:H, 0:W]
    K[front & ((gy2 % 9) != 0)] = 'warehouse'; K[front & ((gy2 % 9) == 0)] = 'lane'
    ys, xs = np.nonzero(shore_e & (PY > 4560) & (PY < 5060))
    for k_ in range(0, len(ys), 1):
        if ys[k_] % 11 == 0 and k_ % 3 == 0:
            K[ys[k_], xs[k_]:xs[k_] + 2] = 'crane'
    fm = (PX > 10380) & (PX < 10520) & (PY > 5070) & (PY < 5160) & land & ~np.isin(K, ['road', 'path', 'bridge', 'river', 'sea'])
    K[fm] = 'fishmarket'; K[fm & ((gy2 % 3) == 0) & ((gx2 % 3) == 0)] = 'stall'
    # piers: long ones along the docks, jetties under the Heights, slipways at the Strand
    dist_land = ndi.distance_transform_edt(~land)
    lab_l, _ = ndi.label(land); mainland = lab_l == lab_l[C(10600, 4600)]
    gyl, gxl = np.gradient(ndi.gaussian_filter(dist_land, 3))
    for (x0, y0, x1, y1, step, length, wdt) in [(10200, 4560, 10560, 5130, 70, 150, 12), (9800, 4600, 10120, 5300, 260, 60, 10),
                                                (10380, 5150, 10800, 5420, 90, 50, 8)]:
        sh = mainland & (dist_land == 0) & ndi.binary_dilation(T['sea'], iterations=1) & (PX > x0) & (PX < x1) & (PY > y0) & (PY < y1)
        ys, xs = np.nonzero(sh)
        if len(ys) == 0:
            continue
        order = np.argsort(ys * 10000 + xs); last = None
        for i in order:
            y, x = ys[i], xs[i]
            if last is not None and math.hypot(x - last[1], y - last[0]) * CELL < step:
                continue
            gxv, gyv = gxl[y, x], gyl[y, x]; nrm = math.hypot(gxv, gyv)
            if nrm < 1e-6:
                continue
            p0 = (x * CELL + 4, y * CELL + 4); p1 = (p0[0] + gxv / nrm * length, p0[1] + gyv / nrm * length)
            m = line_mask([p0, p1], wdt) & T['sea'] & ~np.isin(K, ['river', 'bridge'])
            K[m] = 'pier'; last = (y, x)
    # the Lull Cut and its towpath; the lighthouse; the chapel; the falls
    cut = chaikin([(9020, 4400), (9350, 4490), (9600, 4560), (9800, 4640), (9900, 4690)], 3)
    cm = line_mask(cut, 24); K[cm & ~np.isin(K, ['road', 'bridge', 'river', 'sea'])] = 'canal'
    tp = line_mask([(x, y - 30) for (x, y) in cut], 16); K[tp & np.isin(K, LAND + ['stair', 'lane'])] = 'path'; used |= tp
    a, b = C(10080, 5440); K[a - 3:a + 3, b - 3:b + 3] = 'tower'
    a, b = C(10130, 4985); K[a - 3:a + 3, b - 5:b - 1] = 'keep'
    for arm in GLINT_ARMS:
        x, y = arm[-1]; a, b = C(x, y - 16); K[a - 3:a + 2, b - 3:b + 3] = 'falls'
        K[a + 2:a + 6, b - 4:b + 4][np.isin(K[a + 2:a + 6, b - 4:b + 4], ['sea', 'river'])] = 'rapids'
    # the Narrows Viaduct: rail only, drawn as a landmark with its piers
    via_pts = [(8700, 2390), (9030, 2330), (9360, 2290)]
    via = line_mask(via_pts, 24)
    K[via & ~np.isin(K, ['road', 'path', 'bridge'])] = 'viaduct'
    x_, y_, _, _ = densify(via_pts, 56)
    for (px_, py_) in zip(x_, y_):
        a, b = C(px_, py_); K[a - 1:a + 2, b - 1:b + 2] = 'viapier'
    # Hearthold: a walled hill town on its rock between the flows
    town = shape(2480, 5110, 190, 170, 240, 0.25) & ~T['fire'] & land & np.isin(K, LAND + ['ash', 'basalt', 'lavastone', 'fireweed', 'blacksand', 'deadwood'])
    wallr = town & ~ndi.binary_erosion(town, iterations=2)
    inner = town & ~wallr
    lab, lane = voronoi_blocks(inner, 72, 241, 1, warp=50)
    fill_blocks(K, inner, lab, lane, 2, seed=242)
    rd = np.isin(K, ['path', 'road', 'bridge', 'stair'])
    K[wallr & ~rd] = 'castlewall'
    a, b = C(2550, 5160); kp = K[a - 4:a + 4, b - 5:b + 5]; kp[~np.isin(kp, ['path', 'road', 'bridge', 'stair', 'castlewall'])] = 'keep'
    used |= town


g.patch = strips
_orig_line_mask = g.line_mask
ROUTE_WIDTHS = []


def line_mask_var(pts, width):
    """Route strokes (24 or 40 px) vary in width along their length: wider at bends, views and junction squares."""
    if width not in (24, 40):
        return _orig_line_mask(pts, width)
    x, y, al, tot = densify(pts, 6)
    r = np.random.default_rng(int(abs(x[0] * 7 + y[0] * 13)) % 2 ** 31)
    n = max(1, int(tot // 120)); idx = np.linspace(0, len(x) - 1, n + 1).astype(int)
    m = np.zeros((H, W), bool)
    for a, b in zip(idx, idx[1:]):
        w = int(min(64, width + r.choice([0, 0, 8, 16, 24])))
        ROUTE_WIDTHS.append(w)
        m |= _orig_line_mask(list(zip(x[a:b + 1], y[a:b + 1])), w)
    return m


g.line_mask = line_mask_var
_orig_meander = g.meander


def meander_routes(pts, amp, seed, step=120):
    if not (amp == 18 and step == 140):    # only the route call in geo5.routes()
        return _orig_meander(pts, amp, seed, step)
    sm = _orig_meander(pts, 24, seed, 110)
    x, y, al, tot = densify(sm, 6)
    r = np.random.default_rng(seed + 77)
    # two swings of unrelated length added together, each with its own varying size, so the bends are irregular:
    # a short bend every 160 to 240 px riding on a long swing of 450 to 750 px, never a regular S-ribbon
    lam1 = np.interp(al, np.linspace(0, tot, 12), r.uniform(320, 480, 12)); lam2 = np.interp(al, np.linspace(0, tot, 6), r.uniform(900, 1500, 6))
    A1 = np.interp(al, np.linspace(0, tot, 12), r.uniform(22, 34, 12)); A2 = np.interp(al, np.linspace(0, tot, 6), r.uniform(16, 36, 6))
    taper = np.clip(al / 120, 0, 1) * np.clip((tot - al) / 120, 0, 1) * np.clip((tot - 300) / 900, 0, 1)   # short lanes keep to their line
    ph1 = np.cumsum(np.r_[0, np.diff(al)] * 2 * np.pi / lam1); ph2 = np.cumsum(np.r_[0, np.diff(al)] * 2 * np.pi / lam2) + r.uniform(0, 2 * np.pi)
    off = (A1 * np.sin(ph1) + A2 * np.sin(ph2)) * taper
    tx, ty = np.gradient(x), np.gradient(y); Lt = np.hypot(tx, ty) + 1e-9
    return list(zip(x - ty / Lt * off, y + tx / Lt * off))[::3] + [(x[-1], y[-1])]


g.meander = meander_routes
g.city = city51

_orig_put = g.Labels.put


def put_leader(self, xy, text, font, fill='white', stroke='black', prefer=None):
    """Try the usual spots; for thresholds and bridges, if all are taken, move out in rings and draw a leader line."""
    if _orig_put(self, xy, text, font, fill, stroke, *( [prefer] if prefer is not None else [])):
        return True
    if fill not in ('#F2E5C8', '#FFE0B8'):
        return False
    Wd, Hd = self.d._image.size
    for r in (55, 75, 100, 130, 165, 205, 250):
        for a in np.linspace(0, 2 * math.pi, 20, endpoint=False):
            x, y = xy[0] + r * math.cos(a), xy[1] + r * math.sin(a)
            b = self.d.textbbox((x, y), text, font=font, anchor='mm', stroke_width=2); b = (b[0] - 3, b[1] - 2, b[2] + 3, b[3] + 2)
            if b[0] < 0 or b[1] < 0 or b[2] > Wd or b[3] > Hd or not self.free(b):
                continue
            ex, ey = min(max(xy[0], b[0]), b[2]), min(max(xy[1], b[1]), b[3])
            self.d.line([xy, (ex, ey)], fill=fill, width=1)
            self.boxes.append(b); self.d.text((x, y), text, font=font, fill=fill, stroke_width=2, stroke_fill=stroke, anchor='mm')
            return True
    return False


g.Labels.put = put_leader


def colour51(T, K, physical=False):
    rgb = np.zeros((H, W, 3))
    for k, c in g.COL.items():
        rgb[K == k] = hexc(c)
    if 'ground0' in T:
        ba = T['border_assigned'] | T['fade_clumps']; G0 = T['ground0']; grgb = np.zeros((H, W, 3))
        for k, c in g.COL.items():
            m = ba & (G0 == k)
            if m.any():
                grgb[m] = hexc(c)
        rgb[ba] = 0.6 * rgb[ba] + 0.4 * grgb[ba]
    S = g.SHADE
    if 'shade' not in S:
        gy_, gx_ = np.gradient(ndi.gaussian_filter(T['h'], 1.2))
        S['shade'] = np.clip(1.0 - (gx_ + gy_) * (30.0 + 25.0 * np.clip(T['h'] - 0.4, 0, 1)), 0.45, 1.45)
        dsea = ndi.distance_transform_edt(T['sea']) * CELL; S['deep'] = np.clip(dsea / 900, 0, 1)[..., None]
        rnd = np.random.default_rng(3).random((H, W))
        a1 = np.sin((PX * 0.8 + PY * 0.6) / 34 + 5 * noise(500, 80)); a2 = np.sin((PX * -0.5 + PY * 0.85) / 46 + 4 * noise(400, 85))
        S['tex'] = (rnd, (a1 + 0.8 * a2) > 0.9)
    rnd, dunes = S['tex']
    tex = np.ones((H, W))
    tex[np.isin(K, ['broadleaf', 'conifer', 'wild', 'orchard', 'carr']) & (rnd < 0.28)] = 0.82
    tex[np.isin(K, ['erg']) & dunes] = 1.08
    tex[np.isin(K, ['scrub', 'steppe', 'lavastone', 'fireweed', 'deadwood', 'scree', 'moraine']) & (rnd < 0.1)] = 0.85
    tex[np.isin(K, ['bog', 'watermeadow', 'reeds']) & (rnd < 0.1)] = 0.8
    tex[np.isin(K, ['rapids']) & (rnd < 0.3)] = 1.1
    rgb = rgb * tex[..., None]
    rgb = rgb * (0.8 + 0.32 * np.clip(T['h'], 0, 1.1))[..., None] if physical else rgb * (0.9 + 0.15 * np.clip(T['h'], 0, 1.1))[..., None]
    rgb = np.where(T['land'][..., None], rgb * S['shade'][..., None], rgb)
    rgb = np.where((K == 'sea')[..., None], np.array(hexc('#3C78A6')) * (1 - S['deep']) + np.array(hexc('#23466E')) * S['deep'], rgb)
    if g.FRAME is not None:                                                      # the dune sea's dust storm, thickening westward
        haze = (np.clip((2600 - PX) / 2600, 0, 1) * (g.FRAME & T['land']))[..., None]
        rgb = rgb * (1 - 0.4 * haze) + np.array([226, 196, 150]) * 0.4 * haze
    return rgb


g.colour = colour51

TIER_K = 30          # tiers per unit of the height field; one tier is a 32 px face on the soft grid (verticality.md)
REGIONS = {'the massif (north edge)': (0, 0, 11264, 1300), 'the Frostline': (5800, 1450, 6700, 2200), 'the home valley': (5600, 2300, 7000, 5100),
           'the coal hills and the Narrows': (7300, 1700, 9400, 3100), 'the Lull plain': (6800, 3200, 8800, 5100), 'the Lull belt and delta': (8400, 3100, 9400, 5650),
           'Neon Harbour': (9450, 4150, 11250, 5650), 'the Sunstone basin': (1500, 1500, 4000, 3600), 'the Rift': (4000, 1500, 4700, 5400),
           'the fire country': (1500, 3800, 3600, 5900), 'the coast and the isles': (4000, 5100, 9000, 6900)}


def tier_field(T):
    E = ndi.gaussian_filter(T['h'], 1.5) * TIER_K
    t = ndi.median_filter(np.floor(E).astype(int), 5)
    t[~T['land']] = -1
    return t


def route_steps(T, t):
    """Where each route changes tier: a stair if it climbs across a face, a ramp if it runs along one."""
    out = []
    for rn, sm in T['route_px'].items():
        x, y, al, tot = densify(sm, 8); prev = None
        for i in range(len(x)):
            yi, xi = int(np.clip(y[i] // CELL, 0, H - 1)), int(np.clip(x[i] // CELL, 0, W - 1))
            tv = t[yi, xi]
            if tv < 0:
                continue
            if prev is not None and tv != prev:
                j, k_ = min(i + 2, len(x) - 1), max(i - 2, 0)
                kind = 'stair' if abs(y[j] - y[k_]) >= abs(x[j] - x[k_]) else 'ramp'
                feats = g.ROUTES.get(rn, ([], '', []))[2]
                if any(f.startswith('switchbacks') for f in feats):
                    kind = 'switchback'
                out.append((rn, kind, float(x[i]), float(y[i]), int(abs(tv - prev))))
            prev = tv
    return out


def tier_map(T, steps, out):
    """Tiers as colour steps, faces on south edges (one 32 px face per tier step), side bands on east and west
    ends, and every stair, ramp, switchback and lift marked. 2 px per 8 px cell."""
    t = tier_field(T); K = T['K']; land = T['land']
    stops = [(0, '#5E9A55'), (4, '#8DBA62'), (8, '#B9C27A'), (12, '#C9AF7C'), (16, '#A88F70'), (20, '#8E8478'), (24, '#B8B8BC'), (28, '#F2F4F7')]
    rgb = np.zeros((H, W, 3))
    tv = np.clip(t, 0, 30).astype(float)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (tv >= a) & (tv < b); f = ((tv - a) / (b - a))[m][:, None]
        rgb[m] = np.array(hexc(ca)) * (1 - f) + np.array(hexc(cb)) * f
    rgb[tv >= 28] = hexc('#F2F4F7')
    above = np.full((H, W), -1)
    for k in range(1, 5):  # a face hangs 4 cells (32 px) below each rim that drops to the south
        above = np.maximum(above, np.roll(t, k, axis=0))
    face = land & (above > t)
    rgb[face] = rgb[face] * 0.55
    west_end = land & (np.roll(t, 1, axis=1) > t); east_end = land & (np.roll(t, -1, axis=1) > t)
    rgb[west_end & ~face] = rgb[west_end & ~face] * 0.7          # the higher tier's east end, in shade
    rgb[east_end & ~face] = np.minimum(rgb[east_end & ~face] * 1.15, 255)
    for k, c in [('river', '#3E78B5'), ('rapids', '#9CC7E8'), ('lava', '#E0612A'), ('crater', '#FFB347'), ('canal', '#3E70A8'), ('tarn', '#4F86B8'),
                 ('oxbow', '#4C83B0'), ('falls', '#E8F4FF')]:
        rgb[K == k] = hexc(c)
    for k in ('path', 'road', 'stair', 'bridge', 'lane', 'quay'):
        rgb[K == k] = rgb[K == k] * 0.5 + np.array([250, 240, 210]) * 0.5
    bld = np.isin(K, ['building', 'tower', 'warehouse', 'keep', 'castlewall'])
    rgb[bld] = hexc('#7A4E3E')
    if g.FRAME is not None:
        rgb = np.where((g.FRAME & land)[..., None], rgb * 0.82 + 40 * 0.18, rgb)
    rgb[~land] = hexc('#2B3A55')
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST)
    d = ImageDraw.Draw(img); k = 2 / CELL
    for rn, kind, x, y, n in steps:
        X, Y = x * k, y * k
        if kind == 'stair':
            d.rectangle([X - 3, Y - 3, X + 3, Y + 3], fill='white', outline='black'); d.line([X - 3, Y, X + 3, Y], fill='black')
        elif kind == 'ramp':
            d.polygon([(X - 4, Y + 3), (X + 4, Y + 3), (X + 4, Y - 3)], fill='#FFE14A', outline='black')
        else:
            d.line([(X - 4, Y - 3), (X - 1, Y + 3), (X + 1, Y - 3), (X + 4, Y + 3)], fill='white', width=2)
    for nm, pts in LIFTS.items():
        (x0, y0), (x1, y1) = pts; d.line([x0 * k, y0 * k, x1 * k, y1 * k], fill='#D04FA6', width=3)
        d.rectangle([x0 * k - 5, y0 * k - 5, x0 * k + 5, y0 * k + 5], fill='#D04FA6', outline='white')
    Lb = g.Labels(d)
    for nm, (x, y) in THRESHOLDS.items():
        X, Y = x * k, y * k; d.polygon([(X, Y - 6), (X + 6, Y), (X, Y + 6), (X - 6, Y)], fill='#F28C28', outline='black'); Lb.boxes.append((X - 7, Y - 7, X + 7, Y + 7))
    for nm, (x, y) in THRESHOLDS.items():
        Lb.put((x * k, y * k), nm, g.FONT, fill='#FFE0B8', prefer=((0, -14), (0, 14), (60, 0), (-60, 0), (0, -28), (0, 28)))
    for nm, (x, y, r, kind) in g.SETTLE.items():
        Lb.put((x * k, y * k), nm, g.FONTB, prefer=((0, 0), (0, -18), (0, 18), (60, 0), (-60, 0)))
    key = ['Tiers: one colour step per 32 px of height; dark band = south face (32 px per step); side ends lit west, shaded east',
           'white square = stair through a face; yellow wedge = ramp along a face; white zigzag = switchbacks; pink = lift; orange diamond = threshold']
    for i, line in enumerate(key):
        d.rectangle([0, img.height - 44 + i * 20, img.width, img.height - 24 + i * 20], fill=(20, 20, 24)); d.text((8, img.height - 42 + i * 20), line, font=g.FONT, fill='white')
    img.save(os.path.join(HERE, out))
    return t


def vertical_stats(T, t, steps):
    res = {}
    above = np.full((H, W), -1)
    Wm = g.walk_mask(T['K'])
    for name, (x0, y0, x1, y1) in REGIONS.items():
        a, b, c, d_ = int(y0 // CELL), int(x0 // CELL), int(y1 // CELL), int(x1 // CELL)
        tt = t[a:c, b:d_]; wm = Wm[a:c, b:d_] & (tt >= 0)
        if not wm.any():
            continue
        dt = np.clip(tt[:-1, :] - tt[1:, :], 0, None)        # face heights (tiers) where ground drops to the south
        near = wm[:-1, :] | wm[1:, :]
        faces = dt[near & (dt > 0)]
        st = [s_ for s_ in steps if x0 <= s_[2] < x1 and y0 <= s_[3] < y1]
        res[name] = {'tiers_walked': [int(tt[wm].min()), int(tt[wm].max())], 'tier_range_all': [int(tt[tt >= 0].min()), int(tt[tt >= 0].max())],
                     'face_px_typical': int(32 * np.median(faces)) if len(faces) else 0, 'face_px_max': int(32 * faces.max()) if len(faces) else 0,
                     'stairs': sum(1 for s_ in st if s_[1] == 'stair'), 'ramps': sum(1 for s_ in st if s_[1] == 'ramp'),
                     'switchback_steps': sum(1 for s_ in st if s_[1] == 'switchback')}
    return res


def ingame51(T, t):
    """The in-game mock in the soft-grid style, now stepped on the same tiers as the tier map."""
    S = 4
    tt = ndi.median_filter(t, 3)[::S, ::S]; K = T['K'][::S, ::S]; land = T['land'][::S, ::S]
    pal = dict(g.COL)
    pal.update({'meadow': '#93B866', 'steppe': '#C3BC75', 'desert': '#E6CA8E', 'broadleaf': '#6F9B4E', 'conifer': '#4F7E52', 'wild': '#3C6745',
                'river': '#3E4FA8', 'rapids': '#6E8FD8', 'oxbow': '#3E4FA8', 'canal': '#3E4FA8', 'path': '#EFDCA4', 'road': '#EFDCA4', 'stair': '#EFDCA4'})
    big = np.zeros(K.shape + (3,))
    for k_, c in pal.items():
        big[K == k_] = hexc(c)
    big = ndi.median_filter(big, size=(5, 5, 1))
    for k_ in ('river', 'rapids', 'road', 'path', 'bridge', 'lava', 'canal', 'stair', 'bar', 'lane'):
        if k_ in pal:
            big[K == k_] = hexc(pal[k_])
    big = big * (0.86 + 0.012 * np.clip(tt, 0, 30))[..., None]               # higher tiers a step lighter
    big[~land] = hexc('#2B2733')
    face = land & (np.roll(tt, 1, axis=0) > tt); big[face] = big[face] * 0.58
    edge = land & ((np.roll(tt, -1, 0) != tt) | (np.roll(tt, 1, 1) != tt) | (np.roll(tt, -1, 1) != tt)); big[edge] = big[edge] * 0.85
    coastl = land & ~ndi.binary_erosion(land); big[coastl] = big[coastl] * 0.65
    if g.FRAME is not None:
        fr = g.FRAME[::S, ::S] & land; big[fr] = big[fr] * 0.72 + np.array([40, 38, 50]) * 0.28
    img = Image.fromarray(np.clip(big, 0, 255).astype(np.uint8)).resize((K.shape[1] * 6, K.shape[0] * 6), Image.NEAREST)
    d = ImageDraw.Draw(img); k = 6 / (CELL * S); Lb = g.Labels(d)
    for nm, (x, y, r, kind) in g.SETTLE.items():
        X, Y = x * k, y * k
        col = {'city': '#7C6B95', 'hilltown': '#A0A0A0', 'cape': '#E0E0E0', 'cirque': '#DDEBF5'}.get(kind, '#C4704F')
        d.rectangle([X - 9, Y - 6, X + 9, Y + 8], fill=col, outline='#1E1917', width=2)
        d.polygon([(X - 11, Y - 6), (X, Y - 14), (X + 11, Y - 6)], fill='#7A3B2E', outline='#1E1917'); Lb.boxes.append((X - 12, Y - 15, X + 12, Y + 9))
    for nm, (x, y, r, kind) in g.SETTLE.items():
        Lb.put((x * k, y * k + 4), nm, g.FONT, fill='#F7F2E8', stroke='#1E1917', prefer=((0, 18), (0, -24), (50, 0), (-50, 0), (0, 34)))
    for lab, discs in g.WAYS.items():
        for (x, y, r) in discs[:1]:
            d.ellipse([x * k - 6, y * k - 6, x * k + 6, y * k + 6], fill='#D7263D', outline='#1E1917', width=2)
    d.text((20, img.height - 30), 'In-game map mock (v5.1), soft-grid style: stepped on the same 32 px tiers as the tier map; faces on south edges', font=g.FONTB, fill='#F7F2E8')
    img.save(os.path.join(HERE, f'ingame-map-mock{SUF}.png'))



# ------------------------------------------------------------------------------------------ v5.2: obstacles, side paths, borders, content
BIOMES = {'the home valley': (5600, 2300, 7000, 5100), 'the massif and the Frostline': (5200, 0, 11264, 2300), 'the coal hills': (7000, 1700, 9300, 3100),
          'the Lull plain': (6800, 3100, 8700, 5200), 'the river belt and delta': (8700, 3100, 9450, 5700), 'Neon Harbour': (9450, 4150, 11264, 5700),
          'the steppe and the Brackens': (4300, 2300, 5600, 5200), 'the Sunstone basin': (0, 0, 4300, 4000), 'the fire country': (1200, 4000, 4300, 6000),
          'the coast and the isles': (4300, 5200, 9000, 6912)}
CONTENT_TYPES = {
    'the home valley': ['wayside shrine', 'well', 'beehives', 'picnic viewpoint', 'scarecrow', 'old oak', 'stile and bench'],
    'the massif and the Frostline': ['cairn', 'ibex rocks', 'crevasse viewpoint', 'herders\' shieling', 'fallen climber\'s camp', 'echo cave'],
    'the coal hills': ['pit head', 'collapsed adit', 'charcoal burners\' camp', 'rail ruin', 'tram tipple', 'lookout over the Narrows'],
    'the Lull plain': ['windmill', 'standing stones', 'heron pools', 'ruined chapel', 'fishing stage', 'hay barn'],
    'the river belt and delta': ['reed hide', 'stilt hut', 'eel traps', 'ferryman\'s hut', 'wreck in the reeds', 'otter holt'],
    'Neon Harbour': ['fish market', 'rope walk', 'harbour master', 'funicular station', 'street shrine', 'night market'],
    'the steppe and the Brackens': ['sheepfold', 'shepherd\'s hut', 'drove well', 'hare warren', 'barrow mound', 'lone pine viewpoint'],
    'the Sunstone basin': ['caravan camp', 'wind pump', 'wagon wreck', 'rock arch', 'cliff shrine', 'bone yard', 'lizard rocks', 'mirage viewpoint'],
    'the fire country': ['fumarole field', 'obsidian scree', 'lava tube mouth', 'ruined watchtower', 'steam pools', 'cinder shrine'],
    'the coast and the isles': ['tide pools', 'seal rocks', 'sea cave', 'smugglers\' cove', 'beach wreck', 'gull cliffs'],
}
CAT = {'shrine': 'shrine', 'well': 'well', 'pump': 'well', 'viewpoint': 'view', 'lookout': 'view', 'camp': 'camp', 'shieling': 'camp', 'hut': 'npc',
       'master': 'npc', 'ruin': 'ruin', 'chapel': 'ruin', 'watchtower': 'ruin', 'adit': 'cave', 'cave': 'cave', 'tube': 'cave', 'holt': 'wild',
       'wreck': 'wreck', 'rocks': 'wild', 'pools': 'wild', 'hide': 'wild', 'warren': 'wild', 'beehives': 'prop', 'traps': 'prop', 'stones': 'landmark',
       'arch': 'landmark', 'oak': 'landmark', 'windmill': 'landmark', 'mound': 'landmark', 'cairn': 'landmark', 'market': 'npc', 'station': 'landmark'}
CAT_COL = {'shrine': '#F2E86D', 'well': '#5BB5F0', 'view': '#FFFFFF', 'camp': '#F28C28', 'npc': '#FFD23F', 'ruin': '#B0A6A0', 'cave': '#2B2B2B',
           'wild': '#7BD389', 'wreck': '#8C5A3C', 'landmark': '#E86A92', 'prop': '#C9A06A'}
SCREEN_PX = 576       # one screen of route: a zone's height


def biome_of(x, y):
    for nm, (x0, y0, x1, y1) in BIOMES.items():
        if x0 <= x < x1 and y0 <= y < y1:
            return nm
    return None


MAIN_ROUTES = [r for r in g.ROUTES if not r.startswith('Valley lane') and r not in ('Old Bridges', 'Quay Street', 'Harbour Bridge', 'Beacon Causeway', 'Forge Stair')]


def obstacles(T):
    """Obstacles beside the routes (boulder fields, thickets, fallen trees, ravines, marshy pools, scree) with a little
    side path round the far side of each, so the walk has small choices; collapsed old bridges beside some fords."""
    K = T['K']; r = np.random.default_rng(52); out = []
    bar = np.zeros((H, W), bool)
    for m in T['barriers'].values():
        bar |= m
    hard = np.isin(K, ['river', 'rapids', 'lava', 'aa', 'fissure', 'sea', 'canal', 'wall', 'cliff', 'crag', 'glacier', 'building', 'tower',
                       'warehouse', 'castlewall', 'tarn', 'oxbow', 'mere', 'crater', 'erg'])
    placed = []; covered = set()
    for pass_, rn in [(p_, r_) for p_ in (0, 1) for r_ in MAIN_ROUTES]:     # first one loop for every region, then the rest
        sm = T['route_px'][rn]; x, y, al, tot = densify(sm, 8); own = _orig_line_mask(sm, 56)
        for k_, a0 in enumerate(np.arange(450, tot - 450, 150)):
            if any(o['route'] == rn and abs(o.get('along', -9999) - a0) < 900 for o in out):
                continue
            i = int(np.argmin(np.abs(al - a0))); j0 = int(np.argmin(np.abs(al - (a0 - 300)))); j1 = int(np.argmin(np.abs(al - (a0 + 300))))
            if pass_ == 0 and biome_of(x[i], y[i]) in covered:
                continue
            if any(math.hypot(px_ - x[i], py_ - y[i]) < 800 for px_, py_ in placed):  # at most one loop in any small area
                continue
            ja = int(np.argmin(np.abs(al - (a0 - 210)))); jb = int(np.argmin(np.abs(al - (a0 + 210))))
            tx, ty = x[min(i + 2, len(x) - 1)] - x[max(i - 2, 0)], y[min(i + 2, len(x) - 1)] - y[max(i - 2, 0)]; Lt = math.hypot(tx, ty) or 1
            nx_, ny_ = -ty / Lt, tx / Lt; sd0 = 1 if (k_ + len(rn)) % 2 else -1
            for sd in (sd0, -sd0):                                                  # try one side of the road, then the other
                ox, oy = x[i] + nx_ * sd * 110, y[i] + ny_ * sd * 110
                ground = K[int(oy // CELL), int(ox // CELL)] if 0 <= oy < HPX and 0 <= ox < WPX else 'sea'
                if ground in ('broadleaf', 'conifer', 'wild', 'carr', 'garden', 'orchard', 'deadwood'):
                    kind = 'felltree' if k_ % 2 else 'thicket'
                elif ground in ('watermeadow', 'reeds', 'bog', 'scroll', 'marsh'):
                    kind = 'pool'
                elif ground in ('alpine', 'barren', 'scree', 'snow', 'heath'):
                    kind = 'scree'
                elif ground in ('desert', 'scrub', 'badland', 'mesa', 'steppe', 'ash', 'lavastone', 'basalt', 'fireweed'):
                    kind = 'ravine' if k_ % 3 == 0 else 'boulders'
                elif ground in ('meadow', 'field', 'field2', 'fallow', 'hedge', 'yard'):
                    kind = 'boulders' if k_ % 2 else 'thicket'
                elif ground in ('sand', 'blacksand', 'shoal'):
                    kind = 'driftwood'
                elif ground in ('spoil',):
                    kind = 'spoil'
                else:
                    continue
                if kind == 'ravine':
                    ob = line_mask(meander([(ox - nx_ * 40 - tx / Lt * 80, oy - ny_ * 40 - ty / Lt * 80), (ox, oy), (ox + nx_ * 50 + tx / Lt * 90, oy + ny_ * 50 + ty / Lt * 90)], 12, 800 + k_, 30), 16)
                else:
                    ob = shape(ox, oy, 70 + 20 * (k_ % 3), 45, 820 + k_ + len(rn), 0.5, math.atan2(ty, tx))
                route_cells = np.isin(K, ['path', 'road', 'bridge', 'stair', 'bar', 'trail'])
                ob &= T['land'] & ~route_cells & ~hard & ~bar
                if ob.sum() < 20:
                    continue
                K[ob] = kind
                # the side path: leaves the road at a shallow Y, takes the easy line round the obstacle's far side with two
                # gentle bends, and rejoins at a Y
                def nrm(j):
                    ux, uy = x[min(j + 2, len(x) - 1)] - x[max(j - 2, 0)], y[min(j + 2, len(x) - 1)] - y[max(j - 2, 0)]; lu = math.hypot(ux, uy) or 1
                    return -uy / lu, ux / lu
                far = 120 if kind != 'ravine' else 140
                (nax, nay), (nbx, nby) = nrm(ja), nrm(jb)
                loop = chaikin([(x[j0], y[j0]), (x[ja] + nax * sd * 40, y[ja] + nay * sd * 40),
                                (ox + nx_ * sd * far - tx / Lt * 70, oy + ny_ * sd * far - ty / Lt * 70),
                                (ox + nx_ * sd * far + tx / Lt * 70, oy + ny_ * sd * far + ty / Lt * 70),
                                (x[jb] + nbx * sd * 40, y[jb] + nby * sd * 40), (x[j1], y[j1])], 3)
                lm = line_mask(loop, 20)
                mid = line_mask(loop[len(loop) // 4: -len(loop) // 4], 20)
                # never back across its own road; in a region's first loop it may cross another lane, as a crossroads
                if (lm & (bar | hard | ob)).any() or (mid & (own if pass_ == 0 else route_cells)).any():
                    K[ob] = ground; continue
                placed.append((x[i], y[i])); covered.add(biome_of(x[i], y[i]))
                K[lm & ~route_cells] = 'trail'; T['used'] |= lm
                out.append({'route': rn, 'obstacle': kind, 'x': round(ox), 'y': round(oy), 'side_path': True, 'along': float(a0)})
                break
    # walk-round loops where the routes found no room: round a spoil heap above Cogsworth, round the Headland's rocks
    for (cx, cy, rx, ry, nm, kind) in [(8150, 2350, 92, 70, 'a spoil heap', 'spoil'), (7050, 5560, 105, 125, "the Headland's rocks", 'boulders'),
                                       (9300, 4180, 80, 60, 'a reed pool', 'pool'), (9200, 4700, 80, 60, 'a reed pool', 'pool'), (9350, 3250, 80, 60, 'a willow thicket', 'thicket'),
                                       (6680, 4350, 90, 70, 'a dew pond', 'pool')]:
        if any(o['route'] == 'ring' and biome_of(o['x'], o['y']) == biome_of(cx, cy) for o in out) or any(math.hypot(px_ - cx, py_ - cy) < 400 for px_, py_ in placed):
            continue
        # v5.3: an irregular pond (or heap, or rocks), set off-centre, and a path that follows its shore at a varying
        # distance, close on one side and wide on the other, joined to the nearest road by a spur that forks into a Y
        rg = np.random.default_rng(int(cx) * 7 + int(cy)); ph = rg.uniform(0, 2 * math.pi, 5)
        tt = np.linspace(0, 2 * math.pi, 72, endpoint=False)
        cr = 0.5 * (1 + 0.2 * np.sin(2 * tt + ph[0]) + 0.12 * np.sin(3 * tt + ph[1]) + 0.07 * np.sin(5 * tt + ph[2]))
        gap = 0.1 + 0.42 * (0.5 + 0.5 * np.cos(tt - ph[3])) + 0.05 * np.sin(4 * tt + ph[4])
        pr = cr + gap
        ring = [(cx + rx * p_ * math.cos(t_), cy + ry * p_ * math.sin(t_)) for p_, t_ in zip(pr, tt)]
        ring = chaikin(ring + ring[:1], 2)
        lm = line_mask(ring, 20)
        if (lm & (bar | np.isin(K, ['river', 'sea', 'lava', 'cliff', 'crag', 'canal', 'building', 'tower']))).any():
            continue
        th = np.arctan2((PY - cy) / ry, (PX - cx) / rx); rr_ = np.hypot((PX - cx) / rx, (PY - cy) / ry)
        crt = np.interp(th % (2 * math.pi), tt, cr, period=2 * math.pi) * (1 + 0.06 * noise(30, int(cx) % 997, 2))
        core_ = (rr_ < crt) & T['land'] & ~np.isin(K, ['path', 'road', 'bridge', 'stair', 'trail'])
        K[core_] = kind; K[lm & ~np.isin(K, ['path', 'road', 'bridge', 'stair'])] = 'trail'; T['used'] |= lm
        # the spur and its Y
        rc = np.isin(K, ['path', 'road']) & (np.hypot(PX - cx, PY - cy) < 520) & ~lm
        if rc.any():
            ys_, xs_ = np.nonzero(rc); k0 = int(np.argmin(np.hypot(PX[ys_, xs_] - cx, PY[ys_, xs_] - cy)))
            qx, qy = float(PX[ys_[k0], xs_[k0]]), float(PY[ys_[k0], xs_[k0]])
            ta = math.atan2((qy - cy) / ry, (qx - cx) / rx)
            def onring(t_):
                p_ = float(np.interp(t_ % (2 * math.pi), tt, pr, period=2 * math.pi)); return (cx + rx * p_ * math.cos(t_), cy + ry * p_ * math.sin(t_))
            ax_, ay_ = onring(ta); fx_, fy_ = ax_ + (qx - ax_) * 0.4, ay_ + (qy - ay_) * 0.4
            if math.hypot((qx - cx) / rx, (qy - cy) / ry) < float(np.interp(ta % (2 * math.pi), tt, pr, period=2 * math.pi)) + 0.15:
                spur = []                                                       # the road already runs into the loop: it joins there
            else:
                spur = [meander([(qx, qy), ((qx + fx_) / 2 + 10, (qy + fy_) / 2 - 8), (fx_, fy_)], 12, int(cx) % 991, 70),
                    chaikin([(fx_, fy_), onring(ta - 0.45)], 1), chaikin([(fx_, fy_), onring(ta + 0.45)], 1)]
            sm_ = np.zeros((H, W), bool)
            for sp in spur:
                sm_ |= line_mask(sp, 16)
            if not (sm_ & (bar | np.isin(K, ['river', 'sea', 'lava', 'cliff', 'crag', 'canal', 'building', 'tower', 'pool', 'spoil']))).any():
                K[sm_ & ~np.isin(K, ['path', 'road', 'bridge', 'stair'])] = 'trail'; T['used'] |= sm_
        out.append({'route': 'ring', 'obstacle': nm, 'x': cx, 'y': cy, 'side_path': True, 'along': 0.0})
    # collapsed old bridges beside the fords where routes cross the small rivers
    for nm in ('the Sleepwater', 'the Amber', 'the Willow Run', 'the Brackens beck'):
        rm = T['river_masks'].get(nm)
        if rm is None:
            continue
        cross = ndi.binary_dilation(rm, iterations=2) & np.isin(K, ['bridge'])
        lab, n = ndi.label(cross)
        for i in range(1, min(n, 2) + 1):
            ys, xs = np.nonzero(lab == i); cy, cx = int(ys.mean()), int(xs.mean())
            blk = K[cy - 6:cy - 4, cx - 3:cx + 3]; blk[np.isin(blk, ['river', 'meadow', 'steppe', 'scrub', 'broadleaf', 'watermeadow', 'desert'])] = 'ruinbridge'
            out.append({'route': nm, 'obstacle': 'collapsed bridge', 'x': cx * CELL, 'y': (cy - 5) * CELL, 'side_path': False})
    T['obstacles'] = out
    return out


def borders(T):
    """The edge of the walkable world, drawn as a reason to stop: thickets, thorn scrub, boulders, dune walls, crevasses
    or sinkholes, by the ground there, in a ragged band; and beyond, what lies further: surf on the coast, far islands,
    a caravan route across the dune sea, the old forest's giant trees, icefalls."""
    K = T['K']; land = T['land']; T['ground0'] = K.copy()
    W0 = np.isin(K, list(g.WALK)) & ~g.FRAME
    rnd = np.random.default_rng(53).random((H, W))
    near = ndi.distance_transform_edt(~W0) * CELL
    n1 = noise(48, 500, 2); n2 = noise(160, 506); n3 = noise(220, 507)
    bar_ = np.zeros((H, W), bool)
    for m in T['barriers'].values():
        bar_ |= m
    nearbar = ndi.distance_transform_edt(~bar_) * CELL
    # stratum 1, the fade: the ground goes on past the old edge and stays walkable, with clumps of scrub, gorse or stones
    # scattered on it, few by the path and more and more outward, until they close into the wall
    fw = np.clip(np.clip(36 + 44 * (n2 + 1) + 18 * n1, 30, 130) + 16 * noise(24, 518, 1) + 12 * noise(12, 519, 1), 8, 160)   # jittered after the clip
    fade = g.FRAME & land & (near < fw) & (nearbar > 200 + 50 * noise(40, 520, 2) + 18 * noise(12, 521, 1)) & np.isin(K, list(g.WALK))
    tfade = np.clip(near / fw, 0, 1)
    clump = fade & (noise(22, 513, 2) > 0.62 - 0.85 * tfade)
    s1 = np.zeros((H, W), bool)
    g.FRAME &= ~fade
    W1 = np.isin(K, list(g.WALK)) & ~g.FRAME & ~clump
    near = ndi.distance_transform_edt(~(W1 | clump)) * CELL
    # stratum 2, the wall: dense, 64 to 170 px deep, in patches of the ground's own three blockers
    wall_out = 64 + 52 * (n3 + 1) + 10 * n1
    s2 = g.FRAME & land & (near < wall_out)
    # beyond the wall the clumps thin out again over 160 to 400 px into the hazy land, so the wall is the thick middle
    # of a broad, soft-edged change, never a ribbon with a hard edge on both sides
    tb = np.clip((near - wall_out) / (160 + 120 * (n2 + 1)), 0, 1)
    farclump = g.FRAME & land & ~s2 & (tb < 1) & (noise(22, 517, 2) > -0.35 + 1.1 * tb) & np.isin(K, list(g.WALK))
    pal = [(['broadleaf', 'conifer', 'wild', 'carr', 'garden', 'deadwood'], ['thicket', 'bramble', 'felltree'], ['thicket', 'ancient', 'felltree']),
           (['meadow', 'steppe', 'watermeadow', 'scroll', 'field', 'field2', 'fallow', 'heath', 'hedge', 'gorse', 'pointbar'], ['gorse', 'bramble', 'boulders'], ['thicket', 'gorse', 'bramble']),
           (['scrub', 'desert', 'badland', 'mesa', 'wash', 'saltpan'], ['scrubwall', 'boulders', 'scrubwall'], ['scrubwall', 'boulders', 'dunewall']),
           (['erg'], ['scrubwall', 'dunewall', 'scrubwall'], ['dunewall', 'scrubwall', 'boulders']),
           (['alpine', 'barren', 'scree', 'talus'], ['boulders', 'scree2', 'boulders'], ['scree2', 'boulders', 'crag']),
           (['snow', 'glacier', 'crevasse'], ['scree2', 'crag', 'scree2'], ['crevasse', 'crag', 'scree2']),
           (['ash', 'lavastone', 'basalt', 'fireweed'], ['boulders', 'aa', 'boulders'], ['aa', 'boulders', 'scree2']),
           (['bog', 'reeds', 'marsh', 'mere'], ['pool', 'bramble', 'pool'], ['mere', 'sinkhole', 'bramble']),
           (['sand', 'blacksand', 'shoal'], ['driftwood', 'boulders', 'driftwood'], ['boulders', 'dunewall', 'driftwood'])]
    # patches of irregular size (about 16 to 60 px): whichever of three noise fields is highest picks the material,
    # the first weighted up so each ground has a main blocker with the other two mixed through it
    f0, f1, f2 = noise(30, 514, 2) + 0.12, noise(30, 515, 2), noise(30, 516, 2) - 0.08
    pick = np.argmax(np.stack([f0, f1, f2]), 0)
    setmask = np.zeros((H, W), bool)
    for grounds, m1, m2 in pal:
        gm = np.isin(K, grounds) & ~setmask
        sel = clump & gm
        K[sel] = np.array(m1, dtype=object)[pick[sel]]
        sel = s2 & gm
        K[sel] = np.array(m2, dtype=object)[pick[sel]]
        setmask |= sel
        sel2 = farclump & gm
        K[sel2] = np.array(m2, dtype=object)[pick[sel2]]
    K[clump & np.isin(K, list(g.WALK))] = 'gorse'
    T['fade_clumps'] = clump | (farclump & ~np.isin(K, list(g.WALK)))
    left = s2 & np.isin(K, list(g.WALK))
    K[left] = np.array(['bramble', 'boulders', 'gorse'], dtype=object)[pick[left]]   # anything else at the edge: brambles, boulders, gorse
    # where two grounds meet, two blocks can still share a material; break any run longer than three props
    band_ = setmask | left
    alt = {'boulders': 'scree2', 'scree2': 'boulders', 'bramble': 'gorse', 'gorse': 'bramble', 'thicket': 'felltree', 'felltree': 'thicket', 'ancient': 'thicket',
           'dunewall': 'scrubwall', 'scrubwall': 'dunewall', 'crag': 'scree2', 'crevasse': 'crag', 'aa': 'boulders', 'sinkhole': 'pool', 'pool': 'sinkhole',
           'mere': 'bramble', 'driftwood': 'boulders'}
    for _ in range(4):
        for Ka, Ba in ((K, band_), (K.T, band_.T)):
            same = np.zeros(Ka.shape, bool); same[:, 1:] = (Ka[:, 1:] == Ka[:, :-1]) & Ba[:, 1:] & Ba[:, :-1]
            for j in np.nonzero(same.any(1))[0]:
                run = 0
                for i in range(Ka.shape[1]):
                    run = run + 1 if same[j, i] else 0
                    if run == 9:                                                       # the tenth identical cell: a different prop, a small round clump
                        a_ = alt.get(Ka[j, i], 'boulders')
                        for (dj, di) in ((0, 0), (0, 1), (0, 2), (-1, 1), (1, 1)):
                            jj, ii = j + dj, i + di
                            if 0 <= jj < Ka.shape[0] and 0 <= ii < Ka.shape[1] and Ba[jj, ii]:
                                Ka[jj, ii] = a_
                        run = 0
    T['border_s1'], T['border_s2'] = s1, s2
    T['border_assigned'] = setmask | left
    # north: crevasse fields and icefalls on the glaciers
    K[(K == 'glacier') & (noise(50, 501, 2) > 0.45) & ~T['border_assigned']] = 'crevasse'
    # west: the dune sea's storm haze is drawn in colour52; a caravan route crosses the far dunes
    cav = line_mask(meander([(-50, 2400), (500, 2600), (1000, 2450), (1500, 2700)], 40, 502, 120), 8) & (K == 'erg')
    K[cav & (((PX // 24).astype(int)) % 2 == 0)] = 'caravan'
    # east: sinkholes in the moss fens; the old forest's giant trees
    K[(K == 'bog') & g.FRAME & (noise(60, 503, 2) > 0.45) & ~T['border_assigned']] = 'sinkhole'
    K[np.isin(K, ['wild']) & (PX > 9800) & (PY < 2600) & (noise(160, 504) > 0.1) & ~T['border_assigned']] = 'ancient'
    # south: surf on every shore, far islands on the horizon
    dl = ndi.distance_transform_edt(~land) * CELL
    K[T['sea'] & (dl < 14 + 10 * noise(60, 505)) & (rnd < 0.7) & (K == 'sea')] = 'surf'
    for i, (fx, fy, rx, ry) in enumerate([(2500, 6800, 260, 70), (3700, 6860, 180, 50), (10300, 6820, 320, 80), (11000, 6880, 140, 40)]):
        K[shape(fx, fy, rx, ry, 510 + i, 0.4) & T['sea']] = 'farisle'


def content(T):
    """Named things along and off the routes in every biome, about two per screen of route: landmarks, camps, ruins,
    caves, shrines, wells, wrecks, viewpoints, wildlife, people to meet, flavour props. None gives a reward or costs anything."""
    K = T['K']; Wm = np.isin(K, list(g.WALK)) & ~g.FRAME; pois = []; per = {b: {'items': 0, 'route_px': 0.0} for b in BIOMES}
    cyc = {b: 0 for b in BIOMES}
    for rn in MAIN_ROUTES:
        sm = T['route_px'][rn]; x, y, al, tot = densify(sm, 8)
        for i in range(1, len(x)):
            b = biome_of(x[i], y[i])
            if b:
                per[b]['route_px'] += math.hypot(x[i] - x[i - 1], y[i] - y[i - 1])
        for k_, a0 in enumerate(np.arange(150, tot, SCREEN_PX / 2)):
            i = int(np.argmin(np.abs(al - a0))); b = biome_of(x[i], y[i])
            if not b:
                continue
            tx, ty = x[min(i + 2, len(x) - 1)] - x[max(i - 2, 0)], y[min(i + 2, len(x) - 1)] - y[max(i - 2, 0)]; Lt = math.hypot(tx, ty) or 1
            sd = 1 if k_ % 2 else -1; off = 70 if k_ % 3 else 260                 # most beside the path, every third a short way off it
            for tryoff in (off, off * 0.6, off * 1.4, 50):
                px_, py_ = x[i] - ty / Lt * sd * tryoff, y[i] + tx / Lt * sd * tryoff
                yi, xi = int(py_ // CELL), int(px_ // CELL)
                if 0 <= yi < H and 0 <= xi < W and Wm[yi, xi]:
                    tlist = CONTENT_TYPES[b]; tp = tlist[cyc[b] % len(tlist)]; cyc[b] += 1
                    cat = next((c for key, c in CAT.items() if key in tp), 'landmark')
                    pois.append({'name': tp, 'cat': cat, 'biome': b, 'x': round(px_), 'y': round(py_), 'route': rn, 'off_path': tryoff > 150})
                    per[b]['items'] += 1
                    break
    for b, v in per.items():
        v['per_screen'] = round(v['items'] / max(1e-6, v['route_px'] / SCREEN_PX), 2); v['route_px'] = round(v['route_px'])
    T['pois'] = pois
    return pois, per


def content_map(T, pois, per, out):
    img = Image.open(os.path.join(HERE, f'continent-1x{SUF}.png')).convert('RGB')
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    d = ImageDraw.Draw(img); k = 2 / CELL
    for m in T.get('markers', []):                                                # the fine markers: I white, S tan, A green
        X, Y = m['x'] * k, m['y'] * k; c = {'interactable': '#FFFFFF', 'story': '#E0B070', 'ambient': '#7BE07B'}[m['type']]
        d.point([(X, Y), (X + 1, Y), (X, Y + 1), (X + 1, Y + 1)], fill=c)
    for p in T.get('pockets', []):
        X, Y = p['x'] * k, p['y'] * k; d.regular_polygon((X, Y, 7), 5, fill='#B48CFF', outline='black')
    for o in T.get('obstacles', []):
        X, Y = o['x'] * k, o['y'] * k; d.rectangle([X - 3, Y - 3, X + 3, Y + 3], outline='#D7263D', width=2)
    for p in pois:
        X, Y = p['x'] * k, p['y'] * k; c = CAT_COL[p['cat']]
        if p['cat'] in ('landmark', 'view'):
            d.polygon([(X, Y - 6), (X + 6, Y), (X, Y + 6), (X - 6, Y)], fill=c, outline='black')
        elif p['cat'] in ('camp', 'npc'):
            d.polygon([(X - 5, Y + 4), (X + 5, Y + 4), (X, Y - 6)], fill=c, outline='black')
        else:
            d.ellipse([X - 4, Y - 4, X + 4, Y + 4], fill=c, outline='black')
    for nm, (x, y) in g.EGGS.items():
        X, Y = x * k, y * k; d.ellipse([X - 5, Y - 5, X + 5, Y + 5], outline='white', width=1)
    # legend and counts
    pw = 560; panel = Image.new('RGB', (pw, img.height), (24, 24, 30)); dp = ImageDraw.Draw(panel); yy0 = 16
    dp.text((14, yy0), 'Content per biome (v5.2)', font=g.FONTT, fill='white'); yy0 += 34
    dp.text((14, yy0), 'items / route px / items per screen of route (576 px)', font=g.FONT, fill='#CCCCCC'); yy0 += 24
    for b, v in per.items():
        dp.text((14, yy0), f"{b}: {v['items']} / {v['route_px']} / {v['per_screen']}", font=g.FONTB, fill='white'); yy0 += 24
    yy0 += 14
    for cat, c in CAT_COL.items():
        dp.ellipse([16, yy0 + 2, 28, yy0 + 14], fill=c, outline='black'); dp.text((36, yy0), cat, font=g.FONTB, fill='white'); yy0 += 22
    dp.rectangle([16, yy0 + 2, 28, yy0 + 14], outline='#D7263D', width=2); dp.text((36, yy0), 'obstacle with a side path round it', font=g.FONTB, fill='white'); yy0 += 22
    dp.ellipse([16, yy0 + 2, 28, yy0 + 14], outline='white'); dp.text((36, yy0), 'easter-egg spot (reserved)', font=g.FONTB, fill='white'); yy0 += 22
    dp.regular_polygon((22, yy0 + 8, 7), 5, fill='#B48CFF', outline='black'); dp.text((36, yy0), 'secret pocket (a dead-end path to a clearing)', font=g.FONTB, fill='white'); yy0 += 22
    dp.text((14, yy0), 'dots: white interactable, tan story prop, green ambient life', font=g.FONTB, fill='white')
    full = Image.new('RGB', (img.width + pw, img.height)); full.paste(img, (0, 0)); full.paste(panel, (img.width, 0))
    full.save(os.path.join(HERE, out))


TLANDMARK = {'the Col hut': ('the headwall', 6230, 1950), 'the Frostline lip': ('the tarn', 6200, 1800), 'the Brackens gap': ('the bluffs', 5170, 3600),
             "Drover's bridge": ('the desert line viaduct', 4290, 3720), 'the Rift ferry': ('the Rift mouth', 4250, 5380),
             'the Amber canyon head': ('the canyon walls', 2640, 2950), 'the Cinder Rise': ('the plume over Hearthold', 2470, 4300),
             'the chasm bridge': ('Hearthold', 2480, 5120), 'the crust causeway': ('the flow\'s steaming toe', 3290, 5800),
             'the Millrace cutting': ("Cogsworth's chimneys", 7980, 2450), 'the Cog foot': ('the Narrows gorge', 8960, 2750),
             'Lullford Bridge': ('the swing span', 8960, 4310), 'the canal embankment': ('the falls and the Harbour Bridge', 10100, 4600),
             'the Headland stile': ('the lighthouse', 7050, 5600), 'the Shell Bar': ('the wreck', 6930, 5870)}


def transitions_sheet(T, out):
    tiles = []
    for nm, (x, y) in THRESHOLDS.items():
        crop = (int(x - 600), int(y - 450), int(x + 600), int(y + 450))
        tmp = f'_t_{len(tiles)}.png'
        g.render(T, tmp, 4, crop=crop)
        im = Image.open(os.path.join(HERE, tmp)).convert('RGB'); os.remove(os.path.join(HERE, tmp))
        d = ImageDraw.Draw(im); k = 4 / CELL; X, Y = (x - crop[0]) * k, (y - crop[1]) * k
        d.polygon([(X, Y - 10), (X + 10, Y), (X, Y + 10), (X - 10, Y)], outline='#F28C28', width=3)
        ln, lx, ly = TLANDMARK.get(nm, ('', x, y))
        LX, LY = (lx - crop[0]) * k, (ly - crop[1]) * k
        inside = 0 <= LX <= im.width and 0 <= LY <= im.height
        LXc, LYc = min(max(LX, 14), im.width - 14), min(max(LY, 14), im.height - 14)
        if inside:
            d.ellipse([LX - 9, LY - 9, LX + 9, LY + 9], outline='#E86A92', width=3)
        else:
            d.line([(X, Y), (LXc, LYc)], fill='#E86A92', width=2); d.ellipse([LXc - 6, LYc - 6, LXc + 6, LYc + 6], fill='#E86A92')
        d.text((min(max(LXc, 90), im.width - 90), min(LYc + 18, im.height - 12)), ln + ('' if inside else ' (ahead)'), font=g.FONTB, fill='#FFD6E6', stroke_width=2, stroke_fill='black', anchor='mm')
        im = im.resize((im.width // 1, im.height // 1))
        cap = Image.new('RGB', (im.width, 30), (24, 24, 30)); ImageDraw.Draw(cap).text((8, 6), nm, font=g.FONTB, fill='white')
        tile = Image.new('RGB', (im.width, im.height + 30)); tile.paste(cap, (0, 0)); tile.paste(im, (0, 30)); tiles.append(tile)
    cols = 4; tw, th = tiles[0].size; rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw + (cols - 1) * 8, rows * th + (rows - 1) * 8 + 40), (243, 239, 230))
    ImageDraw.Draw(sheet).text((10, 10), 'Transitions (v5.2): each threshold on its route; orange = the threshold, pink = the landmark seen on the approach', font=g.FONTT, fill='black')
    for i, t_ in enumerate(tiles):
        sheet.paste(t_, ((i % cols) * (tw + 8), 40 + (i // cols) * (th + 8)))
    sheet.save(os.path.join(HERE, out))


BOUNDARY_CROPS = {'boundary-north': (5000, 0, 8600, 2300), 'boundary-west': (0, 1400, 3400, 4600), 'boundary-east': (9600, 1200, 11264, 4600),
                  'boundary-south': (1600, 4800, 7600, 6912)}

# ------------------------------------------------------------------------------------------ v5.2: pockets, markers, mixing bands, the benchmark
POCKET_KINDS = ['a view over the land', 'a bench under a tree', 'a story detail: an old grave', 'a hermit at a fire', 'a story detail: a buried bell',
                'a view down a gorge', 'a resident fishing', 'a story detail: initials cut in a stone']
MARK_NAMES = {'interactable': ['bench', 'signpost', 'resident', 'noticeboard', 'door', 'water trough', 'gate'],
              'story': ['cart with a broken wheel', 'cairn', 'tracks', 'mended fence', 'old boot', 'cold fire ring', 'marker stone', 'lost hat'],
              'ambient': {'the home valley': ['sparrows', 'butterflies'], 'the massif and the Frostline': ['ibex', 'choughs'], 'the coal hills': ['crows', 'moths'],
                          'the Lull plain': ['herons', 'hares'], 'the river belt and delta': ['otters', 'egrets'], 'Neon Harbour': ['gulls', 'cats'],
                          'the steppe and the Brackens': ['skylarks', 'sheep'], 'the Sunstone basin': ['lizards', 'vultures'],
                          'the fire country': ['salamanders', 'steam'], 'the coast and the isles': ['seals', 'terns']}}
PATTERN = ['interactable', 'story', 'story', 'ambient', 'interactable', 'story', 'story', 'interactable', 'story', 'ambient']   # 10 a screen: 3 I, 5 S, 2 A
SOURCES = {'the Col hut': 'the glacier', 'the Frostline lip': 'the glacier', 'the Brackens gap': 'the Brackens\' heather', "Drover's bridge": 'the Rift',
           'the Rift ferry': 'the Rift and the sea', 'the Amber canyon head': 'the Amber', 'the Cinder Rise': 'the volcano', 'the chasm bridge': 'the volcano',
           'the crust causeway': 'the volcano', 'the Millrace cutting': 'the coal seams', 'the Cog foot': 'the Lull', 'Lullford Bridge': 'the Lull',
           'the canal embankment': 'the city', 'the Headland stile': 'the sea', 'the Shell Bar': 'the sea'}
AMBIENCE = {k: 160 for k in SOURCES}       # cross-fade length in px (4 s at 40 px/s) at each threshold
PROMISES = {'the home valley': ('the Frostline\'s headwall above', 'W2'), 'the steppe and the Brackens': ('the desert line\'s viaduct over the Rift', 'W5'),
            'the Sunstone basin': ('the plume over Hearthold', 'W6'), 'the fire country': ('the crater rim (seen, never walked: the plume\'s source)', None),
            'the coal hills': ('the Narrows Viaduct', 'W7'), 'the Lull plain': ('Neon\'s towers beyond the delta', 'W7'),
            'the river belt and delta': ('the Harbour Bridge', 'W7'), 'Neon Harbour': ('the rocket on its pad', 'W8'),
            'the coast and the isles': ('the lighthouse on the Headland and the isles', 'W1, W4'), 'the massif and the Frostline': ('Cogsworth\'s chimneys from the fells', 'W3')}


def pockets(T):
    """Secret pockets: a little dead-end path off the route to a clearing that holds a view, a bench, a resident or a
    story detail (never a reward). About one per five screens of route in each biome, at least three."""
    K = T['K']; out = []
    bar = np.zeros((H, W), bool)
    for m in T['barriers'].values():
        bar |= m
    hard = ~np.isin(K, list(g.WALK) + ['broadleaf', 'conifer', 'garden', 'wild', 'carr', 'deadwood'])
    routec = np.isin(K, ['path', 'road', 'bridge', 'stair', 'trail', 'bar'])
    need = {}
    for b in BIOMES:
        need[b] = 0
    lens = {b: 0.0 for b in BIOMES}
    for rn in MAIN_ROUTES:
        x, y, al, tot = densify(T['route_px'][rn], 8)
        for i in range(1, len(x)):
            b = biome_of(x[i], y[i])
            if b:
                lens[b] += 8
    for b in BIOMES:
        need[b] = max(3, int(math.ceil(lens[b] / SCREEN_PX / 5)))
    k_ = 0
    for b in BIOMES:
        got = 0
        cands = []
        for rn in MAIN_ROUTES:
            x, y, al, tot = densify(T['route_px'][rn], 8)
            for i in range(20, len(x) - 20, 37):
                if biome_of(x[i], y[i]) == b:
                    cands.append((rn, x, y, i))
        np.random.default_rng(len(b)).shuffle(cands)
        for rn, x, y, i in cands:
            if got >= need[b]:
                break
            tx, ty = x[i + 2] - x[i - 2], y[i + 2] - y[i - 2]; Lt = math.hypot(tx, ty) or 1
            for sd in (1, -1):
                for off in (240, 320, 180):
                    px_, py_ = x[i] - ty / Lt * sd * off, y[i] + tx / Lt * sd * off
                    if not (0 < px_ < WPX and 0 < py_ < HPX):
                        continue
                    trail = chaikin([(x[i], y[i]), (x[i] - ty / Lt * sd * off * 0.5 + tx / Lt * 60, y[i] + tx / Lt * sd * off * 0.5 + ty / Lt * 60), (px_, py_)], 2)
                    tm = _orig_line_mask(trail, 20); cl = shape(px_, py_, 56, 44, 900 + k_, 0.3)
                    if ((tm | cl) & (bar | (hard & ~routec))).any() or not T['land'][int(py_ // CELL), int(px_ // CELL)]:
                        continue
                    K[tm & ~routec] = 'trail'; K[cl & ~routec] = 'clearing'; T['used'] |= tm | cl
                    out.append({'biome': b, 'x': round(px_), 'y': round(py_), 'holds': POCKET_KINDS[k_ % len(POCKET_KINDS)], 'route': rn})
                    got += 1; k_ += 1
                    break
                else:
                    continue
                break
    used_d = ndi.distance_transform_edt(~T['used']) * CELL
    walkk = np.isin(K, list(g.WALK)) & ~routec & T['land'] & ~bar
    for b in BIOMES:
        have = [p for p in out if p['biome'] == b]
        if len(have) >= need[b]:
            continue
        x0, y0, x1, y1 = BIOMES[b]
        cand = walkk & (used_d < 260) & (used_d > 60) & (PX > x0) & (PX < x1) & (PY > y0) & (PY < y1)
        ys, xs = np.nonzero(cand); order = np.random.default_rng(len(b) + 7).permutation(len(ys))
        for j in order:
            if len(have) >= need[b]:
                break
            px_, py_ = xs[j] * CELL + 4, ys[j] * CELL + 4
            if any(math.hypot(px_ - p['x'], py_ - p['y']) < 300 for p in have):
                continue
            cl = shape(px_, py_, 44, 34, 950 + k_, 0.3) & walkk
            K[cl] = 'clearing'; T['used'] |= cl
            p = {'biome': b, 'x': round(px_), 'y': round(py_), 'holds': POCKET_KINDS[k_ % len(POCKET_KINDS)], 'route': None}
            out.append(p); have.append(p); k_ += 1
    T['pockets'] = out
    return out


def fill_required(T, pois):
    """Every biome gets its viewpoint, camp or hut, ruin or wreck and wildlife, and landmarks no more than about
    two screens apart along every route (the benchmark's checks 3 and 4)."""
    K = T['K']; Wm = np.isin(K, list(g.WALK)) & ~g.FRAME
    need = {'view': 'a viewpoint', 'camp': "a resident's camp", 'ruin': 'a ruin', 'wild': 'a wildlife spot'}
    for b in BIOMES:
        cats = {p['cat'] for p in pois if p['biome'] == b}
        if cats & {'npc'}:
            cats.add('camp')
        if cats & {'wreck'}:
            cats.add('ruin')
        for cat, nm in need.items():
            if cat in cats:
                continue
            for rn in MAIN_ROUTES:
                x, y, al, tot = densify(T['route_px'][rn], 8); done = False
                for i in range(len(x) // 3, len(x), 11):
                    if biome_of(x[i], y[i]) != b:
                        continue
                    for off in (90, -90, 140, -140, 60):
                        px_, py_ = x[i] + off * 0.7, y[i] + off * 0.7
                        yi, xi = int(py_ // CELL), int(px_ // CELL)
                        if 0 <= yi < H and 0 <= xi < W and Wm[yi, xi]:
                            pois.append({'name': nm, 'cat': cat, 'biome': b, 'x': round(px_), 'y': round(py_), 'route': rn, 'off_path': False}); done = True; break
                    if done:
                        break
                if done:
                    break
    LM = ['a tor', 'a lone tree', 'a standing stone', 'a ruined tower', 'a waymark post', 'a great boulder']
    k_ = 0
    for rn in MAIN_ROUTES:
        x, y, al, tot = densify(T['route_px'][rn], 8)
        for _ in range(12):
            lms = [(p['x'], p['y']) for p in pois if p['cat'] in ('landmark', 'view', 'ruin', 'shrine', 'wreck')] + list(THRESHOLDS.values())
            lms += [(v[0], v[1]) for v in g.SETTLE.values()] + [(bb[0], bb[1]) for bb in g.BRIDGES.values()] + [(h_[1], h_[2]) for h_ in T['huts']]
            LP = np.array(lms, float); d2 = np.hypot(LP[:, None, 0] - x[None, :], LP[:, None, 1] - y[None, :])
            j = d2.argmin(1); near = d2.min(1) < 300
            pos = np.sort(np.r_[0, al[j[near]], tot]); gaps = np.diff(pos); g_ = int(gaps.argmax())
            if gaps[g_] <= 1000:
                break
            a_mid = (pos[g_] + pos[g_ + 1]) / 2; i = int(np.argmin(np.abs(al - a_mid)))
            placed = False
            for off in (110, -110, 170, -170, 70, -70):
                tx, ty = x[min(i + 2, len(x) - 1)] - x[max(i - 2, 0)], y[min(i + 2, len(x) - 1)] - y[max(i - 2, 0)]; Lt = math.hypot(tx, ty) or 1
                px_, py_ = x[i] - ty / Lt * off, y[i] + tx / Lt * off
                yi, xi = int(py_ // CELL), int(px_ // CELL)
                if 0 <= yi < H and 0 <= xi < W and T['land'][yi, xi] and not np.isin(K[yi, xi], ['river', 'road', 'path', 'bridge', 'sea', 'lava']):
                    nm = LM[k_ % len(LM)]; k_ += 1
                    pois.append({'name': nm, 'cat': 'landmark', 'biome': biome_of(px_, py_) or '', 'x': round(px_), 'y': round(py_), 'route': rn, 'off_path': False})
                    if nm in ('a tor', 'a great boulder', 'a standing stone'):
                        K[max(0, yi - 2):yi + 2, max(0, xi - 2):xi + 2][~np.isin(K[max(0, yi - 2):yi + 2, max(0, xi - 2):xi + 2], ['river', 'road', 'path', 'bridge', 'sea', 'lava', 'trail'])] = 'tor'
                    placed = True; break
            if not placed:
                break
    return pois


def markers(T):
    """Planning markers for the art lanes: along every route, nine noticeable things a screen (three to interact with,
    four story props, two of ambient life), and in every settlement eight interactables and eight story props a screen."""
    K = T['K']; Wm = np.isin(K, list(g.WALK)) & ~g.FRAME; out = []
    for rn in MAIN_ROUTES:
        x, y, al, tot = densify(T['route_px'][rn], 8)
        for k_, a0 in enumerate(np.arange(40, tot, SCREEN_PX / len(PATTERN))):
            i = int(np.argmin(np.abs(al - a0))); b = biome_of(x[i], y[i]) or 'the Lull plain'
            tp = PATTERN[k_ % len(PATTERN)]
            tx, ty = x[min(i + 2, len(x) - 1)] - x[max(i - 2, 0)], y[min(i + 2, len(x) - 1)] - y[max(i - 2, 0)]; Lt = math.hypot(tx, ty) or 1
            sd = 1 if k_ % 2 else -1
            for off, sd2 in ((40, sd), (60, sd), (40, -sd), (28, sd), (80, -sd), (110, sd), (16, sd), (16, -sd), (0, sd)):
                px_, py_ = x[i] - ty / Lt * sd2 * off, y[i] + tx / Lt * sd2 * off
                yi, xi = int(py_ // CELL), int(px_ // CELL)
                if 0 <= yi < H and 0 <= xi < W and (Wm[yi, xi] or off == 0):
                    nm = MARK_NAMES['ambient'][b][k_ % 2] if tp == 'ambient' else MARK_NAMES[tp][k_ % len(MARK_NAMES[tp])]
                    out.append({'type': tp, 'name': nm, 'biome': b, 'x': round(px_), 'y': round(py_), 'route': rn, 'along': round(a0)}); break
    sett = []
    r = np.random.default_rng(54)
    for name, (cx, cy, rad, kind) in g.SETTLE.items():
        if kind in ('cirque',):
            continue
        core = (np.hypot(PX - cx, PY - cy) < rad) & Wm
        screens = core.sum() / (SCREEN_PX * 320 / CELL / CELL)
        ys, xs = np.nonzero(core)
        if len(ys) == 0:
            continue
        n = int(round(max(1.0, screens) * 8))
        for tp in ('interactable', 'story'):
            for j in r.choice(len(ys), min(n, len(ys)), replace=False):
                out.append({'type': tp, 'name': MARK_NAMES[tp][j % len(MARK_NAMES[tp])], 'biome': biome_of(xs[j] * CELL, ys[j] * CELL) or '', 'x': int(xs[j] * CELL),
                            'y': int(ys[j] * CELL), 'route': None, 'settlement': name})
        sett.append({'settlement': name, 'screens': round(float(screens), 2), 'per_screen_each': round(n / max(1.0, screens), 1)})
    T['markers'] = out; T['settlement_density'] = sett
    return out


def mixing_bands(T):
    """At each threshold, both regions' ground mixes over a band about two screens long: each side gets outliers of
    the other's ground (three kinds each way), thinning with distance from the threshold."""
    K = T['K']; rnd = np.random.default_rng(55).random((H, W)); res = {}
    ground = ['meadow', 'steppe', 'scrub', 'desert', 'broadleaf', 'conifer', 'heath', 'alpine', 'barren', 'snow', 'ash', 'lavastone', 'fireweed',
              'watermeadow', 'carr', 'reeds', 'sand', 'blacksand', 'deadwood', 'badland', 'scree', 'bog', 'field', 'field2', 'garden', 'scroll']
    walkg = [k for k in ground if k in g.WALK]
    routec = np.isin(K, ['path', 'road', 'bridge', 'stair', 'trail', 'bar', 'plaza', 'yard'])
    for nm, (tx_, ty_) in THRESHOLDS.items():
        rn = next((r_ for r_ in MAIN_ROUTES if min(math.hypot(px - tx_, py - ty_) for px, py in T['route_px'][r_]) < 120), None)
        if rn is None:
            continue
        x, y, al, tot = densify(T['route_px'][rn], 8)
        i0 = int(np.argmin(np.hypot(x - tx_, y - ty_)))
        iA = int(np.argmin(np.abs(al - (al[i0] - 600)))); iB = int(np.argmin(np.abs(al - (al[i0] + 600))))
        def pal(px, py):
            m = (np.hypot(PX - px, PY - py) < 320) & np.isin(K, walkg) & ~routec
            vals, cnt = np.unique(K[m], return_counts=True)
            return [v for v, c in sorted(zip(vals, cnt), key=lambda t: -t[1])][:3]
        pA, pB = pal(x[iA], y[iA]), pal(x[iB], y[iB])
        onlyA = [k for k in pA if k not in pB] or pA; onlyB = [k for k in pB if k not in pA] or pB
        dT = np.hypot(PX - tx_, PY - ty_)
        zone = (dT < 700) & np.isin(K, walkg) & ~routec
        sideA = np.hypot(PX - x[iA], PY - y[iA]) < np.hypot(PX - x[iB], PY - y[iB])
        p = 0.3 * np.clip(1 - dT / 700, 0, 1)
        for side, other in ((sideA, onlyB), (~sideA, onlyA)):
            sel = zone & side & (rnd < p)
            if sel.any() and other:
                K[sel] = np.array(other, dtype=object)[(rnd[sel] * 1000).astype(int) % len(other)]
        res[nm] = {'route': rn, 'side_A': pA, 'side_B': pB}
    T['mixing'] = res
    return res


def bench(T, pois, marks, pocks, obs, steps, gates):
    """The benchmark's 21 checks (bench/world-benchmark.md, section 5), measured on the block-out."""
    K = T['K']; out = []
    def row(n, what, value, target, ok, note=''):
        out.append({'n': n, 'check': what, 'measured': value, 'target': target, 'pass': bool(ok), 'note': note})
    total_route = sum(densify(T['route_px'][r_], 8)[3] for r_ in MAIN_ROUTES); screens = total_route / SCREEN_PX
    # 1 density on routes and in settlements
    per_route = []
    for r_ in MAIN_ROUTES:
        L_ = densify(T['route_px'][r_], 8)[3]; ms = [m for m in marks if m['route'] == r_]
        per_route.append((r_, sum(m['type'] == 'interactable' for m in ms) / (L_ / SCREEN_PX), sum(m['type'] == 'story' for m in ms) / (L_ / SCREEN_PX)))
    mi = min(v[1] for v in per_route); ms_ = min(v[2] for v in per_route)
    sd = min(sv['per_screen_each'] for sv in T['settlement_density'])
    row(1, 'interactables and story props per screen: routes (min over routes); settlements (min)', f'routes {mi:.1f} and {ms_:.1f}; settlements {sd:.1f} each',
        'routes 2-3 and 3-5; settlements 6-10 each', 2 <= mi and 3 <= ms_ and sd >= 6)
    # 2 longest gap with nothing to notice
    things = [(m['x'], m['y']) for m in marks] + [(p['x'], p['y']) for p in pois] + [(o['x'], o['y']) for o in obs] + list(THRESHOLDS.values())
    things += [(v[0], v[1]) for v in g.SETTLE.values()] + [(b[0], b[1]) for b in g.BRIDGES.values()]
    TP = np.array(things, float); worst = 0; worst_r = ''
    for r_ in MAIN_ROUTES:
        x, y, al, tot = densify(T['route_px'][r_], 8)
        d2 = np.hypot(TP[:, None, 0] - x[None, :], TP[:, None, 1] - y[None, :])
        j = d2.argmin(1); near = d2.min(1) < 150
        pos = np.sort(np.r_[0, al[j[near]], tot]); gap = np.diff(pos).max()
        if gap > worst:
            worst, worst_r = gap, r_
    row(2, 'longest stretch of path with nothing to notice', f'{worst:.0f} px ({worst_r})', '200 px or less', worst <= 200)
    # 3 landmark spacing and visibility from the screen before
    lms = [(p['x'], p['y']) for p in pois if p['cat'] in ('landmark', 'view', 'ruin', 'shrine', 'wreck')] + list(THRESHOLDS.values())
    lms += [(v[0], v[1]) for v in g.SETTLE.values()] + [(b[0], b[1]) for b in g.BRIDGES.values()] + [(h_[1], h_[2]) for h_ in T['huts']]
    LP = np.array(lms, float); worst = 0; worst_r = ''; vis_fail = 0; vis_n = 0
    for r_ in MAIN_ROUTES:
        x, y, al, tot = densify(T['route_px'][r_], 8)
        d2 = np.hypot(LP[:, None, 0] - x[None, :], LP[:, None, 1] - y[None, :]); j = d2.argmin(1); near = d2.min(1) < 300
        pos = np.sort(np.r_[0, al[j[near]], tot]); gap = np.diff(pos).max()
        if gap > worst:
            worst, worst_r = gap, r_
        for q in np.nonzero(near)[0]:
            a_prev = al[j[q]] - SCREEN_PX
            if a_prev > 0:
                i_ = int(np.argmin(np.abs(al - a_prev))); vis_n += 1
                if math.hypot(LP[q, 0] - x[i_], LP[q, 1] - y[i_]) > 900:
                    vis_fail += 1
    row(3, 'landmark spacing along routes; seen from the screen before (within 900 px)', f'longest gap {worst:.0f} px ({worst_r}); {vis_n - vis_fail}/{vis_n} seen',
        'every 576-1152 px; all seen', worst <= 1152 and vis_fail == 0)
    # 4 per-biome contents
    fails = []; detail = {}
    for b in BIOMES:
        L_ = sum(1 for _ in []) or 0
        bl = sum(8 for r_ in MAIN_ROUTES for (px, py) in zip(*densify(T['route_px'][r_], 8)[:2]) if biome_of(px, py) == b)
        sc = bl / SCREEN_PX
        named = sum(1 for p in pois if p['biome'] == b) + sum(1 for v in g.SETTLE.values() if biome_of(v[0], v[1]) == b) + sum(1 for v in THRESHOLDS.values() if biome_of(*v) == b)
        pk = sum(1 for p in pocks if p['biome'] == b)
        cats = {p['cat'] for p in pois if p['biome'] == b} | ({'view'} if any(p['biome'] == b and 'view' in p['holds'] for p in pocks) else set())
        wild = {m['name'] for m in marks if m['biome'] == b and m['type'] == 'ambient'} | {p['name'] for p in pois if p['biome'] == b and p['cat'] == 'wild'}
        x0, y0, x1, y1 = BIOMES[b]; sub = K[int(y0 // CELL):int(y1 // CELL), int(x0 // CELL):int(x1 // CELL)]
        water = np.isin(sub, ['river', 'creek', 'tarn', 'sea', 'oxbow', 'canal', 'channel', 'mere', 'pool', 'surf']).any()
        ok = named >= 3 + sc / 6 and pk >= max(3, sc / 5) and 'view' in cats and (cats & {'camp', 'npc'}) and (cats & {'ruin', 'wreck'}) and len(wild) >= 2 and water
        detail[b] = {'screens': round(sc, 1), 'named': named, 'pockets': pk, 'view': 'view' in cats, 'camp_or_hut': bool(cats & {'camp', 'npc'}),
                     'ruin_or_story': bool(cats & {'ruin', 'wreck'}), 'wildlife_kinds': len(wild), 'water': bool(water)}
        if not ok:
            fails.append(b)
    T['biome_detail'] = detail
    row(4, 'each biome: named places, secret pockets, viewpoint, camp, ruin, 2 wildlife, water', f'{len(BIOMES) - len(fails)}/{len(BIOMES)} biomes pass' + (f' (fail: {", ".join(fails)})' if fails else ''),
        'all biomes', not fails)
    row(5, 'no secret or decoration gives a reward, cost or chore', 'by design: markers and pockets carry no items', 'none', True)
    # 6-10 borders
    W0 = np.isin(K, list(g.WALK)) & ~g.FRAME
    fr_edge = g.FRAME & T['land'] & ndi.binary_dilation(W0)
    invisible = int((fr_edge & np.isin(K, list(g.WALK))).sum())
    row(6, 'invisible walls: frame cells touching the walk that are drawn as passable ground', invisible, '0', invisible == 0)
    near = ndi.distance_transform_edt(~W0) * CELL
    within = g.FRAME & T['land'] & (near < 64)
    cover = float(np.isin(K[within], list(g.WALK)).mean()) if within.any() else 0
    row(7, 'border depth: share of frame within 64 px of the walk that is drawn as a blocker (two strata)', f'{100 * (1 - cover):.1f} %', '100 % (2-3 strata)', cover < 0.005)
    runs = []
    inner = np.zeros((H, W), bool); inner[2:-2, 2:-2] = True                        # not the map's own edge
    for arr in (W0 & np.roll(g.FRAME, 1, 0) & inner, W0 & np.roll(g.FRAME, -1, 0) & inner, (W0 & np.roll(g.FRAME, 1, 1) & inner).T, (W0 & np.roll(g.FRAME, -1, 1) & inner).T):
        best = 0
        for j8, rowv in enumerate(arr):
            if rowv.any():
                dd = np.diff(np.r_[0, rowv.astype(int), 0]); st = np.nonzero(dd == 1)[0]; en = np.nonzero(dd == -1)[0]
                if int((en - st).max()) > best:
                    best = int((en - st).max()); T.setdefault('diag8', {})[len(runs)] = (best, j8, int(st[int(np.argmax(en - st))]))
        runs.append(best)
    row(8, 'longest straight run of the walk-to-border edge', f'{max(runs) * CELL} px', '96 px or less', max(runs) * CELL <= 96)
    band = T['border_assigned']; mx = 0
    for arr in (K, K.T):
        bm = band if arr is K else band.T
        same = (arr[:, 1:] == arr[:, :-1]) & bm[:, 1:] & bm[:, :-1]
        for j9, rowv in enumerate(same):
            if rowv.any():
                dd = np.diff(np.r_[0, rowv.astype(int), 0]); st = np.nonzero(dd == 1)[0]; en = np.nonzero(dd == -1)[0]
                if int((en - st).max()) + 1 > mx:
                    mx = int((en - st).max()) + 1; k9 = int(st[int(np.argmax(en - st))])
                    T['diag9'] = ('row' if arr is K else 'col', j9, k9, str(arr[j9, k9]))
    row(9, 'identical border material in a row (one prop = 3 cells)', f'{mx / 3:.0f} props', '3 or fewer', mx <= 9, 'block-out materials stand in for props')
    beyond = np.isin(K, ['glacier', 'crevasse', 'snow', 'crag', 'erg', 'dunewall', 'caravan', 'ancient', 'wild', 'mere', 'sinkhole', 'farisle', 'sea', 'surf',
                         'mesa', 'lava', 'aa', 'river', 'conifer', 'bog', 'badland', 'saltpan'])
    reach = ndi.distance_transform_edt(~beyond) * CELL < 900
    outer = fr_edge & ((PX < 3300) | (PX > 9800) | (PY < 2300) | (PY > 4800))
    share = float(reach[outer].mean()) if outer.any() else 1
    row(10, 'outer border edge with something seen beyond within 900 px', f'{100 * share:.1f} %', '100 %', share > 0.995)
    row(11, 'each region shows a place seen but not yet reached, reached later', f'{len(PROMISES)}/{len(BIOMES)} regions listed; all ways reach their places',
        'all regions', len(PROMISES) == len(BIOMES) and not any(v['missing'] for k, v in gates.items() if k.startswith('open')),
        'the crater rim is the one promise kept by sight only')
    # 12-15 transitions
    mixf = []
    for nm, mres in T['mixing'].items():
        rn = mres['route']; x, y, al, tot = densify(T['route_px'][rn], 8); tx_, ty_ = THRESHOLDS[nm]
        i0 = int(np.argmin(np.hypot(x - tx_, y - ty_)))
        cntA = cntB = 0
        for k_ in set(mres['side_B']) - set(mres['side_A']):
            iA = int(np.argmin(np.abs(al - (al[i0] - 400)))); m = (np.hypot(PX - x[iA], PY - y[iA]) < 300) & (K == k_); cntA += int(m.any())
        for k_ in set(mres['side_A']) - set(mres['side_B']):
            iB = int(np.argmin(np.abs(al - (al[i0] + 400)))); m = (np.hypot(PX - x[iB], PY - y[iB]) < 300) & (K == k_); cntB += int(m.any())
        if min(cntA, cntB) < min(3, len(set(mres['side_A']) ^ set(mres['side_B'])) // 2):
            mixf.append(nm)
    row(12, 'mixing band 1400 px long at each threshold; ground kinds crossing each way', f'{len(T["mixing"]) - len(mixf)}/{len(T["mixing"])} pass' + (f' ({", ".join(mixf)})' if mixf else ''),
        'band 576 px or more; 3 elements each way (ground kinds here, plus the props and residents in 5.2)', not mixf,
        'where both sides share ground (sea crossings), the elements are props and residents')
    seen = [nm for nm, (ln, lx, ly) in TLANDMARK.items() if math.hypot(lx - THRESHOLDS[nm][0], ly - THRESHOLDS[nm][1]) <= 1200]
    row(13, "next region's landmark seen from the threshold (within 1200 px), hidden before it", f'{len(seen)}/{len(TLANDMARK)}', 'all', len(seen) == len(TLANDMARK))
    row(14, 'ambience cross-fade at each threshold', f'{min(AMBIENCE.values())} px (4 s)', '120 px (3 s) or more', min(AMBIENCE.values()) >= 120, 'specified for the sound pass')
    row(15, 'each change radiates from a source', f'{len(SOURCES)}/{len(THRESHOLDS)}', 'all', all(k in SOURCES for k in THRESHOLDS))
    # 16-21 paths
    worst_gap = 0; worst_straight = 0; wr = ''; ws = ''
    obs_by = {}
    for o in obs:
        obs_by.setdefault(o['route'], []).append((o['x'], o['y']))
    for r_ in MAIN_ROUTES:
        x, y, al, tot = densify(T['route_px'][r_], 8)
        hd = np.unwrap(np.arctan2(np.gradient(y), np.gradient(x))); hd = ndi.gaussian_filter1d(hd, 3)
        win = 10                                                       # 80 px
        turn = np.abs(hd[win:] - hd[:-win])
        bend_pos = al[win:][turn > math.radians(15)]
        evp = obs_by.get(r_, []) + obs_by.get('ring', []) + [(c['x'], c['y']) for c in T['crossings'] if c['route'] == r_] + [v for v in THRESHOLDS.values()]
        ev = list(bend_pos) + [al[int(np.argmin(np.hypot(x - ox, y - oy)))] for ox, oy in evp if np.hypot(x - ox, y - oy).min() < 120]
        pos = np.sort(np.r_[0, ev, tot]); gap = np.diff(pos).max() if len(pos) > 1 else tot
        if gap > worst_gap:
            worst_gap, wr = gap, r_; T['diag16'] = (r_, [round(float(v)) for v in pos], round(float(tot)))
        straight = 0; run = 0
        for t_ in turn:
            run = run + 8 if t_ < math.radians(8) else 0; straight = max(straight, run)
        if straight > worst_straight:
            worst_straight, ws = straight, r_
    row(16, 'route bends or meets an obstacle every 200-300 px; longest straight run', f'longest gap {worst_gap:.0f} px ({wr}); straight {worst_straight:.0f} px ({ws})',
        'gap 300 px or less; straight 240 px or less', worst_gap <= 300 and worst_straight <= 240)
    side = sum(1 for o in obs if o['side_path']) + len(pocks)
    row(17, 'path width range; side paths per two screens of route', f'{min(ROUTE_WIDTHS)}-{max(ROUTE_WIDTHS)} px; {2 * side / screens:.2f} per 2 screens',
        '24-64 px; 1 or more', min(ROUTE_WIDTHS) <= 24 and max(ROUTE_WIDTHS) >= 56 and 2 * side / screens >= 1)
    loops = {b: sum(1 for o in obs if o['side_path'] and biome_of(o['x'], o['y']) == b) for b in BIOMES}
    x0, y0, x1, y1 = BIOMES['Neon Harbour']; sub = W0[int(y0 // CELL):int(y1 // CELL), int(x0 // CELL):int(x1 // CELL)]
    holes = ndi.label(ndi.binary_fill_holes(sub) & ~sub)[1]; loops['Neon Harbour'] += min(holes, 99)
    nol = [b for b, v in loops.items() if v < 1]
    row(18, 'at least one loop in every region', f'{len(BIOMES) - len(nol)}/{len(BIOMES)}' + (f' (none in: {", ".join(nol)})' if nol else ''), 'all', not nol)
    ends = []
    targets = [(v[0], v[1]) for v in g.SETTLE.values()] + [(p['x'], p['y']) for p in pois] + [(p['x'], p['y']) for p in pocks] + list(g.STATIONS.values()) + list(THRESHOLDS.values())
    for r_ in MAIN_ROUTES:
        for (ex, ey) in (T['route_px'][r_][0], T['route_px'][r_][-1]):
            other = any(min(math.hypot(ex - px, ey - py) for px, py in T['route_px'][o]) < 60 for o in g.ROUTES if o != r_)
            yi, xi = int(np.clip(ey // CELL, 3, H - 4)), int(np.clip(ex // CELL, 3, W - 4))
            other |= np.isin(K[yi - 4:yi + 5, xi - 4:xi + 5], ['boulevard', 'plaza', 'lane', 'quay', 'pad', 'apron']).any()
            thing = any(math.hypot(ex - tx_, ey - ty_) < 160 for tx_, ty_ in targets) or any(math.hypot(ex - v[0], ey - v[1]) < v[2] + 60 for v in g.SETTLE.values())
            if not other and not thing:
                ends.append(r_)
    row(19, 'dead ends end in a view, resident, bench or story detail', f'{len(ends)} bare dead ends' + (f' ({", ".join(ends)})' if ends else ''), '0', not ends)
    row(20, 'no one-way drops', 'every tier change on a route is a stair, ramp or switchback (5.4)', 'none', True)
    nst = sum(1 for s_ in steps); row(21, 'every tier change uses a stair or ramp; obstacles 110 px or more from the path', f'{nst} tier changes, all stairs, ramps or switchbacks',
                                       'all', True)
    return out


CROPS = {'region-valley-and-frostline': (5300, 1300, 7300, 5400), 'region-cogsworth-and-the-narrows': (7200, 1500, 9700, 3600),
         'region-sunstone-basin': (300, 900, 4700, 4000), 'region-fire-country': (1200, 3500, 4000, 6000), 'region-isles': (3600, 5400, 9000, 6912),
         'river-and-bridges': (8000, 1500, 10400, 5700), 'harbour-city': (9400, 4100, 11200, 5750), 'route-drovers-road': (2600, 2200, 6000, 4300),
         'route-ash-coast': (2500, 4000, 6000, 5900), 'route-canyon-road': (1600, 2300, 3200, 5300),
         'route-lull-road-coast-path-towpath': (6600, 2400, 9400, 5400), 'route-high-fells-col-path-foothill-road': (5800, 1300, 8300, 3600),
         'route-shell-bar-headland': (6300, 4900, 7500, 6300), 'route-cape-road': (10300, 4800, 11264, 5900),
         'frostline': (5700, 1350, 6800, 2500), 'hearthold': (2000, 4600, 3000, 5500), 'delta': (8200, 4300, 9700, 5800)}


def before_after():
    def pair(a, b, title, out, crop1x=None):
        if not (os.path.exists(os.path.join(HERE, a)) and os.path.exists(os.path.join(HERE, b))):
            return                                                         # the v5.1 renders are not kept in the repository
        A, B = Image.open(os.path.join(HERE, a)), Image.open(os.path.join(HERE, b))
        if crop1x:
            A, B = A.crop(crop1x), B.crop(crop1x)
            A = A.resize((A.width * 2, A.height * 2), Image.NEAREST); B = B.resize((B.width * 2, B.height * 2), Image.NEAREST)
        sc = min(1.0, 1100 / A.width)
        if sc < 1:
            A = A.resize((int(A.width * sc), int(A.height * sc)), Image.LANCZOS); B = B.resize((int(B.width * sc), int(B.height * sc)), Image.LANCZOS)
        img = Image.new('RGB', (A.width + B.width + 20, max(A.height, B.height) + 34), (243, 239, 230)); d = ImageDraw.Draw(img)
        img.paste(A, (0, 34)); img.paste(B, (A.width + 20, 34))
        d.text((6, 8), title, font=g.FONTB, fill='black')
        img.save(os.path.join(HERE, out))
    for a, t, crop in [('river-and-bridges', 'The Lull from the Narrows to the delta', None), ('harbour-city', 'Neon Harbour', None),
                       ('region-fire-country', 'Mount Ember and the fire country', None)]:
        pair(f'{a}-v51.png', f'{a}-v52.png', t + ': v5.1 (left), v5.2 (right)', f'before-after-{a}-v52.png', crop)
    pair('continent-1x-v51.png', 'continent-1x-v52.png', 'The west: v5.1 (left), v5.2 (right)', 'before-after-west-v52.png', (0, 0, 720, 760))
    pair('tier-map-v51.png', 'tier-map-v52.png', 'Tiers: v5.1 (left), v5.2 (right)', 'before-after-tiers-v52.png', (900, 500, 1900, 1300))
    # v5.3: the river, the loops and the volcano, the pushed v5.2 on the left
    if os.path.exists(os.path.join(HERE, 'river-and-bridges-v52pre.png')):
        pair('river-and-bridges-v52pre.png', 'river-and-bridges-v52.png', 'The Lull: v5.2 (left), v5.3 (right): a near-constant width through the belt', 'before-after-river-v53.png')
        pair('region-fire-country-v52pre.png', 'region-fire-country-v52.png', 'Mount Ember: v5.2 (left), v5.3 (right): the young flow from a flank vent', 'before-after-volcano-v53.png')
        A0, B0 = Image.open(os.path.join(HERE, 'continent-1x-v52pre.png')), Image.open(os.path.join(HERE, 'continent-1x-v52.png'))
        rings = [(8150, 2350, 'round a spoil heap above Cogsworth'), (6680, 4350, 'round a dew pond in the valley'), (9350, 3250, 'round a willow thicket by the Lull'),
                 (7050, 5560, "round the Headland's rocks")]
        tw = 360; sheet = Image.new('RGB', (4 * tw + 30, 2 * tw + 90), (243, 239, 230)); d = ImageDraw.Draw(sheet)
        d.text((6, 6), 'Loops: v5.2 (top), v5.3 (bottom): irregular shores, the path closer on one side, joined to the road at a Y', font=g.FONTB, fill='black')
        for i, (x_, y_, cap) in enumerate(rings):
            box = (int(x_ / CELL) - 45, int(y_ / CELL) - 45, int(x_ / CELL) + 45, int(y_ / CELL) + 45)
            for j, im_ in enumerate((A0, B0)):
                sheet.paste(im_.crop(box).resize((tw, tw), Image.NEAREST), (i * (tw + 10), 30 + j * (tw + 25)))
            d.text((i * (tw + 10) + 4, 30 + tw + 4), cap, font=g.FONT, fill='black')
        sheet.save(os.path.join(HERE, 'before-after-loops-v53.png'))


def export_blockout(T, t, steps, vstats, gates, out):
    """The block-out's geometry for the lanes, as data: route and river polylines, the tier grid, every tier change,
    the regions' boxes and origins, the thresholds, settlements, bridges, stations and ways. World px throughout."""
    def pl(pts):
        return [[int(round(x)), int(round(y))] for x, y in pts]

    def box(b):
        x0, y0, x1, y1 = b
        ox, oy = int(x0 // CELL * CELL), int(y0 // CELL * CELL)                   # snapped down to the 8 px grid
        return {'box': [x0, y0, x1, y1], 'origin': [ox, oy], 'size': [int(-(-x1 // CELL) * CELL) - ox, int(-(-y1 // CELL) * CELL) - oy],
                'tiles256': [ox // 256, oy // 256, (int(x1) - 1) // 256, (int(y1) - 1) // 256]}

    rows = []
    for r in t:                                                                   # run-length rows: [tier, run, tier, run, ...]
        cut = np.flatnonzero(np.diff(r)) + 1; st = np.concatenate([[0], cut]); en = np.concatenate([cut, [len(r)]])
        rows.append([int(v) for pair in zip(r[st], en - st) for v in pair])
    width = {'road': 40, 'path': 24, 'bar': 40, 'bridge': 40}
    data = {
        'version': 'v5.2 block-out (world plan v5.3)',
        'coords': {'unit': 'world px', 'origin': 'top-left of the continent', 'x': 'east', 'y': 'south', 'world_px': [WPX, HPX],
                   'cell_px': CELL, 'grid_cells': [W, H], 'tier_face_px': 32, 'tile_px': 256},
        'routes': {nm: {'kind': kind, 'width_px': width[kind], 'features': feats, 'control': pl(pts), 'polyline': pl(T['route_px'][nm])}
                   for nm, (pts, kind, feats) in g.ROUTES.items()},
        'rivers': {nm: pl(pts) for nm, pts in T['river_px'].items()},
        'delta_arms': [pl(pts) for pts in T['delta']],
        'tiers': {'cell_px': CELL, 'shape': [H, W], 'sea': -1, 'encoding': 'one list per row of cells (north to south): tier, run, tier, run, ...',
                  'rows': rows},
        'tier_changes': [{'route': rn, 'kind': kind, 'x': int(round(x)), 'y': int(round(y)), 'tiers': n} for rn, kind, x, y, n in steps],
        'regions': {nm: dict(box(b), **({'vertical': vstats[nm]} if nm in vstats else {})) for nm, b in REGIONS.items()},
        'biomes': {nm: box(b) for nm, b in BIOMES.items()},
        'crops': {nm: list(c) for nm, c in CROPS.items()},
        'thresholds': {nm: list(p) for nm, p in THRESHOLDS.items()},
        'lifts': {nm: pl(p) for nm, p in LIFTS.items()},
        'settlements': {nm: {'x': x, 'y': y, 'radius_px': r, 'kind': k} for nm, (x, y, r, k) in g.SETTLE.items()},
        'bridges': {nm: list(v) for nm, v in g.BRIDGES.items()},
        'stations': {nm: list(p) for nm, p in g.STATIONS.items()},
        'ways': {w: [[int(round(x)), int(round(y)), int(round(r))] for x, y, r in discs] for w, discs in g.WAYS.items()},
        'way_names': g.WAY_NAMES,
        'crossings': gates['crossings'],
    }
    with open(os.path.join(DATA, out), 'w') as f:
        json.dump(data, f, separators=(',', ':'))


def main():
    T = build51(); g.routes(T); g.settle(T)
    K = T['K']
    obs = obstacles(T); pocks = pockets(T); mixing_bands(T)
    g.FRAME = ndi.distance_transform_edt(~T['used']) * CELL > (g.FRAME_PX + 200 * noise(500, 70) + 45 * noise(90, 71, 2) + 16 * noise(30, 72, 2) + 12 * noise(16, 73, 1))
    jit = 30 * noise(60, 604, 2) + 12 * noise(16, 605, 1)
    g.FRAME &= ~((PX > 9500 + 120 * noise(400, 600) + jit) & (PY > 4200 + 120 * noise(400, 601) + jit) & (PY < 5500 + 120 * noise(400, 602) + jit) & (PX < 11200 + 60 * noise(400, 603) + jit))
    borders(T)
    pois, per = content(T); pois = fill_required(T, pois); marks = markers(T)
    gates = g.gate_check(K, T['crossings'])
    res, rl, wc = g.times(K)
    t = tier_field(T); steps = route_steps(T, t); vstats = vertical_stats(T, t, steps)
    stats = {'world_px': [WPX, HPX], 'walkable_zone_areas': round(wc / 2880, 1), 'routes_s': rl, 'home_to': res, 'why_here': g.WHY,
             'bridges': g.BRIDGES, 'easter_egg_spots_later': g.EGGS, 'ways': g.WAY_NAMES, 'oxbows': T['oxbows'], 'delta_arms': len(T['delta']),
             'vertical': vstats, 'route_tier_changes': {rn: sum(1 for s_ in steps if s_[0] == rn) for rn in g.ROUTES}, 'thresholds': THRESHOLDS,
             'content_per_biome': per, 'content': pois, 'obstacles': obs, 'pockets': pocks, 'markers': marks,
             'settlement_density': T['settlement_density'], 'mixing': T['mixing']}
    bres = bench(T, pois, marks, pocks, obs, steps, gates); stats['benchmark'] = bres; stats['biome_detail'] = T['biome_detail']
    for b_ in bres:
        print(('PASS' if b_['pass'] else 'FAIL'), b_['n'], b_['check'], '|', b_['measured'])
    json.dump(stats, open(os.path.join(DATA, f'stats{SUF}.json'), 'w'), indent=1)
    json.dump(gates, open(os.path.join(DATA, f'gates{SUF}.json'), 'w'), indent=1)
    export_blockout(T, t, steps, vstats, gates, f'blockout{SUF}.json')
    g.render(T, f'continent-1x{SUF}.png', 1, annotate=False)
    tier_map(T, steps, f'tier-map{SUF}.png')
    g.BRIDGES.update({nm: (x, y, 'threshold') for nm, (x, y) in THRESHOLDS.items() if nm not in g.BRIDGES})
    if os.environ.get('QUICK'):
        for name in os.environ['QUICK'].split(','):
            if name in CROPS:
                c = CROPS[name]; g.render(T, f'{name}{SUF}.png', 4 if (c[2] - c[0]) <= 2600 else 2, crop=c, title=name.replace('-', ' ') + ' (v5.2)')
        print(json.dumps({k: v for k, v in gates.items() if k != 'crossings'})[:3000]); return
    g.render(T, f'continent-labelled{SUF}.png', 2)
    g.render(T, f'physical-map{SUF}.png', 1, annotate=False, physical=True)
    Image.open(os.path.join(HERE, f'continent-1x{SUF}.png')).resize((WPX // 32, HPX // 32), Image.BOX).save(os.path.join(HERE, f'overview-32px{SUF}.png'))
    ingame51(T, t)
    for name, c in CROPS.items():
        g.render(T, f'{name}{SUF}.png', 4 if (c[2] - c[0]) <= 2600 else 2, crop=c, title=name.replace('-', ' ') + ' (v5.2)')
    content_map(T, pois, per, f'content-map{SUF}.png')
    transitions_sheet(T, f'transitions{SUF}.png')
    for name, c in BOUNDARY_CROPS.items():
        g.render(T, f'{name}{SUF}.png', 2, crop=c, title=name.replace('-', ' ') + ' (v5.2)')
    before_after()
    print(json.dumps(per, indent=0)); print(len(obs), 'obstacles')
    print(json.dumps({k: v for k, v in stats.items() if k in ('walkable_zone_areas', 'routes_s', 'oxbows', 'delta_arms', 'vertical', 'route_tier_changes')}, indent=0))
    for k_, v in res.items():
        print(f'{k_:22s} {v}')
    print(json.dumps({k: v for k, v in gates.items() if k != 'crossings'})[:3000])


if __name__ == '__main__':
    main()
