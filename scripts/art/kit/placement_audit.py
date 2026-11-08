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
    'crossroads_well': ('water', 'centrepiece', [], [OFF_ROUTE], 'fine', 'Central to the square.'),
    'crossroads_well_choked': ('water', 'centrepiece', [], [OFF_ROUTE], 'fine', 'The storm-broken well (story stage).'),
    # ---- light and guidance --------------------------------------------------------------------
    'crossroads_kit_lantern': ('light', 'light', None, None, 'fine', 'Along streets, at junctions and gates.'),
    'crossroads_lantern_lit': ('light', 'light', None, None, 'fine', 'As the lantern.'),
    'crossroads_lantern_dark': ('light', 'light', None, None, 'fine', 'As the lantern, unlit (story).'),
    'crossroads_notice_board': ('guide', 'marker', None, None, 'fine', 'On the square, at a route\'s edge.'),
    'crossroads_waystone': ('guide', 'marker', None, None, 'fine', 'At a junction; points down real routes.'),
    'crossroads_bench': ('rest', 'seat', None, None, 'fine', 'Beside a route, facing it.'),
    # ---- gardens, animals, boundaries ----------------------------------------------------------
    'crossroads_fence': ('contain', 'boundary', [], [OFF_ROUTE, OFF_WATER], 'redraw',
                         'One straight post-and-rail segment with no corner post, side run or gate, so it cannot close an enclosure '
                         '(rules.fences). Redraw as runs along x and y with corner posts and a gate, in the styles placement-logic '
                         'gives (wattle, hurdle, picket, rail); the Crossroads slice\'s painters are the model.'),
    'crossroads_beds_dug': ('grow', 'garden', [], [OFF_ROUTE, OFF_WATER], 'redraw',
                            'Four boarded boxes on bare earth that read as crates (Matt\'s Crossroads review); redraw as soil beds '
                            'with crops in a dug patch, inside a garden boundary.'),
    'crossroads_beds_scorched': ('grow', 'garden', [], [OFF_ROUTE, OFF_WATER], 'redraw', 'The burnt stage of the beds: redraw with them.'),
    'crossroads_trough': ('feed', 'trough', [R('within', 'pen', 0, 'inside a pen or paddock with its animals')], [OFF_ROUTE], 'missing',
                          'A trough needs animals and a pen; the kit has neither yet (no animal pieces, no pen boundary).'),
    'crossroads_hay': ('feed', 'feed', [R('within', 'pen', 1, 'in a paddock, a barn or a cart')], [OFF_ROUTE], 'redraw',
                       'Reads as pale slabs, not loose or baled hay; and like the trough it needs a pen. Redraw (the slice\'s hay heap is the model).'),
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

PURPOSES = ('contain', 'exclude', 'mark', 'rest', 'light', 'store', 'feed', 'cross', 'guide', 'work',
            'live', 'grow', 'climb', 'flow', 'care', 'water', 'aftermath')


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

- **Animals** (hens, sheep, a cow or a horse) and **pen boundaries** (hurdles, a chicken run, a
  paddock rail with a gate): without them a trough or hay has nothing to serve. The Crossroads
  slice's painters (#421) are the starting point.
- **Fence corners and gates**, and a **front-garden picket**: see `crossroads_fence`.
- **A signpost for junctions** (a waystone stands in for now) and **a coop / field shelter**.

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
        print('placement audit: %d pieces, each with a purpose' % len(files))
        return 0
    counts = write_doc()
    print('placement audit: %d pieces; %s' % (len(files), counts))
    return 0


if __name__ == '__main__':
    sys.exit(main())
