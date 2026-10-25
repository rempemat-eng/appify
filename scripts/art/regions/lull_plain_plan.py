"""The Lull plain as a region plan (lane G): the land between the valley, Cogsworth's coal
hills, the Lull belt and Gullwick, in Claude F's schema (docs/vision/region-plans.md) with
the Godot-era fights, quest spots and 16:9 windows in Claude I's shape (Claude A,
to-all-assignments-1025: map lanes plan as data only, no art).

Where it comes from:
  - the land: lib/world-land.ts (scripts/art/world_land.py, PLAIN): x 7000 to 8304, from
    Cogsworth's box (y 3296) to the coast, Gullwick's box (Claude I) cut out;
  - the routes: lane G's own Lull Road and Coast Path from lib/world-routes.ts
    (scripts/art/world_routes.py), read at build time, so the plan and the routes agree;
  - the things on the land: the brief, docs/vision/regions/routes-thresholds-edges.md,
    section 5 (moved where the ground needs it, `moved_from` keeps the brief's point);
  - the ground: E's valley brief's farmland variant (scripts/art/biomes/valley.json names
    "the land between" as its user), and C's coast for the shelf above the sea.

Run: python3 scripts/art/regions/lull_plain_plan.py (writes art/regions/lull-plain.json);
check: python3 scripts/art/region_plan.py --check.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'art'))
import world_routes as wr  # noqa: E402

OUT = os.path.join(ROOT, 'art', 'regions', 'lull-plain.json')
BOX = [6976, 3296, 1344, 1888]      # whole 32 px audit cells round x 7000 to 8304, y 3296 to 5168
GULLWICK = (7648, 4848, 8304, 5456)  # Claude I's box, cut out of lane G's land


def _corners(pts):
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        if not ((a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1])):
            out.append(b)
    out.append(pts[-1])
    return out


def _in_box(p):
    x, y = p
    in_box = BOX[0] <= x <= BOX[0] + BOX[2] and BOX[1] <= y <= BOX[1] + BOX[3]
    in_gull = GULLWICK[0] <= x < GULLWICK[2] and GULLWICK[1] <= y < GULLWICK[3]
    return in_box and not in_gull


def _runs(points):
    """The route's stretches inside lane G's land in this box, each as its corners."""
    runs, cur = [], []
    for p in points:
        if _in_box(p[:2]) and wr.owner(p[0], p[1])[0] == wr.BETWEEN:
            cur.append(p)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) > 1]


def routes():
    built, _ = wr.build()
    by_id = {r['id']: r for r in built}
    out = []
    for rid, name in (('lull-road', 'lull_road'), ('coast-path', 'coast_path')):
        r = by_id[rid]
        for k, run in enumerate(_runs(r['points'])):
            out.append({
                'id': name if k == 0 else f'{name}_{k + 1}', 'kind': r['kind'],
                'width': run[0][2],
                'owner_note': "lane G's route (lib/world-routes.ts, scripts/art/world_routes.py); "
                              "this plan draws its land, the line is the routes' own",
                'points': [[p[0], p[1]] for p in _corners(run)],
                'widths': [[p[0], p[1], p[2]] for p in run if p[2] != run[0][2]],
                'tiers_world': sorted({p[3] for p in run}),
            })
    return out


# banks step in and out by a cell every screen width (to-all-volume)
TIERS = [
    {'id': 'north_fields', 'tier': 5,
     'why': "the upper fields under the coal hills' foot, a bank above the plain",
     'outline': [[7000, 3296], [8304, 3296], [8304, 3576], [7960, 3576], [7960, 3608], [7640, 3608],
                 [7640, 3576], [7320, 3576], [7320, 3608], [7000, 3608]]},
    {'id': 'plain', 'tier': 4,
     'why': "the Lull plain: the Lull Road's fields, the mill, the barn, the stones and the chapel",
     'outline': [[7000, 3608], [7320, 3608], [7320, 3576], [7640, 3576], [7640, 3608], [7960, 3608],
                 [7960, 3576], [8304, 3576], [8304, 4592], [8192, 4592], [8192, 4688], [7920, 4688],
                 [7920, 4720], [7600, 4720], [7600, 4688], [7320, 4688], [7320, 4720], [7000, 4720]]},
    {'id': 'shelf', 'tier': 3,
     'why': "the coastal shelf: the Coast Path from the Headland's neck to Gullwick, and north of "
            "Gullwick up to the Lull's lower terrace where the path goes on to Lullford",
     'outline': [[7000, 4720], [7320, 4720], [7320, 4688], [7600, 4688], [7600, 4720], [7920, 4720],
                 [7920, 4688], [8192, 4688], [8192, 4592], [8304, 4592], [8304, 4848], [7648, 4848],
                 [7648, 5168], [7256, 5168], [7256, 5104], [7000, 5104]]},
]

TRODS = [
    {'id': 'lull_road_round', 'width': 24, 'from_lane_g': True, 'obstacle': 'thicket',
     'obstacle_at': [7407, 3994],
     'why': "lane G's side path round the thicket (brief 5): off the road by the barn, back at the "
            "mill's field gate",
     'points': [[7184, 3816], [7184, 3912], [7240, 3912], [7240, 4032], [7608, 4032], [7608, 3960],
                [7680, 3960], [7680, 3896], [7704, 3896]]},
    {'id': 'stones_pocket', 'width': 24, 'from_lane_g': True, 'dead_end': 'story',
     'why': "the brief's pocket: initials cut in a stone, at the standing stones",
     'points': [[7760, 3944], [7760, 4128], [7712, 4128], [7712, 4160]]},
    {'id': 'coast_path_round', 'width': 24, 'from_lane_g': True, 'obstacle': 'thicket',
     'obstacle_at': [7053, 4974],
     'why': "round the thicket's north side on the shelf, inside lane G's land (the routes' side "
            "path ran into the valley's box)",
     'points': [[7016, 5072], [7016, 4936], [7192, 4936], [7192, 5072]]},
    {'id': 'bench_pocket', 'width': 24, 'from_lane_g': True, 'dead_end': 'bench',
     'why': "the brief's pocket: a bench under a tree, looking over the sea from the shelf",
     'points': [[7552, 5072], [7552, 4984], [7600, 4984], [7600, 4840], [7552, 4840], [7552, 4824]]},
    {'id': 'farm_track', 'width': 24,
     'why': "the plain's one north-south track: from the Lull Road by the mill down the bank to "
            "the coast mill and the Coast Path, so the two routes join between the valley and Lullford",
     'points': [[7432, 3896], [7432, 5072]]},
    {'id': 'mill_spur', 'width': 24, 'why': "the coast mill's yard, off the farm track",
     'points': [[7432, 4968], [7280, 4968]]},
    {'id': 'grave_track', 'width': 24, 'dead_end': 'story',
     'why': "up the bank into the north fields to an old grave under a thorn (the brief's pocket "
            "off the Foothill Road, re-seated on lane G's land, where the plain can reach it)",
     'moved_from': [[6960, 3240], [7096, 3408]],
     'points': [[7096, 3816], [7096, 3408]]},
    {'id': 'churchyard_gate', 'width': 24,
     'why': "off the Lull Road through the churchyard's gate, among the graves east of the chapel",
     'points': [[8280, 4144], [8280, 4248]]},
    {'id': 'chapel_lane', 'width': 24, 'why': "from the Coast Path to the shelf's ruined chapel",
     'points': [[8168, 4816], [8008, 4816], [8008, 4792]]},
]

STAIRS = [
    {'id': 'farm_bank', 'on': 'farm_track', 'at': [7432, 4688], 'from_tier': 4, 'to_tier': 3,
     'width': 40, 'kind': 'stone', 'why': "the track down the plain's bank to the shelf"},
    {'id': 'grave_bank', 'on': 'grave_track', 'at': [7096, 3608], 'from_tier': 4, 'to_tier': 5,
     'width': 40, 'kind': 'stone', 'why': "up the north fields' bank"},
]

WATER = [
    {'id': 'heron_pools', 'kind': 'pond', 'closed': True,
     'declared_closed': 'spring-fed meres in a hollow of the plain',
     'why': "the brief's heron pools, north of the Lull Road where it steps south",
     'points': [[7920, 3904], [8016, 3904], [8016, 3952], [7920, 3952]],
     'moved_from': [7975, 3940]},
]

BUILDINGS = [
    {'id': 'road_mill', 'kind': 'windmill', 'kit': 'valley', 'foot': [7440, 3848], 'w': 48,
     'faces': 'south', 'why': "the brief's windmill on the Lull Road, its door on the road"},
    {'id': 'hay_barn', 'kind': 'barn', 'kit': 'valley', 'foot': [7104, 4000], 'w': 64,
     'faces': 'east', 'why': "the brief's hay barn, its yard on the side path round the thicket"},
    {'id': 'road_chapel', 'kind': 'ruined_chapel', 'kit': 'valley', 'foot': [8160, 4232], 'w': 64,
     'faces': 'north', 'why': "the brief's ruined chapel by the Lull Road, a churchyard to its east"},
    {'id': 'coast_mill', 'kind': 'windmill', 'kit': 'valley', 'foot': [7256, 4952], 'w': 48,
     'faces': 'east', 'why': "the brief's windmill on the shelf above the sea, on the farm track"},
    {'id': 'shelf_chapel', 'kind': 'ruined_chapel', 'kit': 'valley', 'foot': [7984, 4784], 'w': 56,
     'faces': 'south', 'why': "the brief's ruined chapel above Gullwick, at the chapel lane's end"},
]

PLACES = [
    {'id': 'road_mill', 'kind': 'farmstead', 'at': [7464, 3840], 'rect': [7400, 3760, 128, 112],
     'why': "the mill and its yard on the Lull Road"},
    {'id': 'hay_barn', 'kind': 'farmstead', 'at': [7136, 3976], 'rect': [7072, 3912, 160, 120],
     'why': "the barn and its rick yard"},
    {'id': 'standing_stones', 'kind': 'landmark', 'at': [7712, 4160], 'rect': [7664, 4120, 112, 96],
     'why': "the ring of stones at the stones pocket's end"},
    {'id': 'churchyard', 'kind': 'ruin', 'at': [8192, 4232], 'rect': [8128, 4168, 176, 128],
     'why': "the ruined chapel and its churchyard"},
    {'id': 'coast_mill', 'kind': 'farmstead', 'at': [7280, 4952], 'rect': [7224, 4880, 120, 112],
     'why': "the coast mill and its yard"},
]

NAMED = [
    {'thing': 'windmill', 'kind': 'landmark', 'at': [7464, 3856], 'route': 'Lull Road', 'moved_from': [7465, 3821]},
    {'thing': 'hay barn', 'kind': 'landmark', 'at': [7136, 4008], 'route': 'Lull Road', 'moved_from': [7139, 3972]},
    {'thing': 'heron pools', 'kind': 'wild', 'at': [7968, 3962], 'route': 'Lull Road', 'moved_from': [7975, 3940]},
    {'thing': 'standing stones', 'kind': 'landmark', 'at': [7744, 4176], 'route': 'Lull Road', 'moved_from': [7745, 4168]},
    {'thing': 'ruined chapel', 'kind': 'ruin', 'at': [8192, 4240], 'route': 'Lull Road', 'moved_from': [8173, 4183]},
    {'thing': 'windmill', 'kind': 'landmark', 'at': [7232, 4960], 'route': 'Coast Path', 'moved_from': [7280, 4940]},
    {'thing': 'ruined chapel', 'kind': 'ruin', 'at': [8048, 4796], 'route': 'Coast Path', 'moved_from': [8008, 4668]},
    {'thing': 'standing stones', 'kind': 'landmark', 'at': [7600, 5136], 'route': 'Coast Path',
     'moved_from': [7597, 5215], 'why': 'the brief put them on the beach below the shelf'},
]

POCKETS = [
    {'holds': 'a story detail: initials cut in a stone', 'at': [7712, 4160], 'trod': 'stones_pocket', 'from_lane_g': True},
    {'holds': 'a bench under a tree', 'at': [7552, 4824], 'trod': 'bench_pocket', 'from_lane_g': True},
    {'holds': 'a story detail: an old grave', 'at': [7096, 3408], 'trod': 'grave_track',
     'from_lane_g': True, 'moved_from': [7093, 3405]},
]

OBSTACLES = [
    {'kind': 'thicket', 'at': [7407, 3994], 'passed_by': 'lull_road_round', 'why': "lane G's obstacle"},
    {'kind': 'thicket', 'at': [7104, 4992], 'passed_by': 'coast_path_round',
     'why': "lane G's obstacle, moved inside the side path's loop", 'moved_from': [7053, 4974]},
]

# the brief's markers on the Lull Road and the Coast Path that fall on lane G's land here
MARKERS = [
    ('S', 'cold fire ring', (7093, 3864)), ('S', 'marker stone', (7140, 3847)), ('I', 'bench', (7072, 3856)),
    ('S', 'cart with a broken wheel', (7224, 3864)), ('A', 'hares', (7291, 3941)),
    ('I', 'noticeboard', (7321, 3864)), ('S', 'mended fence', (7389, 3936)), ('S', 'old boot', (7496, 3854)),
    ('A', 'hares', (7476, 3954)), ('I', 'bench', (7555, 3936)), ('S', 'lost hat', (7640, 3992)),
    ('S', 'cart with a broken wheel', (7648, 3864)), ('I', 'noticeboard', (7720, 3864)),
    ('S', 'tracks', (7800, 3880)), ('A', 'hares', (7796, 3980)), ('I', 'gate', (7889, 4024)),
    ('S', 'cold fire ring', (7913, 4032)), ('S', 'marker stone', (7976, 4024)), ('A', 'hares', (8032, 4064)),
    ('I', 'noticeboard', (8106, 4072)), ('S', 'cairn', (8111, 4085)), ('S', 'tracks', (8206, 4065)),
    ('I', 'gate', (8200, 4128)), ('S', 'old boot', (8256, 4176)),
    ('S', 'cart with a broken wheel', (7090, 5047)), ('I', 'noticeboard', (7168, 5040)),
    ('S', 'mended fence', (7267, 5040)), ('S', 'old boot', (7368, 5040)), ('A', 'hares', (7357, 5104)),
    ('I', 'bench', (7464, 5040)), ('S', 'lost hat', (7453, 5104)), ('S', 'cart with a broken wheel', (7524, 5040)),
    ('I', 'noticeboard', (7581, 5104)), ('S', 'tracks', (7625, 5040)),
    ('I', 'resident', (8200, 4776)), ('S', 'lost hat', (8264, 4795)), ('S', 'cart with a broken wheel', (8256, 4744)),
    ('A', 'hares', (8264, 4656)), ('I', 'gate', (8264, 4640)),
]
BRIEF_MARKERS = {   # where a marker was moved off a path or a building: the brief's point
    (7093, 3864): (7093, 3814), (7224, 3864): (7224, 3875), (7321, 3864): (7321, 3845),
    (7496, 3854): (7463, 3854), (7072, 3856): (7150, 3944), (7389, 3936): (7389, 3913), (7555, 3936): (7555, 3900),
    (7648, 3864): (7648, 3884), (7720, 3864): (7720, 3949), (7800, 3880): (7784, 3880),
    (7889, 4024): (7889, 3948), (7976, 4024): (7976, 3970), (8032, 4064): (8032, 4049),
    (8106, 4072): (8106, 3986), (8200, 4128): (8202, 4168), (8256, 4176): (8287, 4124),
    (7168, 5040): (7184, 5021), (7267, 5040): (7267, 5066), (7368, 5040): (7288, 4969),
    (7357, 5104): (7357, 5041), (7464, 5040): (7427, 4980), (7453, 5104): (7453, 5081),
    (7524, 5040): (7524, 5021), (7581, 5104): (7581, 5100), (7625, 5040): (7625, 5009),
    (8200, 4776): (8183, 4800), (8264, 4795): (8282, 4795), (8256, 4744): (8222, 4717),
    (8264, 4656): (8313, 4686), (7640, 3992): (7610, 3978), (7913, 4032): (7913, 4046),
    (8264, 4640): (8274, 4596),
}


def markers():
    out = []
    for t, what, at in MARKERS:
        route = 'Lull Road' if at[1] < 4600 else 'Coast Path'
        m = {'t': t, 'what': what, 'at': list(at), 'route': route}
        if at in BRIEF_MARKERS and BRIEF_MARKERS[at] != at:
            m['moved_from'] = list(BRIEF_MARKERS[at])
        out.append(m)
    return out


FIGHTS = {
    '_about': "Fights for the Godot era (game-design v2, sections 4.4, 4.5, 9 and 14; Claude A's "
              "to-all-assignments-1025), in Claude I's shape: camps and patrols by Codex's six roles "
              "(the kinds are proposals for Codex), low cover (shoot over) and high cover (blocks "
              "shots), waystones, the shard's crater. Camps refill on each train arrival, never on "
              "a clock. Shardstruck creatures are freed; the Company's surveyors flee. Raids come "
              "only to Crossroads (7.6), so no raiders' camp.",
    'act': 2,
    'story': "the road east (game-design v2, 8.2, act 2): the storm's shards fell on the plain, and "
             "the Company's surveyors are already staking the Lull Road for a line to Neon Harbour",
    'weapons': "the Lull's family (gaffs, net launchers) and the valley's bows; no family of its own",
    'camps': [
        {'id': 'barn_boars', 'roles': ['lunger', 'grunt', 'grunt'], 'kind': 'shardstruck boars',
         'at': [7160, 4064], 'arena': [7064, 4024, 208, 104], 'enemies': [[7144, 4056], [7176, 4072], [7160, 4088]],
         'why': "rooting in the barn's rick yard; the barn is the high cover, the rick a low one"},
        {'id': 'chapel_rooks', 'roles': ['caster', 'swarmer', 'swarmer', 'swarmer', 'swarmer'],
         'kind': 'shardstruck rooks and their rook-mother',
         'at': [8248, 4272], 'arena': [8160, 4240, 144, 104], 'enemies': [[8264, 4256], [8232, 4280], [8256, 4296], [8280, 4280], [8240, 4256]],
         'why': "in the churchyard east of the ruined chapel; the walls are high cover, the "
                "gravestones low"},
    ],
    'patrols': [
        {'id': 'company_surveyors', 'roles': ['grunt', 'shooter'],
         'kind': "the Company's surveyors and their guard (act 2 on)",
         'path': [[7256, 3896], [7760, 3896]],
         'why': "staking the Lull Road between the barn and the stones"},
    ],
    'cover': [
        {'kind': 'high', 'what': "the hay barn's wall", 'rect': [7104, 3952, 64, 48]},
        {'kind': 'low', 'what': 'the hay rick', 'rect': [7200, 4072, 24, 16]},
        {'kind': 'high', 'what': "the chapel's broken walls", 'rect': [8160, 4192, 64, 40]},
        {'kind': 'low', 'what': 'gravestones', 'rect': [8240, 4232, 48, 8]},
        {'kind': 'low', 'what': 'gravestones', 'rect': [8232, 4304, 48, 8]},
        {'kind': 'low', 'what': 'the field wall by the stones', 'rect': [7664, 4216, 96, 8]},
    ],
    'waystones': [
        {'id': 'mill_waystone', 'at': [7480, 3936], 'why': "on the Lull Road at the mill, where the "
                                                           "farm track leaves it"},
        {'id': 'shelf_waystone', 'at': [7408, 5048], 'why': "on the Coast Path at the farm track's foot"},
    ],
    'shard': {'at': [7808, 4224], 'crater': [7784, 4200, 48, 48],
              'why': "a small shard in the field by the standing stones: the stones hum with it"},
    'dungeon': {'none': True, 'why': "the land between has no dungeon; the Lull's is the Sunken "
                                     "Barges (lull-delta, Claude I)"},
}

QUEST_SPOTS = [
    {'id': 'miller', 'at': [7464, 3880],
     'quest': "the miller: the storm jammed the mill's sails, and rooks from the chapel nest in them"},
    {'id': 'farmer', 'at': [7208, 3976], 'quest': "the farmer at the barn: boars in the barley"},
    {'id': 'stones', 'at': [7712, 4152],
     'quest': "initials cut in the stone: a sweetheart's name, which the bargee's cook knows"},
    {'id': 'grave', 'at': [7096, 3416], 'quest': "an old grave under a thorn in the north fields"},
]

WINDOWS = [
    {'id': 'mill_road', 'rect': [7304, 3768, 320, 180], 'focal': [7464, 3840], 'clearing': [7560, 3936],
     'why': "the mill above the road, the waystone and the track leaving south"},
    {'id': 'barn', 'rect': [7000, 3880, 320, 180], 'focal': [7136, 3976], 'clearing': [7200, 4008],
     'why': "the barn and its rick yard, the boars' camp; the side path round the thicket"},
    {'id': 'stones', 'rect': [7600, 4064, 320, 180], 'focal': [7712, 4160], 'clearing': [7808, 4176],
     'why': "the ring of stones and the shard's crater beside it"},
    {'id': 'churchyard', 'rect': [7984, 4128, 320, 180], 'focal': [8192, 4220], 'clearing': [8104, 4200],
     'why': "the ruined chapel and its churchyard, the rooks' camp"},
    {'id': 'coast_mill', 'rect': [7120, 4880, 320, 180], 'focal': [7280, 4936], 'clearing': [7376, 5000],
     'why': "the coast mill on the shelf, the sea below"},
    {'id': 'shelf_chapel', 'rect': [7880, 4664, 320, 180], 'focal': [8008, 4760], 'clearing': [8088, 4840],
     'why': "the chapel above Gullwick's roofs, the Coast Path turning north to Lullford"},
]


def _where(at):
    paths = [r['points'] for r in routes()] + [t['points'] for t in TRODS]

    def d_seg(p, a, b):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        return ((p[0] - ax - dx * t) ** 2 + (p[1] - ay - dy * t) ** 2) ** 0.5
    d = min(d_seg(at, a, b) for pts in paths for a, b in zip(pts, pts[1:]))
    return 'beside the path' if d <= 48 else 'a short way off the path'


def plan():
    return {
        '_about': "The Lull plain as a plan (lane G): the land between the valley, Cogsworth, the "
                  "Lull belt and Gullwick, in Claude F's schema with Claude I's fights, quest spots and "
                  "windows. Generated by scripts/art/regions/lull_plain_plan.py; do not edit by hand.",
        'id': 'lull-plain', 'owner': wr.BETWEEN,
        'biome': 'meadow', 'biomes': ['meadow', 'coast'],
        'biome_variants': {'_about': "E's valley brief (scripts/art/biomes/valley.json) lists the land "
                                     "between as a user of its farmland variant; the shelf takes C's "
                                     "coast (scripts/art/biomes/coast.json)",
                           'meadow': 'valley:farmland', 'coast': 'shelf'},
        'box': BOX,
        'base_tier': {'value': 0, 'provisional': False,
                      'from': "lane G's world tiers (lib/world-routes.ts): the Lull Road at 4, the "
                              "Coast Path at 3"},
        'sources': {'land': 'lib/world-land.ts (scripts/art/world_land.py, PLAIN)',
                    'routes': 'lib/world-routes.ts (scripts/art/world_routes.py)',
                    'brief': 'docs/vision/regions/routes-thresholds-edges.md, section 5'},
        'not_mine': [{'box': [GULLWICK[0], GULLWICK[1], GULLWICK[2] - GULLWICK[0], 5168 - GULLWICK[1]],
                      'owner': 'claude-i', 'why': "Gullwick's box"}],
        'tiers': TIERS,
        'faces': {'_about': "the valley kit's turf banks: 32 px faces with a grass lip, field walls "
                            "along the top where a field ends at the bank",
                  'between_tiers': {'height': 32, 'material': 'turf bank'}},
        'water': WATER,
        'routes': routes(),
        'trods': TRODS,
        'stairs': STAIRS,
        'buildings': BUILDINGS,
        'places': PLACES,
        'named': [dict(n, where=_where(n['at'])) for n in NAMED],
        'pockets': POCKETS,
        'egg_spots': [],
        'markers': markers(),
        'obstacles': OBSTACLES,
        'edges': [{'side': 'south', 'layers': 'the sea is the edge: the shelf drops to a beach with surf; '
                                              'lane G draws the open sea past it (lib/world-land.ts)',
                   'along': [[7256, 5168], [7648, 5168]]},
                  {'side': 'north, east, west', 'layers': "none: open land into Cogsworth's coal hills, "
                                                          "the Lull belt and the valley"}],
        'thresholds': [],
        'residents': [
            {'who': 'the miller', 'at': [7464, 3880], 'note': 'at the mill door, looking up at the sails'},
            {'who': 'a farmer', 'at': [7208, 3976], 'note': "forking hay at the barn"},
            {'who': 'a heron', 'at': [7968, 3960], 'note': 'at the pools'},
            {'who': 'hares', 'at': [7840, 3720], 'note': 'in the fields north of the road'},
        ],
        'ground': {'_about': 'for the painter',
                   'north_fields': 'rough pasture with gorse clumps and dry-stone walls, sheep',
                   'plain': 'fields in hedged strips: barley, hay meadow, pasture; the road between hedges',
                   'shelf': 'short sea-turf with thrift and sea campion above the beach; marram at the edge'},
        'fights': FIGHTS,
        'quest_spots': QUEST_SPOTS,
        'windows': WINDOWS,
    }


def main():
    with open(OUT, 'w') as f:
        json.dump(plan(), f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('lull-plain: wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
