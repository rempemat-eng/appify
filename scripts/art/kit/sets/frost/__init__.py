"""The Frostline set (docs/vision/regions/home-valley-frostline-brackens.md; the Frostline zone,
game/kit/zones/frostline.json), round 2 after the detail and logic audits of #478. Drawn with the
Brackens' renderer and helpers (scripts/art/kit/sets/_common.py) and the house builder.

**Ground** (additive: no existing material, transition or bake hash moves; the painters are
scripts/art/kit/fills.py snow, snow_trod, moraine, ice and scripts/art/kit/edges.py snow_lip,
snow_fray, cornice_bank, ice_edge):

- `snow`: a calm plane in three tones laid by the wind in long drifts, each crest's lee a cool row;
- `snow_trod`: packed snow a tone cooler, worn patches, bootprints in staggered pairs;
- `moraine`: cold granite grit with stones of three sizes, lit caps, dark east sides, old snow;
- `ice`: the tarn frozen over, clear blue ice under wind-laid white, cracks; not walkable;
- transitions: the snow's lip over the trod (an overhang and two rows of shade under a north lip,
  a lit south lip, nothing on the sides), snow thinning over the moraine (stones breaking through
  as edge dressing), a snow cornice over a granite bank on the water and the ice, shore ice on
  open water, the ice's cut edge at the hole.

The Frostline still shows the editor's live tiles: bake.py dispatches only on the painters it
knows, and teaching it these moves every baked zone's hash (its own PR).

**Props.** Snow is modelled as solids lying on what faces the sky, so it is shaded and outlined
like any material. The Col hut at the Frostline hut scale; conifers in four silhouettes from the
woodland pine's tiered painter with snow shelves on the tiers, and a dead snag; granite boulders,
a boulder cluster, stones and headwall crags; granite cairns (standing, toppled, small); the
climbers' fire ring under snow; the sledge and the cut ice stack; the warden's yard (woodpile, skis
and shovel), a bench, a noticeboard, a snow pole and a lost hat; the cirque's 32 px granite face
with its stair and its frozen fall; a plank footbridge over the outlet.

    python3 -m scripts.art.kit.sets.frost           # paint and write the pieces
    python3 -m scripts.art.kit.sets.frost --check   # exit 1 if a picture is stale
"""
from __future__ import annotations

from ._shared import (
    ART as ART,
    B as B,
    BIOMES as BIOMES,
    C as C,
    FACE_PX as FACE_PX,
    FI as FI,
    GRANITE as GRANITE,
    GR_SIB as GR_SIB,
    Image as Image,
    K as K,
    LIP_PX as LIP_PX,
    LUT as LUT,
    OAK as OAK,
    PIECES as PIECES,
    RED as RED,
    RES as RES,
    ROOT as ROOT,
    SNOW as SNOW,
    SNOWS as SNOWS,
    SNOW_LADDER as SNOW_LADDER,
    STANDARD as STANDARD,
    V as V,
    WEATHERED as WEATHERED,
    _block as _block,
    _cap as _cap,
    _chip as _chip,
    _cracks as _cracks,
    _crust as _crust,
    _drift_west as _drift_west,
    _fractures as _fractures,
    _grain as _grain,
    _grain_after as _grain_after,
    _granite_dress as _granite_dress,
    _grow as _grow,
    _mass as _mass,
    _rock as _rock,
    _rock_r2 as _rock_r2,
    _snow_light as _snow_light,
    _snowcap as _snowcap,
    _solo as _solo,
    argparse as argparse,
    hsh as hsh,
    json as json,
    math as math,
    ndi as ndi,
    np as np,
    os as os,
    sys as sys,
    to_rgba as to_rgba,
)
from .ground import (
    ICE_FILL as ICE_FILL,
    MORAINE_FILL as MORAINE_FILL,
    SNOW_FILL as SNOW_FILL,
    STONES as STONES,
    TROD_FILL as TROD_FILL,
    _fill_into as _fill_into,
    _terrain as _terrain,
    _transition as _transition,
    paint_ice as paint_ice,
    paint_moraine as paint_moraine,
    paint_snow as paint_snow,
    paint_snow_trod as paint_snow_trod,
    terrain_pieces as terrain_pieces,
    write_terrain as write_terrain,
)
from .rock import (
    CHEEK as CHEEK,
    COURSES as COURSES,
    RISE as RISE,
    RISER_PX as RISER_PX,
    SET_BACK as SET_BACK,
    STEPS as STEPS,
    STEP_PX as STEP_PX,
    TREAD as TREAD,
    _cheek as _cheek,
    _face as _face,
    _stair_dress as _stair_dress,
    _stair_flat as _stair_flat,
    _stair_steps as _stair_steps,
    _stair_wear as _stair_wear,
    _wall_blocks as _wall_blocks,
    boulder as boulder,
    cairn as cairn,
    crag as crag,
    rock_stair as rock_stair,
    rockface as rockface,
    rockface_fall as rockface_fall,
)
from .structures_props import (
    HUT_SPEC as HUT_SPEC,
    IRON as IRON,
    ROPE as ROPE,
    _plume_frame as _plume_frame,
    bench as bench,
    col_hut as col_hut,
    fire_ring as fire_ring,
    footbridge as footbridge,
    hut_tools as hut_tools,
    lost_hat as lost_hat,
    noticeboard as noticeboard,
    sledge as sledge,
    snow_pole as snow_pole,
    woodpile as woodpile,
)
from .trees import (
    CONIFERS as CONIFERS,
    _shelves as _shelves,
    conifer as conifer,
    snag as snag,
)
from .water_ice import (
    ICE as ICE,
    _floe as _floe,
    _ice_faces as _ice_faces,
    _icefall as _icefall,
    _icicles as _icicles,
    _line as _line,
    _pic as _pic,
    ice_stack as ice_stack,
    open_fall as open_fall,
    plunge as plunge,
    pressure_ridge as pressure_ridge,
)
from .outlet import (
    inflow as inflow,
    outlet as outlet,
    thaw_band as thaw_band,
    woodland_seam as woodland_seam,
)

# ================================================================================================
# the pieces
# ================================================================================================
def _rel(rel, what, cells=None, note=None):
    return B._rel(rel, what, cells, note)



def _piece(pid, name, variants, size, cells, purpose, role, **kw):
    shadow = kw.pop('shadow', None)
    deck = kw.pop('deck', None)
    zsort = kw.pop('z_sort', None)
    pc = B._piece(pid, name, variants, size, cells, purpose, role, shadow=None, **kw)
    pc['biomes'] = list(BIOMES)
    if pid == 'frost_woodland_thaw':                 # the thaw's woodland half lies in the woodland (round 3, P2)
        pc['biomes'] = list(BIOMES) + ['woodland']
    pc['approval']['standard'] = STANDARD
    for v in pc['variants']:
        v['png'] = v['png'].replace(B.RES, RES)
    if pc['rendering'].get('animations'):
        for an in pc['rendering']['animations']:
            an['strip'] = an['strip'].replace(B.RES, RES)
    # the cast shadow (B6, Z4): an ellipse no wider than the footprint and a tenth, its west end at
    # the object's west edge and thrown a little east and down from there; nothing reaches west.
    # (size is the ellipse's radii in world px, dir its centre's offset from the foot.)
    if shadow:
        hw, ry = shadow
        rx = round(hw * 1.1, 1)
        pc['rendering']['cast_shadow'] = {'shape': 'ellipse', 'size': [rx, ry], 'dir': [round(rx - hw, 1), round(ry * 0.6, 1)]}
    else:
        pc['rendering']['cast_shadow'] = {'shape': 'none'}
    if deck:
        pc['gameplay']['deck'] = deck
    if zsort:
        pc['geometry']['z_sort'] = zsort
    pc['audit']['painter'] = {'module': 'scripts.art.kit.sets.frost', 'fn': kw.get('fn') or pid.replace('frost_', ''), 'args': {}}
    pc['audit']['seeded_from'] = 'scripts/art/kit/sets/frost.py'
    return pc



NATURE = B.NATURE

OFF_ROUTE = B.OFF_ROUTE

OFF_WATER = B.OFF_WATER

NEAR_HUT = _rel('within', 'house', 4, 'the warden\'s yard: by the Col hut it serves')



def FACE_LOOKS(base):
    """The face's looks (round 3, R2-F1): three plain runs that differ block for block, so no two
    neighbours match, and the ends for a tier's real ends only."""
    return [('plain', (False, False), base + 5), ('plain_b', (False, False), base + 17), ('plain_c', (False, False), base + 29),
            ('west', (True, False), base + 4), ('east', (False, True), base + 4), ('both', (True, True), base + 4)]



def prop_jobs():
    """(piece id, [(variant id, thunk)], piece kwargs)."""
    trees = dict(purpose='grow', role='tree', composition='cluster', forbids=NATURE, eastward='22 (the tiered pines)')
    return [
        ('frost_col_hut', [('still', lambda: col_hut())], dict(
            name='Col hut', purpose='live', role='house', cells=(10, 4), fp=B._fp(9, 3),
            collision={'shape': 'rect', 'rect': [-34.0, -26.0, 68, 26]}, shadow=(34.0, 5.0), composition='edge',
            door_cells=[[-1, 0], [0, 0]], doors=[{'x': [-30, 12], 'faces': 's'}],
            requires=[_rel('near', 'route', 3, 'on the Col Path, its door on the trod')], forbids=NATURE,
            extra={'provides': ['home', 'hearth']},
            size_class='hut (148 to 252 tall, 178 to 296 wide: size-guide Frostline "huts (eaves 40 to 44, door 32)")',
            eastward='12 (the stone hut: 2.5 A to the ridge, 3 A wide; doors 0.96 to 1.02 A)', fn='col_hut',
            note='The hut warden\'s bothy: rubble granite under slate at the Frostline hut scale (door leaf 87 art px, eaves '
                 '123), snow lying on the roof as a mass with a cornice, icicles at the corners and over the door, a drift '
                 'at the foot with the doorway dug clear; the stove\'s plume loops (8 frames) over the still.')),
        ('frost_spruce', [('still', lambda: conifer('spruce', load=1.0))], dict(
            name='Snowy spruce', cells=(3, 2), fp=B._fp(2, 1), collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]},
            size_class='conifer (a tall spruce)', fn='conifer',
            note='A tall narrow spruce from the woodland pine\'s tiered painter, snow as shelves on its tiers.', **trees)),
        ('frost_pine', [('still', lambda: conifer('pine'))], dict(
            name='Snowy pine', cells=(4, 2), fp=B._fp(2, 1), collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]},
            size_class='conifer (the woodland\'s pine, 79 world px)', fn='conifer',
            note='The woodland pine\'s painter with snow as shelves on its tiers (thick west, thinning east).', **trees)),
        ('frost_pine_squat', [('still', lambda: conifer('squat'))], dict(
            name='Wind-cropped pine', cells=(4, 2), fp=B._fp(2, 1), collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]},
            size_class='conifer (wind-cropped, three quarters of the pine)', fn='conifer',
            note='A squat pine cropped by the wind, its snow shelves on the west.', **trees)),
        ('frost_krummholz', [('still', lambda: conifer('krummholz', load=0.8)), ('low', lambda: conifer('krummholz_b', load=0.8)),
                             ('wide', lambda: conifer('krummholz_c', load=0.8))], dict(
            name='Krummholz', cells=(4, 2), fp=B._fp(3, 1), collision={'shape': 'rect', 'rect': [-9.0, -4.0, 18, 4]},
            size_class='conifer (krummholz: a wind-flattened spruce at the tree line)', fn='conifer',
            note='A pine at the tree line grown low and wide, snow on its tiers.', **trees)),
        ('frost_snag', [('still', lambda: snag())], dict(
            name='Dead pine', cells=(2, 2), fp=B._fp(1, 1), collision={'shape': 'rect', 'rect': [-3.0, -3.0, 6, 3]},
            size_class='snag (a dead spruce, its crown gone)', fn='snag',
            note='A weathered dead pine with a broken top and two stub limbs, snow on the break and the stubs.', **trees)),
        ('frost_boulder', [('a', lambda: boulder('a')), ('b', lambda: boulder('b', seed=46))], dict(
            name='Granite boulder', purpose='mark', role='rock', cells=(3, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-6.0, -5.0, 12, 5]}, shadow=(6.0, 2.0), composition='cluster',
            forbids=NATURE, size_class='boulder (a Frostline granite boulder)', eastward='13 (the boulder, 0.35 x 0.42 A)',
            fn='boulder', note='A granite boulder of two or three facetted masses, a snow cap on its top plane, a west drift.')),
        ('frost_boulder_large', [('still', lambda: boulder('large', seed=45))], dict(
            name='Granite boulder cluster', purpose='mark', role='rock', cells=(5, 3), fp=B._fp(4, 2),
            collision={'shape': 'rect', 'rect': [-12.0, -9.0, 26, 9]}, shadow=(13.0, 3.0), composition='cluster',
            forbids=NATURE, size_class='boulder (a large block with two in its lee)', eastward='13 and 17 (the rocks)',
            fn='boulder', note='A big granite block with two smaller ones in its lee, snow on each top.')),
        ('frost_stone', [('still', lambda: boulder('small'))], dict(
            name='Granite stone', purpose='mark', role='rock', cells=(2, 1), fp=B._fp(1, 1),
            collision={'shape': 'rect', 'rect': [-3.0, -3.0, 6, 3]}, shadow=(3.0, 1.0), composition='cluster',
            forbids=NATURE, size_class='rock (a stone a cell across)', eastward='13', fn='boulder',
            note='A small granite stone with a snow cap, for a cluster\'s lee.')),
        ('frost_crag', [('a', lambda: crag('a')), ('b', lambda: crag('b'))], dict(
            name='Headwall crag', purpose='exclude', role='rock', cells=(7, 3), fp=B._fp(6, 2),
            collision={'shape': 'rect', 'rect': [-24.0, -14.0, 48, 14]}, shadow=(24.0, 4.0), composition='edge',
            forbids=NATURE, size_class='crag (a granite outcrop of the headwall\'s foot, the zone\'s frame)',
            eastward='12 (the cliff\'s stones)', fn='crag',
            note='Granite blocks stacked in a jagged mass with snow on every ledge: the north frame of the cirque.')),
        ('frost_cairn', [('standing', lambda: cairn('standing')), ('toppled', lambda: cairn('toppled')),
                         ('small', lambda: cairn('small'))], dict(
            name='Granite cairn', purpose='guide', role='marker', cells=(2, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]}, shadow=(5.0, 1.5), composition='edge',
            requires=[_rel('near', 'route', 2, 'a waymark beside the Col Path')], extra={'provides': ['feature']},
            forbids=NATURE, size_class='cairn (size-guide: 12 to 28 tall, 12 to 24 wide in world px)', eastward='13 (the boulder)',
            fn='cairn', note='A granite waymark with snow on each ring: standing, toppled east, or a small marker.')),
        ('frost_fire_ring', [('still', lambda: fire_ring())], dict(
            name='Cold fire ring under snow', purpose='mark', role='story', cells=(2, 2), fp=B._fp(2, 2),
            collision={'shape': 'rect', 'rect': [-5.0, -6.0, 10, 6]}, shadow=None, blocks=False, composition='free',
            forbids=NATURE, size_class='campfire (a cold fire ring of stones about a metre across)', eastward='05 and 37 (the camp fires)',
            fn='fire_ring', note='The fallen climbers\' camp: a ring of granite under snow, soot only where scraped.')),
        ('frost_sledge', [('still', lambda: sledge())], dict(
            name="Ice-cutter's sledge", purpose='work', role='story', cells=(5, 2), fp=B._fp(4, 1),
            collision={'shape': 'rect', 'rect': [-13.0, -6.0, 26, 6]}, shadow=(13.0, 2.0), composition='edge',
            requires=[_rel('near', 'water', 4, 'drawn up on the tarn\'s shore, by the ice-cut')], forbids=NATURE,
            size_class='pile (a low sledge under its load of ice blocks: the load is what stands)', eastward='04, 17',
            fn='sledge', note='Curled runners shod with iron, three blocks of lake ice lashed on, the bow saw leaning on it.')),
        ('frost_ice_stack', [('still', lambda: ice_stack())], dict(
            name='Cut ice blocks', purpose='store', role='story', cells=(3, 2), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-10.0, -5.0, 20, 5]}, shadow=(10.0, 2.0), composition='edge',
            requires=[_rel('near', 'water', 4, 'stacked on the shore by the ice-cut')], forbids=NATURE,
            size_class='pile (18 to 52 tall)', eastward='17 (stacked stores)', fn='ice_stack',
            note='Blocks of lake ice cut at the hole, stacked in two courses on the shore.')),
        ('frost_woodpile', [('still', lambda: woodpile())], dict(
            name="Warden's woodpile", purpose='store', role='store', cells=(3, 1), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-11.0, -4.0, 22, 4]}, shadow=(11.0, 2.0), composition='edge',
            requires=[NEAR_HUT], forbids=NATURE, size_class='woodpile', eastward='17 (stacked logs)', fn='woodpile',
            note='Split logs between two stakes, cut ends south, snow on top and at the west end.')),
        ('frost_hut_tools', [('still', lambda: hut_tools())], dict(
            name='Ice saw, axe and shovel', purpose='work', role='story', cells=(2, 1), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -3.0, 10, 3]}, shadow=(5.0, 1.5), composition='edge',
            requires=[NEAR_HUT], forbids=NATURE, size_class='tall_furniture (skis, a shovel and an axe stood in a rack against the wall, 0.9 A)', eastward='17', fn='hut_tools',
            note='The warden\'s ice saw, felling axe and snow shovel leaning on a plank rack by the hut, snow on their tops.')),
        ('frost_bench', [('still', lambda: bench())], dict(
            name='Granite bench', purpose='rest', role='seat', cells=(3, 1), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-9.0, -3.0, 18, 3]}, shadow=(9.0, 1.5), composition='edge',
            requires=[_rel('near', 'route', 2, 'beside the Col Path, looking at the view')], forbids=NATURE,
            size_class='bench (37 to 68 tall, 70 to 107 wide)', eastward='12 and 38 (the bench)', fn='bench',
            note='A granite slab on two blocks, the snow brushed off half the seat.')),
        ('frost_noticeboard', [('still', lambda: noticeboard())], dict(
            name="Warden's noticeboard", purpose='guide', role='sign', cells=(3, 1), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-8.0, -2.0, 16, 2]}, shadow=(8.0, 1.5), composition='edge',
            requires=[_rel('near', 'route', 2, 'where the Col Path comes up')], forbids=NATURE,
            size_class='notice_board', eastward='04 (the noticeboards)', fn='noticeboard',
            note='Two posts, a board under a pent roof with snow on it, notices pinned.')),
        ('frost_snow_pole', [('still', lambda: snow_pole())], dict(
            name='Snow pole', purpose='guide', role='marker', cells=(1, 1), fp=B._fp(1, 1),
            collision={'shape': 'rect', 'rect': [-1.5, -1.5, 3, 2]}, shadow=(2.0, 1.0), composition='edge',
            requires=[_rel('near', 'route', 2, 'marking the Col Path where drifts cover it')], forbids=NATURE,
            size_class='pole (a snow pole marking the trod over the drifts)', eastward='04 (posts)', fn='snow_pole',
            note='A stake banded red and white to find the path under drifts.')),
        ('frost_lost_hat', [('still', lambda: lost_hat())], dict(
            name='Lost hat', purpose='mark', role='story', cells=(1, 1), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='free', forbids=NATURE,
            size_class='unsized (a dropped hat on the snow: no clothing kind in the guide)', eastward='-', fn='lost_hat',
            note='The brief\'s "lost hat": a red bobble hat half drifted over by the path.')),
        ('frost_rockface', [(v, (lambda e=e, sd=sd: rockface(6, sd, ends=e))) for v, e, sd in FACE_LOOKS(101)], dict(
            name='Granite face', purpose='exclude', role='rock', cells=(6, 5), fp=[[c, r] for c in range(-3, 3) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-24.0, -32.0, 48, 32]}, shadow=None, composition='edge', forbids=NATURE,
            size_class='unsized (a 32 world px face, one Frostline tier: size guide "faces 32 in rock with snow lips")',
            eastward='12 (the cliff faces)', fn='rockface',
            note='A south granite face 32 world px high (Eastward 12\'s block cliff): stratified granite blocks with lit '
                 'tops, shaded undersides, dark joints, snow on the ledges, a snow lip over the top and a stony foot; three '
                 'plain looks that tile into one face, and ends (west, east, both) for a tier\'s real ends.')),
        ('frost_rockface_short', [(v, (lambda e=e, sd=sd: rockface(4, sd, ends=e))) for v, e, sd in FACE_LOOKS(211)], dict(
            name='Granite face, short', purpose='exclude', role='rock', cells=(4, 5),
            fp=[[c, r] for c in range(-2, 2) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-16.0, -32.0, 32, 32]}, shadow=None, composition='edge', forbids=NATURE,
            size_class='unsized (a 32 world px face)', eastward='12', fn='rockface', note='A four-cell length of the face.')),
        ('frost_icefall', [('still', lambda: open_fall())], dict(
            name='Thawing fall', purpose='exclude', role='rock', cells=(4, 5), fp=[[c, r] for c in range(-2, 2) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-16.0, -32.0, 32, 32]}, shadow=None, composition='edge',
            size_class='unsized (the outlet falling over the face, 32 world px)', eastward='- (the house fall, eastward-edges 5.3b)',
            fn='open_fall',
            note='The tarn\'s outlet open and thawing (Matt, 23 Nov) where it falls over the cirque\'s step: the house\'s '
                 'sheet as wide as the channel at the lip, widening 5 to 6 texels by its foot with each edge wobbling at its '
                 'own period, in the outlet\'s winter water a step lighter, its 8-frame loop; wet granite either side '
                 'following its edges, a glaze in short runs, and a fringe of short icicles from the lip beside it.')),
        ('frost_rock_stair', [('still', lambda: rock_stair())], dict(
            name='Granite stair', purpose='climb', role='rock_steps', cells=(5, 5), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground',
            size_class='unsized (rough steps cut up the granite face: no stair kind in the guide; 40 world px wide, at least 34)', eastward='12 (the stairs)', fn='rock_stair',
            note='Six steps of laid granite up the face, lit noses over shaded risers, snow in the tread corners, the '
                 'trod worn into the middle, cheeks of the face either side: the Col Path\'s way up the cirque\'s step.')),
        ('frost_outlet', [('still', lambda: outlet())], dict(
            name='Open outlet', purpose='mark', role='water', cells=(16, 36), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground',
            size_class='unsized (the outlet\'s water surface: ground dressing over the zone\'s water cells)',
            eastward='- (eastward-edges 5.3, 5.3a, 5.3c)', fn='outlet',
            note='The tarn\'s outlet open and thawing (Matt, 23 Nov), painted from the zone\'s plan over its water cells: '
                 'calm winter water (water_winter) with a darker thalweg, a dark band stepping back under the north banks, '
                 'the snow\'s broken reflection under the south banks, paired lit streaks along the flow lanes; soft-grid '
                 'banks that wander off the cells on every reach, a face only on north banks and a rim on every other '
                 'shore; the tarn\'s one lead fanning into a ragged mouth; the pool climbing in value into the fall\'s '
                 'tongue; shelf ice and floes near the tarn; the ice-cutter\'s hole in the same water; the climb to the '
                 'brook\'s own colours in tongues along the flow below the bridge. Its foot is the top of its box (it lies under every '
                 'other ground piece); regenerate after changing the zone\'s water cells.')),
        ('frost_inflow', [('still', lambda: inflow())], dict(
            name='Frozen rill', purpose='mark', role='water', cells=(3, 5), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground',
            size_class='unsized (the frozen inflow: ground dressing on the ice)', eastward='-', fn='inflow',
            note='The rill into the tarn frozen over, its banks wandering and its jog a bend: one body tone, clear dark ice '
                 'in short lenses down its middle, wandering cracks, snow banked over both banks, running in under a '
                 'drift\'s scalloped lip at the frame\'s top.')),
        ('frost_plunge', [('still', lambda: plunge())], dict(
            name='Plunge under the thawing fall', purpose='mark', role='water', cells=(5, 2), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground',
            size_class='unsized (foam where the fall lands: ground dressing on the water)', eastward='- (the house plunge, 5.3b)',
            note='The house\'s foam churning where the open fall lands (8 frames, held still under reduced motion), in the '
                 'outlet\'s winter blues, and two floes with their wet contact.')),
        ('frost_thaw', [('band', lambda: thaw_band())], dict(
            name='Thaw at the woodland seam', purpose='mark', role='ground', cells=(47, 5), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='edge', z_sort='ground',
            size_class='unsized (wet snow and bare ground: ground dressing)', eastward='-', fn='thaw_band',
            note='The short thaw band at the woodland\'s north seam (Matt, 23 Nov) across the zone\'s width, its top edge '
                 'wandering: a calm wet crust, bare hollows lit from the upper left growing and merging toward the seam, '
                 'earth in clusters with combed flattened grass, meandering rivulets to the water, a trodden slush lane '
                 'on the Col Path to the door, the snow pulled back round the trees\' feet.')),
        ('frost_woodland_thaw', [('band', lambda: woodland_seam())], dict(
            name='Thaw at the Frostline door (woodland side)', purpose='mark', role='ground', cells=(26, 9), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='edge', z_sort='ground',
            size_class='unsized (old snow, wet scree and flattened grass over the woodland\'s baked ground: dressing)',
            eastward='-', fn='woodland_seam',
            note='The woodland\'s half of the thaw at the Frostline door (round 1 audits of #535), drawn over the '
                 'woodland\'s own ground.png: old snow in the scree\'s lee and along the north edge with no halo, meltwater '
                 'channels to the brook\'s rim, flattened brown grass on the lawn\'s first row. Its foot is its top-left '
                 'corner, the woodland\'s origin, where woodland_base.tscn places it (Claude A, round 2). It is registered '
                 'to ground.png: regenerate it if that picture changes (draft #421).')),
        ('frost_pressure_ridge', [(v, (lambda v=v: pressure_ridge(v))) for v in ('long', 'short', 'side')], dict(
            name='Pressure ridge', purpose='mark', role='water', cells=(3, 1), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='edge', z_sort='ground',
            size_class='unsized (heaved plates of lake ice along the tarn\'s shore: ground dressing on the ice)', eastward='-',
            note='Where the tarn\'s ice pushed against its shore: plates of every size tilted every way along a bending line, '
                 'piled at its kink, lit tops, broken blue fronts, snow banked on the west, a short shade east on the ice.')),
        ('frost_footbridge', [('still', lambda: footbridge())], dict(
            name='Plank footbridge over the outlet', purpose='cross', role='bridge', cells=(5, 2), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground', deck=[-20.0, -16.0, 40.0, 16.0],
            requires=[_rel('on', 'water', None, 'spans the tarn\'s outlet, three cells wide, west to east')],
            size_class='unsized (a plank footbridge five cells long)', eastward='12 (the plank bridge)', fn='footbridge',
            note='Planks across the way, snow in their joints and on the log rails, granite abutments.')),
    ]



def build(write=True, force=False, only=None):
    out = {}
    pieces = []
    for pid, vs, kw in prop_jobs():
        if only and pid not in only:
            continue
        pics = []
        for vid, thunk in vs:
            r = thunk()
            frames = None
            if isinstance(r, tuple):
                r, frames = r
            png = '%s_%s.png' % (pid, vid) if len(vs) > 1 or vid != 'still' else pid + '.png'
            pics.append((vid, r, frames, png))
            out[os.path.join(ART, png)] = to_rgba(r.a)
            if frames:
                out[os.path.join(ART, png[:-4] + '_loop.png')] = to_rgba(K.strip(frames['frames']))
        kw = dict(kw)
        name, purpose, role = kw.pop('name'), kw.pop('purpose'), kw.pop('role')
        cells, fp = kw.pop('cells'), kw.pop('fp')
        variants = []
        for vid, r, frames, png in pics:
            variants.append((vid, 1.0 if not variants else 0.6, png, (r.ax, r.ay)))
            if frames:
                f0 = frames['frames'][0]
                kw['anim'] = {'clip': frames['clip'], 'loop': True, 'frames': len(frames['frames']), 'fps': frames['fps'],
                              'strip': RES + png[:-4] + '_loop.png', 'frame_px': [f0.W, f0.H], 'reduced_motion': 'hold:0',
                              'on_screen_only': True, 'region_px': list(frames['region'])}
        size = (max(r.W for _v, r, _f, _p in pics), max(r.H for _v, r, _f, _p in pics))
        pieces.append(_piece(pid, name, variants, size, cells, purpose, role, fp=fp, **kw))
    if write:
        os.makedirs(ART, exist_ok=True)
        for p in os.listdir(ART):
            if p.endswith('.png') and os.path.join(ART, p) not in out:
                os.remove(os.path.join(ART, p))
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
        for pc in pieces:
            path = os.path.join(PIECES, 'prop', pc['id'] + '.json')
            if force or not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump(pc, f, indent=1)
                    f.write('\n')
    return out



def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    if bad:
        print('frost: stale pictures %s (run python3 -m scripts.art.kit.sets.frost)' % ', '.join(bad[:6]))
        return 1
    print('frost: pictures current')
    return 0



AUDIT = {pid: (kw['purpose'], kw['role'], None, None, 'fine', 'Frostline set (scripts/art/kit/sets/frost.py): ' + kw['note'])
         for pid, _vs, kw in prop_jobs()}



def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    n = write_terrain(force=a.force)
    print('frost: %d pictures, %d ground pieces written' % (len(build(force=a.force)), n))
    return 0
