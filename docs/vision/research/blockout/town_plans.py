"""v55's town plans: each settlement's layout (towns55.py) finished and written as data under towns/<id>.json.

finish() runs after the towns are laid and before the farms round them:
  1. the arrivals: each regional route's part that serves the town, from where it enters the town's box;
  2. the network: the laid street pieces, the squares and the arrivals; a street not joined to an arrival gets a lane to the
     nearest joined street, or is lifted;
  3. access: every building gets a door on the wall nearest its street, and a close (two cells wide) through its yard or
     garden when it stands back from the street; a building no close can reach is lifted with its plot;
  4. the plan: site, streets by class, squares, districts by function, buildings with purpose and occupants, the game layout,
     the ground and a terrain grid of the box, and empty residents and routines for Codex (X3).
The rules (orth, band) and the checker are scripts/review/town_plan.py."""
import heapq
import math
import re

import numpy as np
from scipy import ndimage as ndi

import geo5 as g
from geo5 import CELL
import towns55 as TW

SCHEMA = 'mygame.town_plan/1'
WATER_K = ['sea', 'surf', 'river', 'rapids', 'creek', 'canal', 'oxbow', 'tarn', 'mere', 'channel', 'pool', 'falls', 'lagoon', 'shallows']
BARRIER_K = ['cliff', 'crag', 'wall', 'castlewall', 'lava', 'aa', 'fissure', 'crater', 'shardglass', 'craterrim', 'scorch', 'circle', 'spoil',
             'rockfall', 'closedroad', 'viaduct', 'viapier', 'fence']
GREEN_K = ['meadow', 'watermeadow', 'broadleaf', 'conifer', 'clearing', 'lawn', 'garden', 'wild', 'thicket', 'felltree', 'bramble', 'heath', 'gorse',
           'carr', 'reeds', 'fireweed', 'orchard', 'field', 'field2', 'hedge']
ROUTE_W = {'road': 5, 'path': 3, 'bar': 5, 'bridge': 5, 'trail': 2}
PAD = 120


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower().replace("'", '')).strip('-')


# ------------------------------------------------------------------------------------------ what each town's buildings are for
# per town: shops, workshops, public buildings, inns, and the trades of its households (cycled through its buildings; Codex
# names the people in X3)
TRADES = {
    'crossroads': {'shop': ['the bakery', 'the herbalist', 'the grocer', 'the saddler', 'the draper'], 'workshop': ['the smithy', 'the wheelwright', 'the farrier', 'the cooper'],
                   'public': ['the library', 'the school', 'the meeting hall'], 'inn': ['the Crossed Keys inn'],
                   'home': ['farmhand', 'miller\'s', 'carter\'s', 'shepherd\'s', 'weaver\'s', 'baker\'s', 'drover\'s', 'hurdle-maker\'s', 'retired']},
    'dust-gulch': {'shop': ['the general store', 'the saloon', 'the outfitter', 'the barber', 'the feed store'], 'workshop': ['the repair shop', 'the smithy', 'the harness maker'],
                   'public': ['the assay office', "the sheriff's office (Pendle)", 'the bank', 'the schoolhouse'], 'inn': ['the Railhead hotel'],
                   'home': ['railwayman\'s', 'teamster\'s', 'miner\'s', 'storekeeper\'s', 'muleteer\'s', 'gardener\'s', 'blacksmith\'s']},
    'palm-spring': {'shop': ['the date seller', 'the water seller', 'the spice stall house'], 'workshop': ['the rope and basket maker', 'the saddler'],
                    'public': ["the diviner's house (Mirra)", 'the spring house'], 'inn': ['the caravanserai'],
                    'home': ['gardener\'s', 'date grower\'s', 'caravan guide\'s', 'water carrier\'s', 'herder\'s']},
    'fernhollow': {'shop': ['the village shop', 'the chandler'], 'workshop': ['the joiner', 'the cooper', 'the charcoal burner\'s store', 'the turner'],
                   'public': ['the school', 'the chapel hall'], 'inn': ['the Fern and Axe inn'],
                   'home': ['sawyer\'s', 'forester\'s', 'joiner\'s', 'charcoal burner\'s', 'carter\'s', 'teacher\'s']},
    'cogsworth': {'shop': ['the co-op store', 'the ironmonger', 'the pie shop', 'the tobacconist'], 'workshop': ['the foundry pattern shop', 'the boiler shop', 'the engine works', 'the forge'],
                  'public': ['the works office', 'the institute and reading room', 'the chapel'], 'inn': ['the Engine inn'],
                  'home': ['collier\'s', 'foundryman\'s', 'engine fitter\'s', 'millhand\'s', 'railwayman\'s', 'puddler\'s']},
    'hearthold': {'shop': ['the armourer\'s counter', 'the vintner', 'the potter\'s shop', 'the cloth hall shop'], 'workshop': ['the armourer', 'the smithy', 'the pottery', 'the wine press', 'the glass blower'],
                  'public': ['the guildhall', 'the barracks', 'the chapter house'], 'inn': ['the Gate inn'], 'hall': ["the knights' hall"], 'keep': ['the keep'],
                  'home': ['knight\'s', 'armourer\'s', 'smith\'s', 'potter\'s', 'vintner\'s', 'guard\'s', 'farmer\'s']},
    'cinderwick': {'shop': ['the chandler', 'the fish shop'], 'workshop': ['the glassworks', 'the cooperage', 'the net loft', 'the kiln house'],
                   'public': ['the harbour office'], 'inn': ['the Black Sand inn'],
                   'home': ['fisher\'s', 'glassblower\'s', 'kiln worker\'s', 'boatman\'s']},
    'lagoon-landing': {'shop': ['the chandler', 'the fish market house', 'the dive shop (Brine)'], 'workshop': ['the sail loft', 'the net loft', 'the boatyard shed'],
                       'public': ["the naturalist's house", 'the harbour office'], 'inn': ['the Driftwood Arms'],
                       'home': ['fisher\'s', 'diver\'s', 'boatbuilder\'s', 'net maker\'s', 'ferryman\'s']},
    'highgarth': {'shop': ['the store', 'the wool merchant'], 'workshop': ['the smithy', 'the slate dresser', 'the sawmill shed', 'the weaver'],
                  'public': ['the chapel hall', 'the school'], 'inn': ["the Drovers' inn"],
                  'home': ['quarryman\'s', 'shepherd\'s', 'sawyer\'s', 'weaver\'s', 'drover\'s']},
    'neon-harbour': {'shop': ['a noodle bar', 'a pawn shop', 'a chandler', 'a corner shop', 'a repair stall house', 'a cafe', 'an arcade', 'a tailor'],
                     'workshop': ['a boat engine shop', 'a sign maker', 'a sail loft', 'a cooperage', 'an electrics shop'],
                     'public': ['the ferry office', 'the school', 'the clinic', 'the harbour master'], 'inn': ['the Lantern hotel', 'a boarding house'],
                     'office': ['a Company office', 'a shipping office', 'a bank', 'a trading house'], 'tower': ["the Company's tower", 'an office tower'],
                     'warehouse': ['a bonded warehouse', 'a cold store', 'a goods shed'],
                     'home': ['docker\'s', 'clerk\'s', 'sailor\'s', 'shopkeeper\'s', 'tram driver\'s', 'neon fitter\'s', 'airship crew\'s', 'teacher\'s']},
}
DEFAULT_TRADES = {'shop': ['the shop'], 'workshop': ['the workshop'], 'public': ['the hall'], 'inn': ['the inn'],
                  'home': ['farming', 'fishing', 'carting', 'craft']}
USE_TEXT = {'cottage': 'a cottage', 'house': 'a family house', 'townhouse': 'a terraced townhouse', 'tenement': 'flats round a stair',
            'farmhouse': 'a farmhouse', 'stilt': 'a stilt house over the water', 'chapel': 'the chapel', 'keep': 'the keep', 'hall': 'a hall',
            'mill': 'the mill', 'barn': 'a barn and store', 'warehouse': 'a warehouse', 'station': 'the station', 'boathouse': 'a boathouse',
            'office': 'offices', 'tower': 'a tower', 'hangar': 'a hangar', 'lodge': 'a lodge'}
HOMES = {'cottage', 'house', 'townhouse', 'tenement', 'farmhouse', 'stilt'}
CIVIC = {'shop', 'inn', 'public', 'chapel', 'hall', 'keep'}
WORK = {'workshop', 'mill', 'barn'}
TRANSPORT = {'station', 'warehouse', 'boathouse', 'hangar'}
OFFICE = {'office', 'tower'}

# ------------------------------------------------------------------------------------------ the game layout, per town
# arrival: the route the player first comes in by; first view: what the first screen in shows; landmarks: seen from the
# entries (the checker wants one within two screens of each); later shortcuts; quiet corners next to busy ones.
GAME = {
    'crossroads': {'arrival': 'Valley lane north', 'first_view': 'down the lane from the stone circle into the square: the well in the middle, the bakery and the library either side, the woodland on the right',
                   'landmarks': [('the well and the library on the square', (6296, 3536)), ('the mill on the Sleepwater', (6200, 3905)), ('the halt and its water tank', (5835, 4040)),
                                 ("the inn at the drovers' market", (6712, 3532)), ('your hut and the garden gate', (6316, 3290)),
                                 ("the farrier's forge at Eastgate", (6780, 3420)), ('the weir on Weir Lane', (6400, 4110))],
                   'shortcuts_later': [('the weir footbridge from Weir Lane to the halt farms', (6300, 4100), 'when the miller trusts you (act 2)'),
                                       ('the woodland stile from West Lane to the circle', (5900, 3560), 'after the woodland is cleared')],
                   'quiet_corners': [('the mill green, beside the busy mill yard', (6365, 3905)), ("the library's reading garden off the square", (6250, 3500))]},
    'dust-gulch': {'arrival': "Drover's Road", 'first_view': "Front Street from the east end: the false fronts of the saloon and the store, the depot's water tower over the roofs, the mesa behind",
                   'landmarks': [("the depot's water tower", (2720, 2320)), ('the chapel on West Row', (2300, 2370)), ('the saloon on Front Street', (2600, 2455)),
                                 ('the ore bins on the Lode track', (2650, 2160)), ('the river gardens', (2450, 2650))],
                   'shortcuts_later': [('the dry wash under the line from Corral Lane to the goods yard', (2800, 2400), 'when the stationmaster opens the gate'),
                                       ('the plank bridge over the Amber from Water Street', (2470, 2570), 'after the flood (act 2)')],
                   'quiet_corners': [('the chapel yard behind the busy Front Street', (2290, 2380)), ('the river gardens below Water Street', (2450, 2650))]},
    'palm-spring': {'arrival': "Drover's Road", 'first_view': 'the caravanserai gate and, past it, the spring pool under the palms with steps down to the water',
                    'landmarks': [('the spring pool and its palms', (3282, 2738)), ('the caravanserai', (3420, 2800))],
                    'shortcuts_later': [('the channel path through the date gardens to Palm Row', (3250, 2950), 'when Mirra lets you through the gardens')],
                    'quiet_corners': [('the pool steps, off the busy spring square', (3282, 2700))]},
    'fernhollow': {'arrival': 'Foothill Road', 'first_view': 'out of the trees onto the green: the chapel and the school across it, the sawmill shed and its smoke to the right',
                   'landmarks': [('the chapel on the green', (7230, 3040)), ('the sawmill', (7400, 2975)), ("the charcoal burners' cottages on Fern Lane", (7212, 3280))],
                   'shortcuts_later': [('the timber slide from the wood yards down to Cooper Lane', (7380, 3060), 'when the sawmill runs again')],
                   'quiet_corners': [('the green, beside the noisy sawmill yard', (7232, 3078))]},
    'cogsworth': {'arrival': 'Towpath', 'first_view': "up the towpath road into Engine Street: the foundry's stacks over the brick terraces, the Millrace beside you",
                  'landmarks': [("the foundry's stacks", (8150, 2560)), ('the station and its clock', (8098, 2402)), ('the engine shed', (8380, 2800))],
                  'shortcuts_later': [('the footbridge over the line from Terrace Lane to the pits', (8400, 2620), 'when the works open the gate'),
                                      ('the Millrace culvert from Foundry Row to the river', (8100, 2600), 'once the race is drained')],
                  'quiet_corners': [('the allotments above the terraces, beside the works', (8440, 2500))]},
    'hearthold': {'arrival': 'Ember Way', 'first_view': "up Gate Street from the gate market: the wall on its rock with the gate between two towers, the keep above it, smoke from Smiths' Row to the right",
                  'landmarks': [('the keep on the rock', (2312, 5136)), ('the gate and its towers', (2312, 5416)), ("the smiths' chimneys", (2540, 5470)), ('the gate market', (2312, 5492))],
                  'shortcuts_later': [('the west postern from the castle yard to the Forge Stair', (2184, 5232), 'after the knights accept you'),
                                      ('the vine stair from Smiths\' Row up to the vines', (2560, 5420), 'when the vintner opens her terrace')],
                  'quiet_corners': [('the chapel close inside the wall, beside the drill yard', (2224, 5330)), ('the vines on the cooled ash, above the forges', (2550, 5260))]},
    'cinderwick': {'arrival': 'Ember Way', 'first_view': 'over the roofs to the black-sand cove: the stone quay, boats on the beach, steam from the young flow to the east',
                   'landmarks': [('the stone quay', (2470, 5915)), ('the kilns and their smoke', (2660, 5800))],
                   'shortcuts_later': [('the beach path under the kilns to the Ash Coast', (2680, 5880), 'at low tide')],
                   'quiet_corners': [('the net lofts at the Strand\'s west end, past the busy quay', (2310, 5872))]},
    'lagoon-landing': {'arrival': 'the Driftwood ferry', 'first_view': 'off the ferry at the pier head: the inn and the harbour office, the lagoon bright beyond the roofs',
                       'landmarks': [('the pier head and the inn', (6490, 6420)), ('the lagoon front', (6600, 6555)), ('the boatyard slip', (6810, 6520))],
                       'shortcuts_later': [('stepping stones across the lagoon\'s mouth to the boatyard', (6760, 6560), 'at low tide')],
                       'quiet_corners': [("the naturalist's garden on Net Row, beside the busy pier", (6560, 6470))]},
    'highgarth': {'arrival': 'the Garth Road', 'first_view': 'up the last bend into Garth Street: stepped stone houses on their walls, the market cross, the snow peaks over the roofs',
                  'landmarks': [('the market cross', (7915, 1198)), ('the chapel on Kirk Lane', (7900, 1060)), ('the slate quarry face', (8110, 1110)), ('the sawmill by the Cog', (7705, 1250))],
                  'shortcuts_later': [('the quarry incline down to Low Street', (8040, 1220), 'when the quarry works again'),
                                      ('the Northway past the rockfall', (7815, 545), 'later, with the region north of the range (closed now)')],
                  'quiet_corners': [('the chapel yard above the busy market cross', (7900, 1060))]},
    'neon-harbour': {'arrival': 'Lull Road', 'first_view': 'off the Lull Road at Canalside: the canal basin, the funicular up to the Skyport, the airships over the Heights and the neon of the Company district across the ria',
                     'landmarks': [('the Skyport masts and airships', (10040, 4900)), ("the Company's tower", (11850, 4560)), ('Bridgefoot and the falls', (11135, 4462)),
                                   ('the cranes on the long quay', (11250, 5000)), ('the lido on the East Shore', (12100, 5150)), ('the maglev terminus', (11650, 4565)),
                                   ('the launch tower on the cape', (12125, 6425)), ('the Glintside mills', (11120, 4150)),
                                   ("Canalside's market gardens and the canal", (10000, 4560)), ('Halcyon Row and its canteen', (12020, 5560))],
                     'shortcuts_later': [('the funicular from the canal basin to the Skyport', (10074, 4935), 'when the funicular is repaired'),
                                         ('the skybridge from the Heights over the ria to the old waterfront', (10500, 4600), 'with the Skyport pass'),
                                         ('the maglev from Glintside to the terminus', (11400, 4300), 'with a Company ticket')],
                     'quiet_corners': [('Courtyard Square in the Lanes, between the old waterfront and the Company district', (11470, 4470)),
                                       ('the belvedere on the Heights, over the busy docks', (10200, 5420)), ('the allotments at Glintside', (11170, 4050))]},
}
# how each town sits on its ground (Matt's brief of 27 Oct, the fit to the terrain)
FIT = {'palm-spring': 'the gardens follow the two channels from the spring; houses ring the pool on the dry gravel above them',
       'highgarth': 'the town steps up its terraces on retaining walls: each street on one tier, a stair or a ramp between',
       'hearthold': 'on the one stable rock between the two lava flows; the walls follow the rock\'s rim, the lower town its flank',
       'cogsworth': "homes threaded between the works on the river and the railway: terraces in the strips the works leave",
       'lagoon-landing': 'wrapped round the sheltered lagoon: boathouses and stilt houses on its rim, the pier on the open north shore',
       'neon-harbour': 'the districts blend from the docks on the deep water, through the old waterfront and the Lanes, to the Company flats and up the Heights',
       'dust-gulch': 'on the gravel fan where the Amber leaves the hills: the line and the depot on the flat, homes along the river',
       'crossroads': 'on the flat terraces either side of the Sleepwater where the valley lanes meet; fields on the river terrace',
       'fernhollow': 'in a clearing where Fern Lane meets the Foothill Road: the green in the middle, the woods round it',
       'cinderwick': 'on the cove\'s slope above the black sand: the Strand on the beach, Kiln Lane above it, terraced'}
# the ground each town is made of (item d: painted from these kinds)
GROUND = {
    'neon-harbour': {'old waterfront': 'worn cobbles and stone quays', 'Company district': 'wide composite slab paving in cell-aligned modules, light strips along the cell edges, flush tram and maglev tracks, planters',
                     'the Lanes': 'narrow patched paving, cable runs, awnings and stalls', 'docks': 'steel deck plates, crane rails, painted loading bays',
                     'Heights': 'terraces, stairs and raised walks to the Skyport; the maglev on its viaduct', 'green': 'only in planned pockets: the park, square trees, courtyard plants, roof gardens',
                     'edges': 'mudflats and salt marsh at the delta, allotments and market gardens at Canalside, heath, scrub and dunes on the Cape Road; bare rock and concrete apron at the cape'},
    'dust-gulch': {'centre': 'packed sand street, boardwalks', 'yards': 'sand and adobe yards', 'edges': 'irrigated gardens along the Amber; desert round it'},
    'palm-spring': {'centre': 'packed sand and stone round the pool', 'yards': 'adobe yards', 'edges': 'irrigated green only along the two channels'},
    'hearthold': {'centre': 'basalt setts', 'yards': 'ash and basalt yards', 'edges': 'vines and barley on the old flow\'s weathered ash'},
    'cinderwick': {'centre': 'basalt quay, cinder lanes', 'yards': 'black sand and ash', 'edges': 'the black-sand beach'},
    'highgarth': {'centre': 'slate flags and stone steps', 'yards': 'stone-walled terraces', 'edges': 'walled in-fields and sheepfolds'},
    'cogsworth': {'centre': 'brick setts and cinder paths', 'yards': 'cinder yards', 'edges': 'allotments and spoil'},
    'lagoon-landing': {'centre': 'sand lanes and boardwalks', 'yards': 'sand', 'edges': 'reef shallows in the lagoon'},
    'crossroads': {'centre': 'the square\'s worn paving', 'yards': 'gardens', 'edges': 'fields and orchards on the river terrace'},
    'fernhollow': {'centre': 'packed earth and the green', 'yards': 'wood yards and gardens', 'edges': 'the clearing\'s fields, the woods'},
}


# ------------------------------------------------------------------------------------------ helpers
def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0], float), np.array(pts[-1], float)
    ab = b - a; L = np.hypot(*ab) or 1e-9
    d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / L for p in pts[1:-1]]
    i = int(np.argmax(d)) + 1
    if d[i - 1] > eps:
        return _rdp(pts[:i + 1], eps)[:-1] + _rdp(pts[i:], eps)
    return [pts[0], pts[-1]]


class Net:
    """The street network of one plan, on the plan's box of cells."""

    def __init__(self, box, tp):
        self.c0, self.r0, self.w, self.h = box
        self.tp = tp
        self.ids = np.full((self.h, self.w), -1, int)
        self.elems = []                         # dicts: id, kind ('street', 'square', 'arrival'), mask

    def add(self, el, m):
        el['mask'] = m
        self.elems.append(el)
        self.ids[m & (self.ids < 0)] = len(self.elems) - 1
        return el

    @property
    def mask(self):
        return self.ids >= 0


def finish(T, towns, X):
    """The plans: {plan id: plan dict}; the towns' buildings, closes and lifted orphans changed on T in place."""
    tp = TW._review()
    groups = {}
    for nm, t in towns.items():
        if nm.startswith('Neon Harbour'):
            groups.setdefault('Neon Harbour', []).append(t)
        else:
            groups[nm] = [t]
    plans = {}
    for nm, ts in groups.items():
        p = plan_one(T, nm, ts, X, tp)
        if p:
            plans[p['id']] = p
    return plans


def _box(ts):
    xs, ys = [], []
    for t in ts:
        for b in t.buildings:
            xs += [b['x'], b['x'] + b['w']]; ys += [b['y'], b['y'] + b['h']]
        for s in t.streets:
            for pc in s['pieces']:
                xs += [p[0] for p in pc]; ys += [p[1] for p in pc]
        for q in t.spaces:
            xs += [q['x'] - q['rx'], q['x'] + q['rx']]; ys += [q['y'] - q['ry'], q['y'] + q['ry']]
    if not xs:
        return None
    return [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]


def plan_one(T, name, ts, X, tp):
    K = T['K']; H, W = K.shape
    pid = slug(name)
    fb = _box(ts)
    if fb is None:
        return None
    c0 = max(0, (fb[0] - PAD) // CELL); r0 = max(0, (fb[1] - PAD) // CELL)
    c1 = min(W, (fb[2] + PAD) // CELL + 1); r1 = min(H, (fb[3] + PAD) // CELL + 1)
    box = (c0, r0, c1 - c0, r1 - r0)
    sl = (slice(r0, r1), slice(c0, c1))
    net = Net(box, tp)
    streets_out = []
    # 1. the laid street pieces
    n = 0
    for t in ts:
        for s in t.streets:
            for k, pc in enumerate(s['pieces']):
                n += 1
                sid = f'{pid}-s{n:02d}'
                line = [tuple(v) for v in pc]
                if s['route']:
                    line = [tuple(v) for v in _rdp([list(v) for v in line], 2.0)]
                m = tp.band(line, s['width_cells'], s['metric'], box)
                nmx = s['name'] or None
                if nmx and len(s['pieces']) > 1:
                    nmx = f'{nmx} ({k + 1})'
                el = {'id': sid, 'kind': 'street', 'name': nmx, 'class': s['cls'], 'width_cells': s['width_cells'], 'vertices_px': [list(v) for v in line],
                      'follows_route': s['route'], 'district_town': t.name}
                net.add(el, m)
    for t in ts:
        for j, q in enumerate(t.spaces):
            if 'cells' not in q:
                continue
            cx, cy, cw, ch = q['cells']
            m = np.zeros((box[3], box[2]), bool)
            m[max(0, cy - r0):cy - r0 + ch, max(0, cx - c0):cx - c0 + cw] = True
            m &= T['street'][sl]
            if not m.any():
                continue
            net.add({'id': f'{pid}-q{len([e for e in net.elems if e["kind"] == "square"]) + 1:02d}', 'kind': 'square', 'name': q['name'], 'type': q['kind'],
                     'cells': [int(v) for v in q['cells']], 'district_town': t.name}, m)
    # the built zone's own plan (Crossroads): its routes and places are the town's centre; the valley lanes stop at its edge
    zbox = None
    if any(b.get('plan') for t in ts for b in t.buildings):
        import json, os
        zp = json.load(open(os.path.join(X.ROOT, 'game', 'data', 'plans', 'crossroads.json')))
        ox, oy = zp['origin_on_canvas']; zbox = (ox, oy, ox + zp['box'][2], oy + zp['box'][3])
    # 2. the arrivals
    rmask = np.isin(K[sl], list(TW.ROUTE))
    rdt = ndi.distance_transform_edt(rmask)
    near = ndi.distance_transform_edt(~(net.mask | _bmask(ts, box))) if (net.mask.any() or ts[0].buildings) else None
    arrivals = []
    for rn, pts in T['route_px'].items():
        if rn not in g.ROUTES or 'closed' in rn:
            continue
        kind = g.ROUTES[rn][1]
        inside = [(x >= c0 * CELL and x < c1 * CELL and y >= r0 * CELL and y < r1 * CELL) and not (zbox and zbox[0] <= x < zbox[2] and zbox[1] <= y < zbox[3])
                  for x, y in pts]
        runs, cur = [], []
        for i, ok in enumerate(inside):
            if ok:
                cur.append(i)
            elif cur:
                runs.append(cur); cur = []
        if cur:
            runs.append(cur)
        for run in runs:
            if len(run) < 3:
                continue
            seg = [pts[i] for i in run]
            cc = [(int(y // CELL) - r0, int(x // CELL) - c0) for x, y in seg]
            dmin = min(near[r, c] for r, c in cc if 0 <= r < box[3] and 0 <= c < box[2])
            if dmin > 6:
                continue
            th = [2 * rdt[r, c] - 1 for r, c in cc if 0 <= r < box[3] and 0 <= c < box[2] and rdt[r, c] > 0]
            wc = int(max(2, min(ROUTE_W.get(kind, 3), np.percentile(th, 10) if th else 2)))
            entries = []
            if zbox:                                                   # the end at the zone's edge is where the zone takes over
                pass
            if run[0] > 0 and not _in(pts[run[0] - 1], zbox):
                entries.append([int(round(seg[0][0])), int(round(seg[0][1]))])
            if run[-1] < len(pts) - 1 and not _in(pts[run[-1] + 1], zbox):
                entries.append([int(round(seg[-1][0])), int(round(seg[-1][1]))])
            line = [tuple(v) for v in _rdp([[float(a), float(b)] for a, b in seg], 2.0)]
            aid = f'{pid}-a{len(arrivals) + 1}'
            m = tp.band(line, wc, 'euclid', box)
            bm_ = _bmask(ts, box)
            while wc > 2 and (m & bm_).any():                          # never wider than the route is drawn beside a building
                wc -= 1; m = tp.band(line, wc, 'euclid', box)
            el = net.add({'id': aid, 'kind': 'arrival', 'name': rn, 'class': 'arrival', 'width_cells': wc, 'vertices_px': [[round(a, 1), round(b, 1)] for a, b in line],
                          'follows_route': rn}, m)
            arrivals.append({'id': f'{pid}-arr{len(arrivals) + 1}', 'kind': 'road' if kind == 'road' else 'path', 'route': rn, 'street': aid,
                             'entries_px': entries, 'route_kind': kind})
    for t in ts:
        if t.name == 'Lagoon Landing':                                 # the isles' town is reached by the ferry from Driftwood
            st = g.STATIONS.get('Lagoon pier')
            sx, sy = (st[0], st[1]) if st else (6480, 6406)
            pe = [e for e in net.elems if e.get('name') == 'the Pier']
            if pe:
                v = min(pe[0]['vertices_px'], key=lambda q: q[1])
                pier = [(float(v[0]), float(v[1])), (float(v[0]), float(v[1]) - 3 * CELL)]
            else:
                pier = [(float(sx), float(sy)), (6488.0, 6420.0)]
            aid = f'{pid}-a{len(arrivals) + 1}'
            net.add({'id': aid, 'kind': 'arrival', 'name': 'the ferry landing', 'class': 'arrival', 'width_cells': 2, 'vertices_px': [list(v) for v in pier],
                     'follows_route': None}, tp.band(pier, 2, 'euclid', box))
            sx, sy = pier[1]
            arrivals.append({'id': f'{pid}-arr{len(arrivals) + 1}', 'kind': 'ferry', 'route': 'the Driftwood ferry', 'station': 'Lagoon pier',
                             'street': aid, 'entries_px': [[int(sx), int(sy)]], 'route_kind': 'ferry'})
    # 3. joined to an arrival: orphans get a lane, or are lifted
    pass_ = _passable(T, sl, ts)
    _join(T, net, arrivals, pass_, sl, pid, box, ts)
    # 4. access: doors and closes
    dropped = _access(T, net, pass_, sl, pid, box, ts)
    # 5. no street that serves nothing, no empty block: unused unnamed streets lifted, thin blocks built up or given a named use
    _prune(T, net, sl, ts)
    opens = _blocks(T, net, sl, pid, box, ts)
    dropped += _access(T, net, _passable(T, sl, ts), sl, pid, box, ts)
    if len(ts) > 1:
        _city_paving(T, net, sl, box, ts)
    # 6. the record
    P = _record(T, name, pid, ts, net, arrivals, box, sl, fb, dropped, X)
    P['open_uses'] = opens
    return P


WILD_GREEN = ['meadow', 'watermeadow', 'broadleaf', 'conifer', 'clearing', 'lawn', 'wild', 'thicket', 'felltree', 'bramble', 'heath', 'gorse', 'carr',
              'reeds', 'fireweed', 'scrub', 'steppe']


def _city_paving(T, net, sl, box, ts):
    """Inside a city, grass and trees only where they are planned (plots, parks, squares, allotments): the rest of the open
    ground within the built envelope becomes paved yards."""
    built = _bmask(ts, box).copy()
    for e in _alive(net, ('street', 'square')):
        built |= e['mask']
    env = ndi.binary_fill_holes(ndi.binary_closing(ndi.distance_transform_edt(~built) <= 8, iterations=6)) & T['land'][sl]
    K = T['K'][sl]
    m = env & np.isin(K, WILD_GREEN) & ~T['taken'][sl]
    K[m] = 'yard'
    return int(m.sum())


def _alive(net, kinds=('street', 'square', 'arrival')):
    return [e for e in net.elems if e.get('alive', True) and e['kind'] in kinds]


def _remove(T, net, sl, el):
    others = np.zeros_like(el['mask'])
    for e in _alive(net):
        if e is not el:
            others |= e['mask']
    _unpaint(T, sl, el['mask'] & ~others)
    el['alive'] = False
    net.ids[net.ids == net.elems.index(el)] = -1
    for e in _alive(net):                                           # cells the removed street shared go back to their owners
        net.ids[e['mask'] & (net.ids < 0)] = net.elems.index(e)
    el['mask'] = np.zeros_like(el['mask'])


def _prune(T, net, sl, ts):
    """Unnamed streets no building faces, no close joins and no other street needs to reach a way in: lifted."""
    for it in range(60):
        faced = {b.get('faces') for t in ts for b in t.buildings}
        changed = False
        for el in _alive(net, ('street',)):
            if el.get('name') or el['class'] in ('close', 'arrival', 'main') or el.get('follows_route') or el['id'] in faced:
                continue
            dm = ndi.binary_dilation(el['mask'], iterations=1)
            if any(e.get('class') == 'close' and (e['mask'] & dm).any() for e in _alive(net, ('street',)) if e is not el):
                continue
            rest = np.zeros_like(el['mask'])
            for e in _alive(net):
                if e is not el:
                    rest |= e['mask']
            lab, n = ndi.label(rest)
            good = set()
            for e in _alive(net, ('arrival',)):
                good |= set(np.unique(lab[e['mask']]).tolist()) - {0}
            ok = all(set(np.unique(lab[e['mask']]).tolist()) - {0} <= good for e in _alive(net, ('street', 'square')) if e is not el and e['mask'].any())
            if ok:
                _remove(T, net, sl, el); changed = True
        if not changed:
            return


BLOCK_FORMS = {'neon-harbour': None, 'dust-gulch': ('adobe', 'adobe', 'workshop'), 'palm-spring': ('adobe', 'cottage'), 'hearthold': ('townhouse', 'workshop'),
               'cinderwick': ('cottage', 'townhouse'), 'cogsworth': ('terrace', 'workshop'), 'highgarth': ('house', 'cottage'), 'lagoon-landing': ('cottage', 'boathouse')}
NEON_FORMS = {'the old waterfront': ('oldhouse', 'oldhouse', 'shop'), 'the docks': ('longwarehouse', 'warehouse'), 'the Lanes and the East Shore': ('aptrow', 'terrace'),
              'the Company district': ('slab', 'bigtower'), 'the Heights and the Skyport': ('townhouse', 'house')}
OPEN_USE = {'the old waterfront': ('a pocket park', 'garden'), 'the docks': ('a stacking yard', 'yard'), 'the Lanes and the East Shore': ('a courtyard', 'yard'),
            'the Company district': ('a planted plaza', 'plaza'), 'the Heights and the Skyport': ('a terrace garden', 'garden')}


def block_masks(streets_m, ter_bad):
    """The blocks between the streets: closed regions of the box not touching its edge (the checker's own rule)."""
    lab, n = ndi.label(~streets_m)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    out = []
    for i in range(1, n + 1):
        if i in edge:
            continue
        m = lab == i
        area = int((m & ~ter_bad).sum())
        if 12 <= area <= 1200:
            out.append(m)
    return out


def _covered(T, net, ts, box):
    c0, r0, w, h = box
    cov = np.zeros((h, w), bool)
    for t in ts:
        for b in t.buildings:
            c, r = b['x'] // CELL - c0, b['y'] // CELL - r0
            cov[max(0, r):max(0, r + b['h'] // CELL), max(0, c):max(0, c + b['w'] // CELL)] = True
            if b.get('plot'):
                px_, py_, pw_, ph_, kind = b['plot']
                cov[max(0, py_ - r0):max(0, py_ - r0 + ph_), max(0, px_ - c0):max(0, px_ - c0 + pw_)] = True
        for o in t.outskirts:
            x0, y0, x1, y1 = o['box']
            cov[max(0, y0 // CELL - r0):max(0, y1 // CELL - r0), max(0, x0 // CELL - c0):max(0, x1 // CELL - c0)] = True
    for e in _alive(net):
        if e['kind'] == 'square' or e.get('class') == 'close':
            cov |= e['mask']
    return cov


def _blocks(T, net, sl, pid, box, ts):
    c0, r0, w, h = box
    K = T['K']
    sub = K[sl]
    ter_bad = np.isin(sub, WATER_K + BARRIER_K + list(TW.ROUTE))
    opens = []
    for it in range(3):
        sm = np.zeros((h, w), bool)
        for e in _alive(net, ('street', 'square')):
            if e.get('class') != 'close':
                sm |= e['mask']
        blocks = block_masks(sm, ter_bad)
        cov = _covered(T, net, ts, box)
        thin = [m for m in blocks if (cov & m & ~ter_bad).sum() < 0.5 * (m & ~ter_bad).sum()]
        if not thin:
            break
        for m in thin:
            rr, cc = np.nonzero(m)
            cy, cx = (rr.mean() + r0 + 0.5) * CELL, (cc.mean() + c0 + 0.5) * CELL
            t = min(ts, key=lambda t: math.hypot(t.centre[0] - cx, t.centre[1] - cy))
            dname = t.name.split(': ', 1)[1] if ': ' in t.name else None
            forms = NEON_FORMS.get(dname) if dname else BLOCK_FORMS.get(pid) or ('house', 'cottage')
            # 1. buildings: on the block's free ground next to its streets, while the town has room
            if it < 2 and forms:
                edge_d = ndi.distance_transform_edt(m)
                order = sorted(((r_, c_) for r_, c_ in zip(rr.tolist(), cc.tolist()) if edge_d[r_, c_] <= 2), key=lambda q: (edge_d[q], q))
                k = 0
                for (r, c) in order[::2]:
                    if (cov & m & ~ter_bad).sum() >= 0.5 * (m & ~ter_bad).sum() or t.count() >= t.cap:
                        break
                    form = forms[k % len(forms)]
                    (w0, w1), (d0, d1) = TW.BLD[form]
                    for ww, dd in (((w0 + w1) // 2, (d0 + d1) // 2), ((d0 + d1) // 2, (w0 + w1) // 2)):
                        wc_, dc_ = int(round(ww / CELL)), int(round(dd / CELL))
                        for (ra, ca) in ((r, c), (r - dc_ + 1, c), (r, c - wc_ + 1), (r - dc_ + 1, c - wc_ + 1)):
                            if ra < 0 or ca < 0 or ra + dc_ > h or ca + wc_ > w or not m[ra:ra + dc_, ca:ca + wc_].all():
                                continue
                            if t.put((ca + c0) * CELL, (ra + r0) * CELL, wc_ * CELL, dc_ * CELL, form, True):
                                cov[ra:ra + dc_, ca:ca + wc_] = True; k += 1
                                break
                        else:
                            continue
                        break
            # 2. what is still open: a named use (a park, a yard, a courtyard, a corral, allotments)
            if it == 2 or (cov & m & ~ter_bad).sum() < 0.5 * (m & ~ter_bad).sum():
                if it < 1:
                    continue
                nm, kind = OPEN_USE.get(dname, (('a corral' if pid in ('dust-gulch', 'palm-spring', 'the-lode') else 'allotments'),
                                                ('yard' if pid in ('dust-gulch', 'palm-spring', 'the-lode') else 'garden')))
                free = m & ~cov & ~ter_bad & ~T['taken'][sl] & np.isin(sub, list(TW.BUILDABLE)) & ~np.isin(sub, ['building', 'warehouse', 'tower', 'keep', 'hangar', 'terminal'])
                if free.any():
                    sub[free] = kind
                    fr, fc = np.nonzero(m)
                    opens.append({'id': f'{pid}-o{len(opens) + 1:02d}', 'name': nm, 'kind': kind,
                                  'cells': [int(fc.min() + c0), int(fr.min() + r0), int(fc.max() - fc.min() + 1), int(fr.max() - fr.min() + 1)],
                                  'block_cells': int((m & ~ter_bad).sum())})
                    cov |= m
    return opens



def _in(p, zb):
    return bool(zb) and zb[0] <= p[0] < zb[2] and zb[1] <= p[1] < zb[3]


def _bmask(ts, box):
    c0, r0, w, h = box
    m = np.zeros((h, w), bool)
    for t in ts:
        for b in t.buildings:
            c, r = b['x'] // CELL - c0, b['y'] // CELL - r0
            m[max(0, r):max(0, r + b['h'] // CELL), max(0, c):max(0, c + b['w'] // CELL)] = True
    return m


def _passable(T, sl, ts):
    K = T['K'][sl]
    ok = np.isin(K, list(TW.STREETABLE)) & ~np.isin(K, ['building', 'warehouse', 'tower', 'keep', 'hangar', 'terminal'])
    ok &= ~T['taken'][sl] & ~T['keepout'][sl]
    ok &= ~np.isin(K, BARRIER_K + WATER_K)
    return ok


def _dijkstra(pas, starts, goal, k, limit=140, turn=4):
    """A path of k x k blocks (top-left cells) from any start block to a block touching goal; returns the block list."""
    h, w = pas.shape
    S = np.lib.stride_tricks.sliding_window_view(pas, (k, k)).all(axis=(2, 3))     # block passable
    G = np.lib.stride_tricks.sliding_window_view(goal, (k, k)).any(axis=(2, 3))
    bh, bw = S.shape
    dist = {}
    pq = []
    for (r, c) in starts:
        if 0 <= r < bh and 0 <= c < bw and S[r, c]:
            for d in range(4):
                heapq.heappush(pq, (0, r, c, d, None))
    prev = {}
    seen = set()
    while pq:
        cost, r, c, d, pr = heapq.heappop(pq)
        if (r, c, d) in seen:
            continue
        seen.add((r, c, d)); prev[(r, c, d)] = pr
        if G[r, c]:
            path = []; st = (r, c, d)
            while st is not None:
                path.append((st[0], st[1])); st = prev[st]
            out = []
            for p in path[::-1]:
                if not out or out[-1] != p:
                    out.append(p)
            return out
        if cost > limit:
            continue
        for nd, (dr, dc) in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
            rr, cc = r + dr, c + dc
            if 0 <= rr < bh and 0 <= cc < bw and S[rr, cc] and (rr, cc, nd) not in seen:
                heapq.heappush(pq, (cost + 1 + (turn if (pr is not None and nd != d) else 0), rr, cc, nd, (r, c, d)))
    return None


def _path_line(path, k, box):
    c0, r0, _, _ = box
    pts = [((c + c0 + k / 2) * CELL, (r + r0 + k / 2) * CELL) for r, c in path]
    out = [pts[0]]
    for i in range(1, len(pts)):
        if len(out) >= 2 and ((out[-2][0] == out[-1][0] == pts[i][0]) or (out[-2][1] == out[-1][1] == pts[i][1])):
            out[-1] = pts[i]
        else:
            out.append(pts[i])
    return [(float(a), float(b)) for a, b in out]


def _paint(T, sl, m, box):
    K = T['K'][sl]
    pm = m & ~np.isin(K, list(TW.ROUTE)) & ~np.isin(K, WATER_K)
    K[pm] = 'lane'
    T['street'][sl] |= m; T['used'][sl] |= m


def _unpaint(T, sl, m):
    K = T['K'][sl]; K0 = T['K0'][sl]
    nat = np.where(np.isin(K0, ['sea', 'river', 'canal', 'road', 'path', 'bridge', 'stair', 'creek']), 'meadow', K0)
    nat = np.where(np.isin(nat, ['wild', 'ancient', 'thicket', 'felltree']), 'broadleaf', nat)
    mm = m & ~np.isin(K, list(TW.ROUTE)) & ~np.isin(K, WATER_K)
    K[mm] = nat[mm]
    T['street'][sl] &= ~m


def _join(T, net, arrivals, pas, sl, pid, box, ts):
    for it in range(40):
        lab, n = ndi.label(net.mask)
        good = set()
        for el in net.elems:
            if el['kind'] == 'arrival':
                good |= set(np.unique(lab[el['mask']]).tolist()) - {0}
        bad = [el for el in net.elems if el.get('alive', True) and el['kind'] != 'arrival'
               and not (set(np.unique(lab[el['mask']]).tolist()) - {0}) & good]
        if not bad or not good:
            return
        el = bad[0]
        comp = set(np.unique(lab[el['mask']]).tolist()) - {0}
        cm = np.isin(lab, list(comp))
        goal = np.isin(lab, list(good))
        p2 = pas | cm | goal
        rr, cc = np.nonzero(cm)
        starts = list(zip((rr - 1).tolist(), (cc - 1).tolist()))[::3]
        path = _dijkstra(p2, starts, goal, 3, limit=90)
        if path:
            line = _path_line(path, 3, box)
            if len(line) >= 2:
                m = net.tp.band(line, 3, 'cheb', box)
                _paint(T, sl, m, box)
                net.add({'id': f'{pid}-s{len(net.elems) + 1:02d}', 'kind': 'street', 'name': None, 'class': 'lane', 'width_cells': 3,
                         'vertices_px': [list(v) for v in line], 'follows_route': None, 'link': True}, m)
                continue
        # lifted: an orphan no lane can join
        for e in net.elems:
            if e['kind'] != 'arrival' and (set(np.unique(lab[e['mask']]).tolist()) & comp):
                _unpaint(T, sl, e['mask'])
                e['alive'] = False
                net.ids[net.ids == net.elems.index(e)] = -1
                e['mask'] = np.zeros_like(e['mask'])


def _ring(c, r, cw, ch):
    out = []
    for x in range(c, c + cw):
        out += [(r - 1, x, 'n'), (r + ch, x, 's')]
    for y in range(r, r + ch):
        out += [(y, c - 1, 'w'), (y, c + cw, 'e')]
    return out


def _access(T, net, pas, sl, pid, box, ts):
    c0, r0, w, h = box
    occ = _bmask(ts, box)
    dropped = []
    items = []
    for t in ts:
        for b in t.buildings:
            items.append((t, b))
    for it in range(2):
        dt, (iy, ix) = ndi.distance_transform_edt(~net.mask, return_indices=True)
        order = []
        for t, b in items:
            if b.get('zone_door') and not b.get('door'):          # the zone plan's own door, onto its nearest route or place
                dx_, dy_ = b['zone_door'][0] // CELL, b['zone_door'][1] // CELL
                best = min(((np.maximum(np.abs(rr - (dy_ - r0)), np.abs(cc - (dx_ - c0))).min(), e["id"]) for e in net.elems if e.get('alive', True)
                            for rr, cc in [np.nonzero(e['mask'])] if len(rr)), default=None)
                if best:
                    b['door'] = [int(dx_), int(dy_)]; b['faces'] = best[1]
            if b.get('door'):
                continue
            c, r, cw, ch = b['x'] // CELL - c0, b['y'] // CELL - r0, b['w'] // CELL, b['h'] // CELL
            ring = [(y, x, s) for y, x, s in _ring(c, r, cw, ch) if 0 <= y < h and 0 <= x < w]
            if not ring:
                continue
            dmin = min(dt[y, x] for y, x, s in ring)
            order.append((dmin, id(b), t, b, c, r, cw, ch, ring))
        order.sort(key=lambda o: o[0])
        for dmin, _, t, b, c, r, cw, ch, ring in order:
            # a door within three cells of a street, with clear ground between
            best = None
            for y, x, s in ring:
                if dt[y, x] <= 3.01:
                    ty, tx = iy[y, x], ix[y, x]
                    n_ = int(max(abs(ty - y), abs(tx - x))) + 1
                    line = [(int(round(y + (ty - y) * k / max(1, n_))), int(round(x + (tx - x) * k / max(1, n_)))) for k in range(n_ + 1)]
                    if any(occ[a, b_] for a, b_ in line):
                        continue
                    mid = abs((x - c) - cw / 2) + abs((y - r) - ch / 2)
                    key = (dt[y, x], mid)
                    if best is None or key < best[0]:
                        best = (key, y, x, net.elems[net.ids[ty, tx]]['id'])
            if best:
                _, y, x, fid = best
                b['door'] = [int(x + c0), int(y + r0)]; b['faces'] = fid
                continue
            if it == 0:
                continue                                       # the second pass, after the near ones, lays the closes
            # a close: two cells wide from the wall to the nearest street
            starts = []
            for y, x, s in ring:
                for dy in (-1, 0):
                    for dx in (-1, 0):
                        starts.append((y + dy, x + dx))
            pas2 = pas & ~occ
            path = _dijkstra(pas2 | net.mask, starts, net.mask, 2, limit=70)
            if path:
                line = _path_line(path, 2, box)
                m = net.tp.band(line, 2, 'cheb', box) if len(line) >= 2 else None
                if m is not None and not (m & occ).any():
                    _paint(T, sl, m, box)
                    el = net.add({'id': f'{pid}-c{len([e for e in net.elems if e.get("class") == "close"]) + 1:02d}', 'kind': 'street', 'name': None,
                                  'class': 'close', 'width_cells': 2, 'vertices_px': [list(v) for v in line], 'follows_route': None}, m)
                    # the door: the ring cell inside the close's first block
                    r_, c_ = path[0]
                    cand = [(y, x) for y, x, s in ring if r_ <= y <= r_ + 1 and c_ <= x <= c_ + 1]
                    if not cand:
                        cand = [min(((y, x) for y, x, s in ring), key=lambda p: (p[0] - r_) ** 2 + (p[1] - c_) ** 2)]
                    y, x = cand[0]
                    b['door'] = [int(x + c0), int(y + r0)]; b['faces'] = el['id']
                    dt, (iy, ix) = ndi.distance_transform_edt(~net.mask, return_indices=True)
                    continue
            # lifted: no way in
            dropped.append(dict(b, town=t.name))
            a_, b_ = b['y'] // CELL, b['x'] // CELL
            bm = np.zeros(T['K'].shape, bool); bm[a_:a_ + b['h'] // CELL, b_:b_ + b['w'] // CELL] = True
            if b.get('plot'):
                px_, py_, pw_, ph_, kind = b['plot']
                pm = np.zeros(T['K'].shape, bool); pm[py_:py_ + ph_, px_:px_ + pw_] = True
                pm &= T['K'] == kind
                bm |= pm
            _unpaint(T, (slice(None), slice(None)), bm)
            T['taken'][a_:a_ + b['h'] // CELL, b_:b_ + b['w'] // CELL] = False
            occ[max(0, a_ - r0):a_ - r0 + b['h'] // CELL, max(0, b_ - c0):b_ - c0 + b['w'] // CELL] = False
            t.buildings.remove(b)
            items = [(tt, bb) for tt, bb in items if bb is not b]
    return dropped


def terrain_rows(sub):
    """The box's ground as one character a cell, run-length coded per row."""
    code = np.full(sub.shape, '.', dtype='<U1')
    code[np.isin(sub, GREEN_K)] = 'g'
    code[np.isin(sub, list(TW.ROUTE))] = 'r'
    code[np.isin(sub, WATER_K)] = '~'
    code[np.isin(sub, BARRIER_K)] = '#'
    code[sub == 'bridge'] = 'b'
    return TW._review().rle_encode(code)


def _district_fn(uses):
    n = sum(uses.values()) or 1
    share = lambda S: sum(v for k, v in uses.items() if k in S) / n
    sh = {'homes': share(HOMES), 'market and civic': share(CIVIC), 'crafts and work': share(WORK), 'docks and transport': share(TRANSPORT),
          'offices and trade': share(OFFICE)}
    if sh['homes'] >= 0.7:
        return 'homes'
    best = max((k for k in sh if k != 'homes'), key=lambda k: sh[k])
    if sh[best] == 0:
        return 'homes'
    return best + (' with homes' if sh['homes'] >= 0.3 else '')


def _record(T, name, pid, ts, net, arrivals, box, sl, fb, dropped, X):
    K = T['K']; c0, r0, w, h = box
    tr = TRADES.get(pid, DEFAULT_TRADES)
    lead = ts[0]
    # districts
    dists = []
    if len(ts) > 1:
        for t in ts:
            if t.name.endswith('the Lanes and the East Shore'):        # two places, one district each
                for nb in t.neighbourhoods:
                    dists.append({'name': nb[0], 'centre_px': [int(nb[2]), int(nb[3])], 'declared': nb[1], 'town': t.name})
                continue
            dists.append({'name': t.name.split(': ', 1)[1], 'centre_px': list(map(int, t.centre)), 'declared': t.purpose, 'town': t.name})
    else:
        for nb in lead.neighbourhoods:
            dists.append({'name': nb[0], 'centre_px': [int(nb[2]), int(nb[3])], 'declared': nb[1], 'town': lead.name})
        if not dists:
            dists.append({'name': lead.name, 'centre_px': list(map(int, lead.centre)), 'declared': lead.purpose, 'town': lead.name})
    for d in dists:
        d['id'] = f"{pid}-d-{slug(d['name'])}"; d['buildings'] = []
    # buildings
    bl = []
    cyc = {}

    def nxt(key, default):
        L = tr.get(key) or default
        i = cyc.get(key, 0); cyc[key] = i + 1
        return L[i % len(L)]
    nb_ = 0
    for t in ts:
        for b in t.buildings:
            nb_ += 1
            bid = f'{pid}-b{nb_:03d}'
            cx, cy = b['x'] + b['w'] / 2, b['y'] + b['h'] / 2
            cand = [d for d in dists if d['town'] == t.name] or dists
            d = min(cand, key=lambda d: math.hypot(d['centre_px'][0] - cx, d['centre_px'][1] - cy))
            u = b['use']
            if u in HOMES:
                occ = f"a {nxt('home', DEFAULT_TRADES['home'])} household" + (' (several, one to a floor)' if u == 'tenement' else '')
                purpose = USE_TEXT[u]
            elif u in ('shop', 'workshop', 'public', 'inn', 'office', 'warehouse', 'hall', 'keep'):
                purpose = nxt(u, [USE_TEXT.get(u, u)])
                occ = {'shop': 'the shopkeeper, living above', 'workshop': 'the master and apprentices', 'public': 'staff by day',
                       'inn': 'the innkeeper, staff and guests', 'office': 'clerks by day', 'warehouse': 'porters by day, a night watch',
                       'hall': 'its order or guild', 'keep': 'the lord, the household and the guard'}[u]
            else:
                purpose = USE_TEXT.get(u, u)
                occ = {'chapel': 'the priest, living beside it', 'mill': 'the miller and family', 'barn': 'the farm', 'station': 'the station staff',
                       'boathouse': 'a boat owner', 'tower': 'offices and the Company', 'hangar': 'ground crew', 'lodge': 'the keeper'}.get(u, 'its keepers')
            rec = {'id': bid, 'type': u, 'form': b.get('form', u), 'footprint_cells': [b['x'] // CELL, b['y'] // CELL, b['w'] // CELL, b['h'] // CELL],
                   'rect_px': [b['x'], b['y'], b['w'], b['h']], 'faces': b.get('faces'), 'door_cells': b.get('door'), 'purpose': purpose,
                   'occupants': occ, 'district': d['id'], 'counted': bool(b['counted'])}
            if b.get('plan'):
                rec['from_zone_plan'] = True
            if b.get('form') in TW.FALSE_FRONT:
                rec['false_front'] = True                          # a tall board front on the street side (size-guide.md 4)
            if b.get('plot'):
                px_, py_, pw_, ph_, kind = b['plot']
                rec['plot_cells'] = [px_, py_, pw_, ph_]; rec['plot'] = kind
            bl.append(rec); d['buildings'].append(bid)
    for d in dists:
        uses = {}
        for bid in d['buildings']:
            u = next(x['type'] for x in bl if x['id'] == bid)
            uses[u] = uses.get(u, 0) + (1 if next(x['counted'] for x in bl if x['id'] == bid) else 0)
        d['mix'] = uses; d['function'] = _district_fn(uses)
    for t in ts:
        for o in t.outskirts:
            fn = 'edge: farms and gardens' if o['kind'] in ('field', 'field2', 'orchard', 'garden') else ('docks and works yards' if any(
                k in (o['name'] or '') for k in ('dock', 'slip', 'yard', 'quay', 'kiln', 'quarry')) else 'edge: yards and pens')
            dists.append({'id': f"{pid}-d-{slug(o['name'] or o['kind'])}", 'name': o['name'], 'function': fn, 'declared': o.get('why'), 'box_px': o['box'],
                          'buildings': [], 'town': t.name})
    # streets
    streets = []
    for el in net.elems:
        if el['kind'] in ('street', 'arrival') and el.get('alive', True):
            s = {k: el[k] for k in ('id', 'name', 'class', 'width_cells', 'vertices_px') if k in el}
            if el.get('follows_route'):
                s['follows_route'] = el['follows_route']
            if el.get('link'):
                s['link'] = True
            streets.append(s)
    # what each street connects
    lab = net.ids
    dil = lambda m: ndi.binary_dilation(m, iterations=1)
    for s in streets:
        el = next(e for e in net.elems if e['id'] == s['id'])
        touch = set(np.unique(lab[dil(el['mask'])]).tolist()) - {-1, net.elems.index(el)}
        s['connects'] = sorted(net.elems[i]['id'] for i in touch if net.elems[i].get('alive', True))
    squares = [{'id': e['id'], 'name': e['name'], 'type': e['type'], 'cells': e['cells']} for e in net.elems if e['kind'] == 'square' and e.get('alive', True)]
    gathering = []
    for t in ts:
        for gp in t.gathering:
            gathering.append({'name': gp[0], 'xy_px': [int(gp[1]), int(gp[2])]})
    # the game layout
    GL = GAME.get(pid)
    entries = [e for a in arrivals for e in a['entries_px']]
    if GL:
        lms = [{'name': n_, 'xy': list(xy)} for n_, xy in GL['landmarks']]
        game = {'arrival': GL['arrival'], 'first_view': GL['first_view'], 'landmarks': lms,
                'shortcuts_later': [{'what': a, 'xy': list(b), 'opens': c} for a, b, c in GL['shortcuts_later']],
                'quiet_corners': [{'what': a, 'xy': list(b)} for a, b in GL['quiet_corners']]}
    else:
        big = max(bl, key=lambda b: b['rect_px'][2] * b['rect_px'][3]) if bl else None
        lm = {'name': f"{big['purpose']}, {name}'s largest building" if big else name, 'xy': [big['rect_px'][0] + big['rect_px'][2] // 2, big['rect_px'][1] + big['rect_px'][3] // 2] if big else list(lead.centre)}
        lms = [lm]
        for e in entries:                                          # a small place: the first building seen from each way in
            sd = lambda xy: max(abs(e[0] - xy[0]) / CELL / 40, abs(e[1] - xy[1]) / CELL / 22.5)
            if bl and min(sd(l['xy']) for l in lms) > 1.8:
                nb = min(bl, key=lambda b: sd((b['rect_px'][0] + b['rect_px'][2] // 2, b['rect_px'][1] + b['rect_px'][3] // 2)))
                lms.append({'name': f"{nb['purpose']} at the edge, seen first from the {next(a['route'] for a in arrivals if e in a['entries_px'])}",
                            'xy': [nb['rect_px'][0] + nb['rect_px'][2] // 2, nb['rect_px'][1] + nb['rect_px'][3] // 2]})
        game = {'arrival': arrivals[0]['route'] if arrivals else None, 'first_view': f"{name} from the {arrivals[0]['route'] if arrivals else 'shore'}: {lm['name']} ahead",
                'landmarks': lms, 'shortcuts_later': [], 'quiet_corners': []}
    if entries:
        game['first_screen_cells'] = [[int(e[0] // CELL - 20), int(e[1] // CELL - 11), 40, 22.5] for e in entries[:1]]
    game['screens'] = [round((fb[2] - fb[0]) / CELL / 40, 1), round((fb[3] - fb[1]) / CELL / 22.5, 1)]
    tiers = T['tiers_pre'][sl]
    counted = sum(1 for b in bl if b['counted'])
    tgt = lead.target if len(ts) == 1 else (60, 90)
    size = lead.size if len(ts) == 1 else 'city'
    lv = [L for L in T.get('levelled', []) if fb[0] - 8 <= L[0] <= fb[2] and fb[1] - 8 <= L[1] <= fb[3]]
    plan = {
        'schema': SCHEMA, 'id': pid, 'name': name, 'size': 'large' if size.startswith('large') else ('medium' if size.startswith('medium') else size),
        'size_note': size, 'target': list(tgt), 'buildings_counted': counted,
        'grid': {'cell_px': CELL, 'screen_cells': [40, 22.5], 'origin': 'world px, top-left of the continent (blockout-v55.json coords)',
                 'street_classes': {'arrival': "the regional route's own width", 'main': 6, 'side': 4, 'lane': 3, 'close': 2}},
        'site': {'reason': lead.purpose if len(ts) == 1 else 'the ria\'s deep water at the end of the Lull Road and the line: the continent\'s port, its trade and the Company',
                 'terrain': lead.setting if len(ts) == 1 else 'round the ria\'s head and east shore, on the flats east of it and up the Heights to the west',
                 'fit': FIT.get(pid, ''), 'dry': pid in ('dust-gulch', 'palm-spring', 'the-lode'), 'fortified': any(getattr(t, 'fort', None) for t in ts),
                 'authored': 'by hand (towns55.hearthold)' if pid == 'hearthold' else 'by the layout generator from hand-written streets', 'tiers': [int(tiers.min()), int(tiers.max())], 'levelled_footprints': len(lv)},
        'footprint_px': fb,
        'fortification': next((t.fort for t in ts if getattr(t, 'fort', None)), None),
        'arrivals': arrivals, 'streets': streets, 'squares': squares, 'districts': dists, 'gathering_places': gathering,
        'size_table_px': {f: [list(TW.BLD[f][0]), list(TW.BLD[f][1])] for f in sorted({b['form'] for b in bl if not b.get('from_zone_plan')})},
        'buildings': bl, 'lifted': [{'type': d['use'], 'rect_px': [d['x'], d['y'], d['w'], d['h']], 'why': 'no close could reach it'} for d in dropped],
        'outskirts': [o for t in ts for o in t.outskirts],
        'game_layout': game,
        'ground': GROUND.get(pid, {'centre': 'worn earth', 'yards': 'gardens', 'edges': 'fields'}),
        'terrain': {'box_cells': [int(c0), int(r0), int(w), int(h)], 'codes': {'.': 'land', 'g': 'green ground (grass, gardens, woods, fields)', 'r': 'route', '~': 'water', '#': 'barrier (cliff, wall, lava)', 'b': 'bridge'},
                    'rows': terrain_rows(K[sl])},
        'residents': [], 'routines': [],
        'x3_notes': 'For Codex (X3): fill residents (name, building id as home, workplace building id, role) and routines (resident, time '
                    'of day, place: a building id, square id or street id). Each building lists its occupants as a role; keep homes and '
                    'workplaces to the ids here, and walk residents on the streets (ids) only.',
    }
    return plan


# ------------------------------------------------------------------------------------------ item (d): the ground each town is made of
# A material raster (one code a cell) the map tints the ground with: a subtle change of colour on the same cells, not a new
# style, and nothing the walk or the checks read. Each town: worn or paved centres, yards in the local material, gardens and
# fields at the edges; Neon Harbour's ground layered by age, green only in its planned pockets, and its edges (the delta's
# mud and salt marsh, Canalside's market gardens, the heath and dunes on the Cape Road, bare rock and concrete on the cape).
MATERIALS = {   # code: (name, rgb, how much of it is mixed into the ground's colour)
    1: ('worn cobbles', (140, 138, 140), 0.75), 2: ('composite slab', (176, 192, 206), 0.8), 3: ('patched paving', (128, 134, 146), 0.75),
    4: ('steel deck plates', (96, 110, 128), 0.8), 5: ('terrace stone', (156, 160, 168), 0.75), 6: ('made land, paved', (146, 156, 170), 0.75),
    7: ('mudflat', (128, 118, 98), 0.6), 8: ('salt marsh', (120, 134, 104), 0.5), 9: ('heath and scrub', (150, 146, 104), 0.4),
    10: ('dunes', (214, 198, 150), 0.5), 11: ('bare rock', (138, 134, 128), 0.6), 12: ('concrete apron', (188, 188, 182), 0.65),
    13: ('packed sand', (212, 184, 136), 0.55), 14: ('adobe yards', (196, 146, 112), 0.5), 15: ('basalt setts', (92, 88, 90), 0.6),
    16: ('ash yards', (128, 120, 112), 0.5), 17: ('slate flags', (112, 124, 136), 0.55), 18: ('stone terraces', (160, 150, 132), 0.5),
    19: ('brick setts', (150, 92, 72), 0.55), 20: ('cinder yards', (96, 86, 80), 0.5), 21: ('boardwalk', (170, 132, 92), 0.55),
    22: ('sand', (224, 206, 160), 0.5), 23: ('reef shallows', (96, 196, 190), 0.45), 24: ('worn paving', (168, 156, 132), 0.5),
    25: ('packed earth', (150, 122, 92), 0.45), 26: ('dry gravel', (196, 178, 140), 0.45)}
TOWN_MAT = {   # plan id: (streets and squares, yards, open ground inside the town or None)
    'dust-gulch': (13, 14, 13), 'palm-spring': (13, 14, 26), 'the-lode': (13, 14, None), 'hearthold': (15, 16, 16), 'cinderwick': (15, 16, None),
    'cinder-springs': (15, 16, None), 'ember-forge': (15, 16, None), 'highgarth': (17, 18, None), 'cogsworth': (19, 20, 20),
    'lagoon-landing': (21, 22, 22), 'crossroads': (24, 25, None), 'fernhollow': (25, 25, None), 'lullford': (24, 25, None),
    'driftwood': (22, 22, None), 'gullwick': (22, 22, None), 'canalside': (24, 25, None), 'glintside': (1, 25, None),
    'halcyon-row': (24, 22, None), 'launch-cape': (12, 12, None)}
NEON_MAT = {'the old waterfront': 1, 'the docks': 4, 'the Lanes and the East Shore': 3, 'the Company district': 2, 'the Heights and the Skyport': 5}
STREET_K = ['lane', 'plaza', 'boulevard', 'arcade', 'quay', 'road', 'path', 'stair', 'trail', 'dock', 'stall', 'fishmarket']
OPEN_K = ['meadow', 'watermeadow', 'steppe', 'scrub', 'broadleaf', 'conifer', 'clearing', 'lawn', 'heath', 'gorse', 'fallow', 'thicket', 'felltree',
          'bramble', 'wild', 'tor', 'boulders', 'scree', 'barren', 'desert', 'sand', 'alpine', 'carr', 'reeds', 'fireweed']


def ground(T, plans, towns, X):
    """The material raster T['mat'] (int8) and each plan's ground: the materials and their cell counts."""
    K = T['K']; H, W = K.shape
    mat = np.zeros((H, W), np.int8)
    street = np.isin(K, STREET_K)
    yard = np.isin(K, ['yard'])
    opn = np.isin(K, OPEN_K)
    sea = np.isin(K, ['sea', 'surf'])
    for pid, P in plans.items():
        if pid == 'neon-harbour' or pid not in TOWN_MAT:
            continue
        sm, ym, om = TOWN_MAT[pid]
        x0, y0, x1, y1 = P['footprint_px']
        a, b, c, d = max(0, (y0 - 40) // CELL), max(0, (x0 - 40) // CELL), min(H, (y1 + 40) // CELL), min(W, (x1 + 40) // CELL)
        win = (slice(a, c), slice(b, d))
        mat[win][street[win]] = sm
        mat[win][yard[win]] = ym
        if om is not None:
            if pid == 'palm-spring':                                   # green only along the channels and round the pool
                wet = np.isin(K[win], ['channel', 'creek', 'pool', 'river'])
                far = ndi.distance_transform_edt(~wet) * CELL > 48
                mat[win][opn[win] & far] = om
            else:
                mat[win][opn[win]] = om
        if pid == 'lagoon-landing':                                    # the lagoon's reef shallows: sea within 40 px of its shore
            near = ndi.distance_transform_edt(sea[win]) * CELL
            mat[win][sea[win] & (near <= 40) & (np.arange(a, c)[:, None] * CELL > 6560)] = 23
    # Neon Harbour: its districts' ground by age, made land between, green only in the planned pockets
    P = plans.get('neon-harbour')
    if P:
        ts = {t.name.split(': ', 1)[1]: t for nm, t in towns.items() if nm.startswith('Neon Harbour')}
        lab = np.zeros((H, W), np.int8)                                 # each built cell labelled with its district's material
        for n_, t in ts.items():
            code = NEON_MAT[n_]
            for bd in t.buildings:
                lab[bd['y'] // CELL:(bd['y'] + bd['h']) // CELL, bd['x'] // CELL:(bd['x'] + bd['w']) // CELL] = code
            for st in t.streets:
                for pc in st['pieces']:
                    for (ax, ay), (bx, by) in zip(pc, pc[1:]):
                        lab[int(min(ay, by) // CELL):int(max(ay, by) // CELL) + 1, int(min(ax, bx) // CELL):int(max(ax, bx) // CELL) + 1] = code
            for q in t.spaces:
                if 'cells' in q:
                    cx_, cy_, cw_, ch_ = q['cells']; lab[cy_:cy_ + ch_, cx_:cx_ + cw_] = code
        built = lab > 0
        # the city: within 48 px of what is built, and the blocks the streets close round; its ground by its nearest district
        city = ndi.binary_fill_holes(ndi.binary_closing(ndi.distance_transform_edt(~built) * CELL <= 48, iterations=6)) & T['land']
        _, (iy, ix) = ndi.distance_transform_edt(~built, return_indices=True)
        near = lab[iy, ix]
        green = np.isin(K, ['garden', 'orchard', 'field', 'field2', 'hedge'])            # the planned pockets stay green
        paved = city & ~green & (street | yard | opn | np.isin(K, ['apron', 'pier', 'crane', 'quay']))
        mat[paved] = near[paved]
        made = paved & (ndi.distance_transform_edt(~sea) * CELL <= 32) & (mat != 4)      # the made land along the waterfront
        mat[made] = 6
        # the edges: the delta's mud and salt marsh, the Cape Road's heath and dunes, the cape's rock and apron
        dsea = ndi.distance_transform_edt(~(sea | np.isin(K, ['river', 'channel', 'creek']))) * CELL
        land_open = T['land'] & opn & ~city & (mat == 0)
        dm = np.zeros((H, W), bool)                                     # the delta: its arms and 12 cells round them
        for arm in (T.get('delta') or []):
            a_ = np.asarray(arm, float)
            dm[np.clip((a_[:, 1] // CELL).astype(int), 0, H - 1), np.clip((a_[:, 0] // CELL).astype(int), 0, W - 1)] = True
        dm = ndi.distance_transform_edt(~dm) <= 12
        mat[land_open & dm & (dsea <= 24)] = 7
        mat[land_open & dm & (dsea > 24) & (dsea <= 96)] = 8
        cr = np.asarray(T['route_px']['Cape Road'], float)
        dcr = np.full((H, W), 1e9)
        seed = np.zeros((H, W), bool)
        seed[np.clip((cr[:, 1] // CELL).astype(int), 0, H - 1), np.clip((cr[:, 0] // CELL).astype(int), 0, W - 1)] = True
        dcr = ndi.distance_transform_edt(~seed) * CELL
        road = land_open & (dcr <= 220) & (g.PY > 5050) & (g.PY < 5800) & (mat == 0)
        mat[road & (dsea <= 80)] = 10
        mat[road & (dsea > 80)] = 9
        cape = T['land'] & (g.PX > 11650) & (g.PY > 5800) & (mat == 0)
        mat[cape & np.isin(K, ['apron', 'pad'])] = 12
        mat[cape & ~np.isin(K, ['apron', 'pad', 'building', 'hangar', 'warehouse', 'tower']) & ~street] = 11
    T['mat'] = mat
    for pid, P in plans.items():
        c0, r0, w, h = P['terrain']['box_cells']
        sub = mat[r0:r0 + h, c0:c0 + w]
        codes, counts = np.unique(sub[sub > 0], return_counts=True)
        P['ground']['materials_cells'] = {MATERIALS[int(k)][0]: int(n) for k, n in zip(codes, counts)}
    return mat
