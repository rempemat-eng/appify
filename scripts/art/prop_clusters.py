"""Prop clusters as data: named recipes that build atmosphere from props, a seeded placer
that drops one into a region plan, and the checks that keep it walkable and tappable.

Claude B, 21 Oct (crew board a-to-b-clusters). Matt, 21 Oct: "i really want you to use
eastwards soft grids, cleanliness, the way they create atmosphere using props and their
pixel density". Eastward's places feel lived in because props come in groups with a job:
a tree with a bench in its shade and a lamp beside it, a hedge with a stile where the path
goes through, a cart with the sacks stacked against it. Ground between the groups stays
calm (to-all-clean). This file holds those groups as data so every lane builds them the
same way, at any art density: every number here is in world units (8 px cells, world px),
never in texels, so the library carries over unchanged when the art moves to 2x.

A recipe is drawn with its front to the south (the side a walker comes from, where the
path runs). Each member names a size-guide kind, the prop keys that may fill it (in order
of preference), its foot in cells, whether it blocks the walk, whether it is tapped (then
it gets a 34 x 34 world px hit box at its foot, 45 CSS px on a 402 px phone: size-guide 1),
where the walker stands to use it, and its light and shadow. Clear zones (a bench's front,
a door's apron, a fire's ring) stay walkable. Plant dressing grows at the bases of the
members that ask for it, one clump every 16 to 32 world px (eastward-edges 8: one per 16
to 32 of edge), never on a path, a clear zone or a stand.

The placer turns and mirrors a recipe so its front faces the nearest path, snaps it to the
8 px grid and keeps the first candidate (in seeded order) that passes every check:

- each footprint inside the area and the plan's box, on one tier, off faces, one cell back
  from a lip (world-rules 6.5; region_plan's tiers and faces, Claude F's schema);
- no blocking foot, dressing or clear zone on a route, trod or stair (the walking band:
  world-rules 6.6), except a recipe's crossing (a stile in a hedge), which a path must run
  through;
- every stand and clear zone reachable from a path on the walk grid (4 px), and nothing
  that was reachable before (paths, markers, named things, other clusters) cut off;
- hit boxes at least 34 x 34 and apart from every other hit box (this cluster's, other
  clusters', the plan's interactable markers);
- clusters at least 4 cells apart (world-rules 6.3), at most 4 live glows a screen area
  (art-style.md: "a handful of live glows per screen").
- on dry ground: a plan's water (streams and rivers by width, pools and lakes by outline,
  the sea outside a 'coast' outline) and its buildings drawn as rects are walls, and no
  ground prop stands in them (world-rules 6.1);
- every member keeps its reason (prop-logic.md 2: owner, job, way in, footing, neighbours):
  each recipe names its owner, each member its job, and the placement rules in REASONS say
  why it stands there: a bench faces a path or a view, a lamp lights a path, a rail stands by
  the street, a boat or a bollard by water, stores by a building or a lived-in place.

Cluster places a lane writes by hand (no 'orient' yet, as lane D's plans have them) are
listed as notes, not faults, until they are turned into placements with --place.

Plans carry placements as {"recipe", "at", "orient", "mirror", "seed"} under "clusters"
(the shape of the cliff core's set-piece placements, {piece, biome, at, seed}); `--check`
holds every plan in art/regions/ that has some to the same rules.

Run:
    python3 scripts/art/prop_clusters.py --build      (writes scripts/art/prop_clusters.json)
    python3 scripts/art/prop_clusters.py --check      (recipes, the JSON up to date, the
                                                       placer's self-test, plans' clusters)
    python3 scripts/art/prop_clusters.py --place PLAN RECIPE (--area ID | --near X,Y) [--seed N]
                                                      (PLAN: an id in art/regions/ or a .json path)
                                                      (prints a placement for the plan)
    python3 scripts/art/prop_clusters.py --draw [OUT_DIR] (a diagram of each recipe: feet,
                                                       clear zones, stands, hit boxes, dressing)
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'prop_clusters.json')
PLANS = os.path.join(ROOT, 'art', 'regions')
SIZE_GUIDE = os.path.join(HERE, 'size_guide.json')
LEDGER = os.path.join(HERE, 'asset_ledger.json')

CELL = 8            # the soft grid (size-guide 1)
WALK = 4            # the walk grid
FACE = 32           # a tier's south face hangs 32 px under its rim (region_plan.Ground)
HIT = 34            # a tappable prop's hit box, world px (size-guide 1)
ART_ACROSS = 300    # world px across the phone (lib/pixel-scale.ts)
PHONE_CSS = 402     # the narrowest phone we lay out for (README: play-test at 402 x 874)
MIN_TOUCH_CSS = 44
DRESS_EVERY = (16, 32)   # plant dressing at bases, world px apart (eastward-edges 8, ours)
CLUSTER_GAP = 4 * CELL   # clusters of different owners at least 4 cells apart (world-rules 6.3)
GLOWS_PER_AREA = 4
BESIDE = 48         # 'beside the path' (region_plan.BESIDE): a front this near a path
ORIENTS = ('s', 'e', 'w', 'n')
FRONT = {'s': (0, 1), 'n': (0, -1), 'e': (1, 0), 'w': (-1, 0)}

# plant dressing by biome: small, clumped, placed by rule (to-all-clean: never speckle)
DRESSING = {
    'meadow': ['tuft', 'flowers_white', 'flowers_yellow'],
    'field': ['tuft', 'cow_parsley', 'poppies'],
    'farm': ['tuft', 'nettles', 'dock'],
    'shore': ['marram', 'sea_pinks'],
    'woodland': ['fern_small', 'tuft_shade', 'bluebells'],
    'town': ['joint_weeds', 'moss_joint'],
    'steppe': ['feather_grass', 'dry_tuft'],
    'moor': ['heather', 'bilberry', 'tuft'],
    # Claude C's biome plants (scripts/art/biomes/coast.json and city.json, #196)
    'coast': ['marram', 'thrift', 'sea_campion'],
    'isles': ['sea_grape', 'marram'],
    'rainforest': ['fern_small', 'moss_cushion'],
    'canal': ['joint_weeds', 'buddleia'],
    # Claude D's plants (art/regions/sunstone.json, #193)
    'desert': ['sage', 'bunchgrass'],
    'oasis': ['reeds', 'bunchgrass'],
}


def m(role, kind, props, at, foot, blocks=True, tap=False, stand=None, turn=None, place='ground',
      shadow='cast', crown=None, light=None, dress=True, story=False, against=None, optional=False,
      fixed=False, job=None, reason=None):
    """A member: role in the cluster, size-guide kind, prop keys by preference, foot cell
    offset and size (cells), and how it behaves. `turn` gives the props and kind for the
    east-, west- and north-facing turns of a member that faces somewhere (a bench); a
    member with a `turn` may only take the turns it lists ('s' is always its own). A
    `fixed` member has one view (a tent's door, a cart's shafts, a boat's keel line) and
    keeps its cluster facing south (mirroring is still allowed)."""
    if fixed:
        turn = {'fixed': True}
    out = {'job': job} if job else {}
    out.update({'role': role, 'kind': kind, 'props': props, 'at': list(at), 'foot': list(foot),
           'blocks': blocks, 'tap': tap, 'place': place, 'shadow': shadow, 'dress': dress})
    if reason:
        out['reason'] = list(reason)  # placement-logic rules (REASONS), checked in a plan
    if stand:
        out['stand'] = [list(p) for p in stand]
    if turn:
        out['turn'] = turn
    if crown:
        out['crown'] = crown    # cells: the crown's radius over the foot, for the shade pool
    if light:
        out['light'] = light    # {"glow": world px radius, "live": bool, "colour": name}
    if story:
        out['story'] = True     # the cluster's one personal object (world-rules 6.3)
    if against:
        out['against'] = against  # role it must stand within 1 cell of (world-rules 6.4)
    if optional:
        out['optional'] = True
    return out


BENCH_TURN = {'e': {'props': ['bench_east'], 'kind': 'bench_side'},
              'w': {'props': ['bench_west'], 'kind': 'bench_side'}}

RECIPES = {
    'meadow_nook': {
        'biomes': ['meadow', 'valley', 'park', 'moor'],
        'dressing': 'meadow',
        'why': 'a rest under a tree beside the way: the bench in the tree\'s shade faces the path, '
               'a lamp at its east end lights it at night, flowers at the trunk and the bench legs',
        'size': [10, 7],
        'members': [
            m('tree', 'broadleaf', ['oak', 'tree', 'beech'], (2, 3), (1, 1), crown=3.5, shadow='pool'),
            m('bush', 'bush', ['bush', 'holly'], (0, 4), (2, 1)),
            m('bench', 'bench', ['bench_oak', 'bench', 'forest_bench'], (4, 4), (4, 1), tap=True,
              stand=[(5, 5), (6, 5)], turn=BENCH_TURN),
            m('lamp', 'lamp', ['lamp', 'lantern'], (9, 4), (1, 1), light={'glow': 40, 'live': True, 'colour': 'lamp'}),
            m('flowers', 'flowers', ['flowers_white', 'flowers_yellow'], (1, 5), (2, 1), blocks=False, dress=False),
        ],
        'clear': [{'why': 'the bench\'s front (size-guide 1: 4 x 2)', 'rect': [4, 5, 4, 2]}],
        'decals': [{'what': 'shade pool under the crown', 'of': 'tree'}],
    },
    'field_edge': {
        'biomes': ['meadow', 'valley', 'field', 'farm', 'moor'],
        'dressing': 'field',
        'why': 'a field boundary where a footpath goes through: a hedge either side of a step stile in a gap of 4 cells (a 24 px trod centred on a grid line keeps its band clear of both hedge ends), '
               'a hedgerow oak, cow parsley and tufts along the hedge foot on both sides',
        'size': [14, 6],
        'members': [
            m('hedge_w', 'hedge', ['hedge'], (0, 2), (5, 2), shadow='cast',
              turn={'e': {'props': ['hedge_side'], 'kind': 'hedge'}, 'w': {'props': ['hedge_side'], 'kind': 'hedge'},
                    'n': {'props': ['hedge'], 'kind': 'hedge'}}),
            m('stile', 'gate', ['stile_step', 'squeeze_stile'], (5, 2), (4, 2), blocks=False, dress=False,
              turn={'e': {'props': ['stile_step_side'], 'kind': 'gate'}, 'w': {'props': ['stile_step_side'], 'kind': 'gate'},
                    'n': {'props': ['stile_step'], 'kind': 'gate'}}),
            m('hedge_e', 'hedge', ['hedge'], (9, 2), (5, 2),
              turn={'e': {'props': ['hedge_side'], 'kind': 'hedge'}, 'w': {'props': ['hedge_side'], 'kind': 'hedge'},
                    'n': {'props': ['hedge'], 'kind': 'hedge'}}),
            m('hedgerow_tree', 'broadleaf', ['oak', 'beech'], (12, 1), (1, 1), crown=3, shadow='pool',
              optional=True),
        ],
        'clear': [{'why': 'the stile\'s approach, south', 'rect': [5, 4, 4, 2]},
                  {'why': 'the stile\'s approach, north', 'rect': [5, 0, 4, 2]}],
        'crossing': {'rect': [5, 0, 4, 6], 'max_width': 24,
                     'why': 'a footpath (a trod, 24 px) runs through the stile, north to south; a road gets a gate'},
    },
    'farmyard': {
        'biomes': ['farm', 'valley', 'field'],
        'dressing': 'farm',
        'why': 'the work corner of a yard: a handcart with sacks and crates stacked against it and a '
               'barrel at its tail, a stone trough with its front clear for the beasts, a bale, the '
               'farmer\'s boots left by the trough (the personal object)',
        'size': [13, 6],
        'members': [
            m('cart', 'handcart', ['handcart', 'cart'], (0, 1), (4, 2), fixed=True),
            m('sacks', 'sack', ['sack'], (4, 1), (1, 1), against='cart', dress=False),
            m('crates', 'crate_stack', ['crate', 'lobster_pots'], (4, 2), (2, 1), against='cart', dress=False),
            m('barrel', 'barrel', ['barrel', 'trough_barrel'], (6, 2), (1, 1), against='crates', dress=False),
            m('bale', 'bale', ['round_bale', 'haystack'], (11, 0), (2, 2)),
            m('trough', 'trough', ['trough_stone', 'trough_timber', 'trough'], (8, 3), (4, 1), tap=True,
              stand=[(9, 4), (10, 4)]),
            m('boots', 'furniture_low', ['boots'], (12, 3), (1, 1), blocks=False, dress=False, story=True),
        ],
        'clear': [{'why': 'the trough\'s front', 'rect': [8, 4, 4, 2]}],
        'decals': [{'what': 'worn yard ground and straw', 'rect': [0, 3, 8, 3]}],
    },
    'shore': {
        'biomes': ['shore', 'coast', 'beach', 'isles'],
        'dressing': 'shore',
        'from_path': 160,  # the beach above the tideline, a short way off the shore path
        'why': 'a fisher\'s bit of beach above the tideline: a boat drawn up keel-up, a net rack with '
               'pots and a buoy stacked against it, a driftwood log to sit on facing the sea, an oilskin '
               'hat left on the boat (the personal object), marram at the bases',
        'size': [14, 6],
        'members': [
            m('boat', 'rowing_boat', ['upturned_boat', 'boat_blue', 'boat_red'], (0, 1), (7, 2), fixed=True),
            m('net_rack', 'net_rack', ['net_rack'], (8, 1), (5, 1)),
            m('pots', 'crate_stack', ['lobster_pots'], (8, 2), (2, 1), against='net_rack', dress=False),
            m('buoy', 'buoy', ['buoy'], (13, 1), (1, 1), against='net_rack', dress=False),
            m('log', 'log', ['driftwood', 'mossy_log'], (3, 4), (5, 1), tap=True, stand=[(4, 5), (5, 5)]),
            m('hat', 'furniture_low', ['oilskin_hat'], (1, 3), (1, 1), blocks=False, dress=False, story=True),
        ],
        'clear': [{'why': 'the log\'s front, toward the sea', 'rect': [3, 5, 5, 1]}],
    },
    'woodland_glade': {
        'biomes': ['woodland', 'forest', 'valley'],
        'dressing': 'woodland',
        'why': 'an open glade ringed by trees, a mossy log to sit on at its south side, a stump and '
               'ferns at the trunks, a sun patch on the open ground (light fades may dither: '
               'eastward-edges 5.4)',
        'size': [12, 10],
        'members': [
            m('tree_nw', 'broadleaf', ['oak', 'beech'], (1, 1), (1, 1), crown=3, shadow='pool'),
            m('tree_n', 'birch', ['birch'], (6, 0), (1, 1), crown=2.5, shadow='pool'),
            m('tree_ne', 'broadleaf', ['beech', 'oak'], (10, 2), (1, 1), crown=3, shadow='pool'),
            m('tree_sw', 'young_tree', ['sapling', 'tree_small'], (0, 7), (1, 1), crown=2, shadow='pool'),
            m('log', 'log', ['mossy_log'], (4, 7), (5, 1), tap=True, stand=[(5, 8), (6, 8), (7, 8)]),
            m('stump', 'stump', ['stump'], (10, 7), (1, 1)),
            m('ferns', 'fern', ['fern', 'fern_small'], (2, 4), (2, 1), blocks=False, dress=False),
            m('mushrooms', 'flowers', ['mushroom_ring', 'agaric'], (8, 5), (1, 1), blocks=False, dress=False,
              story=True),
        ],
        'clear': [{'why': 'the glade\'s open middle', 'rect': [3, 3, 5, 3]},
                  {'why': 'the log\'s front', 'rect': [4, 8, 5, 2], 'front': True}],
        'lights': [{'kind': 'sun_patch', 'at': [5.5, 4.5], 'r': 24, 'live': False}],
    },
    'town_square_corner': {
        'biomes': ['town', 'village', 'city', 'valley'],
        'dressing': 'town',
        'why': 'a corner of a square against a wall: a lamp at the corner, a bench along the wall '
               'facing out, a planter at its end, a noticeboard with its front clear, a cat\'s saucer '
               'by the planter (the personal object); weeds only in the paving\'s joints',
        'size': [11, 5],
        'members': [
            m('lamp', 'lamp', ['lamp', 'gas_lamp', 'city_lamp'], (0, 1), (1, 1),
              light={'glow': 40, 'live': True, 'colour': 'lamp'}),
            m('bench', 'bench', ['bench', 'bench_oak', 'iron_bench'], (1, 1), (4, 1), tap=True,
              stand=[(2, 2), (3, 2)], turn=BENCH_TURN),
            m('planter', 'planter', ['potted_plant', 'planter'], (5, 1), (2, 1)),
            m('saucer', 'furniture_low', ['bowl'], (7, 2), (1, 1), blocks=False, dress=False, story=True),
            m('noticeboard', 'sign', ['noticeboard_glazed', 'noticeboard_roofed', 'notice_board'], (9, 1), (1, 1),
              tap=True, stand=[(9, 2)]),
        ],
        'clear': [{'why': 'the bench\'s front', 'rect': [1, 2, 4, 2]},
                  {'why': 'the noticeboard\'s front', 'rect': [8, 2, 3, 2]}],
        'against': 'a wall or a face along the north side',
    },
    'steppe_camp': {
        'biomes': ['steppe', 'desert', 'moor'],
        'dressing': 'steppe',
        'why': 'a herders\' camp: a tent with its door to the fire, a fire ring with a kettle on it '
               '(the personal object), sacks against the tent, a camel kneeling on the lee side, '
               'feather grass at the bases',
        'size': [18, 8],
        'from_path': 160,  # a short way off the way (region_plan.OFF), not beside it
        'members': [
            m('tent', 'tent', ['tent'], (0, 0), (8, 4), fixed=True),
            m('sacks', 'sack', ['sack'], (8, 2), (1, 1), against='tent', dress=False),
            m('fire', 'campfire', ['fire_pit', 'campfire'], (10, 4), (3, 2), tap=True, stand=[(9, 5), (13, 5), (11, 6)],
              light={'glow': 48, 'live': True, 'colour': 'fire'}, dress=False),
            m('kettle', 'furniture_low', ['kettle'], (12, 4), (1, 1), blocks=False, dress=False, story=True),
            m('camel', 'camel', ['camel', 'camel_b'], (12, 0), (6, 2), place='ground'),
        ],
        'clear': [{'why': 'the tent door\'s apron (size-guide 1: 4 x 2)', 'rect': [2, 4, 4, 2]},
                  {'why': 'the fire\'s ring, 1 cell all round', 'rect': [9, 6, 5, 1]}],
        'decals': [{'what': 'a rug before the door', 'rect': [2, 4, 4, 1]}],
    },
    'moor_wayside': {
        'biomes': ['moor', 'highland', 'valley'],
        'dressing': 'moor',
        'why': 'a wayside rest on open moor: a stone bench in the lee of a cairn and a standing stone, '
               'gorse behind, a sprig of heather left on the stone (the personal object)',
        'size': [11, 5],
        'members': [
            m('gorse', 'bush', ['gorse_a', 'gorse_b', 'bush'], (0, 0), (3, 2)),
            m('cairn', 'cairn', ['cairn_trail', 'cairn_tall', 'cairn'], (3, 1), (2, 2)),
            m('bench', 'bench', ['bench_stone', 'bench_oak'], (5, 2), (4, 1), tap=True, stand=[(6, 3), (7, 3)],
              turn={'e': {'props': ['bench_stone_side'], 'kind': 'bench_side'},
                    'w': {'props': ['bench_stone_side'], 'kind': 'bench_side'}}),
            m('stone', 'standing_stone', ['standing_stone_low', 'standing_stone'], (9, 1), (2, 1)),
            m('sprig', 'flowers', ['heather_sprig'], (10, 2), (1, 1), blocks=False, dress=False, story=True),
        ],
        'clear': [{'why': 'the bench\'s front', 'rect': [5, 3, 4, 2]}],
    },
    # --- asked for by lane H (h-to-b-1240): the wharf and the lock -----------------------
    'canal_side': {
        'biomes': ['town', 'city', 'coal-hills', 'canal', 'valley'],
        'dressing': 'canal',
        'owner': 'the lock-keeper and the boat people',
        'why': 'the coping of a canal or lock beside the towpath: bollards at the edge to tie up to, '
               'a mooring ring let into the coping, a coil of rope left by a boat, the lock-keeper\'s '
               'bench facing the towpath, his tin mug on it (the personal object)',
        'size': [12, 4],
        'members': [
            m('bollard_w', 'bollard', ['bollard', 'city_quay_bollard'], (1, 0), (1, 1), dress=False,
              job='a boat ties up to it', reason=['by:water:16']),
            m('ring', 'bollard', ['mooring_ring'], (5, 0), (1, 1), blocks=False, dress=False,
              job='a ring in the coping for a short stop', reason=['by:water:16']),
            m('rope', 'furniture_low', ['rope_coil'], (3, 0), (1, 1), dress=False,
              job='rope coiled down off a boat', against='bollard_w'),
            m('bollard_e', 'bollard', ['bollard', 'city_quay_bollard'], (10, 0), (1, 1), dress=False,
              job='a boat ties up to it', reason=['by:water:16']),
            m('bench', 'bench', ['iron_bench', 'bench'], (5, 1), (4, 1), tap=True, stand=[(6, 2), (7, 2)],
              turn=BENCH_TURN, job='the lock-keeper sits and waits for boats', reason=['faces:path|view']),
            m('mug', 'furniture_low', ['tin_mug'], (9, 1), (1, 1), blocks=False, dress=False, story=True,
              job='the lock-keeper\'s tea'),
        ],
        'clear': [{'why': 'the bench\'s front', 'rect': [5, 2, 4, 2], 'front': True}],
    },
    # --- asked for by lane C (c-to-b-isle-recipes): the Tidebloom Isles -------------------
    'lagoon_hamlet': {
        'biomes': ['coast', 'isles', 'beach'],
        'dressing': 'isles',
        'owner': 'the fruit packers of Lagoon Landing',
        'why': 'the yard by the packing shed\'s door: a hammock slung between two palms, crates of fruit '
               'stacked against each other, a water butt at the end of the stack under the eave, a sun hat '
               'left on the ground by the far palm (the personal object)',
        'size': [13, 4],
        'members': [
            m('palm_w', 'palm', ['palm', 'coconut_palm'], (0, 1), (1, 1), crown=3, shadow='pool',
              job='nature; holds one end of the hammock'),
            m('hammock', 'hammock', ['hammock'], (1, 1), (6, 1), tap=True, stand=[(3, 2), (4, 2)],
              job='a rest between shifts', dress=False, fixed=True),
            m('palm_e', 'palm', ['palm', 'coconut_palm'], (7, 1), (1, 1), crown=3, shadow='pool',
              job='nature; holds the other end'),
            m('hat', 'furniture_low', ['sun_hat'], (8, 2), (1, 1), blocks=False, dress=False, story=True,
              job='a packer\'s hat'),
            m('crates', 'crate_stack', ['fruit_crates', 'crate'], (9, 1), (2, 1), dress=False,
              job='fruit packed for the ferry', reason=['by:dwelling:96']),
            m('crate_b', 'crate', ['fruit_crates', 'crate'], (11, 1), (1, 1), against='crates', dress=False,
              job='an empty waiting to be filled'),
            m('water_butt', 'barrel', ['water_butt', 'barrel'], (12, 1), (1, 1), against='crate_b', dress=False,
              job='rain off the shed roof', reason=['by:dwelling:96']),
        ],
        'clear': [{'why': 'the hammock\'s front', 'rect': [1, 2, 6, 2], 'front': True}],
    },
    'turtle_beach': {
        'biomes': ['coast', 'isles', 'beach'],
        'dressing': 'coast',
        'from_path': 160,
        'owner': 'the turtle warden',
        'why': 'a nest kept clear above the tideline: a ring of shells round it that nobody steps in, the '
               'warden\'s tally post with this season\'s count, a slate tied to it (the personal object); '
               'no boat, nothing on the sand between the nest and the sea',
        'size': [9, 5],
        'members': [
            m('nest', 'rock', ['shell_ring'], (1, 1), (3, 2), dress=False,
              job='the nest, ringed with shells so it is not trodden on', reason=['by:water:128']),
            m('post', 'sign', ['tally_post'], (6, 1), (1, 1), tap=True, stand=[(6, 2)],
              job='the warden counts the nests on it', reason=['by:water:160']),
            m('slate', 'furniture_low', ['tally_slate'], (7, 1), (1, 1), blocks=False, dress=False, story=True,
              job='the warden\'s slate'),
        ],
        'clear': [{'why': 'the tally post\'s front', 'rect': [5, 2, 3, 2], 'front': True},
                  {'why': 'the sand round the nest', 'rect': [0, 3, 5, 2]}],
    },
    'rainforest_clearing': {
        'biomes': ['coast', 'isles', 'rainforest', 'woodland'],
        'dressing': 'rainforest',
        'owner': 'the naturalist',
        'why': 'a clearing under the giant tree: tree ferns either side, the naturalist\'s specimen table '
               'with its front clear, a mossy log to sit on, a butterfly net leaning by the table (the '
               'personal object)',
        'size': [11, 6],
        'members': [
            m('fern_w', 'small_palm', ['tree_fern'], (0, 1), (2, 2), crown=2.5, shadow='pool', job='nature'),
            m('net', 'furniture_low', ['butterfly_net'], (2, 2), (1, 1), blocks=False, dress=False, story=True,
              job='the naturalist\'s net'),
            m('table', 'furniture_table', ['specimen_table'], (3, 1), (3, 2), tap=True, stand=[(4, 3)],
              job='specimens laid out to draw', dress=False),
            m('fern_e', 'small_palm', ['tree_fern'], (9, 0), (2, 2), crown=2.5, shadow='pool', job='nature'),
            m('log', 'log', ['mossy_log'], (7, 3), (4, 1), tap=True, stand=[(8, 4), (9, 4)],
              job='a seat for watching the canopy', reason=['faces:path|view']),
        ],
        'clear': [{'why': 'the table\'s front', 'rect': [3, 3, 3, 2]},
                  {'why': 'the log\'s front', 'rect': [7, 4, 4, 2], 'front': True}],
    },
    'headwaters_shelter': {
        'biomes': ['coast', 'isles', 'rainforest', 'moor', 'valley'],
        'dressing': 'rainforest',
        'owner': 'whoever is caught by the rain',
        'why': 'a rain shelter: a thatched roof on four posts, a rail along the back, a bench under the roof '
               'facing the way, a water butt under the eave against a post (it fills from the roof)',
        'size': [7, 4],
        'members': [
            m('roof', 'pavilion', ['rain_shelter'], (0, 0), (6, 4), blocks=False, place='overhead',
              shadow='pool', dress=False, job='keeps the rain off'),
            m('post_nw', 'pole', ['shelter_post'], (0, 0), (1, 1), job='holds the roof'),
            m('post_ne', 'pole', ['shelter_post'], (5, 0), (1, 1), job='holds the roof'),
            m('post_sw', 'pole', ['shelter_post'], (0, 3), (1, 1), job='holds the roof'),
            m('post_se', 'pole', ['shelter_post'], (5, 3), (1, 1), job='holds the roof'),
            m('rail', 'fence', ['shelter_rail'], (1, 0), (4, 1), dress=False, job='a back to lean on'),
            m('bench', 'bench', ['bench_oak', 'bench'], (1, 1), (4, 1), tap=True, stand=[(2, 2), (3, 2)],
              against='rail', dress=False, job='a dry seat', reason=['faces:path|view']),
            m('water_butt', 'barrel', ['water_butt', 'barrel'], (6, 2), (1, 1), against='post_se', dress=False,
              job='fills from the roof'),
        ],
        'clear': [{'why': 'the bench\'s front, under the roof', 'rect': [1, 2, 4, 2], 'front': True}],
    },
    # --- lane D's plans (d-to-b-clusters, #193): the first of its nineteen ----------------
    'windpump_stop': {
        'biomes': ['steppe', 'desert', 'canyon', 'frontier'],
        'dressing': 'desert',
        'owner': 'the drovers on the road',
        'why': 'a stop on the road: a wind pump filling a stone trough for the beasts, a bench in the pump\'s '
               'shade, a tin cup left on the trough\'s rim (the personal object)',
        'size': [13, 6],
        'members': [
            m('pump', 'windpump', ['windpump'], (0, 0), (4, 4), fixed=True, job='lifts water for the trough'),
            m('trough', 'trough', ['trough', 'trough_stone'], (4, 3), (4, 1), tap=True, stand=[(5, 4), (6, 4)],
              against='pump', job='water for the beasts'),
            m('cup', 'furniture_low', ['tin_cup'], (8, 3), (1, 1), blocks=False, dress=False, story=True,
              job='a drover\'s cup'),
            m('bench', 'bench', ['bench', 'bench_oak'], (9, 3), (4, 1), tap=True, stand=[(10, 4), (11, 4)],
              turn=BENCH_TURN, job='a rest in the pump\'s shade', reason=['faces:path|view']),
        ],
        'clear': [{'why': 'the trough\'s front', 'rect': [4, 4, 4, 2], 'front': True},
                  {'why': 'the bench\'s front', 'rect': [9, 4, 4, 2]}],
    },
    'oasis_nook': {
        'biomes': ['desert', 'oasis', 'steppe', 'canyon'],
        'dressing': 'oasis',
        'owner': 'the water-seller',
        'why': 'shade by the spring\'s pool: two date palms, a bench in their shade facing the path, the '
               'water-seller\'s awning with jars stacked against it, a waterskin hung on the near palm '
               '(the personal object)',
        'size': [15, 6],
        'members': [
            m('palm_w', 'palm', ['date_palm', 'palm'], (0, 1), (1, 1), crown=3.5, shadow='pool',
              job='nature; grows where the water is', reason=['by:water:96']),
            m('bench', 'bench', ['bench', 'bench_oak'], (1, 3), (4, 1), tap=True, stand=[(2, 4), (3, 4)],
              turn=BENCH_TURN, job='a seat in the shade', reason=['faces:path|view']),
            m('palm_e', 'palm', ['date_palm', 'palm'], (6, 0), (1, 1), crown=3.5, shadow='pool',
              job='nature; grows where the water is', reason=['by:water:128']),
            m('skin', 'furniture_low', ['waterskin'], (7, 1), (1, 1), blocks=False, dress=False, story=True,
              job='the seller\'s own waterskin'),
            m('awning', 'stall', ['water_awning', 'stall'], (8, 1), (6, 2), tap=True, stand=[(10, 3), (11, 3)],
              fixed=True, dress=False, job='water sold by the cup'),
            m('jars', 'jar', ['jars', 'jar'], (14, 2), (1, 1), against='awning', dress=False, job='full jars'),
            m('jars_b', 'jar', ['jars', 'jar'], (14, 1), (1, 1), against='awning', dress=False, job='empties'),
        ],
        'clear': [{'why': 'the bench\'s front', 'rect': [1, 4, 4, 2], 'front': True},
                  {'why': 'the awning\'s customer band (size-guide 1: 6 x 2)', 'rect': [8, 3, 6, 2]}],
        'lights': [{'kind': 'shade_pool', 'at': [3.5, 2.5], 'r': 28, 'live': False}],
    },
    'frontier_street_corner': {
        'biomes': ['frontier', 'desert', 'canyon', 'town'],
        'dressing': 'desert',
        'owner': 'the store on the corner',
        'why': 'a corner of the street in front of a false front: a lantern on a post at the corner, barrels '
               'and a crate stacked against the boardwalk, a hitching rail at the street\'s edge parallel to '
               'it, a pair of spurs hung on the rail (the personal object)',
        'size': [11, 4],
        'members': [
            m('lantern', 'lamp', ['lantern_post', 'lamp'], (0, 1), (1, 1),
              light={'glow': 40, 'live': True, 'colour': 'lamp'}, job='lights the corner', reason=['lights:path']),
            m('barrel_a', 'barrel', ['barrel'], (1, 0), (1, 1), dress=False, job='stock for the store',
              reason=['by:dwelling:48']),
            m('barrel_b', 'barrel', ['barrel'], (2, 0), (1, 1), against='barrel_a', dress=False, job='stock'),
            m('crate', 'crate', ['crate', 'dynamite_crate'], (1, 1), (1, 1), against='barrel_a', dress=False,
              job='a delivery not yet carried in'),
            m('rail', 'rail', ['hitching_rail'], (5, 2), (5, 1), dress=False, job='horses tied while their riders shop',
              reason=['near:path:24']),
            m('spurs', 'furniture_low', ['spurs'], (10, 2), (1, 1), blocks=False, dress=False, story=True,
              job='a rider\'s spurs'),
        ],
        'clear': [{'why': 'the rail\'s street side', 'rect': [5, 3, 5, 1], 'front': True}],
    },
}


# The prop contract for the first eight recipes (prop-logic.md 2: owner, job, way in,
# footing, neighbours): the owner of each recipe, each member's job, and the placement
# rules (REASONS) that make it stand where it stands.
CONTRACT = {
    'meadow_nook': ('the park keeper, for walkers on the way', {
        'tree': ('nature; shades the bench', []), 'bush': ('nature', []),
        'bench': ('a rest in the shade', ['faces:path|view']),
        'lamp': ('lights the bench and the way at night', ['lights:path']),
        'flowers': ('nature', [])}),
    'field_edge': ('the farmer whose field it bounds', {
        'hedge_w': ('keeps the stock in', []), 'hedge_e': ('keeps the stock in', []),
        'stile': ('lets walkers over without opening a gate', []),
        'hedgerow_tree': ('nature; left standing in the hedge', [])}),
    'farmyard': ('the farmer', {
        'cart': ('carries sacks from the field', []), 'sacks': ('grain off the cart', []),
        'crates': ('produce for market', []), 'barrel': ('water or cider', []),
        'bale': ('fodder for the winter', []), 'trough': ('water for the beasts', []),
        'boots': ('the farmer\'s boots, left to dry', [])}),
    'shore': ('the fisher', {
        'boat': ('drawn up keel-up for mending', ['by:water:96']),
        'net_rack': ('nets hung to dry', ['by:water:128']), 'pots': ('lobster pots, stacked', []),
        'buoy': ('a spare float', []), 'log': ('a seat facing the sea', ['by:water:48']),
        'hat': ('the fisher\'s oilskin hat', [])}),
    'woodland_glade': ('nature, and walkers who rest there', {
        'tree_nw': ('nature', []), 'tree_n': ('nature', []), 'tree_ne': ('nature', []),
        'tree_sw': ('nature', []), 'log': ('a fallen trunk to sit on', ['faces:path|view']),
        'stump': ('what a woodcutter left', []), 'ferns': ('nature', []),
        'mushrooms': ('nature; the ring a story tells of', [])}),
    'town_square_corner': ('the shop on the corner and the town', {
        'lamp': ('lights the corner', ['lights:path']), 'bench': ('a seat on the square', ['faces:path|view']),
        'planter': ('the shopkeeper\'s flowers', ['by:dwelling:48']),
        'saucer': ('milk for the shop\'s cat', []), 'noticeboard': ('the town\'s notices', ['near:path:48'])}),
    'steppe_camp': ('the herders', {
        'tent': ('where the herders sleep', []), 'sacks': ('their stores', []),
        'fire': ('warmth and cooking', []), 'kettle': ('tea on the fire', []),
        'camel': ('their pack animal, resting', [])}),
    'moor_wayside': ('walkers on the moor', {
        'gorse': ('nature; the wind\'s lee', []), 'cairn': ('marks the way', ['near:path:64']),
        'bench': ('a rest out of the wind', ['faces:path|view']), 'stone': ('an old marker', []),
        'sprig': ('heather left on the stone', [])}),
}
for _name, (_owner, _jobs) in CONTRACT.items():
    RECIPES[_name]['owner'] = _owner
    for _mm in RECIPES[_name]['members']:
        _job, _why = _jobs[_mm['role']]
        _mm.setdefault('job', _job)
        if _why:
            _mm.setdefault('reason', list(_why))


# --- the library as data ---------------------------------------------------------------

def ledger_grades() -> dict:
    """Prop key -> the best grade the asset ledger gives it (KEEP over REWORK over RETIRE)."""
    try:
        with open(LEDGER) as fh:
            assets = json.load(fh)['assets']
    except (OSError, KeyError, ValueError):
        return {}
    rank = {'KEEP': 0, 'REWORK': 1, 'RETIRE': 2}
    out = {}
    for a in assets.values():
        n, g = a.get('name'), a.get('grade')
        if n and g and (n not in out or rank[g] < rank[out[n]]):
            out[n] = g
    return out


def library() -> dict:
    return {
        '_about': ('Prop clusters as data (scripts/art/prop_clusters.py, Claude B, a-to-b-clusters 21 Oct). '
                   'Every size is in world units (8 px cells; world px for radii and spacing), so the library '
                   'holds at any art density. Recipes face south; the placer turns them to face a path. '
                   'Generated by `prop_clusters.py --build`; edit the script, not this file.'),
        'cell': CELL, 'walk': WALK, 'hit_min': HIT, 'dress_every': list(DRESS_EVERY),
        'cluster_gap': CLUSTER_GAP, 'glows_per_area': GLOWS_PER_AREA, 'dressing': DRESSING,
        'recipes': RECIPES,
    }


def library_text() -> str:
    return json.dumps(library(), indent=1, sort_keys=True) + '\n'


def size_kinds() -> dict:
    with open(SIZE_GUIDE) as fh:
        return json.load(fh)['kinds']


def check_recipes() -> list:
    """Each recipe on its own: feet inside its size, blocking feet apart, clear zones and
    stands free of blocking feet, hit boxes apart, stores against their host, one story
    object, kinds the size guide knows (or flagged as new)."""
    out, kinds = [], size_kinds()
    for name, r in RECIPES.items():
        W, H = r['size']
        roles = {mm['role']: mm for mm in r['members']}
        if len(roles) != len(r['members']):
            out.append(f'{name}: two members share a role')
        if r['dressing'] not in DRESSING:
            out.append(f'{name}: unknown dressing {r["dressing"]}')
        for mm in r['members']:
            x, y = mm['at']
            w, h = mm['foot']
            if x < 0 or y < 0 or x + w > W or y + h > H:
                out.append(f'{name}: {mm["role"]} foot {mm["at"]}+{mm["foot"]} leaves the {W} x {H} cells')
            if mm['kind'] not in kinds and mm['kind'] not in NEW_KINDS:
                out.append(f'{name}: {mm["role"]} kind {mm["kind"]} is neither in the size guide nor NEW_KINDS')
            if mm['tap'] and not mm.get('stand'):
                out.append(f'{name}: tapped {mm["role"]} has no stand')
            if mm.get('against') and mm['against'] not in roles:
                out.append(f'{name}: {mm["role"]} stands against an unknown {mm["against"]}')
            elif mm.get('against'):
                if gap(rect_of(mm), rect_of(roles[mm['against']])) > 1:
                    out.append(f'{name}: {mm["role"]} is more than a cell from {mm["against"]} (world-rules 6.4)')
        if not r.get('owner'):
            out.append(f'{name}: no owner (prop-logic.md 2)')
        for mm in r['members']:
            if not mm.get('job'):
                out.append(f'{name}: {mm["role"]} has no job (prop-logic.md 2)')
            for rule in mm.get('reason', []):
                bits = rule.split(':')
                if bits[0] not in REASONS or (bits[0] in ('near', 'by') and len(bits) != 3):
                    out.append(f'{name}: {mm["role"]} has a malformed rule {rule}')
        if sum(1 for mm in r['members'] if mm.get('story')) > 1:
            out.append(f'{name}: more than one personal object')
        blocks = [rect_of(mm) for mm in r['members'] if mm['blocks']]
        for i, a in enumerate(blocks):
            for b in blocks[i + 1:]:
                if overlap(a, b):
                    out.append(f'{name}: blocking feet {a} and {b} overlap')
        keep = [c['rect'] for c in r.get('clear', [])] + [[sx, sy, 1, 1] for mm in r['members'] for sx, sy in mm.get('stand', [])]
        for k in keep:
            for b in blocks:
                if overlap(k, b):
                    out.append(f'{name}: clear zone or stand {k} is under a blocking foot {b}')
        hits = [hit_box_cells(mm) for mm in r['members'] if mm['tap']]
        for i, a in enumerate(hits):
            for b in hits[i + 1:]:
                if overlap(a, b, eps=1e-6):
                    out.append(f'{name}: hit boxes {a} and {b} overlap')
    return out


# kinds a recipe uses that the size guide does not have yet (asked of Claude A on the board)
NEW_KINDS = {'hedge': 'a clipped or laid hedge, n x 2 cells, 16 to 24 tall'}


# --- cell geometry ---------------------------------------------------------------------

def rect_of(mm) -> list:
    return [mm['at'][0], mm['at'][1], mm['foot'][0], mm['foot'][1]]


def overlap(a, b, eps=0.0) -> bool:
    return a[0] < b[0] + b[2] - eps and b[0] < a[0] + a[2] - eps and a[1] < b[1] + b[3] - eps and b[1] < a[1] + a[3] - eps


def gap(a, b) -> float:
    """Chebyshev gap between two rects (0 when they touch or overlap)."""
    dx = max(b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2]), 0)
    dy = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), 0)
    return max(dx, dy)


def hit_box_cells(mm) -> list:
    """The 34 x 34 hit box at a tapped member's foot, in cells: bottom on the foot's bottom,
    centred on the foot (size-guide 1: "at its foot")."""
    x, y = mm['at']
    w, h = mm['foot']
    s = HIT / CELL
    return [x + w / 2 - s / 2, y + h - s, s, s]


def turn_rect(r, orient: str, mirror: bool, W: float, H: float) -> list:
    """A rect (cells) of a south-facing recipe of W x H cells, turned so its front faces
    `orient`, then mirrored across the front's axis."""
    x, y, w, h = r
    if orient == 's':
        out, WW = [x, y, w, h], W
    elif orient == 'n':
        out, WW = [W - x - w, H - y - h, w, h], W
    elif orient == 'e':
        out, WW = [y, W - x - w, h, w], H
    else:  # 'w'
        out, WW = [H - y - h, x, h, w], H
    if mirror:
        if orient in ('s', 'n'):
            out[0] = WW - out[0] - out[2]
        else:
            HH = W
            out[1] = HH - out[1] - out[3]
    return out


def turned_size(r, orient):
    W, H = r['size']
    return (W, H) if orient in ('s', 'n') else (H, W)


def allowed(r, orient) -> bool:
    for mm in r['members']:
        if orient != 's' and 'turn' in mm and orient not in mm['turn']:
            return False
    return True


def expand(recipe_name: str, at, orient='s', mirror=False, seed=0, kinds=None, grades=None) -> dict:
    """A placement made concrete in world px: each member's prop, foot rect, hit box and
    stands; clear zones; crossing; lights; decals; and the dressing clumps (seeded)."""
    r = RECIPES[recipe_name]
    W, H = r['size']
    ox, oy = at
    grades = grades if grades is not None else {}

    def px(rc):
        x, y, w, h = turn_rect(rc, orient, mirror, W, H)
        return [ox + x * CELL, oy + y * CELL, w * CELL, h * CELL]

    members = []
    for mm in r['members']:
        t = mm.get('turn', {}).get(orient) if orient != 's' else None
        props = (t or mm)['props']
        kind = (t or mm)['kind']
        foot = px(rect_of(mm))
        item = {'role': mm['role'], 'kind': kind, 'prop': props[0], 'props': props, 'foot': foot,
                'job': mm.get('job', ''), 'reason': list(mm.get('reason', [])),
                'blocks': mm['blocks'], 'tap': mm['tap'], 'place': mm['place'], 'shadow': mm['shadow'],
                'grade': grades.get(props[0], 'new')}
        # the anchor: the foot's bottom middle (size-guide 1: the anchor is the foot)
        item['anchor'] = [foot[0] + foot[2] / 2, foot[1] + foot[3]]
        if mm['tap']:
            item['hit'] = [item['anchor'][0] - HIT / 2, item['anchor'][1] - HIT, HIT, HIT]
            item['stand'] = [[c[0] + CELL / 2, c[1] + CELL / 2] for c in (px([sx, sy, 1, 1]) for sx, sy in mm['stand'])]
        if mm.get('crown'):
            item['crown'] = mm['crown'] * CELL
        if mm.get('light'):
            item['light'] = mm['light']
        for k in ('story', 'optional'):
            if mm.get(k):
                item[k] = True
        members.append(item)
    clear = [dict({'why': c['why'], 'rect': px(c['rect'])}, **({'front': True} if c.get('front') else {}))
             for c in r.get('clear', [])]
    crossing = px(r['crossing']['rect']) if r.get('crossing') else None
    lights = [dict(mm['light'], at=mm['anchor'], of=mm['role']) for mm in members if mm.get('light')]
    for lt in r.get('lights', []):
        cx, cy, _, _ = px([lt['at'][0], lt['at'][1], 0, 0])
        lights.append({'kind': lt['kind'], 'at': [cx, cy], 'r': lt['r'], 'live': lt['live']})
    decals = []
    for d in r.get('decals', []):
        if d.get('of'):
            tree = next(mm for mm in members if mm['role'] == d['of'])
            rad = tree.get('crown', 2 * CELL)
            # the crown's shade pool, thrown east and down (house-style 6: a round blob only
            # under round things such as a tree's crown)
            decals.append({'what': d['what'], 'at': [tree['anchor'][0] + rad * 0.3, tree['anchor'][1] + rad * 0.15],
                           'r': [rad * 0.9, rad * 0.45]})
        else:
            decals.append({'what': d['what'], 'rect': px(d['rect'])})
    out = {'recipe': recipe_name, 'at': list(at), 'orient': orient, 'mirror': mirror, 'seed': seed,
           'members': members, 'clear': clear, 'lights': lights, 'decals': decals}
    if crossing:
        out['crossing'] = crossing
    out['dressing'] = dress(r, members, clear, crossing, seed)
    return out


def dress(r, members, clear, crossing, seed) -> list:
    """Plant dressing at the bases of the members that ask for it: walk each foot's south,
    west and east edges (the base you see; the north edge is hidden behind the prop) and
    drop a clump every 16 to 32 px, seeded; never in a clear zone, on a stand, on a
    crossing or under another blocking foot. Each clump is 2 or 3 pieces of one kind."""
    rnd = random.Random(f'{r["dressing"]}:{seed}')
    kinds = DRESSING[r['dressing']]
    keep = [c['rect'] for c in clear] + ([crossing] if crossing else [])
    for mm in members:
        for sx, sy in mm.get('stand', []):
            keep.append([sx - CELL / 2, sy - CELL / 2, CELL, CELL])
    blocks = [mm['foot'] for mm in members if mm['blocks']]
    out = []
    for mm in members:
        src = next((x for x in r['members'] if x['role'] == mm['role']), None)
        if not src or not src['dress'] or not mm['blocks']:
            continue
        x, y, w, h = mm['foot']
        # the base: west side up from the foot, the south edge, the east side (px, outward 3 px)
        edge = [(x - 3, y + h - t) for t in range(0, int(h) + 1, 2)][::-1] + \
               [(x + t, y + h + 2) for t in range(0, int(w) + 1, 2)] + \
               [(x + w + 3, y + h - t) for t in range(0, int(h) + 1, 2)]
        walked, nxt = 0.0, rnd.uniform(DRESS_EVERY[0] / 2, DRESS_EVERY[1] / 2)
        for a, b in zip(edge, edge[1:]):
            walked += math.hypot(b[0] - a[0], b[1] - a[1])
            if walked < nxt:
                continue
            nxt = walked + rnd.uniform(*DRESS_EVERY)
            p = [round(b[0]), round(b[1])]
            spot = [p[0] - 2, p[1] - 2, 4, 4]
            if any(overlap(spot, k) for k in keep) or any(overlap(spot, bb) for bb in blocks if bb is not mm['foot']):
                continue
            out.append({'what': rnd.choice(kinds), 'at': p, 'pieces': rnd.choice((2, 3)), 'of': mm['role']})
    return out


# --- the plan's ground (Claude F's schema: art/regions/<id>.json) ----------------------

def dist_to_line(p, pts) -> float:
    best = 1e9
    for a, b in zip(pts, pts[1:]):
        ax, ay, bx, by = *a, *b
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


def nearest_on_lines(p, lines):
    best = (1e9, None)
    for pts in lines:
        for a, b in zip(pts, pts[1:]):
            ax, ay, bx, by = *a, *b
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy or 1.0
            t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
            q = (ax + t * dx, ay + t * dy)
            d = math.hypot(p[0] - q[0], p[1] - q[1])
            if d < best[0]:
                best = (d, q)
    return best


class Ground:
    """The plan on the 4 px walk grid: tier, face, path band and blockers per cell. Tiers
    and faces read as region_plan.Ground reads them (screen space; a tier's south face
    hangs FACE px under its south rim, carved from the ground below)."""

    def __init__(self, plan: dict):
        self.plan = plan
        self.x0, self.y0, self.w, self.h = plan['box']
        W, H = self.w // WALK, self.h // WALK
        self.tier = np.zeros((H, W), np.int16)
        for t in sorted(plan.get('tiers', []), key=lambda t: t['tier']):
            img = Image.new('L', (W, H), 0)
            ImageDraw.Draw(img).polygon([((x - self.x0) / WALK, (y - self.y0) / WALK) for x, y in t['outline']], fill=1)
            mk = np.asarray(img).astype(bool)
            self.tier[mk] = np.maximum(self.tier[mk], t['tier'])
        self.face = np.zeros_like(self.tier, bool)
        top = int(self.tier.max()) - int(self.tier.min())
        for d in range(1, top * FACE // WALK + 1):
            up = np.vstack([self.tier[:1].repeat(d, 0), self.tier[:-d]])
            self.face |= (up - self.tier) * FACE > (d - 1) * WALK
        self.paths = [p for p in plan.get('routes', []) + plan.get('trods', [])]
        self.stairs = plan.get('stairs', [])
        # the walking band of each path, per cell
        self.band = np.zeros_like(self.face)
        self.stair = np.zeros_like(self.face)
        ys, xs = np.mgrid[0:H, 0:W]
        cx = self.x0 + xs * WALK + WALK / 2
        cy = self.y0 + ys * WALK + WALK / 2
        for pth in self.paths:
            half = pth['width'] / 2
            self.band |= _line_dist(cx, cy, pth['points']) <= half
        for st in self.stairs:
            self.stair |= np.hypot(cx - st['at'][0], cy - st['at'][1]) <= st['width'] / 2 + 8
        self.H, self.W = H, W
        # water (and lava): not walkable, and what 'by:water' measures from. Plans list water
        # as polylines with a width or closed outlines (Claude C's and D's plans); a plan with
        # a 'coast' (land outlines) has the sea everywhere outside them.
        self.wet = np.zeros_like(self.face)
        for wt in plan.get('water', []) + plan.get('lava', []):
            pts = wt.get('points') or wt.get('outline')
            if not pts:
                continue
            if wt.get('closed') or 'outline' in wt:
                self.wet |= self._poly(pts)
            else:
                self.wet |= _line_dist(cx, cy, pts) <= wt.get('width', 16) / 2
        self.water = self.wet.copy()
        for wt in plan.get('lava', []):
            pts = wt.get('points') or wt.get('outline')
            if pts and not (wt.get('closed') or 'outline' in wt):
                self.water &= ~(_line_dist(cx, cy, pts) <= wt.get('width', 16) / 2)
        coast = plan.get('coast')
        if isinstance(coast, dict) and coast:
            land = np.zeros_like(self.face)
            for outline in coast.values():
                if isinstance(outline, list) and len(outline) > 2 and isinstance(outline[0], list):
                    land |= self._poly(outline)
            sea = ~land
            self.wet |= sea
            self.water |= sea
        # buildings drawn as rects in a plan block the walk (a pier or a deck does not)
        self.built = np.zeros_like(self.face)
        for st in plan.get('structures', []) or []:
            if st.get('rect') and st.get('kind') not in WALK_ON:
                for r, c in self.cells(st['rect']):
                    if self.inside(r, c):
                        self.built[r, c] = True
        self.band &= ~self.wet | self.stair
        self._wd = None

    def water_dist(self, x, y) -> float:
        """World px from (x, y) to the nearest water, on an 8 px grid (1e9 with none)."""
        if self._wd is None:
            from collections import deque
            H, W = (self.H + 1) // 2, (self.W + 1) // 2
            d = np.full((H, W), 1e9)
            dq = deque()
            for r, c in np.argwhere(self.water[::2, ::2]):
                d[r, c] = 0
                dq.append((r, c))
            while dq:
                r, c = dq.popleft()
                for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= rr < H and 0 <= cc < W and d[rr, cc] > d[r, c] + 8:
                        d[rr, cc] = d[r, c] + 8
                        dq.append((rr, cc))
            self._wd = d
        r, c = int((y - self.y0) // 8), int((x - self.x0) // 8)
        if 0 <= r < self._wd.shape[0] and 0 <= c < self._wd.shape[1]:
            return float(self._wd[r, c])
        return 1e9

    def _poly(self, pts):
        img = Image.new('L', (self.W, self.H), 0)
        ImageDraw.Draw(img).polygon([((x - self.x0) / WALK, (y - self.y0) / WALK) for x, y in pts], fill=1)
        return np.asarray(img).astype(bool)

    def near(self, mask, rect, n) -> bool:
        x, y, w, h = rect
        cells = [rc for rc in self.cells([x - n, y - n, w + 2 * n, h + 2 * n]) if self.inside(*rc)]
        return any(mask[rc] for rc in cells)

    def cell(self, x, y):
        return int((y - self.y0) // WALK), int((x - self.x0) // WALK)

    def cells(self, rect):
        """Walk cells (row, col) a world rect covers (cells whose centre lies inside it)."""
        x, y, w, h = rect
        c0 = math.ceil((x - self.x0) / WALK - 0.5)
        c1 = math.floor((x + w - self.x0) / WALK - 0.5)
        r0 = math.ceil((y - self.y0) / WALK - 0.5)
        r1 = math.floor((y + h - self.y0) / WALK - 0.5)
        return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]

    def inside(self, r, c):
        return 0 <= r < self.H and 0 <= c < self.W


WALK_ON = {'pier', 'jetty', 'deck', 'bridge', 'boardwalk', 'quay', 'pontoon'}


def _line_dist(cx, cy, pts):
    best = np.full(cx.shape, 1e9)
    for a, b in zip(pts, pts[1:]):
        ax, ay, bx, by = *a, *b
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1.0
        t = np.clip(((cx - ax) * dx + (cy - ay) * dy) / L2, 0, 1)
        best = np.minimum(best, np.hypot(cx - ax - t * dx, cy - ay - t * dy))
    return best


# Placement logic: why a member stands where it does. Each rule is a string on the member:
#   faces:path|view  its stands are within BESIDE of a path, or within 160 px of a view
#                    (a place or named thing of kind 'view': a bench faces a path or a view)
#   lights:path      a path within its glow (a lamp lights a way, not a field)
#   near:path:N      its foot within N px of a path (a hitching rail, a noticeboard, a cairn)
#   by:water:N       water within N px of its foot (a boat, a net rack, a bollard, a palm)
#   by:dwelling:N    a building or a lived-in place within N px (stores, a planter, a butt)
DWELLING_KINDS = {'hamlet', 'village', 'town', 'frontier', 'farm', 'house', 'cottage', 'inn', 'shed', 'hut',
                  'npc', 'station', 'shop', 'store', 'workshop', 'mill', 'boathouse', 'camp', 'cabin', 'bothy'}
VIEW_KINDS = {'view', 'lookout', 'viewpoint'}
REASONS = ('faces', 'lights', 'near', 'by')


def plan_things(plan: dict, kinds) -> list:
    """Points or rects of the plan's places, named things and structures of the given kinds."""
    out = []
    for p in plan.get('places', []) + plan.get('named', []) + (plan.get('structures') or []):
        if p.get('kind') in kinds:
            if p.get('rect'):
                out.append(p['rect'])
            elif p.get('at'):
                out.append([p['at'][0], p['at'][1], 0, 0])
            elif p.get('from'):
                out.append([p['from'][0], p['from'][1], 0, 0])
    return out


def rect_dist(a, b) -> float:
    dx = max(b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2]), 0)
    dy = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), 0)
    return math.hypot(dx, dy)


def reason_fault(G, plan, mm, rule: str):
    """None when the member keeps its rule in this plan, else what is wrong."""
    parts = rule.split(':')
    lines = [p['points'] for p in G.paths]
    foot = mm['foot']
    if parts[0] == 'faces':
        stands = mm.get('stand') or [[foot[0] + foot[2] / 2, foot[1] + foot[3] + CELL / 2]]
        sx = sum(s[0] for s in stands) / len(stands)
        sy = sum(s[1] for s in stands) / len(stands)
        ok = False
        if 'path' in parts[1].split('|') and lines:
            ok = nearest_on_lines((sx, sy), lines)[0] <= BESIDE
        if not ok and 'view' in parts[1].split('|'):
            ok = any(rect_dist([sx, sy, 0, 0], v) <= 160 for v in plan_things(plan, VIEW_KINDS))
        return None if ok else f'faces no {" or ".join(parts[1].split("|"))} (its front is more than {BESIDE} px from one)'
    if parts[0] == 'lights':
        r = (mm.get('light') or {}).get('glow', 40)
        if not lines or nearest_on_lines(mm['anchor'], lines)[0] > r:
            return f'lights no path within its {r} px glow'
        return None
    if parts[0] == 'near':
        n = float(parts[2])
        cx, cy = foot[0] + foot[2] / 2, foot[1] + foot[3] / 2
        if not lines or nearest_on_lines((cx, cy), lines)[0] - max(foot[2], foot[3]) / 2 > n:
            return f'is more than {n:.0f} px from a path'
        return None
    if parts[0] == 'by':
        n = float(parts[2])
        if parts[1] == 'water':
            return None if G.near(G.water, foot, n) else f'is more than {n:.0f} px from water'
        if parts[1] == 'dwelling':
            homes = plan_things(plan, DWELLING_KINDS)
            ok = any(rect_dist(foot, h) <= n for h in homes) or G.near(G.built, foot, n)
            return None if ok else f'is more than {n:.0f} px from a building or a lived-in place'
    return f'has an unknown rule {rule}'


def plan_points(plan: dict, skip=()) -> list:
    """The plan's standing things as (point, what, tapped): markers, named things, pockets."""
    out = []
    for mk in plan.get('markers', []):
        if tuple(mk['at']) not in skip:
            out.append((mk['at'], mk['what'], mk['t'] == 'I'))
    for n in plan.get('named', []):
        if tuple(n['at']) not in skip:
            out.append((n['at'], n['thing'], False))
    for pk in plan.get('pockets', []):
        out.append((pk['at'], pk['holds'], False))
    return out


def reach(G: Ground, blocked, window=None, base=None) -> np.ndarray:
    """Cells reachable from any path band on the walk grid: same tier only, except within
    a stair's reach; faces and blocked cells are walls. With a `window` (r0, r1, c0, c1),
    only the window is walked: its sources are the path bands in it and the cells on its
    rim that `base` (the whole plan's reach) already reaches, so a change inside the
    window is judged without walking the whole plan again."""
    ok = ~G.face & ~blocked & ~G.wet & ~G.built
    seen = np.zeros_like(ok)
    r0, r1, c0, c1 = window or (0, G.H, 0, G.W)
    src = G.band[r0:r1, c0:c1].copy()
    if base is not None:
        rim = np.zeros_like(src)
        rim[0, :] = rim[-1, :] = True
        rim[:, 0] = rim[:, -1] = True
        src |= rim & base[r0:r1, c0:c1]
    src &= ok[r0:r1, c0:c1]
    stack = [(r + r0, c + c0) for r, c in np.argwhere(src)]
    for r, c in stack:
        seen[r, c] = True
    tier, stair = G.tier, G.stair
    while stack:
        r, c = stack.pop()
        t = tier[r, c]
        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if r0 <= rr < r1 and c0 <= cc < c1 and ok[rr, cc] and not seen[rr, cc]:
                if tier[rr, cc] != t and not (stair[r, c] or stair[rr, cc]):
                    continue
                seen[rr, cc] = True
                stack.append((rr, cc))
    return seen


def blocked_by(G: Ground, placements, plan_pts) -> np.ndarray:
    b = np.zeros_like(G.face)
    for pl in placements:
        for mm in pl['members']:
            if mm['blocks']:
                for r, c in G.cells(mm['foot']):
                    if G.inside(r, c):
                        b[r, c] = True
    for p, _, _ in plan_pts:  # a marker or named thing stands on a 2 x 2 walk-cell foot
        for r, c in G.cells([p[0] - 4, p[1] - 4, 8, 8]):
            if G.inside(r, c):
                b[r, c] = True
    return b


def touch_css() -> float:
    return HIT * PHONE_CSS / ART_ACROSS


def check_placement(plan: dict, pl: dict, others=(), area=None, G: Ground | None = None, skip=(),
                    base=None, fast: bool = False) -> list:
    """Every rule a placed cluster must keep in its plan (see the module's docstring)."""
    out = []
    G = G or Ground(plan)
    name = f'{plan.get("id", "plan")}: {pl["recipe"]} at {tuple(pl["at"])}'
    r = RECIPES[pl['recipe']]
    if pl['at'][0] % CELL or pl['at'][1] % CELL:
        out.append(f'{name}: off the {CELL} px grid')
    bx, by, bw, bh = area or plan['box']
    feet = [mm['foot'] for mm in pl['members']]
    keep = [c['rect'] for c in pl['clear']]
    stands = [s for mm in pl['members'] for s in mm.get('stand', [])]
    for f in feet + keep:
        if f[0] < bx or f[1] < by or f[0] + f[2] > bx + bw or f[1] + f[3] > by + bh:
            out.append(f'{name}: {f} leaves the {"area" if area else "box"}')
            return out
    # ground: one tier per foot, off faces, a cell back from a lip
    for mm in pl['members']:
        cells = [rc for rc in G.cells(mm['foot']) if G.inside(*rc)]
        tiers = {int(G.tier[rc]) for rc in cells}
        if len(tiers) > 1:
            out.append(f'{name}: {mm["role"]} straddles tiers {sorted(tiers)}')
        if any(G.face[rc] for rc in cells):
            out.append(f'{name}: {mm["role"]} stands on a face')
        if mm['blocks']:
            x, y, w, h = mm['foot']
            below = [rc for rc in G.cells([x, y + h, w, CELL]) if G.inside(*rc)]
            if any(G.face[rc] for rc in below):
                out.append(f'{name}: {mm["role"]} is less than a cell back from a lip')
    for c in pl['clear']:
        cells = [rc for rc in G.cells(c['rect']) if G.inside(*rc)]
        if any(G.face[rc] for rc in cells):
            out.append(f'{name}: clear zone ({c["why"]}) runs onto a face')
    # on dry ground (a ground prop never stands in water: world-rules 6.1)
    for mm in pl['members']:
        if mm['place'] in ('wet', 'floating', 'overhead'):
            continue
        cells = [rc for rc in G.cells(mm['foot']) if G.inside(*rc)]
        if any(G.wet[rc] for rc in cells):
            out.append(f'{name}: {mm["role"]} stands in water')
        if mm['blocks'] and any(G.built[rc] for rc in cells):
            out.append(f'{name}: {mm["role"]} stands inside a building')
    # why each thing stands where it does (prop-logic.md 2 and A's a-to-b-188)
    for mm in pl['members']:
        for rule in mm.get('reason', []):
            f = reason_fault(G, plan, mm, rule)
            if f:
                out.append(f'{name}: {mm["role"]} {f}')
    # off the ways, except a crossing; the crossing must carry a path
    cross = pl.get('crossing')
    for mm in pl['members']:
        if not mm['blocks'] and not mm.get('story') and mm['kind'] not in ('flowers', 'fern'):
            continue
        cells = [rc for rc in G.cells(mm['foot']) if G.inside(*rc)]
        if cross:
            cells = [rc for rc in cells if not _in(rc, G, cross)]
        if any(G.band[rc] or G.stair[rc] for rc in cells):
            out.append(f'{name}: {mm["role"]} stands on a path or a stair')
    for d in pl['dressing']:
        rc = G.cell(*d['at'])
        if G.inside(*rc) and (G.band[rc] or G.stair[rc]):
            out.append(f'{name}: dressing {d["what"]} at {tuple(d["at"])} grows on a path')
    if cross:
        cx, cy = cross[0] + cross[2] / 2, cross[1] + cross[3] / 2
        lines = [p['points'] for p in G.paths]
        mx = r['crossing'].get('max_width', 64)
        foot_paths = [p['points'] for p in G.paths if p['width'] <= mx]
        d, _ = nearest_on_lines((cx, cy), foot_paths) if foot_paths else (1e9, None)
        if d > CELL:
            out.append(f'{name}: no footpath runs through its crossing ({d:.0f} px from the nearest)')
        wide = [p['id'] for p in G.paths if p['width'] > mx and dist_to_line((cx, cy), p['points']) <= CELL + p['width'] / 2]
        if wide:
            out.append(f'{name}: its crossing sits on {wide[0]}, too wide for a stile (a road gets a gate)')
    # the front beside a path: the front clear zone (or the first stand) within BESIDE of one
    lines = [p['points'] for p in G.paths]
    if lines and not cross:
        fronts = [c['rect'] for c in pl['clear'] if c.get('front')]
        front = fronts[0] if fronts else keep[0] if keep else [stands[0][0] - 4, stands[0][1] - 4, 8, 8] if stands else None
        if front:
            d, _ = nearest_on_lines((front[0] + front[2] / 2, front[1] + front[3] / 2), lines)
            lim = r.get('from_path', BESIDE)
            if d > lim:
                out.append(f'{name}: its front is {d:.0f} px from a path (at most {lim})')
    if fast and out:
        return out
    # reachability: stands and clear zones reachable; nothing cut off that was reachable.
    # Walked in a window round the cluster (its rim fed from the whole plan's reach).
    pts = plan_points(plan, skip)
    blocked0 = blocked_by(G, list(others), pts)
    if base is None:
        base = reach(G, blocked0)
    allx = [f[0] for f in feet + keep] + [f[0] + f[2] for f in feet + keep]
    ally = [f[1] for f in feet + keep] + [f[1] + f[3] for f in feet + keep]
    (ra, ca), (rb, cb) = G.cell(min(allx) - 128, min(ally) - 128), G.cell(max(allx) + 128, max(ally) + 128)
    win = (max(0, ra), min(G.H, rb + 1), max(0, ca), min(G.W, cb + 1))
    before = base
    after = base.copy()
    after[win[0]:win[1], win[2]:win[3]] = reach(G, blocked0 | blocked_by(G, [pl], []), win, base)[win[0]:win[1], win[2]:win[3]]
    for s in stands:
        rc = G.cell(*s)
        if not (G.inside(*rc) and after[rc]):
            out.append(f'{name}: stand {tuple(s)} cannot be reached from a path')
    for c in pl['clear']:
        cells = [rc for rc in G.cells(c['rect']) if G.inside(*rc)]
        if cells and not any(after[rc] for rc in cells):
            out.append(f'{name}: clear zone ({c["why"]}) cannot be reached')
        blk = blocked_by(G, [pl], [])
        if any(blk[rc] for rc in cells):
            out.append(f'{name}: clear zone ({c["why"]}) is under a foot')
    for p, what, _ in pts:
        ring = [rc for rc in G.cells([p[0] - 10, p[1] - 10, 20, 20]) if G.inside(*rc)]
        if any(before[rc] for rc in ring) and not any(after[rc] for rc in ring):
            out.append(f'{name}: cuts {what} at {tuple(p)} off from the paths')
    for o in others:
        for mm in o['members']:
            for s in mm.get('stand', []):
                rc = G.cell(*s)
                if G.inside(*rc) and before[rc] and not after[rc]:
                    out.append(f'{name}: cuts off the stand of {o["recipe"]}\'s {mm["role"]}')
    # touch: 34 x 34 world px (44 CSS px or more) and apart from every other hit box
    if touch_css() < MIN_TOUCH_CSS:
        out.append(f'{name}: a {HIT} px hit box is {touch_css():.1f} CSS px (under {MIN_TOUCH_CSS})')
    hits = [(mm['role'], mm['hit']) for mm in pl['members'] if mm.get('hit')]
    for _, hb in hits:
        if hb[2] < HIT or hb[3] < HIT:
            out.append(f'{name}: hit box {hb} under {HIT} px')
    others_hits = [(f'{o["recipe"]}.{mm["role"]}', mm['hit']) for o in others for mm in o['members'] if mm.get('hit')]
    others_hits += [(what, [p[0] - HIT / 2, p[1] - HIT, HIT, HIT]) for p, what, tapped in pts if tapped]
    for i, (ra, a) in enumerate(hits):
        for rb, b in hits[i + 1:] + others_hits:
            if overlap(a, b, eps=1e-6):
                out.append(f'{name}: hit box of {ra} overlaps {rb}\'s')
    # clusters apart (world-rules 6.3)
    mine = [mm['foot'] for mm in pl['members'] if mm['blocks']]
    for o in others:
        for f in (mm['foot'] for mm in o['members'] if mm['blocks']):
            for g in mine:
                if gap(f, g) < CLUSTER_GAP:
                    out.append(f'{name}: less than {CLUSTER_GAP} px from {o["recipe"]} at {tuple(o["at"])}')
                    break
            else:
                continue
            break
    # not on another thing of the plan
    for p, what, _ in pts:
        for f in feet:
            if f[0] - 4 < p[0] < f[0] + f[2] + 4 and f[1] - 4 < p[1] < f[1] + f[3] + 4:
                out.append(f'{name}: stands on {what} at {tuple(p)}')
    for e in plan.get('egg_spots', []):
        for f in feet:
            if math.hypot(f[0] + f[2] / 2 - e['at'][0], f[1] + f[3] / 2 - e['at'][1]) < e['keep_clear_r'] + max(f[2], f[3]) / 2:
                out.append(f'{name}: stands on the egg spot {e["what"]}')
    return out


def _in(rc, G, rect):
    r, c = rc
    x = G.x0 + c * WALK + WALK / 2
    y = G.y0 + r * WALK + WALK / 2
    return rect[0] <= x < rect[0] + rect[2] and rect[1] <= y < rect[1] + rect[3]


def check_glows(plan: dict, placements) -> list:
    out = []
    for a in plan.get('areas', []) or [{'id': 'box', 'rect': plan['box']}]:
        x, y, w, h = a['rect']
        n = sum(1 for pl in placements for lt in pl['lights'] if lt.get('live')
                and x <= lt['at'][0] < x + w and y <= lt['at'][1] < y + h)
        if n > GLOWS_PER_AREA:
            out.append(f'{plan.get("id", "plan")}: area {a["id"]} has {n} live glows (at most {GLOWS_PER_AREA})')
    return out


# --- the placer ------------------------------------------------------------------------

def place(plan: dict, recipe: str, area=None, near=None, seed: int = 0, others=(), radius: int = 64,
          skip=(), G: Ground | None = None):
    """Drop `recipe` into the plan: inside `area` (a world rect, or the id of one of the
    plan's areas) or within `radius` px of `near` (then the cluster's front centre lands
    near that point, as when it fills a marker). Returns (placement, None) or (None, the
    faults of the best candidate it tried)."""
    G = G or Ground(plan)
    r = RECIPES[recipe]
    grades = ledger_grades()
    if isinstance(area, str):
        area = next(a['rect'] for a in plan['areas'] if a['id'] == area)
    rnd = random.Random(f'{recipe}:{seed}')
    lines = [p['points'] for p in G.paths]
    cands = []
    for orient in ORIENTS:
        if not allowed(r, orient):
            continue
        W, H = turned_size(r, orient)
        for mirror in (False, True):
            if near is not None:
                xs = range(int((near[0] - radius - W * CELL) // CELL), int((near[0] + radius) // CELL) + 1)
                ys = range(int((near[1] - radius - H * CELL) // CELL), int((near[1] + radius) // CELL) + 1)
            else:
                ax, ay, aw, ah = area or plan['box']
                xs = range(math.ceil(ax / CELL), (ax + aw) // CELL - W + 1)
                ys = range(math.ceil(ay / CELL), (ay + ah) // CELL - H + 1)
            for cx in xs:
                for cy in ys:
                    cands.append((orient, mirror, cx * CELL, cy * CELL))
    rnd.shuffle(cands)

    def score(c):
        """Prefer a front that faces the nearest path (and, near a point, sits near it)."""
        orient, mirror, x, y = c
        W, H = turned_size(r, orient)
        mx, my = x + W * CELL / 2, y + H * CELL / 2
        s = 0.0
        if lines:
            d, q = nearest_on_lines((mx, my), lines)
            fx, fy = FRONT[orient]
            if q is not None and d > 0:
                s -= ((q[0] - mx) * fx + (q[1] - my) * fy) / d * 40  # facing it
            fr = turn_rect(front_rect, orient, mirror, *r['size'])
            df, _ = nearest_on_lines((x + (fr[0] + fr[2] / 2) * CELL, y + (fr[1] + fr[3] / 2) * CELL), lines)
            s += max(0.0, df - min(r.get('from_path', BESIDE), BESIDE) / 2)  # its front beside it
        for (rc, n) in wants_water:  # members that stand by water, near it
            wr = turn_rect(rc, orient, mirror, *r['size'])
            s += max(0.0, G.water_dist(x + (wr[0] + wr[2] / 2) * CELL, y + (wr[1] + wr[3] / 2) * CELL) - n / 2)
        if r.get('crossing') and lines:
            cr = turn_rect(r['crossing']['rect'], orient, mirror, *r['size'])
            foot = [p['points'] for p in G.paths if p['width'] <= r['crossing'].get('max_width', 64)] or lines
            s += nearest_on_lines((x + (cr[0] + cr[2] / 2) * CELL, y + (cr[1] + cr[3] / 2) * CELL), foot)[0] * 20
        if near is not None:
            s += math.hypot(mx - near[0], my - near[1])
        return s

    fronts = [c['rect'] for c in r.get('clear', []) if c.get('front')] or [c['rect'] for c in r.get('clear', [])]
    front_rect = fronts[0] if fronts else [0, r['size'][1] - 1, r['size'][0], 1]
    wants_water = [(rect_of(mm), float(rule.split(':')[2])) for mm in r['members']
                   for rule in mm.get('reason', []) if rule.startswith('by:water')]
    cands.sort(key=score)
    base = reach(G, blocked_by(G, list(others), plan_points(plan, skip)))
    best = None
    for orient, mirror, x, y in cands[:2000]:
        pl = expand(recipe, [x, y], orient, mirror, seed, grades=grades)
        faults = check_placement(plan, pl, others, area=area, G=G, skip=skip, base=base, fast=True)
        if not faults:
            return pl, None
        if best is None or len(faults) < len(best):
            best = faults
    return None, best or ['no candidate inside the area']


def as_plan_entry(pl: dict) -> dict:
    return {'recipe': pl['recipe'], 'at': pl['at'], 'orient': pl['orient'], 'mirror': pl['mirror'], 'seed': pl['seed']}


# --- checks over plans and the self-test ------------------------------------------------

NOTES: list = []


def check_plans() -> list:
    out = []
    if not os.path.isdir(PLANS):
        return out
    grades = ledger_grades()
    for f in sorted(os.listdir(PLANS)):
        if not f.endswith('.json'):
            continue
        with open(os.path.join(PLANS, f)) as fh:
            plan = json.load(fh)
        entries = plan.get('clusters', [])
        if not entries:
            continue
        G = Ground(plan)
        placed = []
        for e in entries:
            if 'orient' not in e:
                # a cluster place a lane wrote by hand, waiting for a recipe and the placer (lane
                # D's plans): reported, not held to the rules until it is a placement
                key = e['recipe'].replace(' ', '_').replace('-', '_')
                NOTES.append(f'{plan["id"]}: cluster place "{e["recipe"]}" at {tuple(e.get("at", ()))} is not a '
                             f'placement yet ({"recipe " + key + " exists" if key in RECIPES else "no recipe yet"}; '
                             f'run --place to make one)')
                continue
            if e['recipe'] not in RECIPES:
                out.append(f'{plan["id"]}: unknown cluster recipe {e["recipe"]}')
                continue
            if plan.get('biome') not in RECIPES[e['recipe']]['biomes'] and not e.get('any_biome'):
                out.append(f'{plan["id"]}: {e["recipe"]} belongs in {RECIPES[e["recipe"]]["biomes"]}, '
                           f'not {plan.get("biome")} (set any_biome on the entry to place it anyway)')
            pl = expand(e['recipe'], e['at'], e.get('orient', 's'), e.get('mirror', False), e.get('seed', 0), grades=grades)
            skip = {tuple(e['replaces'])} if e.get('replaces') else set()
            out += check_placement(plan, pl, placed, G=G, skip=skip)
            placed.append(pl)
        out += check_glows(plan, placed)
    return out


def test_plan() -> dict:
    """A small meadow for the self-test: a raised knoll with a stair, a winding trod and a
    road, a canal with its towpath, a pond, a cottage and a view."""
    return {
        'id': 'selftest', 'biome': 'meadow', 'box': [0, 0, 640, 480],
        'tiers': [{'id': 'knoll', 'tier': 1, 'outline': [[400, 40], [600, 40], [600, 200], [400, 200]]}],
        'routes': [{'id': 'road', 'width': 32, 'points': [[0, 296], [200, 296], [320, 312], [640, 312]]}],
        'trods': [{'id': 'trod', 'width': 24, 'points': [[160, 296], [160, 160], [240, 80], [240, 0]]},
                  {'id': 'up', 'width': 24, 'points': [[480, 312], [480, 160]]},
                  {'id': 'towpath', 'width': 24, 'points': [[0, 464], [320, 464]]}],
        'stairs': [{'id': 'knoll_stair', 'on': 'up', 'at': [480, 216], 'from_tier': 0, 'to_tier': 1, 'width': 40}],
        'water': [{'id': 'canal', 'kind': 'canal', 'width': 24, 'points': [[0, 420], [320, 420]]},
                  {'id': 'pond', 'kind': 'pool', 'closed': True,
                   'points': [[560, 400], [632, 400], [632, 472], [560, 472]]}],
        'structures': [{'kind': 'cottage', 'rect': [200, 200, 64, 40]}],
        'places': [{'id': 'view', 'kind': 'view', 'at': [600, 260]}],
        'markers': [{'t': 'I', 'what': 'bench', 'at': [96, 264]}, {'t': 'S', 'what': 'cairn', 'at': [560, 360]}],
        'areas': [{'id': 'west', 'rect': [0, 0, 320, 480]}, {'id': 'east', 'rect': [320, 0, 320, 480]}],
    }


FIRST_EIGHT = ('meadow_nook', 'field_edge', 'farmyard', 'shore', 'woodland_glade', 'town_square_corner',
               'steppe_camp', 'moor_wayside')


def self_test() -> list:
    out = []
    plan = test_plan()
    G = Ground(plan)
    for i, name in enumerate(RECIPES):  # each recipe on its own
        pl, faults = place(plan, name, area=None, seed=i, G=G)
        if pl is None:
            out.append(f'self-test: {name} found no place in the test meadow: {faults[:3]}')
    placed = []
    for i, name in enumerate(FIRST_EIGHT):  # and eight together, each clear of the others
        pl, faults = place(plan, name, area=None, seed=i, others=placed, G=G)
        if pl is None:
            out.append(f'self-test: {name} found no place beside the others: {faults[:3]}')
            continue
        again = check_placement(plan, pl, placed, G=G)
        if again:
            out.append(f'self-test: {name} placed but fails its own check: {again[:3]}')
        placed.append(pl)
        e = expand(name, pl['at'], pl['orient'], pl['mirror'], pl['seed'])
        if e != expand(name, pl['at'], pl['orient'], pl['mirror'], pl['seed']):
            out.append(f'self-test: {name} does not expand the same twice')
    # the checks must catch what they claim to catch
    bad = expand('meadow_nook', [184, 280], 's', False, 0)    # on the road
    if not any('path' in f for f in check_placement(plan, bad, G=G)):
        out.append('self-test: a nook on the road was not caught')
    bad = expand('meadow_nook', [400, 184], 's', False, 0)    # its feet on the knoll's face
    if not any('face' in f or 'tiers' in f or 'lip' in f for f in check_placement(plan, bad, G=G)):
        out.append('self-test: a nook over the knoll\'s face was not caught')
    first = place(plan, 'meadow_nook', area='west', seed=3, G=G)[0]
    if first:
        twin = dict(expand('meadow_nook', [first['at'][0] + 8, first['at'][1]], first['orient'], first['mirror'], 3))
        if not any('hit box' in f or 'apart' in f or 'from meadow_nook' in f for f in check_placement(plan, twin, [first], G=G)):
            out.append('self-test: two nooks a cell apart were not caught')
    # a wall of blockers round a stand: unreachable
    walled = expand('farmyard', [16, 360], 's', False, 0)
    ring = {'recipe': 'farmyard', 'at': [0, 0], 'members': [
        {'role': 'wall', 'blocks': True, 'foot': [s[0] - 12, s[1] - 12, 24, 4]} for s in walled['members'][5]['stand']] + [
        {'role': 'wall', 'blocks': True, 'foot': [s[0] - 12, s[1] + 8, 24, 4]} for s in walled['members'][5]['stand']] + [
        {'role': 'wall', 'blocks': True, 'foot': [s[0] - 12, s[1] - 12, 4, 24]} for s in walled['members'][5]['stand']] + [
        {'role': 'wall', 'blocks': True, 'foot': [s[0] + 8, s[1] - 12, 4, 24]} for s in walled['members'][5]['stand']],
        'clear': [], 'lights': [], 'dressing': []}
    fl = check_placement(plan, walled, [ring], G=G)
    if not any('cannot be reached' in f for f in fl):
        out.append('self-test: a walled-in stand was not caught')
    # the stile needs a path through it
    fe = expand('field_edge', [8, 8], 's', False, 0)
    if not any('crossing' in f for f in check_placement(plan, fe, G=G)):
        out.append('self-test: a stile with no path through it was not caught')
    # the placement logic: a lamp with no path in its glow, a boat far from water, a stall of
    # stores far from any building, a bollard in the canal
    lamp = expand('meadow_nook', [8, 8], 's', False, 0)
    fl = check_placement(plan, lamp, G=G)
    if not any('lights no path' in f for f in fl):
        out.append('self-test: a lamp lighting no path was not caught')
    boat = expand('shore', [8, 8], 's', False, 0)
    if not any('from water' in f for f in check_placement(plan, boat, G=G)):
        out.append('self-test: a boat far from water was not caught')
    yard = expand('lagoon_hamlet', [304, 24], 's', False, 0)
    if not any('building' in f for f in check_placement(plan, yard, G=G)):
        out.append('self-test: fruit crates far from any building were not caught')
    wet = expand('canal_side', [64, 408], 's', False, 0)
    if not any('in water' in f for f in check_placement(plan, wet, G=G)):
        out.append('self-test: a bollard in the canal was not caught')
    # a touch target at the phone's narrowest is 44 CSS px or more
    if touch_css() < MIN_TOUCH_CSS:
        out.append(f'self-test: hit box {touch_css():.1f} CSS px')
    out += check_glows(plan, placed)
    return out


# --- a diagram per recipe ----------------------------------------------------------------

COLOURS = {'blocks': (120, 92, 60, 255), 'soft': (150, 190, 110, 255), 'clear': (250, 240, 200, 255),
           'hit': (220, 70, 70, 255), 'stand': (40, 120, 220, 255), 'dress': (60, 140, 60, 255),
           'light': (250, 200, 60, 255), 'crown': (70, 110, 60, 255), 'path': (205, 180, 140, 255),
           'ground': (180, 205, 150, 255)}


def draw(pl: dict, path_pts=None, scale: int = 4, margin: int = 24) -> Image.Image:
    xs = [mm['foot'][0] for mm in pl['members']] + [mm['foot'][0] + mm['foot'][2] for mm in pl['members']]
    ys = [mm['foot'][1] for mm in pl['members']] + [mm['foot'][1] + mm['foot'][3] for mm in pl['members']]
    x0, y0 = min(xs) - margin - 24, min(ys) - margin - 40
    x1, y1 = max(xs) + margin + 24, max(ys) + margin + 24
    img = Image.new('RGBA', (int((x1 - x0) * scale), int((y1 - y0) * scale)), COLOURS['ground'])
    d = ImageDraw.Draw(img)

    def R(rc):
        return [(rc[0] - x0) * scale, (rc[1] - y0) * scale, (rc[0] + rc[2] - x0) * scale - 1, (rc[1] + rc[3] - y0) * scale - 1]

    for gx in range(int(x0) - int(x0) % CELL, int(x1), CELL):
        d.line([((gx - x0) * scale, 0), ((gx - x0) * scale, img.height)], fill=(170, 195, 140, 255))
    for gy in range(int(y0) - int(y0) % CELL, int(y1), CELL):
        d.line([(0, (gy - y0) * scale), (img.width, (gy - y0) * scale)], fill=(170, 195, 140, 255))
    if path_pts:
        d.line([((x - x0) * scale, (y - y0) * scale) for x, y in path_pts], fill=COLOURS['path'], width=24 * scale)
    for c in pl['clear']:
        d.rectangle(R(c['rect']), fill=COLOURS['clear'])
    for mm in pl['members']:
        if mm.get('crown'):
            ax, ay = mm['anchor']
            rr = mm['crown']
            d.ellipse([(ax - rr - x0) * scale, (ay - 2.4 * rr - y0) * scale, (ax + rr - x0) * scale, (ay - 0.4 * rr - y0) * scale],
                      outline=COLOURS['crown'], width=2)
    for mm in pl['members']:
        d.rectangle(R(mm['foot']), fill=COLOURS['blocks' if mm['blocks'] else 'soft'], outline=(40, 30, 20, 255))
        d.text((R(mm['foot'])[0] + 3, R(mm['foot'])[1] + 2), mm['role'], fill=(255, 255, 255, 255))
        if mm.get('hit'):
            d.rectangle(R(mm['hit']), outline=COLOURS['hit'], width=2)
        for s in mm.get('stand', []):
            d.ellipse([(s[0] - 2 - x0) * scale, (s[1] - 2 - y0) * scale, (s[0] + 2 - x0) * scale, (s[1] + 2 - y0) * scale],
                      fill=COLOURS['stand'])
    for lt in pl['lights']:
        rr = lt.get('glow', lt.get('r', 24))
        d.ellipse([(lt['at'][0] - rr - x0) * scale, (lt['at'][1] - rr - y0) * scale,
                   (lt['at'][0] + rr - x0) * scale, (lt['at'][1] + rr - y0) * scale], outline=COLOURS['light'], width=2)
    for dd in pl['dressing']:
        d.ellipse([(dd['at'][0] - 2 - x0) * scale, (dd['at'][1] - 2 - y0) * scale,
                   (dd['at'][0] + 2 - x0) * scale, (dd['at'][1] + 2 - y0) * scale], fill=COLOURS['dress'])
    d.text((6, 6), f'{pl["recipe"]} ({pl["orient"]}{", mirrored" if pl["mirror"] else ""})', fill=(20, 20, 20, 255))
    return img


def main(argv) -> int:
    if '--build' in argv:
        with open(OUT, 'w') as fh:
            fh.write(library_text())
        print(f'wrote {os.path.relpath(OUT, ROOT)}: {len(RECIPES)} recipes')
        return 0
    if '--check' in argv:
        faults = check_recipes()
        try:
            with open(OUT) as fh:
                if fh.read() != library_text():
                    faults.append(f'{os.path.relpath(OUT, ROOT)} is stale: run prop_clusters.py --build')
        except OSError:
            faults.append(f'{os.path.relpath(OUT, ROOT)} is missing: run prop_clusters.py --build')
        faults += self_test()
        faults += check_plans()
        for n in NOTES:
            print('NOTE', n)
        for f in faults:
            print('FAULT', f)
        print(f'prop clusters: {len(RECIPES)} recipes, {len(faults)} faults')
        return 1 if faults else 0
    if '--place' in argv:
        i = argv.index('--place')
        plan_id, recipe = argv[i + 1], argv[i + 2]
        with open(plan_id if plan_id.endswith('.json') else os.path.join(PLANS, f'{plan_id}.json')) as fh:
            plan = json.load(fh)
        seed = int(argv[argv.index('--seed') + 1]) if '--seed' in argv else 0
        area = argv[argv.index('--area') + 1] if '--area' in argv else None
        near = [float(v) for v in argv[argv.index('--near') + 1].split(',')] if '--near' in argv else None
        others = [expand(e['recipe'], e['at'], e.get('orient', 's'), e.get('mirror', False), e.get('seed', 0))
                  for e in plan.get('clusters', [])]
        skip = {tuple(near)} if near else set()
        if plan.get('biome') not in RECIPES[recipe]['biomes']:
            print(f'note: {recipe} belongs in {RECIPES[recipe]["biomes"]}, this plan is {plan.get("biome")}; '
                  'add "any_biome": true to the entry if you mean it')
        pl, faults = place(plan, recipe, area=area, near=near, seed=seed, others=others, skip=skip)
        if pl is None:
            print('no place:', *faults, sep='\n  ')
            return 1
        entry = as_plan_entry(pl)
        if near:
            entry['replaces'] = [int(v) for v in near]
        print(json.dumps(entry))
        for mm in pl['members']:
            print(f'  {mm["role"]:<12} {mm["prop"]:<20} {mm["grade"]:<7} foot {mm["foot"]}'
                  + (f' hit {mm["hit"]}' if mm.get('hit') else ''))
        print(f'  {len(pl["dressing"])} dressing clumps, {len(pl["lights"])} lights')
        return 0
    if '--draw' in argv:
        rest = [a for a in argv[1:] if not a.startswith('--')]
        out_dir = rest[0] if rest else os.path.join(tempfile.gettempdir(), 'napattack-prop-clusters')
        os.makedirs(out_dir, exist_ok=True)
        for name, r in RECIPES.items():
            W, H = r['size']
            pl = expand(name, [64, 64], 's', False, 0, grades=ledger_grades())
            y = 64 + (H + 2) * CELL
            pts = [[0, y], [64 + W * CELL + 64, y]]
            if r.get('crossing'):
                cx = 64 + (r['crossing']['rect'][0] + r['crossing']['rect'][2] / 2) * CELL
                pts = [[cx, 0], [cx, 64 + H * CELL + 64]]
            draw(pl, pts).save(os.path.join(out_dir, f'{name}.png'))
        print('drew', len(RECIPES), 'recipes to', out_dir)
        return 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
