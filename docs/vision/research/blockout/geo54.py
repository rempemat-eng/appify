"""World plan v5.3's block-out, v54: the continent overview map, second pass (Matt, 27 Oct 18:23), on top of geo53.py.

"continue to make further improvements, especially the mountains to the north and the sandy desert. make the biomes a
tiny touch more visually separated where it makes sense (not a huge amount but a bit here and there to better
differentiate the biomes)".

v54 keeps v53's geography and every place (README.md, "v54"). The ground model (tiers, routes, kinds, ways) is v53's, so
blockout, stats and gates repeat v53's numbers; each gains a `v54` block with what the map adds: the northern range (its
snowline, named peaks, passes and glaciers), the desert's wind, dunes, mesas and buttes, salt flats and dry beds, the
biome edges, the label hierarchy and the home valley inset. Everything in the `v54` block that is not already ground in
the block-out is a proposal for the owning lane (D: the desert; F: the massif's edge; G: the edges).

Run from this folder:  python3 -I geo54.py              (data and every map, about seven minutes)
                       RENDER_ONLY=1 python3 -I geo54.py (the maps again from out/state-v54.pkl, a few minutes)
It writes blockout-v54.json, stats-v54.json and gates-v54.json next to itself (committed) and the renders to out/ (or
$BLOCKOUT_OUT); MAP54_OUT, if set, also receives the maps. Needs geo53.py, geo52.py and geo5.py beside it."""
import json, os, pickle, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo53 as V
from geo53 import CIRCLE, CROSSROADS, CRATERS, NEW_ROUTES, POI53, WAYSTONES, BUILT, ACT1, hero_speed

DATA, HERE, ROOT = V.DATA, V.HERE, V.ROOT
SUF = '-v54'

# ------------------------------------------------------------------------------------------ v54 tables
# The northern range. SNOWLINE is in the height field's units (geo52's snowline runs 0.79 to 0.93 by aspect; the map
# draws one clear line). The range's peaks are drawn from the height field; the highest in each stretch is named.
SNOWLINE = 0.90
PEAK_NAMES = [  # (west edge of the stretch in world px, name): the highest peak in each stretch takes the name
    (1900, 'Whitepike'), (3300, 'the Greyhorn'), (4700, 'Rime Fell'), (7000, 'the Anvil'), (9200, 'Old Cairn')]
# Passes: where a route crosses the range or a ridge, drawn as a notch (no peak within NOTCH_PX, the crest dipping toward it)
PASSES = {'the ridge col': (6210, 1890, 'Col Path', 'W2', "the Frostline's lip: the valley's way up to the tarn (W2)"),
          'the Fells saddle': (6587, 1611, 'High Fells', '', 'the High Fells path over the shoulder east of the tarn'),
          'the Lode notch': (3040, 1700, 'Lode Track', 'W5', "the mule track's top, at the mine mouth")}
NOTCH_PX = 110
# Named glaciers (their tongues are the block-out's glacier cells; the name sits on the largest body near the point)
GLACIERS = {'the Rime glacier': (6150, 1250, "above the tarn: the ice caves are under its snout (act 1, the Rime Wyrm)"),
            'the West ice': (2300, 380, 'the massif\'s western ice field, past the walk')}
# The desert. One wind: a dry north-north-westerly off the massif. Dune crests run across it, lee (slip) faces to the
# south-south-east (shaded, as every south face on the map); the dune sea's dunes are tall, the sand sheet's low.
WIND_FROM_DEG = 340
DUNES = {'erg': {'wavelength_px': 150, 'relief': 1.0, 'note': 'the dune sea: tall transverse dunes'},
         'desert': {'wavelength_px': 70, 'relief': 0.35, 'note': 'the sand sheet and interdune flats: low ripples'}}
# Buttes (small mesas) proposed for lane D on open desert and scrub, clear of routes; the block-out's mesas are kept.
BUTTES = {'the Chimney': (3120, 3330, 46), 'the Anvil butte': (2470, 2230, 52), 'Table Rock': (3690, 3020, 60),
          'the Sentinels': (1880, 3170, 40), 'the Ember butte': (3960, 4180, 44)}
# Salt flats: the salt lake (block-out) and two small pans on the dune sea's interdune flats (proposed)
SALT_FLATS = {'the bitter pans': (720, 3360, 150, 90), 'the white pan': (1180, 4480, 120, 72)}
# Dry riverbeds (washes) leading to the oasis at Palm Spring, where the Willow Run comes up again (proposed; the
# block-out's Dry Fork and Brackens wash are drawn the same way)
DRY_BEDS = {'the Thirst wash': [(2940, 3520), (3060, 3330), (3190, 3140), (3300, 2990), (3400, 2880)],
            'the Long wash': [(3640, 3470), (3610, 3260), (3560, 3080), (3520, 2930)]}
# Biome edges the map sharpens a little (drawing only)
EDGES = {'forest': 'a darker rim on every forest edge (trees and ground)',
         'moor': "the Brackens' heath a touch more heather-coloured, with a thin darker edge against the valley",
         'ash': "the fire country's ash: a dark rim and a fall-off of ash flecks onto the ground beside it",
         'fens': 'the moss fens drawn with a marsh pattern (water lines and tufts)',
         'floodplain': "the Lull's watermeadows cooler, with a dotted flood line at their edge",
         'sand to steppe': 'the dune sea, sand sheet, scrub and steppe blended over about 100 px (no hard edge)'}
# The label hierarchy: tier 1 always, tier 2 where it fits, tier 3 only where space allows (and on the main map not
# inside the inset's box, where the inset names them)
LABEL_TIERS = {1: 'region names, towns and villages, the stone circle', 2: 'great craters, biome names, named peaks, gates with a way',
               3: 'small places, other gates, passes, water and route names'}
INSET = (4800, 1400, 8100, 4400)       # the home valley inset's box (world px): the valley, the Frostline, the Brackens' east


def v54_block(F):
    """The v54 block for the JSON (F: map54.features)."""
    return {'snowline_h': SNOWLINE, 'named_peaks': F['named_peaks'], 'passes': F['passes'], 'notch_px': NOTCH_PX,
            'glaciers': F['glaciers'], 'range': F['range'], 'wind_from_deg': WIND_FROM_DEG, 'dunes': DUNES,
            'buttes': F['buttes'], 'salt_flats': F['salt_flats'], 'dry_beds': {nm: [list(p) for p in pts] for nm, pts in DRY_BEDS.items()},
            'edges': EDGES, 'label_tiers': LABEL_TIERS, 'inset': list(INSET),
            'note': "drawing additions and proposals on v53's ground; tiers, routes, kinds and ways are v53's"}


def data_stage():
    V.SUF = SUF
    S = V.data_stage()                         # writes blockout/stats/gates -v54 (v53's ground) and out/state-v53.pkl
    import map54
    F = map54.features(S, sys.modules[__name__])
    blk = v54_block(F)
    st = json.load(open(os.path.join(DATA, f'stats{SUF}.json')))
    st['v54'] = blk
    json.dump(st, open(os.path.join(DATA, f'stats{SUF}.json'), 'w'), indent=1)
    bj = json.load(open(os.path.join(DATA, f'blockout{SUF}.json')))
    bj['version'] = 'v5.3 block-out, v54 (world plan v5.3; the overview map of 27 Oct, second pass)'
    bj['v54'] = blk
    with open(os.path.join(DATA, f'blockout{SUF}.json'), 'w') as f:
        json.dump(bj, f, separators=(',', ':'))
    shutil.copy(os.path.join(HERE, 'state-v53.pkl'), os.path.join(HERE, 'state-v54.pkl'))
    return S


if __name__ == '__main__':
    if os.environ.get('RENDER_ONLY'):
        S = pickle.load(open(os.path.join(HERE, 'state-v54.pkl'), 'rb'))
    else:
        S = data_stage()
    if os.environ.get('QUICK') != 'data':
        import map54
        map54.render_all(S, sys.modules[__name__])
