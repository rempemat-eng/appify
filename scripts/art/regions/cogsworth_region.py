"""Cogsworth's region outside the town: the land's tiers, its water, the routes laid on it and
the set pieces placed on it, as data in world px (resolution independent).

Lane H (Claude H). Matt, 21 Oct (crew board to-all-density): the art moves to a higher
density after a pilot, so until the verdict the lanes work on what carries over unchanged:
layout and composition, routes and thresholds, walk masks, set-piece placement as data, prop
logic. And 11:44 (to-all-grid-2x): outlines follow the cell grid in straight runs along x
or y with rounded corners, direction changes at cell boundaries; the detail lives inside the
shape, not in a meandering outline. This module is that layout for the region the brief
gives lane H (docs/vision/regions/cogsworth-coal-hills-narrows.md): the coal hills, the
Narrows gorge and its viaduct, Fernhollow, the Cog above and below the town, and the
named things, spoil heaps and camps along Claude G's routes. The town inside its box is
cogsworth_plan.py's.

What it holds, on the world's 8 px cells over the footprint (x 7000 to 9304, y 1700 to
3304):

- TIERS: the land's tops as rectangles on the grid, painted lowest first (a tier is a 32 px
  south face; G's tier numbers: the town's street is 7, the Cog in town 6). The massif's
  benches step down to the south-east where the High Fells come down; the Fern hills'
  shoulder carries the Foothill Road over tier 9; the coal hills rise east of the town to
  the Narrows' rims; the Cog's valley and the confluence lie low.
- WATER: the Cog above the town and below it to the confluence, the Lull through the Narrows
  and on south-east, the eel pond at Fernhollow; each a course of cells at its own tier,
  cut into the land (a cut's sides are faces where the land is higher to the north, side
  bands to the west and east).
- ROUTES: the High Fells, the Foothill Road and the Towpath inside the box, lane H's own
  lines (inside a region's box its plan draws the routes: g-to-all-region-rule), meeting
  Claude G's at the box edge (MEETS, route-meets.md), with their STAIRS, bridges, the
  pockets' trods and a side trod; each is laid at its tier, so the land under it agrees.
- SET PIECES: the named things with the prop or kit piece each needs and its footprint, the
  spoil heaps, the viaduct's piers, Fernhollow's cottages, sawpit and log stores, each a
  footprint of cells it blocks.

`check()` holds it to what a layout can show: every route vertex on land of its own tier
(within a tier-change's run), no route on water except at its crossings, no set piece on a
route, on water or in the town box, each named thing within 64 px of its route, the
gorge's water continuous from the footprint's north edge to the confluence, Fernhollow's
doors on its road, the town's gates on the tiers G gives them. `preview()` draws it.

    python3 scripts/art/regions/cogsworth_region.py --check
    python3 scripts/art/regions/cogsworth_region.py --export   (writes art/regions/cogsworth.json, the plan
                                                               in Claude F's schema, which npm run
                                                               check:region-plans holds to its rules)
    python3 scripts/art/regions/cogsworth_region.py [OUT_DIR]
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cogsworth_plan as plan  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CELL = 8
X0, Y0 = 7000, 1696
W, H = 2304, 1608                         # the footprint on the grid (x 7000 to 9304, y 1696 to 3304)
COLS, ROWS = W // CELL, H // CELL
TOWN_TIER = {0: 6, 1: 6, 2: 7, 3: 8}      # the town plan's local tiers on the world's (the canal is half a tier)

# --- the land's tops (world px rectangles, x0, y0, x1, y1), lowest first ------------------------
BASE_TIER = 5
TIERS = [
    # the Cog's valley and everything above the confluence's lowland
    (6, [(7000, 1696, 9304, 2984), (7000, 2984, 8432, 3304)]),
    # the plain's shelf west of the confluence and the hills' foot; Fernhollow on the road
    (7, [(7000, 1696, 9304, 2920), (7000, 2920, 8432, 3304)]),
    # the massif's foot across the north, the coal hills east of the town, the coal forest
    # between the Foothill Road and the High Fells, the Fern hills' shoulder above Fernhollow
    # (the notch at x 7536 to 7616 is the road's way down to the Millrace bridge)
    (8, [(7000, 1696, 9304, 2008), (8336, 2008, 9304, 2776), (7000, 2008, 7616, 2680), (7000, 2680, 7536, 3072)]),
    # the massif's benches step down south-east, one per stair of the High Fells, each a face
    # and a path's width apart (rims 56 px: a face plus more than a cell); the knoll on the
    # shoulder; the coal hills
    (9, [(7000, 1696, 7608, 1888), (7000, 1696, 9304, 1784), (7288, 2832, 7448, 2984), (8400, 2008, 9304, 2720)]),
    (10, [(7000, 1696, 7480, 1832), (7000, 1696, 9304, 1736), (8560, 2072, 9304, 2688)]),
    (11, [(7000, 1696, 7408, 1776)]),
    (12, [(7000, 1696, 7360, 1720)]),
]

# --- water: (id, tier, course of world px points, width) ------------------------------------------
WATER = [
    ('cog-upper', 6, [(7664, 1696), (7664, 1968)], 40),          # under the High Fells' footbridge (W3, G #189) at x 7664          # off the massif into the town's west side
    # the Cog below the town and the Lull through the Narrows follow the block-out's rivers
    # (docs/vision/research/blockout, #187) on the grid: the Cog joins the Lull at about
    # (8880, 3112), past the Cog foot where the Towpath crosses it
    ('cog-lower', 5, [(8328, 2904), (8368, 2904), (8368, 3064), (8632, 3064), (8632, 3112), (8888, 3112)], 48),
    ('lull-narrows', 4, [(9032, 1696), (9032, 2576), (8984, 2576), (8984, 2896), (8888, 2896), (8888, 3112)], 44),
    ('lull-below', 4, [(8888, 3112), (8888, 3200), (8920, 3200), (8920, 3304)], 72),
    ('eel-pond', 7, [(7040, 3256), (7072, 3256)], 32),
]
# where each water body comes from and goes (a stream leaving the box names where it goes)
WATER_ENDS = {
    'cog-upper': {'source': 'the massif: the Cog off the High Fells, north of the box (Claude G)', 'outlet': "the town's Cog (cogsworth_plan.py)"},
    'cog-lower': {'source': "the town's Cog, leaving its south-east corner", 'outlet': 'lull-below, at the confluence (8888, 3112)'},
    'lull-narrows': {'source': 'the Lull, from the old forest north of the box (Claude G)', 'outlet': 'lull-below, at the confluence (8888, 3112)'},
    'lull-below': {'source': 'lull-narrows and cog-lower at the confluence', 'outlet': "the Lull belt, south of the box (Claude I's lull-delta)"},
    'eel-pond': {'declared_closed': True, 'note': 'a spring-fed pond at Fernhollow'},
}
# the routes' bridges over the streams and the falls where a stream steps down a tier (lane R,
# 22 and 23 Oct: a path crosses water only on a declared bridge; a stream drops only at a fall)
WATER_ENDS['cog-upper']['bridges'] = [{'at': [7664, 1944], 'span': 64, 'kind': 'bridge',
                                       'name': "the High Fells' footbridge over the Cog (W3), a rockfall on it"}]
WATER_ENDS['cog-lower']['bridges'] = [{'at': [8496, 3064], 'span': 64, 'kind': 'bridge',
                                       'name': "the Cog foot bridge: the Towpath's footbridge to the Lull bank"}]
WATER_ENDS['cog-lower']['falls'] = [{'at': [8336, 2904], 'drop_tiers': 1,
                                     'what': "the town weir, where the Cog leaves Cogsworth for the lowland"},
                                    {'at': [8856, 3112], 'drop_tiers': 1,
                                     'what': "the Cog's last weir, into the Lull at the confluence"}]
GORGE_RIM = 2         # tiers of wall each side of the Lull's cut stand at least this high

# --- the routes inside the box: lane H's own lines -------------------------------------------
# Claude A and Claude G, 21 Oct (crew board g-to-all-region-rule, a-to-gh-meets): inside a
# region's box the region plan draws the route's line, its stairs and its width; lane G meets
# it at the box edge (docs/vision/regions/route-meets.md on claude-g/blockout) and takes the
# lines as drawn. So these are lane H's data, not a copy of lib/world-routes.ts. Every leg
# runs along x or y (to-all-grid-2x); every change of tier is a stair on a north-south leg
# rising northward, cutting a south face (eastward-edges 6.3, region_plan.py #194).
# Vertices (x, y, width, tier); the tier changes between two vertices only on a stair leg.
ROUTES = {
    # off the massif at tier 12 down four benches, a stair at each face, east along each
    # bench, over the Cog on the footbridge (W3) to the town's north gate at tier 8
    'High Fells': [(7272, 1696, 24, 12), (7272, 1764, 24, 11), (7384, 1764, 24, 11), (7384, 1820, 24, 10),
                   (7456, 1820, 24, 10), (7456, 1876, 24, 9), (7584, 1876, 24, 9), (7584, 1944, 24, 8),
                   (7824, 1944, 24, 8), (7824, 1968, 24, 8)],
    # from the home valley at tier 7 east past Fernhollow, up onto the Fern hills' shoulder,
    # north through the coal forest beside the knoll, then down to the Millrace bridge and the
    # town's west gate at tier 7
    'Foothill Road': [(7000, 3192, 48, 7), (7240, 3192, 48, 7), (7240, 3048, 48, 8), (7480, 3048, 48, 8),
                      (7480, 2808, 48, 8), (7512, 2808, 48, 8), (7512, 2648, 48, 8), (7576, 2648, 48, 8),
                      (7576, 2736, 48, 7), (7624, 2736, 48, 7)],
    # from the town's east gate on the riverside quay at tier 7 east, then south down two
    # faces, over the Cog foot on its bridge, to the Lull belt at tier 5
    'Towpath': [(8328, 2840, 32, 7), (8456, 2840, 32, 7), (8456, 2968, 32, 6), (8496, 2968, 32, 6),
                (8496, 3200, 32, 5), (8480, 3200, 32, 5), (8480, 3296, 32, 5)],
}
# Stairs: (route, x, y at the face, upper tier, lower tier, width). The upper tier is north.
STAIRS = [
    ('High Fells', 7272, 1736, 12, 11, 40), ('High Fells', 7384, 1792, 11, 10, 40),
    ('High Fells', 7456, 1848, 10, 9, 40), ('High Fells', 7584, 1904, 9, 8, 40),
    ('Foothill Road', 7240, 3088, 8, 7, 48), ('Foothill Road', 7576, 2696, 8, 7, 48),
    ('Towpath', 8456, 2936, 7, 6, 40), ('Towpath', 8496, 3000, 6, 5, 40),
]
CROSSINGS = {'High Fells': [(7664, 1944, 64)],      # the footbridge over the Cog (W3: g-to-h-cog-footbridge)
             'Foothill Road': [(7664, 2736, 80)],   # the Millrace bridge at the west gate (in the town)
             'Towpath': [(8496, 3064, 64)]}         # the Cog foot bridge
# Where lane G meets each route at the box edge (route-meets.md: cell, world px, tier, width)
MEETS = {'High Fells': (7272, 1696, 12, 24), 'Foothill Road': (7000, 3192, 7, 48), 'Towpath': (8480, 3296, 5, 32)}
# Dead-end trods to the secret pockets (lane G placed them; inside the box they are lane H's):
# (route, holds, trod points from the route, clearing), each at the tier where it leaves.
POCKET_TRODS = [
    ('High Fells', 'a story detail: a buried bell', [(7536, 1876), (7536, 1800)], (7592, 1800)),
    ('High Fells', 'a view down a gorge', [(7272, 1764), (7176, 1764)], (7176, 1764)),
    ('Foothill Road', 'a resident fishing', [(7576, 2736), (7576, 2960), (7680, 2960)], (7696, 2960)),
    ('Foothill Road', 'a story detail: a buried bell', [(7512, 2720), (7320, 2720), (7320, 2752)], (7216, 2752)),
]
# Side paths round an obstacle, inside the box (lane G's leave the box here)
SIDE_TRODS = [
    ('Towpath', 'a fallen tree: the way round, south to lane G', [(8496, 3168), (8448, 3168), (8448, 3296)]),
]
# The pocket inside the town box, laid by the town's plan
POCKETS_IN_TOWN = [('Towpath', 'a view down the Cog from the riverside quay', (8016, 2856))]
# Prop clusters outside the town (Claude B's recipes, scripts/art/prop_clusters.py): where
# each goes and why; the placer seats it beside its path, off the walk, and checks its
# reasons. (recipe, near, radius, seed). Placed in order, each keeping its distance from the
# ones before. The recipes name the coal hills 'coal-hills' (h-to-b-2110 asks for the biome
# files' ids), so each entry carries any_biome until then.
CLUSTER_SPOTS = [
    ('canal_side', (8560, 3020), 160, 1),      # the bargee's bank at the Cog foot bridge
    ('woodland_glade', (7300, 3260), 160, 1),  # Fernhollow's edge of the wet woods, south of the road
    ('woodland_glade', (7380, 2900), 160, 1),  # the coal forest beside the Foothill Road
    ('mine_yard', (7520, 1900), 200, 1),       # a prospector's adit in a bench face on the High Fells
    ('moor_wayside', (7700, 1900), 160, 1),    # a waymark where the High Fells reach the footbridge
]
# --- the Godot era (Claude A, 25 Oct: to-all-godot-1080, to-all-assignments-1025) --------------
# The game is landscape, a 960 x 540 art grid at density 3: one screen is 320 x 180 world px.
# What a zone needs beyond the layout, as data: the screens to compose, the camps (an arena with
# cover and the roles of the wild creatures in it: game/enemies' rusher, shooter, shield, elite;
# they are freed, not killed), one dungeon entrance, quest spots and waystones.
SCREEN = (320, 180)
SCREENS = [   # (id, x, y, what the frame is composed round)
    ('fernhollow', 7000, 3116, "the cottages north of the Foothill Road, the eel pond and the windmill south of it"),
    ('pit_head', 7120, 2860, "the pit head and the Deep Seam's mouth beside the road, the knoll behind"),
    ('coal_forest', 7232, 2600, "the burners' camp and the clearing in the coal forest, the road's north leg"),
    ('high_fells_descent', 7232, 1696, "the four benches and their stairs off the massif, the tor"),
    ('footbridge', 7536, 1800, "the High Fells' footbridge over the Cog, the wayside cairn, the echo cave"),
    ('spoil_loop', 8024, 1816, "the spoil heap above the town with the loop round it"),
    ('cog_foot', 8336, 2936, "the town weir, the Cog foot bridge, the lock-keeper's bench, the lookout"),
    ('gorge_head', 8520, 2760, "the tipple yard above the Narrows, the gorge's rim east"),
    ('narrows_viaduct', 8840, 2216, "the Narrows and the viaduct over the white water"),
]
CAMPS = [   # (id, arena x0, y0, x1, y1, roles, cover [(what, rect)], why)
    ('spoil_loop', 8064, 1840, 8304, 1960, ['rusher', 'rusher', 'rusher', 'shooter'],
     [('the spoil heap', (8136, 1904, 8232, 1960)), ('tipped tubs', (8088, 1864, 8104, 1880)),
      ('a sleeper stack', (8264, 1880, 8288, 1896))],
     "a shard in the heap's crown has woken the coal moles; one throws clinker from the top"),
    ('coal_forest', 7240, 2640, 7416, 2744, ['shield', 'rusher', 'rusher'],
     [('felled trunks', (7280, 2680, 7320, 2688)), ('a ring of stumps', (7360, 2704, 7376, 2720))],
     "the charcoal smoke drew a wild thicket-hog and its litter to the burners' clearing"),
    ('gorge_head', 8560, 2816, 8800, 2912, ['shooter', 'shooter', 'rusher', 'elite'],
     [('boulders off the rim', (8616, 2848, 8640, 2864)), ('a fallen viaduct stone', (8712, 2872, 8744, 2888)),
      ("the tipple's spoil", (8664, 2824, 8688, 2840))],
     "the Narrows' crows gone wild over the tipple yard, with the starfall's elite on the rim"),
]
DUNGEON = {'id': 'deep_seam', 'name': 'The Deep Seam', 'at': (7248, 3004), 'door': (7232, 2996, 7264, 3012),
           'zone': 'deep_seam', 'route': 'Foothill Road',
           'why': "the old pit under the headframe; a shard fell down the shaft and the seam glows"}
QUEST_SPOTS = [   # (id, x, y, kind, what)
    ('echo_cave', 7596, 1852, 'story', 'a voice answers from the cave in the bench face'),
    ('climbers_camp', 7308, 1820, 'story', "the fallen climber's camp: a journal and a frayed rope"),
    ('bell_fells', 7592, 1800, 'story', 'the buried bell on the High Fells (a pocket)'),
    ('bell_forest', 7216, 2752, 'story', 'the buried bell in the coal forest (a pocket)'),
    ('eel_pond', 7124, 3256, 'fetch', "the eel-catcher's lost trap"),
    ('tram_tipple', 8368, 2812, 'talk', 'the tipple-man at his chute'),
    ('rail_ruin', 8520, 2880, 'story', 'the rails end at a view down the Cog'),
    ('narrows_lookout', 8552, 2976, 'view', 'the lookout over the Narrows'),
]
WAYSTONES = [   # (id, x, y, why); the town's own is the station square's (cogsworth_plan)
    ('footbridge', 7600, 1968, "where the High Fells reach the Cog, by the wayside cairn"),
    ('fernhollow', 7300, 3150, "the hamlet on the Foothill Road"),
    ('cog_foot', 8560, 3024, "the north bank by the Cog foot bridge, on the way to Lullford"),
]
TIER_CHANGE_RUN = 64  # route px either side of a change where its tier may be either


def load_routes():
    """The routes on this land: lane H's own lines (g-to-all-region-rule)."""
    return ROUTES, CROSSINGS, 'lane H (inside the box)'


# --- set pieces: (id, what, prop or kit piece, rect of cells it stands on, world px) ----------------
SET_PIECES = [
    # named things (brief 5), each beside or a short way off its route
    ('burners-camp', 'charcoal burners\' camp', 'charcoal_clamp, burners_hut, cordwood (B #163)', (7384, 2760, 7448, 2808)),
    ('collapsed-adit', 'collapsed adit', 'a face piece of the cliff core', (7296, 3104, 7336, 3112)),
    ('pit-head', 'pit head', 'pit_head (B #163)', (7224, 2952, 7272, 2992)),
    ('windmill', 'windmill', 'windmill (B #172)', (7168, 3240, 7216, 3288)),
    ('loops-view', 'a terrace edge over the loops', 'a bench at the shoulder\'s south rim', (7144, 3040, 7176, 3064)),
    ('eel-camp', 'an eel-catcher\'s camp', 'traps, a smoking rack, a tarp (B queue)', (7104, 3240, 7144, 3272)),
    ('tor', 'a tor', 'a set piece of the cliff core\'s highland rock', (7416, 1744, 7464, 1784)),
    ('climbers-camp', 'fallen climber\'s camp', 'a tarp, a rope, a cold fire (B queue)', (7288, 1808, 7328, 1832)),
    ('echo-cave', 'echo cave', 'a face piece of the cliff core', (7576, 1840, 7616, 1864)),
    ('cairn', 'cairn', 'cairn (B, REWORK)', (7984, 1912, 8008, 1936)),
    ('crow-roost', 'a crow roost in a dead pine', 'a dead pine (forest kit) with crows', (7848, 1896, 7880, 1928)),
    ('rail-ruin', 'rail ruin', 'rails, sleepers, a tipped wagon (B queue)', (8488, 2864, 8552, 2896)),
    ('tram-tipple', 'tram tipple', 'tram_tipple (B #163)', (8344, 2808, 8392, 2816)),
    ('narrows-lookout', 'lookout over the Narrows', 'narrows_lookout (B #163)', (8536, 2960, 8568, 2992)),
    # spoil heaps (brief 2), one with the loop round it above the town
    ('spoil-1', 'spoil heap', 'a heap of shale and coal waste, its foot spread', (7512, 2232, 7608, 2296)),
    ('spoil-2', 'spoil heap (the loop)', 'the spoil heap the loop goes round', (8136, 1904, 8232, 1960)),
    ('spoil-3', 'spoil heap', 'below the riverside, by the tipple', (8392, 3104, 8456, 3144)),
    ('spoil-4', 'spoil heap', 'on the Cog\'s west bank', (7512, 2104, 7600, 2160)),
    ('spoil-5', 'spoil heap', 'on the coal hills', (8360, 2264, 8448, 2320)),
    # the Narrows Viaduct's piers, standing on the gorge's walls and its floor (rail only)
    ('viaduct-pier-w', 'viaduct pier', "the viaduct's piers (B, P4)", (8984, 2312, 9000, 2344)),
    ('viaduct-pier-m', 'viaduct pier', "the viaduct's piers (B, P4)", (9040, 2312, 9056, 2344)),
    ('viaduct-pier-e', 'viaduct pier', "the viaduct's piers (B, P4)", (9096, 2312, 9112, 2344)),
    # Fernhollow: woodcutters' cottages along the Foothill Road, the sawpit and the log stores
    ('fern-cottage-1', 'timber cottage', 'house kits: valley timber front', (7016, 3112, 7064, 3160)),
    ('fern-cottage-2', 'timber cottage', 'house kits: valley timber front', (7088, 3112, 7136, 3160)),
    ('fern-cottage-3', 'timber cottage', 'house kits: valley timber front', (7152, 3112, 7200, 3160)),
    ('fern-sawpit', 'sawpit', 'a pit with its trestle, a log on it, sawdust (B queue)', (7312, 3224, 7352, 3256)),
    ('fern-logs', 'log stores', 'log_store from the house kits, three stacks', (7376, 3224, 7424, 3256)),
]
# The land's cover and its edges in layers (brief 6): (kind, what stands there, rect).
# 'wall': the biome's three blockers in uneven patches, unwalkable; 'fade': walkable ground
# with clumps thickening toward the wall; 'wood': the coal forest's dark conifers, walkable
# under them only where a path runs. G draws what lies beyond the footprint.
COVER = [
    ('wall', 'scree, boulders and crags (the massif)', (7000, 1696, 7208, 1736)),
    ('wall', 'scree, boulders and crags (the massif)', (7376, 1696, 9304, 1736)),   # the High Fells come in between, along the bench
    ('fade', 'scree thinning among heather', (7000, 1736, 9304, 1784)),
    ('wall', 'bramble, fallen trees, then thicket and old trees (the old forest)', (9208, 1784, 9304, 3304)),
    ('fade', 'bramble and birch scrub', (9160, 1784, 9208, 3304)),
    ('wood', 'dark conifers and felled timber (the coal forest)', (7000, 2008, 7480, 2744)),
    ('wood', 'dark conifers on the coal hills', (8616, 1784, 8984, 2552)),
    ('wood', 'conifers on the hills north of the town', (7712, 1784, 8336, 1904)),
    ('wood', "the Fern hills' wet woods round Fernhollow", (7000, 2744, 7104, 3152)),
]
DOORS = {   # Fernhollow's doors: (piece, door x, door y) on the cottage's foot
    'fern-cottage-1': (7040, 3160), 'fern-cottage-2': (7112, 3160), 'fern-cottage-3': (7176, 3160),
}
NEAR = {    # named thing -> its route (brief 5)
    'burners-camp': 'Foothill Road', 'collapsed-adit': 'Foothill Road', 'pit-head': 'Foothill Road',
    'windmill': 'Foothill Road', 'loops-view': 'Foothill Road', 'eel-camp': 'Foothill Road',
    'tor': 'High Fells', 'climbers-camp': 'High Fells', 'echo-cave': 'High Fells', 'cairn': 'High Fells',
    'crow-roost': 'High Fells', 'rail-ruin': 'Towpath', 'tram-tipple': 'Towpath', 'narrows-lookout': 'Towpath',
}
NEAR_PX = {'beside': 96, 'off': 240}   # Manhattan px from the nearest point of the route's line


def _along(pts, step=8):
    """Points every `step` px along a route's line."""
    out = []
    for (ax, ay, *_), (bx, by, *_) in zip(pts[:-1], pts[1:]):
        n = max(1, int(max(abs(bx - ax), abs(by - ay)) // step))
        out += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n + 1)]
    return out


# --- rasterizing ---------------------------------------------------------------------------
def _cells(rect):
    x0, y0, x1, y1 = rect
    c0, r0 = max(0, (x0 - X0) // CELL), max(0, (y0 - Y0) // CELL)
    c1, r1 = min(COLS, -(-(x1 - X0) // CELL)), min(ROWS, -(-(y1 - Y0) // CELL))
    return slice(r0, max(r0, r1)), slice(c0, max(c0, c1))   # empty when the rect lies off the footprint


def _course(points, width):
    """The cells a course covers at a width: a square of the width stamped every 4 px along
    each run (a 45 degree step between two runs stays a step, not a box)."""
    m = np.zeros((ROWS, COLS), bool)
    hw = width // 2
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        n = max(1, int(max(abs(bx - ax), abs(by - ay)) // 4))
        for i in range(n + 1):
            x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            m[_cells((int(x - hw), int(y - hw), int(x + hw), int(y + hw)))] = True
    return m


def land():
    """The region at 8 px cells: tier (int), water (bool), route (route name or ''), town box."""
    tier = np.full((ROWS, COLS), BASE_TIER, int)
    for t, rects in TIERS:
        for r in rects:
            tier[_cells(r)] = t
    # the town: its plan's tiers on the world's
    T = plan.rasterize()['tier']                         # 4 px cells
    tx, ty = plan.TOWN_ORIGIN
    town = np.zeros((ROWS, COLS), bool)
    town[_cells((tx, ty, tx + plan.TOWN_W, ty + plan.TOWN_H))] = True
    t8 = T[::2, ::2]
    r0, c0 = (ty - Y0) // CELL, (tx - X0) // CELL
    sub = tier[r0:r0 + t8.shape[0], c0:c0 + t8.shape[1]]
    sub[:] = np.vectorize(lambda v: TOWN_TIER.get(int(v), 7))(t8[:sub.shape[0], :sub.shape[1]])
    # water cut into the land at its tier; the Lull's gorge keeps its walls standing
    water = np.zeros((ROWS, COLS), bool)
    for wid, t, pts, width in WATER:
        m = _course(pts, width) & ~town
        tier[m] = t
        water |= m
    routes, crossings, source = load_routes()
    route = np.full((ROWS, COLS), '', object)
    # each route is cut into or built up on the land at its own tier (a terrace for the path,
    # a bridge's deck over the water at its crossings); the change between two tiers falls on
    # the leg where G puts its stair or round-end
    for name, pts in routes.items():
        cross = crossings.get(name, [])
        for (ax, ay, aw, at), (bx, by, bw, bt) in zip(pts[:-1], pts[1:]):
            m = _course([(ax, ay), (bx, by)], max(aw, bw)) & ~town
            route[m & (route == '')] = name
            # a bridge's deck carries the route's tier over the water (the bridge is declared on
            # the water in WATER_ENDS, so a path crosses a stream only there)
            if at == bt:
                tier[m] = at
            mid = ((ax + bx) / 2, (ay + by) / 2)
            if any(abs(mid[0] - cx) + abs(mid[1] - cy) <= span for cx, cy, span in cross):
                water[m] = False
    for name, trods in _pocket_trods().items():
        for pts, t in trods:
            m = _course(pts, 24) & ~town & ~water & (route == '')
            tier[m] = t
    return dict(tier=tier, water=water, town=town, route=route, routes=routes, crossings=crossings, source=source)


def check(L=None, verbose=True) -> list:
    L = L or land()
    faults, notes = [], []
    tier, water, town, route = L['tier'], L['water'], L['town'], L['route']

    def cell(x, y):
        return (y - Y0) // CELL, (x - X0) // CELL

    def inside(x, y):
        return X0 <= x < X0 + W and Y0 <= y < Y0 + H
    for t, rects in TIERS:
        for (x0, y0, x1, y1) in rects:
            if any(v % CELL for v in (x0, y0, x1, y1)):
                faults.append(f'tier {t}: rect {(x0, y0, x1, y1)} is off the grid')
    # each route vertex on land of its own tier (or within a tier change's run), not on water
    for name, pts in L['routes'].items():
        cross = L['crossings'].get(name, [])
        ch = [i for i in range(1, len(pts)) if pts[i][3] != pts[i - 1][3]]
        for i, (x, y, w, t) in enumerate(pts):
            if not inside(x, y):
                continue
            r, c = cell(x, y)
            if town[r, c]:
                continue
            near_change = any(abs(x - pts[j][0]) + abs(y - pts[j][1]) <= TIER_CHANGE_RUN for j in ch)
            on_bridge = any(abs(x - cx) + abs(y - cy) <= span for cx, cy, span in cross)
            if water[r, c] and not on_bridge:
                faults.append(f'{name}: vertex {(x, y)} stands on water')
            if tier[r, c] != t and not near_change and not on_bridge:
                faults.append(f'{name}: vertex {(x, y)} at tier {t} on land of tier {tier[r, c]}')
    # the routes: legs along x or y, the ends where lane G meets them, every change of tier a
    # stair on a north-south leg with the upper tier to the north, on the face it cuts
    for name, pts in L['routes'].items():
        for (ax, ay, *_), (bx, by, *_) in zip(pts[:-1], pts[1:]):
            if ax != bx and ay != by:
                faults.append(f'{name}: leg {(ax, ay)} to {(bx, by)} runs off the grid (x or y only)')
        mx, my, mt, mw = MEETS[name]
        ends = [p for p in (pts[0], pts[-1]) if (p[0], p[1]) == (mx, my)]
        if not ends:
            faults.append(f'{name}: does not end at lane G\'s meet {(mx, my)}')
        elif (ends[0][3], ends[0][2]) != (mt, mw):
            faults.append(f'{name}: meets lane G at tier {ends[0][3]}, width {ends[0][2]} (route-meets.md: {mt}, {mw})')
        changes = [(a, b) for a, b in zip(pts[:-1], pts[1:]) if a[3] != b[3]]
        mine = [st for st in STAIRS if st[0] == name]
        for a, b in changes:
            for t in range(min(a[3], b[3]), max(a[3], b[3])):
                hit = [st for st in mine if st[4] == t and st[3] == t + 1
                       and min(a[0], b[0]) <= st[1] <= max(a[0], b[0]) and min(a[1], b[1]) <= st[2] <= max(a[1], b[1])]
                if not hit:
                    faults.append(f'{name}: tier {t + 1} to {t} between {a[:2]} and {b[:2]} has no stair')
        for _, x, y, up, down, width in mine:
            leg = [(a, b) for a, b in zip(pts[:-1], pts[1:]) if a[0] == b[0] == x and min(a[1], b[1]) <= y <= max(a[1], b[1])]
            if not leg:
                faults.append(f'{name}: stair at {(x, y)} is not on a north-south leg')
            if width < 34:
                faults.append(f'{name}: stair at {(x, y)} is {width} px (34 at least)')
            r, c = cell(x, y)
            ru, rd = cell(x, y - 20)[0], cell(x, y + 20)[0]   # the tops above and below the face's middle
            if not (tier[max(0, ru), c] == up and tier[min(ROWS - 1, rd), c] == down):
                faults.append(f'{name}: stair at {(x, y)} does not cut the face from tier {up} (north) to {down}')
    # the town plan's copies of the named things are the middles of the set pieces here
    mid = {p[0]: ((p[3][0] + p[3][2]) // 2, (p[3][1] + p[3][3]) // 2) for p in SET_PIECES}
    for nm, _k, at, *_ in plan.NAMED:
        if nm in mid and tuple(at) != mid[nm]:
            faults.append(f'cogsworth_plan.NAMED {nm} at {tuple(at)}: the set piece\'s middle is {mid[nm]}')
    # set pieces: on the grid, on land, off routes, out of the town and on the land's top
    blocks = np.zeros(tier.shape, bool)
    for pid, what, piece, rect in SET_PIECES:
        sl = _cells(rect)
        if any(v % CELL for v in rect):
            faults.append(f'{pid}: rect {rect} is off the grid')
        if water[sl].any() and 'pier' not in pid:
            faults.append(f'{pid}: stands in water')
        if (route[sl] != '').any():
            faults.append(f'{pid}: stands on {sorted(set(route[sl][route[sl] != ""]))[0]}')
        if town[sl].any():
            faults.append(f'{pid}: inside the town box')
        if blocks[sl].any():
            faults.append(f'{pid}: overlaps another set piece')
        blocks[sl] = True
        if len(set(tier[sl].ravel().tolist())) > 1 and 'pier' not in pid:
            notes.append(f'{pid}: stands across a tier edge {sorted(set(tier[sl].ravel().tolist()))}')
    # cover: a wall or a wood never closes a route (a path runs on through a wood)
    for kind, what, rect in COVER:
        sl = _cells(rect)
        if any(v % CELL for v in rect):
            faults.append(f'cover {what}: rect {rect} is off the grid')
        if kind == 'wall' and (route[sl] != '').any():
            faults.append(f'a wall ({what}) stands across a route')
    # named things within reach of their route
    for pid, rname in NEAR.items():
        rect = {p[0]: p[3] for p in SET_PIECES}[pid]
        cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
        pts = L['routes'].get(rname, [])
        d = min((abs(cx - x) + abs(cy - y) for x, y in _along(pts)), default=1e9)
        where = 'off' if pid in ('collapsed-adit', 'climbers-camp', 'cairn', 'rail-ruin', 'crow-roost') else 'beside'
        if d > NEAR_PX[where]:
            faults.append(f'{pid}: {d:.0f} px from the {rname} ({where} the path: {NEAR_PX[where]} px at most)')
    # Fernhollow's doors open onto the road (a cell of route within 24 px below the door)
    for pid, (dx, dy) in DOORS.items():
        r, c = cell(dx, dy)
        below = route[r:r + 4, c - 1:c + 2]
        if not (below != '').any():
            notes.append(f'{pid}: its door at {(dx, dy)} needs a path to the road (a garden path, drawn with the hamlet)')
    # the gorge's water runs on from the north edge to the confluence
    lull = _course(WATER[2][2], WATER[2][3])
    if not lull[0].any() or not lull[cell(8888, 3112)]:
        faults.append('the Lull does not run from the north edge to the confluence')
    # the town's gates sit on the tiers G gives them
    for g, (gx, gy), e in plan.TOWN_GATES:
        wx, wy = plan.TOWN_ORIGIN[0] + min(gx, plan.TOWN_W - 1), plan.TOWN_ORIGIN[1] + min(gy, plan.TOWN_H - 1)
        r, c = cell(wx, wy)
        want = {'High Fells': 8, 'Foothill Road': 7, 'Towpath': 7}[g]
        got = tier[min(r, ROWS - 1), min(c, COLS - 1)]
        if got != want:
            faults.append(f'the {g} gate at {(wx, wy)} is on tier {got} (G gives {want})')
    # the Godot era's data: screens inside the box; each camp's arena on one tier, dry, out of the
    # town, its cover inside it and off the routes, joined to a route on its own tier; the
    # dungeon door, quest spots and waystones on dry land near a route
    for i, x, y, _w in SCREENS:
        if not (X0 <= x and x + SCREEN[0] <= X0 + W and Y0 <= y and y + SCREEN[1] <= BOX[1] + BOX[3]):
            faults.append(f'screen {i} leaves the box')
    for i, x0, y0, x1, y1, roles, cov, _why in CAMPS:
        sl = _cells((x0, y0, x1, y1))
        t = tier[sl]
        main = np.bincount(t.ravel()).argmax()
        if (t == main).mean() < 0.85:
            faults.append(f'camp {i}: its arena is not on one tier ({(t == main).mean():.0%})')
        if water[sl].any() or town[sl].any():
            faults.append(f'camp {i}: its arena runs into water or the town')
        for w, (a, b, c, d) in cov:
            if not (x0 <= a and c <= x1 and y0 <= b and d <= y1):
                faults.append(f'camp {i}: {w} lies outside the arena')
            if (route[_cells((a, b, c, d))] != '').any():
                faults.append(f'camp {i}: {w} stands on a route')
        if not set(roles) <= {'rusher', 'shooter', 'shield', 'elite'}:
            faults.append(f'camp {i}: unknown roles {roles}')
        lab, _n = ndi.label((tier == main) & ~water)
        ids = set(np.unique(lab[sl][t == main])) - {0}
        if not ((route != '') & np.isin(lab, list(ids))).any():
            faults.append(f'camp {i}: no route reaches its arena on its tier')
    pts = [('dungeon ' + DUNGEON['id'], DUNGEON['at'])] + [('quest spot ' + q[0], q[1:3]) for q in QUEST_SPOTS] + \
          [('waystone ' + w_[0], w_[1:3]) for w_ in WAYSTONES]
    lines = [q for pts_ in L['routes'].values() for q in _along(pts_)]
    lines += [q for _n, _h, tp, cl in POCKET_TRODS for q in _along([*tp, cl])]   # the pockets' trods
    for nm, (x, y) in pts:
        r, c = cell(x, y)
        if water[r, c]:
            faults.append(f'{nm} at {(x, y)} stands in water')
        if min(abs(x - a) + abs(y - b) for a, b in lines) > 240:
            faults.append(f'{nm} at {(x, y)} is more than 240 px from a route')
    # the plan file in F's schema is this module's output, never edited by hand
    if os.path.exists(PLAN_PATH):
        with open(PLAN_PATH) as fh:
            if json.load(fh) != json.loads(json.dumps(export_plan(L))):
                faults.append(f'{os.path.relpath(PLAN_PATH, ROOT)} is stale: run cogsworth_region.py --export')
    else:
        faults.append(f'{os.path.relpath(PLAN_PATH, ROOT)} is missing: run cogsworth_region.py --export')
    if verbose:
        print(f'cogsworth region: {COLS} x {ROWS} cells; routes from {L["source"]}; '
              f'{len(SET_PIECES)} set pieces; tiers {tier.min()} to {tier.max()}')
        for n in notes:
            print('  note:', n)
        for f in faults:
            print('  FAULT:', f)
        print('cogsworth region:', 'ok' if not faults else f'{len(faults)} fault(s)')
    return faults


# --- the plan in F's schema (art/regions/<id>.json, region_plan.py) -------------------------
PLAN_PATH = os.path.join(ROOT, 'art', 'regions', 'cogsworth.json')
BASE = 4                                   # the plan's tier 0 is world tier 4 (the Lull)
BOX = [X0, Y0, W, 1600]                    # whole 32 px audit cells (y 1696 to 3296)


def _rects(mask):
    """A mask of cells as rectangles: runs along each row, merged down while they repeat."""
    out, open_ = [], {}
    for r in range(mask.shape[0] + 1):
        runs = set()
        if r < mask.shape[0]:
            row = mask[r]
            c = 0
            while c < len(row):
                if row[c]:
                    c1 = c
                    while c1 < len(row) and row[c1]:
                        c1 += 1
                    runs.add((c, c1))
                    c = c1
                else:
                    c += 1
        for key in list(open_):
            if key not in runs:
                r0 = open_.pop(key)
                out.append((key[0], r0, key[1], r))
        for key in runs:
            open_.setdefault(key, r)
    return out


def export_plan(L=None) -> dict:
    """The region (and the town's tiers) as a plan in Claude F's schema, so region_plan.py's
    checks and every reader of art/regions/ see Cogsworth the same way as the Brackens."""
    L = L or land()
    plan_box_rows = BOX[3] // CELL
    t = L['tier'][:plan_box_rows]
    tiers = []
    for k in range(int(t.min()), int(t.max()) + 1):
        if k - BASE <= 0:
            continue
        for i, (c0, r0, c1, r1) in enumerate(_rects(t == k)):
            x0, y0, x1, y1 = X0 + c0 * CELL, Y0 + r0 * CELL, X0 + c1 * CELL, Y0 + r1 * CELL
            tiers.append({'id': f't{k}_{i}', 'tier': k - BASE, 'outline': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]})
    rid = {'High Fells': 'high_fells', 'Foothill Road': 'foothill_road', 'Towpath': 'towpath'}
    kind = {'High Fells': 'path', 'Foothill Road': 'road', 'Towpath': 'path'}
    routes, trods, stairs, pockets, town_pockets = [], [], [], [], []
    for name, pts in ROUTES.items():
        routes.append({'id': rid[name], 'kind': kind[name], 'width': max(24, min(64, min(p[2] for p in pts))),
                       'owner_note': ("lane H's line inside its box (g-to-all-region-rule); lane G meets it at the box edge "
                                      f"at {list(MEETS[name][:2])}, tier {MEETS[name][2]} (route-meets.md)"),
                       'points': [[p[0], p[1]] for p in pts]})
    for name, x, y, up, down, width in STAIRS:
        stairs.append({'id': f'{rid[name]}_stair_{x}_{y}', 'on': rid[name], 'at': [x, y],
                       'from_tier': up - BASE, 'to_tier': down - BASE, 'width': width, 'kind': 'stair'})
    for i, (name, holds, pts, (cx, cy)) in enumerate(POCKET_TRODS):
        tid = f'{rid[name]}_pocket_{i}'
        trods.append({'id': tid, 'why': f'a dead end to a secret pocket: {holds}', 'width': 24,
                      'points': [list(p) for p in pts] + [[cx, cy]],
                      'dead_end': 'view' if 'view' in holds else 'story' if 'story' in holds else 'resident'})
        pockets.append({'holds': holds, 'at': [cx, cy], 'trod': tid})
    for i, (name, why, pts) in enumerate(SIDE_TRODS):
        trods.append({'id': f'{rid[name]}_side_{i}', 'why': why, 'width': 24, 'points': [list(p) for p in pts]})
    for name, holds, (cx, cy) in POCKETS_IN_TOWN:
        town_pockets.append({'holds': holds, 'at': [cx, cy], 'route': name,
                             'note': "inside the town box: laid by the town's plan on the riverside quay"})
    named = [{'thing': {'burners-camp': "charcoal burners' camp"}.get(n[0], n[0].replace('-', ' ')), 'kind': n[1], 'at': list(n[2]),
              'route': n[3], 'where': n[4], 'piece': n[5]} for n in plan.NAMED]
    markers = [{'t': k, 'what': what, 'at': list(at)} for route, pts in plan.MARKERS.items() for k, what, at in pts
               if not (plan.TOWN_ORIGIN[0] <= at[0] < plan.TOWN_ORIGIN[0] + plan.TOWN_W and plan.TOWN_ORIGIN[1] <= at[1] < plan.TOWN_ORIGIN[1] + plan.TOWN_H)
               and BOX[0] <= at[0] <= BOX[0] + BOX[2] and BOX[1] <= at[1] <= BOX[1] + BOX[3]]
    water = [dict({'id': wid, 'kind': 'stream' if width < 64 else 'river', 'width': width, 'tier': wt - BASE,
                   'points': [list(p) for p in pts]}, **WATER_ENDS[wid]) for wid, wt, pts, width in WATER]
    # none is in the cliff core's library yet: each is proposed, drawn by Claude B or the kit
    set_pieces = [{'piece': pid, 'biome': 'gorge' if 'pier' in pid else 'coal_hills', 'at': [x0, y0], 'size': [x1 - x0, y1 - y0],
                   'what': what, 'kit': piece, 'seed': i + 1, 'proposed': True}
                  for i, (pid, what, piece, (x0, y0, x1, y1)) in enumerate(SET_PIECES)]
    tx, ty = plan.TOWN_ORIGIN
    out = {
        '_about': ("Cogsworth, the coal hills, the Narrows and Fernhollow as a plan (Claude H, lane H, 21 Oct), in Claude F's "
                   "schema (docs/vision/region-plans.md). Written by scripts/art/regions/cogsworth_region.py --export from "
                   "cogsworth_region.py and cogsworth_plan.py (the town); do not edit by hand. World px on the 11264 x 6912 "
                   "canvas; tiers are this plan's (world tier = tier + base_tier)."),
        'id': 'cogsworth', 'owner': 'claude-h', 'biome': 'coal_hills', 'biomes': ['mill_town', 'gorge', 'woodland'],   # scripts/art/biomes/ (#201); Fernhollow on the woodland
        'box': BOX,
        'base_tier': {'value': BASE, 'provisional': False, 'from': "Claude G's tier numbers (route-meets.md): the town's street 7, the Lull 4"},
        'tiers': tiers,
        'routes': routes, 'trods': trods, 'stairs': stairs, 'water': water,
        'places': [{'id': p_['id'], 'kind': p_['kind'], 'at': list(p_['at']) if 'at' in p_ else list(p_['box'][:2]), 'why': p_['why']}
                   for p_ in plan.PLACES],
        'town': {'origin': [tx, ty], 'size': [plan.TOWN_W, plan.TOWN_H], 'plan': 'scripts/art/regions/cogsworth_plan.py',
                 'placements': plan.placements()},
        'named': named, 'pockets': pockets, 'pockets_in_town': town_pockets,
        'egg_spots': [{'what': w, 'at': list(at), 'keep_clear_r': 32} for w, at in plan.RESERVED],
        'markers': markers,
        'obstacles': [],
        'set_pieces': set_pieces,
        'edges': [{'side': kind, 'what': what, 'rect': list(rect)} for kind, what, rect in COVER],
        'thresholds': [{'id': t_['id'], 'at': list(t_['at']), 'route': t_['route'], 'sides': list(t_['sides']), 'band': list(t_['band']),
                        'landmark': t_['landmark'], 'residents': t_['residents']} for t_ in plan.THRESHOLDS],
        'residents': [{'who': 'woodcutter', 'at': [7240, 3060], 'note': 'Fernhollow'}, {'who': 'charcoal burner', 'at': [7416, 2816], 'note': "the burners' camp"},
                      {'who': 'bargee', 'at': [8528, 3024], 'note': 'the Cog foot (threshold), on the north bank by the bridge'}],
        'ground': {'_about': "Ground kinds by place; the coal hills' own colour is dark green and black spoil (world plan 5.3).",
                   'coal hills': 'rough sooty grass, heather out of flower, shale and spoil, dark conifers',
                   'the Narrows': 'gritstone walls, white water, ferns in the spray',
                   'Fernhollow': 'wet woodland floor, ferns, sawdust and log stores, a cottage garden each',
                   'the town': "cogsworth_plan.py's ground kinds"},
    }
    # the markers and named things moved to the nearest point beside their path, off it and off
    # its stairs, by F's own placer (region_plan.fix), so the plan passes region_plan's checks
    sys.path.insert(0, os.path.dirname(HERE))
    import region_plan
    for m in out['markers']:
        m.setdefault('moved_from', list(m['at']))
    region_plan.fix(out)
    for m in out['markers']:
        if m.get('moved_from') == m['at']:
            m.pop('moved_from')
    out['clusters'] = _clusters(out)
    out['screen'] = {'size': list(SCREEN), 'why': '960 x 540 art at density 3 (docs/godot.md)'}
    out['screens'] = [{'id': i, 'rect': [x, y, *SCREEN], 'what': w} for i, x, y, w in SCREENS]
    out['camps'] = [{'id': i, 'arena': [x0, y0, x1 - x0, y1 - y0], 'tier': int(L['tier'][((y0 + y1) // 2 - Y0) // CELL, ((x0 + x1) // 2 - X0) // CELL]) - BASE,
                     'roles': roles, 'cover': [{'what': w, 'rect': [a, b, c - a, d - b]} for w, (a, b, c, d) in cov], 'why': why}
                    for i, x0, y0, x1, y1, roles, cov, why in CAMPS]
    out['dungeon'] = dict(DUNGEON, at=list(DUNGEON['at']), door=[DUNGEON['door'][0], DUNGEON['door'][1],
                                                               DUNGEON['door'][2] - DUNGEON['door'][0], DUNGEON['door'][3] - DUNGEON['door'][1]])
    out['quest_spots'] = [{'id': i, 'at': [x, y], 'kind': k, 'what': w} for i, x, y, k, w in QUEST_SPOTS]
    out['waystones'] = [{'id': i, 'at': [x, y], 'why': w} for i, x, y, w in WAYSTONES]
    return out


def _clusters(out) -> list:
    """CLUSTER_SPOTS seated by Claude B's placer on the finished plan, in order."""
    import prop_clusters as pc
    placed = []
    # the set pieces stand where they stand: walls to the placer, as a plan's structures are
    walls = [{'id': sp['piece'], 'kind': 'set_piece', 'rect': [sp['at'][0], sp['at'][1], sp['size'][0], sp['size'][1]]}
             for sp in out['set_pieces']]
    for recipe, near, radius, seed in CLUSTER_SPOTS:
        e, faults = pc.place(dict(out, clusters=placed, structures=walls), recipe, near=near, seed=seed, others=placed,
                             radius=radius)
        if e is None:
            raise SystemExit(f'cogsworth: {recipe} near {near} finds no place: {faults}')
        e.pop('replaces', None)
        e['any_biome'] = True
        placed.append(e)
    return placed


def _route_tier_at(name, x, y):
    """The tier of the route vertex nearest (x, y)."""
    return min(ROUTES[name], key=lambda p: abs(p[0] - x) + abs(p[1] - y))[3]


def _pocket_trods():
    """The dead-end trods to the pockets and the side trods, each at the tier of the route
    where it leaves."""
    out = {}
    for name, holds, pts, clearing in POCKET_TRODS:
        out.setdefault(name, []).append((list(pts) + [clearing], _route_tier_at(name, *pts[0])))
    for name, why, pts in SIDE_TRODS:
        out.setdefault(name, []).append((list(pts), _route_tier_at(name, *pts[0])))
    return out


def preview(L=None, scale=0.5):
    """The region in its tiers (darker lower), water, routes, the town and the set pieces."""
    L = L or land()
    t = L['tier']
    lo, hi = t.min(), t.max()
    v = ((t - lo) / max(1, hi - lo))
    img = np.zeros((ROWS, COLS, 3), np.uint8)
    img[..., 0] = (70 + 110 * v).astype(np.uint8)
    img[..., 1] = (90 + 100 * v).astype(np.uint8)
    img[..., 2] = (60 + 60 * v).astype(np.uint8)
    face = np.zeros(t.shape, bool)
    face[1:] = t[:-1] > t[1:]
    img[face] = (img[face] * 0.45).astype(np.uint8)
    img[L['water']] = (60, 110, 170)
    img[L['route'] != ''] = (214, 190, 140)
    img[L['town'] & (L['route'] == '')] = (img[L['town'] & (L['route'] == '')] * 0.8 + np.array([60, 20, 20])).astype(np.uint8)
    k = CELL * scale
    pic = Image.fromarray(img).resize((int(COLS * k), int(ROWS * k)), Image.NEAREST)
    d = ImageDraw.Draw(pic)
    for kind, what, (x0, y0, x1, y1) in COVER:
        col = {'wall': (60, 50, 50), 'fade': (140, 120, 90), 'wood': (30, 70, 40)}[kind]
        d.rectangle(((x0 - X0) * scale, (y0 - Y0) * scale, (x1 - X0) * scale - 1, (y1 - Y0) * scale - 1), outline=col, width=2)
    for pid, what, piece, (x0, y0, x1, y1) in SET_PIECES:
        box = ((x0 - X0) * scale, (y0 - Y0) * scale, (x1 - X0) * scale - 1, (y1 - Y0) * scale - 1)
        d.rectangle(box, outline=(255, 220, 80), fill=(120, 60, 40) if 'spoil' in pid else None)
        if 'spoil' not in pid and 'pier' not in pid:
            d.text((box[2] + 2, box[1]), pid, fill=(255, 245, 210))
    for tt in range(lo, hi + 1):
        ys, xs = np.nonzero(t == tt)
        if len(ys):
            i = len(ys) // 2
            d.text((xs[i] * k, ys[i] * k), str(tt), fill=(255, 255, 255))
    return pic


def main(argv):
    if '--check' in argv:
        sys.exit(1 if check() else 0)
    if '--export' in argv:
        with open(PLAN_PATH, 'w') as fh:
            json.dump(export_plan(), fh, indent=1)
            fh.write('\n')
        try:   # the repository's formatter, as every other JSON under art/ is written
            import subprocess
            subprocess.run(['npx', 'oxfmt', '--write', PLAN_PATH], cwd=ROOT, capture_output=True, timeout=120)
        except Exception:  # noqa: BLE001 (the check compares the data, not its layout)
            pass
        print('wrote', PLAN_PATH)
        return
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-cogsworth-region')
    os.makedirs(out, exist_ok=True)
    L = land()
    preview(L).save(os.path.join(out, 'region-half.png'))
    print('wrote', out)
    sys.exit(1 if check(L) else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
