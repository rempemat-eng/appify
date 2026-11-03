"""The placement-logic audit of the kit's pieces (docs/vision/placement-logic.md, Matt, 2 Nov:
"think deeply about parts of the game like fences. where would they be? what would they fence in?").

Every prop and structure answers four questions: what it is for (its purpose), who uses it, why it
stands here and not elsewhere (its requires and forbids, checked by relations.py on every kit zone),
and how people reach it. This table is the one source for those answers; it writes them into the
pieces and the audit page:

    python3 -m scripts.art.kit.placement_audit           write purpose/requires/forbids into the
                                                         pieces and docs/vision/placement-audit.md
    python3 -m scripts.art.kit.placement_audit --check   exit 1 if a piece lacks a purpose or
                                                         differs from this table

Verdicts: 'fine' (drawing and placement fit the purpose), 'fixed' (its data or a placement was
corrected in this audit), 'redraw' (the drawing does not fit its purpose; listed for the art queue),
'missing' (it cannot be placed sensibly until a companion piece exists).
"""
from __future__ import annotations

import json
import os
import sys

from scripts.art.kit.schema import PIECES, ROOT

DOC = os.path.join(ROOT, 'docs', 'vision', 'placement-audit.md')


def R(rel, what, cells=None, note=None):
    r = {'rel': rel, 'what': what}
    if cells is not None:
        r['cells'] = cells
    if note:
        r['note'] = note
    return r


OFF_ROUTE = R('on', 'route')
OFF_WATER = R('on', 'water')
NATURE = [OFF_ROUTE, OFF_WATER]
HOUSE_ROLE = 'house'

# id: (purpose, role or None to keep, requires, forbids, verdict, note)
TABLE = {
    # ---- the woodland ------------------------------------------------------------------------
    'woodland_oak': ('grow', 'tree', [], NATURE, 'fine', 'Woodland and field-edge tree; never on a path or in water. Trunk box authored (2 Nov).'),
    'woodland_beech': ('grow', 'tree', [], NATURE, 'fine', 'As the oak.'),
    'woodland_birch': ('grow', 'tree', [], NATURE, 'fine', 'As the oak.'),
    'woodland_pine': ('grow', 'tree', [], NATURE, 'fixed', 'As the oak; one\'s trunk stood on the rill\'s bank and moved a cell west (2 Nov).'),
    'woodland_hollow_tree': ('grow', 'tree', [], NATURE, 'fine', 'A landmark tree; a creature\'s home in story.'),
    'woodland_willow': ('grow', 'tree', [R('within', 'water', 4, 'willows grow by water')], NATURE, 'fixed',
                        'Willows grow by water: requires water within 4 cells. It stood far from any water with its trunk on the east path; moved to the river\'s south bank (2 Nov).'),
    'woodland_sapling': ('grow', 'tree', [], NATURE, 'fine', 'Young growth at a wood\'s edge or in a clearing.'),
    'woodland_bush': ('grow', 'shrub', [], NATURE, 'fine', 'Understorey under and between trees, at path margins.'),
    'woodland_bush_b': ('grow', 'shrub', [], NATURE, 'fixed', 'One stood on the cascade\'s face; moved onto the raised ground (2 Nov).'),
    'woodland_bush_c': ('grow', 'shrub', [], NATURE, 'fine', 'As the bush.'),
    'woodland_holly': ('grow', 'shrub', [], NATURE, 'fine', 'Understorey.'),
    'woodland_holly_b': ('grow', 'shrub', [], NATURE, 'fixed', 'One crossed the zone\'s west edge once its solid box was restored; moved inside (2 Nov).'),
    'woodland_bramble': ('grow', 'shrub', [], NATURE, 'fine', 'Thickets at the wood\'s edge; blocks the way like a hedge.'),
    'woodland_bramble_b': ('grow', 'shrub', [], NATURE, 'fixed', 'One overlapped an oak\'s trunk; moved clear (2 Nov).'),
    'woodland_stump': ('mark', 'stump', [], NATURE, 'fine', 'Where a tree was felled: near paths and clearings, with mushrooms at its foot.'),
    'woodland_mossy_log': ('rest', 'log', [], NATURE, 'fine', 'A fallen trunk lying along the ground, a seat in a clearing.'),
    'woodland_boulder': ('mark', 'rock', [], [R('not_overlap', 'rock'), OFF_ROUTE], 'fixed',
                         'Talus under the escarpment and bank stones; one overlapped an oak\'s trunk and was moved clear (2 Nov).'),
    'woodland_forest_bench': ('rest', 'seat', None, None, 'fine',
                              'Beside the path, facing it, at the stone ring\'s view.'),
    'woodland_standing_stone': ('mark', 'marker', [R('within', 'marker', 4, 'one of a ring: its neighbours within four cells')], [OFF_ROUTE], 'fine', 'A stone of the ring.'),
    'woodland_standing_stone_b': ('mark', 'marker', [R('within', 'marker', 4)], [OFF_ROUTE], 'fine', 'A stone of the ring.'),
    'woodland_standing_stone_broken': ('mark', 'marker', [R('within', 'marker', 4)], [OFF_ROUTE], 'fine', 'A stone of the ring, broken.'),
    'woodland_standing_stone_lean': ('mark', 'marker', [R('within', 'marker', 4)], [OFF_ROUTE], 'fine', 'A stone of the ring, leaning.'),
    'woodland_standing_stone_low': ('mark', 'marker', [R('within', 'marker', 4)], [OFF_ROUTE], 'fixed',
                                    'A stone of the ring; the east one stood on the north-south path\'s edge and moved a half cell clear (2 Nov).'),
    'woodland_standing_stone_runes': ('mark', 'marker', [R('within', 'marker', 4)], [OFF_ROUTE], 'fine', 'The ring\'s rune stone.'),
    'woodland_lintel': ('mark', 'ruin', [R('within', 'marker', 2, 'a lintel fallen from the ring')], [OFF_ROUTE], 'fine', 'Fallen among the ring\'s stones.'),
    'woodland_stone_top': ('mark', 'ruin', [R('within', 'marker', 3, 'a capstone fallen from the ring')], [OFF_ROUTE], 'fine', 'Fallen beside the ring.'),
    'woodland_stone_sign': ('guide', 'marker', [R('at_edge', 'route')], [OFF_ROUTE], 'fine', 'A way-marker at a path; not placed yet.'),
    # ---- crossings, stairs and water -----------------------------------------------------------
    'woodland_footbridge': ('cross', 'bridge', [R('on', 'water', note='spans a channel 3 cells wide, north to south'),
                                                R('adjacent', 'route', 1, 'a route meets it at both ends')], [], 'fixed',
                            'Its two rules.requires faults: a walkable piece now stands on its deck\'s cells, the water it spans (relations._deck_cells).'),
    'footbridge_2': ('cross', 'bridge', None, [], 'fine', 'Exactly where a route meets a two-cell stream, the route\'s width.'),
    'footbridge_4': ('cross', 'bridge', None, [], 'fine', 'As footbridge_2, over four cells.'),
    'stepping_stones_1': ('cross', 'bridge', None, [], 'fixed', 'A footpath over a rill; its deck includes its landing stones, so the path meets it within a cell (was "adjacent", which no landing can satisfy).'),
    'stepping_stones_2': ('cross', 'bridge', None, [], 'fixed', 'As stepping_stones_1, over a stream.'),
    'log_steps': ('climb', 'stair', None, [], 'fine', 'Where a route climbs a face; on the face, a route at head and foot.'),
    'log_steps_1': ('climb', 'stair', None, [], 'fine', 'As log_steps.'),
    'log_steps_3': ('climb', 'stair', None, [], 'fine', 'As log_steps.'),
    **{'waterfall_%d%s' % (n, t): ('flow', 'waterfall', None, [], 'fixed',
                                   'Water crossing a rim: the sheet starts at the rim, the channel\'s width, foam on the pool only (2 Nov).')
       for n in (1, 2, 3, 4) for t in ('', '_tall')},
    # ---- the village: homes and work ----------------------------------------------------------
    'crossroads_bakery': ('live', 'house', [], [OFF_ROUTE, OFF_WATER], 'fine', 'A shop-home on the square; its door onto a route.'),
    'crossroads_fern_cottage': ('live', 'house', [], [OFF_ROUTE, OFF_WATER], 'fine', 'A cottage on a lane.'),
    'crossroads_herbalist': ('live', 'house', [], [OFF_ROUTE, OFF_WATER], 'fine', 'A shop-home.'),
    'crossroads_hut': ('live', 'house', [], [OFF_ROUTE, OFF_WATER], 'fine', 'The companion\'s hut.'),
    'crossroads_library': ('live', 'house', [], [OFF_ROUTE, OFF_WATER], 'fine', 'A public building on the square.'),
    'crossroads_north_cottages': ('live', 'house', [], [OFF_ROUTE, OFF_WATER], 'fine', 'A terrace on the north lane.'),
    'crossroads_smithy': ('work', 'forge', [], [OFF_ROUTE, OFF_WATER], 'fine', 'The forge: the hearth anvil, coal and grindstone gather round.'),
    'crossroads_anvil': ('work', 'workplace', None, None, 'fine', 'Beside the forge.'),
    'crossroads_coal': ('store', 'store', [R('near', 'forge', 2, 'fuel for the forge')], [OFF_ROUTE], 'fine', 'Heaped by the forge.'),
    'crossroads_grindstone': ('work', 'workplace', [R('near', 'forge', 3)], [OFF_ROUTE], 'fine', 'In the smithy\'s yard.'),
    'crossroads_woodpile': ('store', 'store', [R('within', HOUSE_ROLE, 2, 'fuel against the gable wall of a house with a chimney')], [OFF_ROUTE], 'fine',
                            'Against a gable wall or under the eaves; never away from a hearth.'),
    'crossroads_barrel': ('store', 'store', [R('within', HOUSE_ROLE, 2, 'goods kept by a house, shop or stall')], [OFF_ROUTE], 'fine', 'By a door or a shop, never loose on a lawn.'),
    'crossroads_crates': ('store', 'store', [R('within', HOUSE_ROLE, 2)], [OFF_ROUTE], 'fine', 'As the barrel.'),
    'crossroads_sacks': ('store', 'store', [R('within', HOUSE_ROLE, 2)], [OFF_ROUTE], 'fine', 'As the barrel.'),
    'crossroads_handcart': ('store', 'cart', [R('at_edge', 'route')], [OFF_ROUTE], 'fine', 'At a road\'s edge by a shop or the market.'),
    'crossroads_stall': ('work', 'stall', [R('at_edge', 'route')], [OFF_ROUTE], 'fine', 'In rows on the square with aisles; its front to the route.'),
    'crossroads_flower_tub': ('care', 'planter', [R('within', HOUSE_ROLE, 1, 'by a door or under a window')], [OFF_ROUTE], 'fine', 'By a door.'),
    'crossroads_well': ('water', 'centrepiece', [R('near', HOUSE_ROLE, 8, 'water for homes: a square or a farmyard')],
                        [OFF_ROUTE, R('not_near', 'water', 6, 'never beside a river that is easier to draw from')], 'fixed',
                        'Central to the square. Props sweep (3 Nov): requires homes within 8 cells, forbids a river within 6.'),
    'crossroads_well_choked': ('water', 'centrepiece', [], [OFF_ROUTE], 'fine', 'The storm-broken well (story stage).'),
    # ---- light and guidance --------------------------------------------------------------------
    'crossroads_kit_lantern': ('light', 'light', [R('at_edge', 'route', 1)], [OFF_ROUTE, R('not_near', 'centrepiece', 1, 'never on a well')],
                               'fixed', 'Along streets, at junctions and gates. Props sweep (3 Nov): never on a well.'),
    'crossroads_lantern_lit': ('light', 'light', [R('at_edge', 'route', 1)], [OFF_ROUTE, R('not_near', 'centrepiece', 1, 'never on a well')],
                               'fixed', 'As the lantern; its solid box is the plinth (was 22 world px deep up the post).'),
    'crossroads_lantern_dark': ('light', 'light', [R('at_edge', 'route', 1)], [OFF_ROUTE, R('not_near', 'centrepiece', 1, 'never on a well')],
                                'fixed', 'As the lantern, unlit (story).'),
    'crossroads_notice_board': ('guide', 'marker', None, None, 'fine', 'On the square, at a route\'s edge.'),
    'crossroads_waystone': ('guide', 'marker', [R('at_corner', 'route', 2, 'at a junction: routes on two sides at right angles')], [], 'fixed',
                            'At a junction, pointing down real routes. Props sweep (3 Nov): at_corner route (was at_edge, which a straight path also met).'),
    'crossroads_bench': ('rest', 'seat', None, None, 'fine', 'Beside a route, facing it.'),
    # ---- gardens, animals, boundaries ----------------------------------------------------------
    'crossroads_fence': ('contain', 'boundary', [], [OFF_ROUTE, OFF_WATER], 'fixed',
                         'Retired (3 Nov): one straight post-and-rail segment could not close an enclosure. Replaced by the '
                         'modular fence cells `fence_wattle_*` and `fence_picket_*` (scripts/art/kit/fences.py): straights, '
                         'corners, Ts, a cross, end posts and a gate three cells wide, which close loops (enclosures.py).'),
    'crossroads_beds_dug': ('grow', 'garden', [], [OFF_ROUTE, OFF_WATER], 'fixed',
                            'Redrawn (3 Nov, scripts/art/kit/farm.py): three soil ridges with a crop on each (cabbage, leek, lettuce; '
                            'carrot, cabbage, beans) in a dug patch with a rough spade edge, no boards. Holds crops for a kitchen '
                            "garden's wattle (placement.enclosure)."),
    'crossroads_beds_scorched': ('grow', 'garden', [], [OFF_ROUTE, OFF_WATER], 'fixed',
                                 'Redrawn with the beds (3 Nov): the same ridges burnt, crops black stubs in ash, green coming back.'),
    'crossroads_trough': ('feed', 'trough', [R('near', 'stock', 4, 'its animals drink from it'),
                                             R('within', 'boundary', 4, 'inside their pen or paddock')], [OFF_ROUTE], 'fixed',
                          'The kit now has animals (`farm_sheep*`, `farm_hen_*`, role stock) and pens (the fence cells): it stands '
                          'inside a fold with its flock (placement.enclosure: what sheep and horses need).'),
    'crossroads_hay': ('feed', 'feed', [R('near', 'stock', 6, 'feed forked out for the stock, in a paddock, a fold or a barn')],
                       [OFF_ROUTE], 'fixed',
                       'Redrawn (3 Nov): three tied bales stacked, and a heap forked out loose; placed by the animals it feeds.'),
    'crossroads_bush': ('grow', 'shrub', [], NATURE, 'fine', 'Hedges and garden shrubs.'),
    'crossroads_bush_nonblocking': ('grow', 'shrub', [], NATURE, 'fine', 'Low shrubs the companion walks through.'),
    'crossroads_oak': ('grow', 'tree', [], NATURE, 'fine', 'The square\'s tree.'),
    'crossroads_boulder': ('mark', 'rock', [], [R('not_overlap', 'rock'), OFF_ROUTE], 'fine', 'Field stones at the village edge.'),
    # ---- the storm's aftermath (story stages only) --------------------------------------------
    **{k: ('aftermath', 'clutter', [], [OFF_WATER], 'fine', 'Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored.')
       for k in ('crossroads_debris_a', 'crossroads_debris_b', 'crossroads_debris_c', 'crossroads_debris_d',
                 'crossroads_square_rubble_a', 'crossroads_square_rubble_b', 'crossroads_square_puddles',
                 'crossroads_smithy_rubble', 'crossroads_fern_rubble', 'crossroads_crater_smoke')},
}


def _farm_rows():
    """The modular fences and the farmyard (scripts/art/kit/fences.py, farm.py): their purpose,
    role, requires and forbids are written by those painters (None keeps them)."""
    rows = {}
    for style, purpose in (('wattle', 'contain'), ('picket', 'mark'), ('rail', 'contain')):
        for mask in range(1, 16):
            jn = ''.join(c for i, c in enumerate('nesw') if mask & (1 << i))
            rows['fence_%s_%s' % (style, jn)] = (purpose, 'boundary', None, None, 'fine',
                                                 'A %s fence cell (arms %s): closes a loop with its neighbours (enclosures.py).' % (style, jn))
        for ax in ('ew', 'ns'):
            rows['fence_%s_gate_%s' % (style, ax)] = (purpose, 'gate', None, None, 'fine',
                                                       'A %s gate three cells wide, on the path its owner walks (requires on route).' % style)
    rows.update({
        'farm_hen_white': ('live', 'stock', None, None, 'fine', 'In a chicken run of 3 to 4 cells, near its coop.'),
        'farm_hen_brown': ('live', 'stock', None, None, 'fine', 'As the white hen.'),
        'farm_hen_speckled': ('live', 'stock', None, None, 'fine', 'As the white hen.'),
        'farm_sheep': ('live', 'stock', None, None, 'fine', 'In a fold of 6 to 10 cells with its trough and shelter.'),
        'farm_sheep_graze': ('live', 'stock', None, None, 'fine', 'As the sheep.'),
        'farm_sheep_lie': ('live', 'stock', None, None, 'fine', 'As the sheep.'),
        'farm_coop': ('live', 'coop', None, None, 'fine', 'In the run\'s back corner against its fence; the hens about it.'),
        'farm_shelter': ('live', 'shelter', None, None, 'fine', 'Its back to the fold\'s hurdles, its open side away from the weather.'),
        'garden_flower_border': ('care', 'planter', None, None, 'fine', 'In a front garden, beside the door path.'),
        'fence_rail_stile_ew': ('contain', 'stile', None, None, 'fine', 'Where a footpath crosses a paddock\'s rails: people over, stock in.'),
        'fence_rail_stile_ns': ('contain', 'stile', None, None, 'fine', 'As the stile along x.'),
        'farm_cow': ('live', 'stock', None, None, 'fine', 'In a paddock of 10 cells or more with water and a field shelter.'),
        'farm_calf': ('live', 'stock', None, None, 'fine', 'As the cow, near her.'),
        'farm_horse': ('live', 'stock', None, None, 'fine', 'In a paddock of 10 cells or more with water and a field shelter.'),
        'farm_pig': ('live', 'stock', None, None, 'fine', 'In the run before its sty, with a wallow and a trough.'),
        'farm_goat': ('live', 'stock', None, None, 'fine', 'In a pen of 4 to 8 cells with a shelter and water.'),
        'farm_goat_b': ('live', 'stock', None, None, 'fine', 'As the goat.'),
        'farm_sty': ('live', 'sty', None, None, 'fine', 'The north wall of its pigs\' run, its door and trough facing into it.'),
        'farm_wallow': ('live', 'wallow', None, None, 'fine', 'In the pigs\' run, off the trodden way.'),
        'farm_churns': ('store', 'churns', None, None, 'fine', 'By a yard or paddock gate, where the cart stops.'),
        'farm_water_butt': ('water', 'water_butt', None, None, 'fine', 'Against a building, under its downpipe.'),
        'farm_wheelbarrow': ('work', 'barrow', None, None, 'fine', 'By the muck heap or the beds it serves.'),
        'farm_scarecrow': ('grow', 'scarecrow', None, None, 'fine', 'In the crops, never on the path.'),
        'farm_feed_sacks': ('store', 'sacks', None, None, 'fine', 'By the stock they feed, at a shelter or coop.'),
        'farm_muck_heap': ('store', 'muck_heap', None, None, 'fine', 'Beside the pens it is mucked out of, away from the house door.'),
    })
    return rows


TABLE.update(_farm_rows())


def _commons_rows():
    """The village commons (scripts/art/kit/commons.py): written by that painter (None keeps)."""
    rows = {
        'commons_washing_line': ('work', 'washing_line', 'In a house\'s back yard (needs home 4, yard side); never in wild woods.'),
        'commons_chopping_block': ('work', 'chopping_block', 'Near a hearth (needs hearth 6), by the woodpile.'),
        'commons_woodpile': ('store', 'store', 'Against a house with a chimney (needs hearth 4).'),
        'commons_bench': ('rest', 'seat', 'Facing a feature, a view, water or the land falling away (faces, 6 cells).'),
        'commons_notice_board': ('guide', 'marker', 'At a route\'s edge where people pass; never in wild woods.'),
        'commons_pump': ('water', 'centrepiece', 'On a green near homes; a feature benches face.'),
        'commons_stall_produce': ('work', 'stall', 'At a route\'s edge on the green or square, beside its pair.'),
        'commons_stall_cloth': ('work', 'stall', 'As the produce stall.'),
        'commons_cart': ('store', 'cart', 'At a road\'s edge, off the way.'),
        'commons_shrine': ('mark', 'marker', 'At the wayside; a feature to face.'),
    }
    out = {pid: (pu, ro, None, None, 'fine', note) for pid, (pu, ro, note) in rows.items()}
    for pts in ('nes', 'esw', 'nsw', 'new', 'nesw'):
        out['commons_fingerpost_' + pts] = ('guide', 'signpost', None, None, 'fine',
                                            'At a junction whose routes leave %s (points).' % '-'.join(pts.upper()))
    return out


TABLE.update(_commons_rows())

# What the existing pieces offer the placement logic (provides) and where they never stand (avoid):
# check_plan reads them; apply() writes them.
LOGIC = {
    **{pid: {'provides': ['home', 'hearth']} for pid in ('crossroads_bakery', 'crossroads_fern_cottage', 'crossroads_herbalist',
                                                         'crossroads_hut', 'crossroads_north_cottages')},
    'crossroads_library': {'provides': ['hearth']},
    'crossroads_smithy': {'provides': ['hearth']},
    'crossroads_well': {'provides': ['feature', 'water']},
    'crossroads_well_choked': {'provides': ['feature']},
    **{pid: {'provides': ['feature', 'view']} for pid in ('woodland_standing_stone', 'woodland_standing_stone_b', 'woodland_standing_stone_broken',
                                                          'woodland_standing_stone_lean', 'woodland_standing_stone_low',
                                                          'woodland_standing_stone_runes')},
    **{pid: {'provides': ['view', 'water']} for pid in ('waterfall_1', 'waterfall_1_tall', 'waterfall_2', 'waterfall_2_tall', 'waterfall_3',
                                                        'waterfall_3_tall', 'waterfall_4', 'waterfall_4_tall')},
    **{pid: {'avoid': ['wild_woods']} for pid in ('crossroads_kit_lantern', 'crossroads_lantern_lit', 'crossroads_lantern_dark',
                                                  'crossroads_notice_board', 'crossroads_stall')},
}

PURPOSES = ('contain', 'exclude', 'mark', 'rest', 'light', 'store', 'feed', 'cross', 'guide', 'work',
            'live', 'grow', 'climb', 'flow', 'care', 'water', 'aftermath')


# ------------------------------------------------------------------------------------------------
# the placement logic relations cannot say (round 3, 3 Nov): what a piece needs near it, what it
# faces, where it never stands and where a signpost's arms point
# ------------------------------------------------------------------------------------------------
DIRS = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}


def _plan_logic_context(plan, lib, mats):
    from scripts.art.kit import relations as RL
    ctx = RL._context(plan, mats)
    if ctx is None:
        return None
    grid, tiers, width, height = ctx
    route = {c for c, m in grid.items() if RL._matches_material('route', m, mats)}
    water = {c for c, m in grid.items() if RL._matches_material('water', m, mats)}
    placed = []
    for i, e in enumerate(plan.get('pieces', [])):
        piece = lib.get(e.get('piece'))
        if piece is None or RL._position(e, plan) is None:
            continue
        placed.append((i, e, piece, RL._occupied(e, piece, plan), RL._position(e, plan)))
    return RL, grid, tiers, route, water, placed


def _dist(a, b):
    return min((max(abs(x - X), abs(y - Y)) for x, y in a for X, Y in b), default=10 ** 6)


def check_plan(plan, lib=None, mats=None) -> list:
    """rules.needs, rules.faces, rules.avoid and rules.points on a kit plan (see the schema's
    placement.needs, faces, avoid and points)."""
    from scripts.art.kit import relations as RL
    lib = lib if lib is not None else RL.default_library()
    mats = mats if mats is not None else RL.default_materials()
    c = _plan_logic_context(plan, lib, mats)
    if c is None:
        return []
    RL, grid, tiers, route, water, placed = c
    out = []

    def f(check, eid, msg, at):
        out.append({'check': check, 'message': '%s: %s' % (eid, msg), 'at': at, 'severity': 'fault'})
    providers = {}
    for i, e, piece, occ, pos in placed:
        for tag in (piece.get('placement') or {}).get('provides', []):
            providers.setdefault(tag, []).append((i, e, piece, occ, pos))
    trees = [pos for i, e, piece, occ, pos in placed if (piece.get('placement') or {}).get('role') == 'tree']
    for i, e, piece, occ, pos in placed:
        pl = piece.get('placement') or {}
        eid = str(e.get('id', e.get('piece')))
        at = e.get('at')
        for need in pl.get('needs', []):
            ok = False
            for j, e2, p2, occ2, pos2 in providers.get(need['what'], []):
                if j == i or _dist(occ, occ2) > need['cells']:
                    continue
                if need.get('side') == 'yard' and pos[1] > pos2[1] + 1e-6:
                    continue                                # in front of the house: not its yard
                ok = True
                break
            if not ok:
                f('rules.needs', eid, 'needs a %s within %g cells%s%s' % (need['what'], need['cells'], ' (in its yard)' if need.get('side') == 'yard' else '',
                                                                       ': ' + need['note'] if need.get('note') else ''), at)
        if pl.get('faces'):
            fc = pl['faces']
            facing = str(e.get('facing', 's')).lower()
            dx, dy = DIRS.get(facing, (0, 1))
            targets = set()
            for tag in fc['what']:
                if tag == 'water':
                    targets |= water
                elif tag == 'lower':
                    targets |= {cc for cc, t in tiers.items() if any(tiers.get(o, t) > t for o in occ)}
                for j, e2, p2, occ2, pos2 in providers.get(tag, []):
                    if j != i:
                        targets |= occ2
            seen = False
            for x, y in targets:
                rx, ry = x + 0.5 - pos[0], y + 0.5 - pos[1]
                dot, cross = rx * dx + ry * dy, rx * dy - ry * dx
                if 0 < dot <= fc['cells'] + 0.5 and abs(cross) <= dot + 1e-7:
                    seen = True
                    break
            if not seen:
                f('rules.faces', eid, 'faces %s and sees no %s within %g cells%s' % (facing, ' or '.join(fc['what']), fc['cells'],
                                                                                  ': ' + fc['note'] if fc.get('note') else ''), at)
        if 'wild_woods' in pl.get('avoid', []):
            near_trees = sum(1 for t in trees if max(abs(t[0] - pos[0]), abs(t[1] - pos[1])) <= 4)
            homes = [occ2 for j, e2, p2, occ2, pos2 in providers.get('home', [])]
            if near_trees >= 3 and not any(_dist(occ, o) <= 8 for o in homes):
                f('rules.avoid', eid, 'stands in wild woods (%d trees within 4 cells, no home within 8)' % near_trees, at)
        if pl.get('points'):
            # the ways out of the junction: for each side, a route crossing the band 3 to 5 cells
            # out from the post (2 either side of its line), so a two-cell lane counts once
            fx, fy = int(pos[0]), int(pos[1] - 1e-7)
            dirs = set()
            for d, (ux, uy) in DIRS.items():
                for k in range(3, 6):
                    for w in range(-2, 3):
                        cx_, cy_ = fx + ux * k + uy * w, fy + uy * k + ux * w
                        if (cx_, cy_) in route:
                            dirs.add(d)
            if len(dirs) < 3:
                f('rules.points', eid, 'a signpost stands at no junction (routes leave its corner %s: three or more ways make one)'
                  % (''.join(d for d in 'nesw' if d in dirs) or 'nowhere'), at)
            elif set(pl['points']) != dirs:
                f('rules.points', eid, 'its arms point %s but the routes leave the junction %s' % (''.join(d for d in 'nesw' if d in pl['points']),
                                                                                                   ''.join(d for d in 'nesw' if d in dirs)), at)
    return out


def check_zones() -> list:
    """check_plan over every kit zone: (zone, finding)."""
    out = []
    zdir = os.path.join(ROOT, 'game', 'kit', 'zones')
    for fn in sorted(os.listdir(zdir)):
        if fn.endswith('.json'):
            plan = json.load(open(os.path.join(zdir, fn)))
            out += [(fn[:-5], x) for x in check_plan(plan)]
    # the review studies built from kit pieces (farm_study, village_study)
    from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
    from scripts.art.kit import farm_study, village_study
    for name, mod in (('farm_study', farm_study), ('village_study', village_study)):
        out += [(name, x) for x in check_plan(mod.plan())]
    return out


def _files():
    out = {}
    for kind in ('prop', 'structure'):
        d = os.path.join(PIECES, kind)
        for f in sorted(os.listdir(d)):
            if f.endswith('.json'):
                out[f[:-5]] = os.path.join(d, f)
    return out


def apply(piece: dict) -> dict:
    purpose, role, req, forb, _v, _n = TABLE[piece['id']]
    pl = piece.setdefault('placement', {})
    pl.update(LOGIC.get(piece['id'], {}))
    pl['purpose'] = purpose
    if role:
        pl['role'] = role
    if req is not None:
        if req:
            pl['requires'] = req
        else:
            pl.pop('requires', None)
    if forb is not None:
        if forb:
            pl['forbids'] = forb
        else:
            pl.pop('forbids', None)
    return piece


def write_doc():
    counts = {}
    rows = []
    for pid in sorted(TABLE):
        purpose, role, req, forb, verdict, note = TABLE[pid]
        counts[verdict] = counts.get(verdict, 0) + 1
        p = json.load(open(_files()[pid]))
        pl = p.get('placement', {})
        rq = '; '.join('%s %s%s' % (r['rel'], r['what'], (' %g' % r['cells']) if 'cells' in r else '') for r in pl.get('requires', [])) or '-'
        fb = '; '.join('%s %s' % (r['rel'], r['what']) for r in pl.get('forbids', [])) or '-'
        rows.append('| `%s` | %s | %s | %s | %s | **%s** | %s |' % (pid, purpose, pl.get('role') or '-', rq, fb, verdict, note.replace('|', '/')))
    head = """# Placement audit (Claude A, 2 Nov)

Matt, 2 Nov: "think deeply about parts of the game like fences. where would they be? what would they
fence in?" Every prop and structure in `game/kit/pieces` has been checked against
[placement-logic.md](placement-logic.md): what it is for (**purpose**), where it may stand (**requires**,
**forbids**, read by `scripts/art/kit/relations.py` on every kit zone in `check:kit`), and whether its
drawing fits that purpose. The table is generated from `scripts/art/kit/placement_audit.py`, which also
writes each piece's `placement.purpose`, requires and forbids; `--check` (in `check:kit`) fails when a
piece has no purpose or drifts from the table. Terrain materials and transitions are ground, not
placed objects, and are not listed.

Verdicts: **fine** (fits), **fixed** (its data or a placement was corrected in this audit), **redraw**
(the drawing does not fit its purpose: the art queue), **missing** (cannot be placed sensibly until a
companion piece exists).

Totals: %s.

## Placements fixed in the kit zones

- `woodland_kit`: the footbridge's two `rules.requires` faults (a walkable piece now stands on its
  deck's cells, so the bridge stands on the water it spans with the path meeting it at both banks);
  the willow's trunk off the east path; a bush off the cascade's face; the stone ring's east stone
  clear of the north-south path; with the woodland's solid boxes restored, a holly inside the zone's
  west edge, a bramble clear of an oak, a boulder clear of the oak by the pool; the north path ends
  in trodden ground at the glade instead of stopping dead in the lawn; the waterfall's top.
- `kitlab_widths`: the stepping stones' path relation (their deck carries their landing stones).
- `kitlab`, `kitlab_tiers`: nothing out of place (a lab's bench, oak, stump and boulders beside its
  routes).

## Missing pieces

- ~~Animals and pen boundaries~~ (3 Nov): hens, sheep, a hen ark, a field shelter and fence cells in
  wattle and picket that close loops (`scripts/art/kit/farm.py`, `fences.py`; the loops and what they
  hold are checked by `enclosures.py`). Still missing: a cow, a horse and a paddock rail.
- ~~A signpost for junctions~~ (3 Nov): fingerposts, one per set of arms (`commons_fingerpost_*`);
  their arms must point along the routes that leave the junction (`placement.points`): the routes crossing a band 3 to 5 cells out from the post on each side.

## Placement logic beyond relations (3 Nov)

`placement_audit.check_plan` (in `--check`, over every kit zone and the village-green study) reads
four fields relations cannot express: **needs** (a tag some piece `provides` within N cells, e.g. a
woodpile needs a hearth; `side: yard` means behind the provider, so washing never hangs before the
front door), **faces** (from the piece's `facing`, a cone N cells deep must hold a feature, a view,
water or lower ground), **avoid** (`wild_woods`: three or more trees within 4 cells and no home
within 8) and **points** (a signpost's arms equal the sides on which routes leave it, read 3 to 5 cells
out, so a two-cell lane counts once; three ways or more make a junction).

## Table

| Piece | Purpose | Role | Requires | Forbids | Verdict | Why, and what was done |
|---|---|---|---|---|---|---|
""" % ', '.join('%d %s' % (counts[k], k) for k in ('fine', 'fixed', 'redraw', 'missing') if k in counts)
    open(DOC, 'w').write(head + '\n'.join(rows) + '\n')
    return counts


def main(argv=None) -> int:
    check = '--check' in (argv if argv is not None else sys.argv[1:])
    files = _files()
    bad = [k for k in files if k not in TABLE] + [k for k in TABLE if k not in files]
    if bad:
        print('placement audit: not in both the table and the pieces: %s' % ', '.join(sorted(bad)))
        return 1
    stale = []
    for pid, f in files.items():
        p = json.load(open(f))
        want = apply(json.loads(json.dumps(p)))
        if TABLE[pid][0] not in PURPOSES:
            stale.append(pid + ' (unknown purpose)')
        if want != p:
            if check:
                stale.append(pid)
            else:
                open(f, 'w').write(json.dumps(want, indent=1) + '\n')
    if check:
        if stale:
            print('placement audit: pieces differ from the table: %s (run python3 -m scripts.art.kit.placement_audit)' % ', '.join(stale))
            return 1
        zf = check_zones()
        if zf:
            for z, x in zf:
                print('placement audit: %s %s %s' % (z, x['check'], x['message']))
            return 1
        print('placement audit: %d pieces, each with a purpose; kit zones and the studies meet needs, faces, avoid and points' % len(files))
        return 0
    counts = write_doc()
    print('placement audit: %d pieces; %s' % (len(files), counts))
    return 0


if __name__ == '__main__':
    sys.exit(main())
