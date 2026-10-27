"""World plan v5.3's block-out, v53: the continent overview map (Matt, 27 Oct 17:25), on top of geo52.py.

"update and improve this overview map and add little place names and biome names for all. can you make it feel like a game
map a bit more (in the way the terrain is distributed and the different zones/biomes), i like the current version and its
realism but it can be changed a bit (not super massively) to be more fun and interesting to play ... also can you add a
ruler for scale (in the soft grid sense)."

v53 keeps v52's land, rivers, settlements and routes, and adds (README.md, "v53"):
- the stone circle in the woodland as the map's centre, and the ring of great shard craters round it: one per region, each
  with a glassy scorch streaking back toward the circle and a short trail from the nearest route (world-and-cast.md);
- four new routes that close loops and give shortcuts: the Heather Way (the woodland's circle over the Brackens' moor
  top to the Brackens gap), the Glass Road (Dust Gulch round the glass field to the Amber canyon), Fern Lane (Fernhollow
  down to the Lull Road) and Gull Lane (the Lull Road down to Gullwick);
- the act 1 places that had no point yet (the ice caves, the Saddle House, Old Fang's barrow, the spur tor), the waystones
  (the Cogsworth plan's and Crossroads' as planned, the rest proposed), the built zones (woodland, Crossroads, Undercroft);
- a stylised overview map in the house palette (tiers as soft-grid plateaus with south faces, flat biome blocks, tree
  and peak marks, upper-left light), with region, biome, place, water and route names, the rail and ferry lines, the
  waystones, overlays (built zones, act 1's route with numbered beats, the crater ring) and a soft-grid scale ruler.

Run from this folder:  python3 -I geo53.py            (data and every map, about six minutes)
                       RENDER_ONLY=1 python3 -I geo53.py   (the maps again from out/state-v53.pkl, under a minute)
It writes blockout-v53.json, stats-v53.json and gates-v53.json next to itself (committed) and the renders to out/ (or
$BLOCKOUT_OUT); MAP53_OUT, if set, also receives the overview maps. Needs geo52.py and geo5.py beside it."""
import json, math, os, pickle, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage as ndi
from skimage.graph import MCP_Geometric
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import geo5 as g
import geo52 as G
from geo5 import noise, chaikin, densify, raster, line_mask, shape, capsule, H, W, CELL, PX, PY, WPX, HPX, hexc

DATA = G.DATA
HERE = G.HERE
ROOT = os.environ.get('REPO_ROOT') or os.path.normpath(os.path.join(DATA, '..', '..', '..', '..'))
SUF = '-v53'

# ------------------------------------------------------------------------------------------ v53 tables
# The stone circle in the woodland's glade (the woodland zone's standing stones, placed in the valley plan's woodland rect;
# Claude A's golden screen keeps the exact spot) and Crossroads' square (crossroads.json, origin 5976, 3248).
CIRCLE = (5800, 3000)
CROSSROADS = (6296, 3536)
# The great shard craters (world-and-cast.md 2): one per region, in a rough ring round the circle. Each crater's scorch runs
# from the crater toward the circle. (x, y, bowl radius px, region, what the Starfall did there)
CRATERS = {
    'the Crossroads crater': (6484, 3712, 36, 'the home valley', "the slice's shard, in the park (crossroads.json), the ring's centre stone"),
    'the Frostline crater': (6480, 1590, 70, 'the Frostline', 'on the snowfield above the tarn; the shard crows over the col, the Rime Wyrm under the lake'),
    'the Heather crater': (5300, 2390, 70, 'the Brackens', "on the moor top; the shard wolves scatter the flock"),
    'the Seam crater': (8260, 2130, 80, 'the coal hills', "in the coal hills above Cogsworth; the Company fences the seam"),
    'the Lull crater': (8150, 3560, 75, 'the Lull', "on the plain's west bank; the smugglers' landing"),
    'the Company crater': (10780, 4130, 85, 'Neon Harbour', "fenced in the Company's yard north of the new town; its light sold as neon"),
    'the Lagoon crater': (6330, 6420, 60, 'the Tidebloom Isles', "on the main isle's west shoulder; the basalt wakes"),
    'the Glass field': (2160, 2760, 95, 'the Sunstone basin', "out on the desert's edge, glass to the horizon; the drill stops the spring"),
    'the Ember crater': (3700, 4870, 80, 'the fire country', "on the ash fields between the flows; the dragon shardstruck"),
}
# Four new routes: loops and shortcuts (every region of four areas or more has a loop; world-plan 2, rule 5).
NEW_ROUTES = {
    'Heather Way': ([(6020, 3330), (5800, 3000), (5560, 2840), (5340, 2630), (5170, 2560), (5080, 2800), (5060, 3060), (5064, 3300),
                     (5130, 3560), (5200, 3760)], 'path', []),
    'Glass Road': ([(2700, 2470), (2540, 2540), (2390, 2660), (2330, 2860), (2430, 3040), (2600, 3170), (2690, 3150)], 'path', []),
    'Fern Lane': ([(7150, 3130), (7210, 3260), (7180, 3400), (7260, 3520), (7240, 3660), (7310, 3780), (7300, 3900)], 'path', []),
    'Gull Lane': ([(7900, 3970), (7860, 4300), (7930, 4650), (7950, 4990)], 'path', []),
}
NEW_ROUTE_WHY = {
    'Heather Way': "the circle's own road west: from the woodland's glade over the Brackens' moor top, past the Heather crater and the drove well, down to the Brackens gap; closes a loop with the Drover's Road",
    'Glass Road': "Dust Gulch round the glass field to the Amber canyon; a loop off the Canyon Road",
    'Fern Lane': "Fernhollow straight down to the Lull Road: a shortcut that closes the Foothill Road and the Lull Road into a loop",
    'Gull Lane': "the Lull Road down to Gullwick: a loop with the Coast Path, and Gullwick no longer a dead end off one path",
}
# Act 1's places with no point yet (docs/story/act1.md; world-and-cast.md 1), proposed here for lanes E and F
POI53 = {
    'the ice caves': (6080, 1660, 'cave', 'under the glacier snout: the Rime Wyrm (act 1)'),
    'the Saddle House': (6440, 2010, 'shrine', "the col's monastery on the headwall (world-and-cast.md fit 2; Tam)"),
    'the bothy': (6520, 2168, 'hut', "the Frostline's hut and its warden (frostline.json cabin_meadow)"),
    "Old Fang's barrow": (4930, 2980, 'cave', 'the barrow on the Brackens (act 1, The cut rope)'),
    'the spur tor': (4990, 1960, 'view', 'the Heather spur: the old ram; Iona joins (act 1)'),
    'the lighthouse': (6600, 4995, 'tower', "Driftwood's light, Velvet's (act 1)"),
    'the Millrace landslip': (7650, 2740, 'gate', 'W3 (act 1, last quest)'),
}
# Waystones (world-and-cast.md: chips of the circle). 'plan' where a plan places one, 'proposed' otherwise.
WAYSTONES = {
    'Crossroads': (6396, 3608, 'plan'), 'the footbridge': (7600, 1968, 'plan'), 'Fernhollow': (7300, 3150, 'plan'),
    'the Cog foot': (8560, 3024, 'plan'), 'Cogsworth': (7960, 2420, 'plan'),
    'the Col hut': (6250, 2380, 'proposed'), 'the bothy': (6560, 2200, 'proposed'), 'the Brackens gap': (5240, 3720, 'proposed'),
    'Driftwood': (6400, 4920, 'proposed'), 'Lullford': (8700, 4250, 'proposed'), 'Gullwick': (7920, 5090, 'proposed'),
    'Lagoon Landing': (6540, 6170, 'proposed'), 'Palm Spring': (3450, 2770, 'proposed'), 'Dust Gulch': (2800, 2400, 'proposed'),
    'Hearthold': (2480, 5120, 'proposed'), 'Cinderwick': (2740, 5600, 'proposed'), 'the market (Neon)': (9816, 4416, 'proposed'),
    'Launch Cape': (10960, 5520, 'proposed'),
}
# The zones built in the game today (art/regions/valley.json zones; game/data/plans/*.json)
BUILT = {'the woodland': (5640, 2432, 6136, 3344), 'Crossroads': (5976, 3248, 6616, 3808),
         'the Undercroft (below)': (CIRCLE[0] - 384, CIRCLE[1] - 108, CIRCLE[0] + 384, CIRCLE[1] + 108)}
# Act 1 (docs/story/act1.md): one order of the beats, after the slice. The strands run side by side.
ACT1 = [('Crossroads', CROSSROADS, 'after the slice: Moss asks for bread for the Col hut'),
        ('the ridge col', (6290, 2350), 'free the shard crows (W2)'),
        ('the bothy', (6520, 2168), 'the hut warden'),
        ('the High Fells', (6760, 1660), 'free the ibex'),
        ('the ice caves', (6080, 1660), 'the Rime Wyrm; Tam joins'),
        ('the lantern', (6288, 3568), "the Frostline's shard home"),
        ('the Brackens gap', (5200, 3760), 'the scattered flock'),
        ("Old Fang's barrow", (4930, 2980), 'the drove well; Old Fang'),
        ('the spur tor', (4990, 1960), 'the old ram; Iona joins'),
        ('the lighthouse', (6600, 4995), "Driftwood's quay; Velvet joins"),
        ('the stone circle', CIRCLE, "the circle wakes; Cairn's trial"),
        ('Crossroads', (6300, 3500), 'the wolf moon'),
        ('the halt', (5760, 4048), "the halt's platform"),
        ('the Millrace landslip', (7650, 2740), 'free the landslip (W3)')]


def hero_speed():
    """The hero's walk speed from the cast manifest (Bramble, art px a second at density 3), in world px a second."""
    m = json.load(open(os.path.join(ROOT, 'game', 'assets', 'characters', 'bramble', 'manifest.json')))
    return float(m['walk_speed']), float(m['walk_speed']) / 3.0


for nm, v in NEW_ROUTES.items():
    g.ROUTES[nm] = v
G.MAIN_ROUTES[:] = [r for r in g.ROUTES if not r.startswith('Valley lane') and r not in
                    ('Old Bridges', 'Quay Street', 'Harbour Bridge', 'Beacon Causeway', 'Forge Stair')]
CRATER_KINDS = {'shardglass': '#7262A4', 'craterrim': '#584187', 'scorch': '#4A3A5E', 'circle': '#C5B8A4'}
g.COL.update(CRATER_KINDS)
g.WALK |= set(CRATER_KINDS)
NATURAL = set(g.OK) | {'heath', 'scree', 'snow', 'alpine', 'barren', 'erg', 'talus', 'moraine', 'fallow', 'carr', 'scroll', 'wash',
                       'meadow', 'steppe', 'scrub', 'desert', 'watermeadow', 'gorse', 'clearing', 'field', 'field2', 'hedge',
                       'wild', 'ancient', 'thicket', 'bramble', 'boulders'}   # a crater blasts its own clearing in deep forest


# ------------------------------------------------------------------------------------------ the circle and the craters
def craters(T):
    """Paint each great shard crater (a glass bowl, a rim and a scorch streaking toward the circle) and a trail from it to
    the nearest route, only over natural ground (never water, a route, a settlement or a barrier)."""
    K = T['K']; out = {}
    allp = []
    for rn in G.MAIN_ROUTES:
        x, y, _, _ = densify(T['route_px'][rn], 16)
        allp += [(rn, float(a), float(b)) for a, b in zip(x, y)]
    arr = np.array([(a, b) for _, a, b in allp])
    T['crater_mask'] = np.zeros((H, W), bool)
    for i, (nm, (cx, cy, r, region, story)) in enumerate(CRATERS.items()):
        dx, dy = CIRCLE[0] - cx, CIRCLE[1] - cy; dist = math.hypot(dx, dy)
        rec = {'x': cx, 'y': cy, 'radius_px': r, 'region': region, 'story': story, 'distance_to_circle_px': round(dist)}
        if dist < 1:
            continue
        ux, uy = dx / dist, dy / dist
        bowl = shape(cx, cy, r, r * 0.86, 900 + i, 0.22)
        rimm = shape(cx, cy, r + 20, (r + 20) * 0.88, 900 + i, 0.22) & ~bowl
        tip = (cx + ux * 3.6 * r, cy + uy * 3.6 * r)
        scorch = capsule([(cx + ux * r * 0.4, cy + uy * r * 0.4), tip], 0.95 * r, 0.12 * r, 920 + i, 0.4) & ~bowl & ~rimm
        rays = np.zeros((H, W), bool)
        for k, off in enumerate((-0.5, 0.0, 0.45)):                   # glass rays inside the scorch, all toward home
            a = math.atan2(uy, ux) + off * 0.35
            rays |= line_mask([(cx, cy), (cx + math.cos(a) * 3.2 * r, cy + math.sin(a) * 3.2 * r)], 10)
        paint = np.isin(K, list(NATURAL)) & ~T['used_routes']
        K[scorch & paint] = 'scorch'; K[scorch & rays & paint] = 'shardglass'
        K[rimm & paint] = 'craterrim'; K[bowl & paint] = 'shardglass'
        crater = (scorch | rimm | bowl) & paint
        # the trail from the crater's rim to the nearest route point that is not inside the crater's own scorch
        dd = np.hypot(arr[:, 0] - cx, arr[:, 1] - cy); j = int(np.argmin(dd)); rn, qx, qy = allp[j]
        trail = line_mask([(cx, cy), ((cx + qx) / 2 + 30 * math.sin(i), (cy + qy) / 2 + 30 * math.cos(i)), (qx, qy)], 16)
        K[trail & np.isin(K, list(NATURAL | {'scorch', 'craterrim'})) & ~T['used_routes'] & ~bowl] = 'trail'
        T['crater_mask'] |= crater | trail
        T['used'] |= crater | trail
        heading = math.degrees(math.atan2(tip[1] - cy, tip[0] - cx)); home = math.degrees(math.atan2(dy, dx))
        rec.update({'scorch_tip': [round(tip[0]), round(tip[1])], 'scorch_heading_deg': round(heading, 1), 'bearing_home_deg': round(home, 1),
                    'points_home': abs(((heading - home + 180) % 360) - 180) < 1.0, 'trail_to': rn, 'trail_px': round(float(dd[j])),
                    'painted_cells': int(crater.sum())})
        out[nm] = rec
    # the circle itself: a ring of stones in a clearing (drawn small; the woodland zone holds the real one)
    ring = shape(CIRCLE[0], CIRCLE[1], 40, 40, 960, 0.1) & ~shape(CIRCLE[0], CIRCLE[1], 30, 30, 960, 0.1)
    K[ring & np.isin(K, list(NATURAL))] = 'circle'
    out['the Crossroads crater'] = {'x': 6484, 'y': 3712, 'radius_px': 36, 'region': 'the home valley', 'distance_to_circle_px':
                                    round(math.hypot(6484 - CIRCLE[0], 3712 - CIRCLE[1])), 'story': CRATERS['the Crossroads crater'][4],
                                    'note': "inside Crossroads' plan (the park round the crater); not repainted here", 'points_home': True}
    T['craters'] = out
    return out


# ------------------------------------------------------------------------------------------ the data stage
def data_stage():
    T = G.build51(); g.routes(T); g.settle(T)
    craters(T)
    K = T['K']
    obs = G.obstacles(T); pocks = G.pockets(T); G.mixing_bands(T)
    g.FRAME = ndi.distance_transform_edt(~T['used']) * CELL > (g.FRAME_PX + 200 * noise(500, 70) + 45 * noise(90, 71, 2) + 16 * noise(30, 72, 2) + 12 * noise(16, 73, 1))
    jit = 30 * noise(60, 604, 2) + 12 * noise(16, 605, 1)
    g.FRAME &= ~((PX > 9500 + 120 * noise(400, 600) + jit) & (PY > 4200 + 120 * noise(400, 601) + jit) & (PY < 5500 + 120 * noise(400, 602) + jit) & (PX < 11200 + 60 * noise(400, 603) + jit))
    G.borders(T)
    pois, per = G.content(T); pois = G.fill_required(T, pois); marks = G.markers(T)
    gates = g.gate_check(K, T['crossings'])
    res, rl, wc = g.times(K)
    t = G.tier_field(T); steps = G.route_steps(T, t); vstats = G.vertical_stats(T, t, steps)
    art_speed, speed = hero_speed()
    k_ = g.SPEED / speed
    hero = {nm: {kk: (round(v * k_, 1) if v is not None else None) for kk, v in d.items()} for nm, d in res.items()}
    # reachability of the new places with every way open
    Wm = g.walk_mask(K); lab, _ = ndi.label(Wm); hy, hx = g.nearest_walk(Wm, *g.HOME); home = lab[hy, hx]
    reach = {}
    for nm, p in [(n, c[:2]) for n, c in CRATERS.items()] + [(n, c[:2]) for n, c in POI53.items()] + [(n, c[:2]) for n, c in WAYSTONES.items()] + [('the stone circle', CIRCLE)]:
        yy_, xx_ = g.nearest_walk(Wm, *p); reach[nm] = {'reached': bool(lab[yy_, xx_] == home), 'snap_px': round(math.hypot(xx_ * CELL + 4 - p[0], yy_ * CELL + 4 - p[1]))}
    stats = {'world_px': [WPX, HPX], 'walkable_zone_areas': round(wc / 2880, 1), 'routes_s': rl, 'home_to': res, 'why_here': g.WHY,
             'bridges': g.BRIDGES, 'easter_egg_spots_later': g.EGGS, 'ways': g.WAY_NAMES, 'oxbows': T['oxbows'], 'delta_arms': len(T['delta']),
             'vertical': vstats, 'route_tier_changes': {rn: sum(1 for s_ in steps if s_[0] == rn) for rn in g.ROUTES}, 'thresholds': G.THRESHOLDS,
             'content_per_biome': per, 'content': pois, 'obstacles': obs, 'pockets': pocks, 'markers': marks,
             'settlement_density': T['settlement_density'], 'mixing': T['mixing'],
             'v53': {'circle': CIRCLE, 'crossroads': CROSSROADS, 'craters': T['craters'], 'new_routes': NEW_ROUTE_WHY, 'poi': POI53,
                     'waystones': WAYSTONES, 'reachable_with_every_way_open': reach,
                     'hero': {'cast': 'bramble', 'walk_speed_art_px_s': art_speed, 'walk_speed_world_px_s': round(speed, 2),
                              'cells_s': round(speed / CELL, 3), 'screen_1080p_s': round(320 / speed, 1),
                              'note': 'home_to and routes_s keep the plan speed of 40 px a second for comparison with v52; home_to_at_hero_speed uses the manifest'},
                     'home_to_at_hero_speed': hero}}
    bres = G.bench(T, pois, marks, pocks, obs, steps, gates); stats['benchmark'] = bres; stats['biome_detail'] = T['biome_detail']
    for b_ in bres:
        print(('PASS' if b_['pass'] else 'FAIL'), b_['n'], b_['check'], '|', b_['measured'])
    json.dump(stats, open(os.path.join(DATA, f'stats{SUF}.json'), 'w'), indent=1)
    json.dump(gates, open(os.path.join(DATA, f'gates{SUF}.json'), 'w'), indent=1)
    G.export_blockout(T, t, steps, vstats, gates, f'blockout{SUF}.json')
    bj = json.load(open(os.path.join(DATA, f'blockout{SUF}.json')))
    bj['version'] = 'v5.3 block-out, v53 (world plan v5.3; the overview map of 27 Oct)'
    bj['v53'] = {'circle': list(CIRCLE), 'crossroads': list(CROSSROADS),
                 'craters': {nm: {k: v for k, v in c.items() if k in ('x', 'y', 'radius_px', 'region', 'scorch_tip', 'scorch_heading_deg', 'trail_to')}
                             for nm, c in T['craters'].items()},
                 'new_routes': list(NEW_ROUTES), 'poi': {nm: [x, y, k] for nm, (x, y, k, _) in POI53.items()},
                 'waystones': {nm: [x, y, s] for nm, (x, y, s) in WAYSTONES.items()}, 'built': {nm: list(b) for nm, b in BUILT.items()},
                 'act1': [[nm, list(p), what] for nm, p, what in ACT1]}
    with open(os.path.join(DATA, f'blockout{SUF}.json'), 'w') as f:
        json.dump(bj, f, separators=(',', ':'))
    print(json.dumps({k: v for k, v in gates.items() if k != 'crossings'})[:3000])
    print(json.dumps(reach))
    # the realistic texture (v52's look) as a toggle layer, and the state the maps are drawn from
    real = np.clip(g.colour(T, K), 0, 255).astype(np.uint8)
    if g.FRAME is not None:
        real = np.where((g.FRAME & T['land'])[..., None], (real * 0.9 + np.array([40, 44, 52]) * 0.1).astype(np.uint8), real)
    kinds = sorted(set(K.ravel().tolist())); idx = {k: i for i, k in enumerate(kinds)}
    codes = np.vectorize(idx.get, otypes=[np.int16])(K)
    state = {'kinds': kinds, 'K': codes, 'h': T['h'].astype(np.float32), 'land': T['land'], 'sea': T['sea'], 'tiers': t.astype(np.int16),
             'frame': g.FRAME, 'route_px': T['route_px'], 'river_px': T['river_px'], 'delta': T['delta'], 'real': real,
             'routes': {nm: (kind, feats) for nm, (pts, kind, feats) in g.ROUTES.items()}, 'crater_mask': T['crater_mask'],
             'craters': T['craters'], 'stats_home': res, 'hero': stats['v53']['hero']}
    pickle.dump(state, open(os.path.join(HERE, 'state-v53.pkl'), 'wb'))
    return state


if __name__ == '__main__':
    if os.environ.get('RENDER_ONLY'):
        S = pickle.load(open(os.path.join(HERE, 'state-v53.pkl'), 'rb'))
    else:
        S = data_stage()
    if os.environ.get('QUICK') != 'data':
        import map53
        map53.render_all(S, sys.modules[__name__])
