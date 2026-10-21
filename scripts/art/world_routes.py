"""The routes between the regions, as data on the world canvas (lane G).

Matt, 20 Oct 12:36: "more empty parts of the maps should first be planned out along
natural footpaths or other sorts of paths and the terrain should be build around it".
World plan v5.3 (docs/vision/world-plan.md, section 6) lays the routes first and fits the
ground to each; the brief is docs/vision/regions/routes-thresholds-edges.md. The region
lanes build up to these lines, so they come before any ground is painted.

This file is the source of every road, path, bar, bridge and causeway between the
regions, in world px on the v5.3 canvas (11264 x 6912 px, 8 px cells, one tier a 32 px
south face). For each route it fixes:

  - the line: a centre line on the 8 px grid, one vertex every 32 px or less;
  - the width at each vertex (24 to 64 px: wider at bends, junction squares and
    thresholds);
  - the tier at each vertex, and every place the route changes tier: a stair (cut through
    the face, 34 px or more open, about 36 px of route per tier), a ramp (along the face
    at 1 in 3, 96 px per tier) or a switchback (a short Z, 64 px per tier);
  - the crossings: fords, bridges, ferries, causeways, the bar and the stile, with the
    way (W1 to W9) that stands on each;
  - the thresholds (the fifteen places where one region becomes another);
  - the side paths round obstacles and the dead-end paths to secret pockets;
  - the meeting cells: where each route passes from one owner's land into another's.

Where the lines come from. The block-out (Claude A's geo52.py and stats-v52.json) is not
in the repository. The briefs place every route's markers (ten a screen, either side of
the path), its thresholds and its ends; ANCHORS below is the centre line fitted through
them (an elastic line through the markers' medians, outliers dropped, simplified to
within 10 px). Walk lengths match the briefs' times at 40 px/s within 10 % for 16 of the
20 routes (`blockout` keeps the brief's numbers beside ours). The build then smooths each
line, lays the plan's irregular bends on it (a short bend of 160 to 240 px riding a long
swing of 450 to 750 px, never a regular S, plan 5.6), straightens it over bridges and
fords, and snaps it to the grid.

Tiers. The block-out's height field stepped the plain and the hills into many low tiers
(the High Fells 35 changes in 1960 px, more than ramps or stairs can fit), and the plan
asks for fewer, deliberate banks (section 5.4). TIERS below gives each route a profile
that fits: every change has room for its stair, ramp or switchback, routes beside water
only fall downstream, and the ends meet the tiers given in STOPS. The region lanes match
their ground to the tier at each meeting cell; a lane that needs another tier there says
so on the crew board and this file changes.

Who draws what. Inside a region's footprint the region lane paints the route's surface to
this line, width and tier, with its own kits. Between the footprints, the land and the
route are lane G's, and the threshold objects are lane G's everywhere.

Run: python3 scripts/art/world_routes.py (writes lib/world-routes.ts and
docs/vision/regions/route-meets.md; ROUTES_PREVIEW=<file.png> also draws the routes over
the footprints). The check is lib/world-routes.test.ts (npm run check:world-routes).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import worlds  # noqa: E402

CANVAS = (11264, 6912)
GRID = 8
TIER_PX = 32
WALK_PX_S = 40            # walking speed on the block-out (plan 6.1)
STEP = 8                  # resampling step along a line, px
VERTEX_EVERY = 32         # at most this much route between exported vertices
RUN = {'stair': 36, 'ramp': 96, 'switchback': 64}   # route px each tier change takes
WIDTH_MIN, WIDTH_MAX = 24, 64
MEET_MARGIN = 0           # a footprint's box edge is the owners' line

# The footprints (regions/README.md), by owner. Lanes F, H and I took parts of E's and
# C's regions on 21 Oct (crew board: to-all-1005, to-c-handover). Where boxes overlap, the
# first owner listed holds the cell. Land in no box is lane G's: the land between.
FOOTPRINTS = [
    ('claude-e', 'the home valley', (5600, 2300, 7000, 5100)),
    ('claude-e', 'the Headland', (6800, 5100, 7250, 5800)),
    ('claude-f', 'the Frostline', (5700, 1300, 6800, 2300)),
    ('claude-f', 'the Brackens', (4800, 1300, 5600, 4000)),
    ('claude-h', 'Cogsworth and the coal hills', (7000, 1700, 9300, 3300)),
    ('claude-i', 'the Lull belt', (8700, 3300, 9450, 5900)),
    ('claude-i', 'Neon Harbour', (9450, 3900, 11264, 5900)),
    ('claude-i', 'Lullford', (8300, 3950, 8700, 4650)),
    ('claude-i', 'Gullwick', (7650, 4850, 8300, 5450)),
    ('claude-d', 'the Sunstone basin', (0, 0, 4800, 4300)),
    ('claude-d', 'the fire country', (0, 4000, 5600, 5850)),
    ('claude-c', 'the Tidebloom Isles', (3700, 5800, 9800, 6912)),
]
BETWEEN = 'claude-g'

# Places the routes start and end at (region briefs, section 2), with the tier the
# route meets there. `tier` is the route's tier at its end in that place.
STOPS = {
    'valley-halt': ('the valley halt', (5850, 4050)),
    'valley-east': ('the valley, east lane', (6760, 3760)),
    'valley-fern': ('the valley, Fern hills lane', (6760, 3400)),
    'valley-col': ('the valley, Col Path foot', (6280, 2960)),
    'driftwood': ('Driftwood', (6420, 4960)),
    'headland-neck': ("the Headland's neck, east of Driftwood", (6900, 5110)),
    'headland-tip': ('the Headland tip', (7060, 5630)),
    'lagoon-landing': ('Lagoon Landing', (6560, 6200)),
    'frostline': ('the Frostline', (6220, 1800)),
    'fernhollow': ('Fernhollow', (7150, 3080)),
    'cogsworth': ('Cogsworth', (7980, 2450)),
    'lullford': ('Lullford', (8700, 4300)),
    'gullwick': ('Gullwick', (7950, 5130)),
    'lull-east-bank': ('Lullford Bridge, east bank', (9150, 4320)),
    'neon-market': ('Neon Harbour, the market', (9980, 4360)),
    'neon-docks': ('Neon Harbour, the docks', (10336, 4400)),
    'neon-heights': ('Neon Harbour, the Heights', (9800, 4985)),
    'neon-quay': ('Neon Harbour, the quay at the bridge', (10440, 4990)),
    'gull-strand': ('the Gull Strand', (10448, 5320)),
    'beacon-isle': ('Beacon Isle', (10096, 5440)),
    'skyport': ('the Skyport', (10600, 4950)),
    'launch-cape': ('the Launch Cape', (10980, 5560)),
    'palm-spring': ('Palm Spring', (3480, 2800)),
    'dust-gulch': ('Dust Gulch', (2760, 2420)),
    'the-lode': ('the Lode', (3060, 1650)),
    'hearthold': ('Hearthold', (2480, 5120)),
    'ember-forge': ('the Ember forge', (2460, 4860)),
    'cinderwick': ('Cinderwick', (2760, 5640)),
}
HOME = 'valley-halt'   # the hut's valley: everything joined to it at the start

# Stops inside one settlement are joined by its own streets and lanes (the region lane's
# ground), with no way between them: the gate check treats each group as one place.
SAME_PLACE = [
    ('valley-halt', 'valley-east', 'valley-fern', 'valley-col', 'driftwood', 'headland-neck'),
    ('neon-market', 'neon-docks', 'neon-heights', 'neon-quay', 'gull-strand', 'skyport'),
]

# Journeys beside the routes (plan 6.2): they open with the way of the route they run
# beside, and are links in the gate check, not walked lines.
LINKS = [
    ('the ferry', 'driftwood', 'lagoon-landing', 'W4'),
    ('the desert line', 'valley-halt', 'dust-gulch', 'W5'),
    ('the maglev', 'cogsworth', 'neon-market', 'W7'),
    ('the valley train', 'valley-halt', 'cogsworth', 'W3'),
]

# The centre lines, fitted to the briefs' markers (see the module note), in world px.
ANCHORS = {
    'col-path': [(6280, 2960), (6256, 2720), (6272, 2560), (6272, 2360), (6224, 2320), (6240, 2128), (6224, 1992), (6208, 1944), (6208, 1888)],
    'high-fells': [(6304, 1760), (6504, 1648), (6648, 1632), (6696, 1648), (6752, 1640), (6808, 1656), (6960, 1624), (7104, 1648), (7120, 1616), (7192, 1648), (7248, 1712), (7376, 1768), (7456, 1856), (7568, 1920), (7760, 2152), (7848, 2336), (7896, 2352), (7920, 2392)],
    'foothill-road': [(6760, 3400), (6944, 3216), (7216, 3128), (7336, 3024), (7392, 3008), (7504, 2928), (7728, 2632), (7776, 2616), (7792, 2568), (7848, 2504), (7904, 2480)],
    'towpath': [(8040, 2560), (8128, 2624), (8184, 2688), (8216, 2728), (8224, 2824), (8264, 2904), (8472, 3008), (8504, 3064), (8496, 3136), (8472, 3184), (8480, 3512), (8448, 3616), (8464, 3760), (8480, 3800), (8472, 3944), (8512, 4088), (8568, 4168), (8648, 4224)],
    'lull-road': [(6760, 3760), (6896, 3800), (6976, 3856), (7080, 3848), (7168, 3896), (7448, 3896), (7488, 3920), (7768, 3928), (7928, 4008), (7976, 4008), (8112, 4048), (8328, 4168), (8376, 4168), (8456, 4208), (8496, 4208), (8536, 4240), (8624, 4280), (8872, 4272), (8912, 4304), (9096, 4336), (9232, 4336), (9264, 4360), (9352, 4376), (9400, 4400), (9552, 4360), (9656, 4368), (9704, 4384), (9840, 4360), (9872, 4392), (9984, 4360)],
    'coast-path': [(6656, 4928), (6704, 4984), (6808, 5056), (6920, 5080), (7136, 5072), (7296, 5016), (7576, 5056), (7760, 5048), (7856, 5080), (7912, 5072), (8088, 4944), (8232, 4784), (8240, 4736), (8312, 4624), (8392, 4560), (8472, 4536), (8544, 4464), (8640, 4328)],
    'headland-lane': [(6896, 5112), (6976, 5240), (7032, 5520), (7064, 5568), (7056, 5616)],
    'shell-bar': [(7056, 5640), (6984, 5776), (6848, 5936), (6792, 6024), (6736, 6048), (6704, 6080)],
    'drovers-road': [(5800, 4064), (5728, 4000), (5456, 3936), (5424, 3896), (5272, 3800), (4968, 3576), (4824, 3560), (4656, 3496), (4400, 3504), (4320, 3448), (4272, 3432), (4192, 3392), (4144, 3328), (4104, 3320), (3944, 3104), (3896, 3088), (3832, 3032), (3792, 3024), (3688, 2928), (3520, 2872), (3392, 2808), (3288, 2712), (3240, 2704), (3176, 2656), (3128, 2640), (3032, 2536), (2904, 2472), (2864, 2472)],
    'lode-track': [(2832, 2328), (2864, 2248), (2856, 2136), (2896, 2112), (2912, 2000), (2944, 1968), (3040, 1696)],
    'canyon-road': [(2800, 2560), (2800, 2608), (2784, 2648), (2800, 2824), (2760, 2936), (2728, 2968), (2688, 3088), (2696, 3136), (2616, 3256), (2576, 3296), (2544, 3368), (2560, 3448), (2552, 3488), (2424, 3664), (2400, 3744), (2288, 3864), (2264, 3928), (2208, 3976), (2152, 4000), (2048, 4232), (1952, 4368), (1952, 4472), (1992, 4648), (2056, 4816), (2296, 5024), (2440, 5080)],
    'forge-stair': [(2472, 5040), (2464, 4896)],
    'ember-way': [(2472, 5120), (2304, 5264), (2264, 5320), (2232, 5376), (2256, 5480), (2320, 5528), (2392, 5560), (2456, 5560), (2632, 5616), (2704, 5616)],
    'ash-coast': [(5800, 4152), (5720, 4192), (5592, 4360), (5576, 4416), (5496, 4488), (5424, 4512), (5376, 4576), (5208, 4696), (5160, 4704), (5056, 4744), (4952, 4872), (4864, 4928), (4816, 4944), (4768, 4992), (4704, 5016), (4672, 5072), (4560, 5152), (4488, 5176), (4208, 5208), (4168, 5224), (4016, 5216), (3952, 5264), (3728, 5352), (3712, 5392), (3584, 5440), (3568, 5472), (3456, 5536), (3000, 5624), (2864, 5624), (2784, 5648)],
    'delta-road': [(9152, 4320), (9184, 4344), (9192, 4400), (9256, 4432), (9280, 4488), (9352, 4504), (9360, 4560), (9416, 4616), (9416, 4648), (9472, 4696), (9496, 4752), (9544, 4768), (9584, 4824), (9648, 4840), (9656, 4896), (9728, 4912), (9768, 4936), (9800, 4984)],
    'harbour-bridge': [(9800, 4984), (10440, 4992)],
    'old-bridges': [(9984, 4360), (10336, 4392)],
    'quay-street': [(10336, 4400), (10376, 4720), (10440, 4992), (10448, 5320)],
    'beacon-causeway': [(10448, 5320), (10096, 5440)],
    'cape-road': [(10600, 4952), (10656, 5024), (10784, 5120), (10816, 5200), (10848, 5240), (10864, 5296), (10952, 5432), (10976, 5520)],
}

# id: name, kind, from, to, base width, (brief walk s, brief tier changes), bends.
# bends: (long swing amplitude, short bend amplitude) in px; 0 for built straight things.
ROUTES = [
    ('col-path', 'Col Path', 'path', 'valley-col', 'frostline', 24, (28, 7), (14, 6)),
    ('high-fells', 'High Fells', 'path', 'frostline', 'cogsworth', 24, (49, 35), (18, 7)),
    ('foothill-road', 'Foothill Road', 'road', 'valley-fern', 'cogsworth', 40, (38, 17), (22, 7)),
    ('towpath', 'Towpath', 'path', 'cogsworth', 'lullford', 32, (48, 9), (14, 6)),
    ('lull-road', 'Lull Road', 'road', 'valley-east', 'neon-market', 40, (87, 13), (24, 8)),
    ('coast-path', 'Coast Path', 'path', 'driftwood', 'lullford', 32, (56, 1), (18, 7)),
    ('headland-lane', 'Headland Lane', 'path', 'headland-neck', 'headland-tip', 32, (14, 0), (10, 6)),
    ('shell-bar', 'Shell Bar', 'bar', 'headland-tip', 'lagoon-landing', 48, (15, 0), (20, 8)),
    ('drovers-road', "Drover's Road", 'road', 'valley-halt', 'dust-gulch', 40, (90, 22), (24, 8)),
    ('lode-track', 'Lode Track', 'path', 'dust-gulch', 'the-lode', 24, (18, 2), (12, 6)),
    ('canyon-road', 'Canyon Road', 'path', 'dust-gulch', 'hearthold', 32, (75, 28), (18, 7)),
    ('forge-stair', 'Forge Stair', 'path', 'hearthold', 'ember-forge', 32, (4, 3), (0, 0)),
    ('ember-way', 'Ember Way', 'path', 'hearthold', 'cinderwick', 32, (18, 9), (12, 6)),
    ('ash-coast', 'Ash Coast', 'path', 'valley-halt', 'cinderwick', 32, (91, 7), (22, 8)),
    ('delta-road', 'Delta Road', 'path', 'lull-east-bank', 'neon-heights', 32, (56, 11), (12, 6)),
    ('harbour-bridge', 'Harbour Bridge', 'bridge', 'neon-heights', 'neon-quay', 40, (None, 3), (0, 0)),
    ('old-bridges', 'Old Bridges', 'road', 'neon-market', 'neon-docks', 40, (9, 0), (0, 0)),
    ('quay-street', 'Quay Street', 'road', 'neon-docks', 'gull-strand', 40, (24, 6), (14, 6)),
    ('beacon-causeway', 'Beacon Causeway', 'causeway', 'gull-strand', 'beacon-isle', 32, (None, 0), (0, 0)),
    ('cape-road', 'Cape Road', 'road', 'skyport', 'launch-cape', 40, (18, 3), (12, 6)),
]

# Each route's tier profile: (tier at its start, [legs]); a leg is (from fraction, to
# fraction, kind or kinds, tiers after each change), its changes spread evenly in it.
TIERS = {
    'col-path': (7, [(0.10, 0.96, 'switchback', [8, 9, 10, 11, 12, 13, 14])]),
    'high-fells': (14, [(0.14, 0.42, 'ramp', [15, 16]), (0.42, 0.50, 'stair', [17, 18]),
                        (0.52, 0.82, 'stair', [17, 16, 15, 14, 13, 12, 11]),
                        (0.83, 0.98, 'stair', [10, 9, 8, 7])]),
    'foothill-road': (5, [(0.08, 0.52, 'ramp', [6, 7, 8, 9]), (0.70, 0.98, 'ramp', [8, 7])]),
    'towpath': (7, [(0.04, 0.20, 'stair', [6, 5]), (0.30, 0.80, 'ramp', [4, 3])]),
    'lull-road': (4, [(0.04, 0.20, 'ramp', [5, 6]), (0.30, 0.58, 'ramp', [5, 4, 3])]),
    'coast-path': (3, [(0.20, 0.30, 'ramp', [2])]),
    'headland-lane': (3, []),
    'shell-bar': (0, []),
    'drovers-road': (4, [(0.02, 0.16, 'ramp', [5, 6]), (0.24, 0.34, 'ramp', [5]),
                         (0.58, 0.96, 'ramp', [6, 7, 8])]),
    'lode-track': (8, [(0.15, 0.92, 'switchback', [9, 10])]),
    'canyon-road': (8, [(0.03, 0.12, 'stair', [7, 6, 5]), (0.20, 0.30, 'ramp', [6]),
                        (0.40, 0.84, 'ramp', [7, 8, 9, 10, 11]), (0.92, 0.99, 'stair', [12])]),
    'forge-stair': (12, [(0.05, 0.95, 'stair', [13, 14, 15])]),
    'ember-way': (11, [(0.03, 0.97, 'stair', [10, 9, 8, 7, 6, 5, 4, 3, 2])]),
    'ash-coast': (4, [(0.02, 0.12, 'ramp', [3]), (0.38, 0.46, 'ramp', [2]), (0.54, 0.62, 'ramp', [3])]),
    'delta-road': (3, [(0.25, 0.95, 'ramp', [4, 5, 6])]),
    'harbour-bridge': (6, [(0.80, 1.00, 'stair', [5, 4, 3])]),
    'old-bridges': (3, []),
    'quay-street': (3, [(0.55, 0.95, 'ramp', [2, 1])]),
    'beacon-causeway': (1, []),
    'cape-road': (3, [(0.40, 0.70, 'ramp', [4])]),
}

# Crossings on the routes: route, kind, name, at (brief), span (px of route), way.
# A ford is walked through shallows, a bridge over its deck; a ferry's span is water the
# walk does not cross (the boat does); a causeway is walked; the bar is walked at low tide.
CROSSINGS = [
    ('headland-lane', 'stile', 'the Headland stile', (6990, 5300), 32, 'W1'),
    ('col-path', 'step', 'the Frostline lip', (6230, 2040), 48, 'W2'),
    ('high-fells', 'step', 'the east col', (6560, 1640), 48, 'W2'),
    ('foothill-road', 'bridge', 'the Millrace bridge', (7650, 2740), 64, 'W3'),
    ('towpath', 'bridge', 'the Cog foot bridge', (8530, 3060), 64, 'W3'),
    ('high-fells', 'step', 'the rockfall above the Cog', (7800, 2240), 48, 'W3'),
    ('shell-bar', 'bar', 'the Shell Bar', (6900, 5900), 160, 'W4'),
    ('drovers-road', 'bridge', "Drover's bridge", (4330, 3440), 128, 'W5'),
    ('ash-coast', 'ferry', 'the Rift ferry', (4180, 5240), 96, 'W5'),
    ('canyon-road', 'bridge', 'the chasm bridge', (2170, 4920), 96, 'W6'),
    ('ash-coast', 'causeway', 'the crust causeway', (3300, 5560), 128, 'W6'),
    ('lull-road', 'bridge', 'Lullford Bridge and its swing span', (8960, 4310), 192, 'W7'),
    ('drovers-road', 'ford', 'the Willow Run ford', (3408, 2776), 48, None),
    ('canyon-road', 'ford', 'the Amber ford', (2680, 2976), 48, None),
    ('harbour-bridge', 'bridge', 'the Harbour Bridge', (10060, 4988), 480, None),
    ('beacon-causeway', 'causeway', 'the Beacon Causeway', (10272, 5380), 300, None),
    ('old-bridges', 'bridge', 'the old bridges', (10160, 4376), 200, None),
]

# The fifteen thresholds (brief section 2): id, name, route, at, object, mixing band,
# landmark seen and where, residents crossing, what the change radiates from.
THRESHOLDS = [
    ('col-hut', 'the Col hut', 'col-path', (6290, 2350), 'a stone hut with a bench and a water trough',
     'meadow, broadleaf, garden -> alpine, meadow, broadleaf', 'the headwall', (6230, 1950),
     'sheep and their shepherd graze up as far as the hut; walkers with staffs; choughs and an ibex on the scree above; the hut warden comes down for bread', 'the glacier'),
    ('frostline-lip', 'the Frostline lip', 'col-path', (6230, 2040), "the lip's moraine step",
     'meadow, broadleaf, alpine -> alpine, snow, meadow', 'the tarn', (6200, 1800),
     'the warden and an ice-cutter with a sledge go up; meltwater, and an ibex on the moraine looking down', 'the glacier'),
    ('brackens-gap', 'the Brackens gap', 'drovers-road', (5200, 3760), 'the gap between the two bluffs',
     'meadow, field, field2 -> steppe, meadow, broadleaf', 'the bluffs', (5170, 3600),
     "a drover takes his flock out west; his dog ranges ahead; skylarks over the bluffs; a peat-cutter's cart comes in to the valley", "the Brackens' heather"),
    ('drovers-bridge', "Drover's bridge", 'drovers-road', (4330, 3440), 'a stone bridge over the Rift gorge',
     'steppe, meadow, broadleaf -> scrub, meadow, steppe', 'the desert line viaduct', (4290, 3720),
     'the flock goes on to the far folds; a water-seller crosses to trade; lizards on the parapet; a vulture over the gorge', 'the Rift'),
    ('rift-ferry', 'the Rift ferry', 'ash-coast', (4180, 5240), "the ferry landings and the ferryman's rope",
     'meadow, broadleaf, sand -> deadwood, meadow, blacksand', 'the Rift mouth', (4250, 5380),
     'the ferryman (he lives here) takes fishers and goats across; terns and a black-sand beachcomber come the other way', 'the Rift and the sea'),
    ('amber-canyon-head', 'the Amber canyon head', 'canyon-road', (2770, 2650), 'the canyon head where the trail drops in',
     'desert, garden, meadow -> ash, desert, badland', 'the canyon walls', (2640, 2950),
     'a mule train comes down from the Lode with ore; orchard hands walk up from the fan; a vulture rides the canyon draught', 'the Amber'),
    ('cinder-rise', 'the Cinder Rise', 'canyon-road', (2270, 3860), 'a ridge of cinders the trail crests',
     'ash, desert, badland -> ash, desert, lavastone', 'the plume over Hearthold', (2470, 4300),
     'prospectors with sample bags go south; ash dust drifts north onto the bushes; a salamander basks on the ridge', 'the volcano'),
    ('chasm-bridge', 'the chasm bridge', 'canyon-road', (2170, 4920), 'a bridge over the young flow\'s chasm',
     'ash, desert, lavastone -> steppe, ash, scrub', 'Hearthold', (2480, 5120),
     "carters bring charcoal and ore to the forge; Hearthold's gate guard walks the bridge; steam drifts across", 'the volcano'),
    ('crust-causeway', 'the crust causeway', 'ash-coast', (3300, 5560), 'a causeway of laid slabs over the crusted flow',
     'deadwood, meadow, blacksand -> meadow, deadwood, blacksand', "the flow's steaming toe", (3290, 5800),
     "charcoal burners from Cinderwick carry sacks west; goats from the coast browse the dead forest's fireweed", 'the volcano'),
    ('millrace-cutting', 'the Millrace cutting', 'foothill-road', (7650, 2740), 'a cutting through the bank, the Millrace bridge at its foot',
     'broadleaf, garden, meadow -> garden, meadow, broadleaf', "Cogsworth's chimneys", (7980, 2450),
     'miners walk up to the pits; a coal cart comes down; woodcutters from Fernhollow with a timber wagon; crows over the cut', 'the coal seams'),
    ('cog-foot', 'the Cog foot', 'towpath', (8530, 3060), 'the towpath bridge over the Cog at the confluence',
     'broadleaf, garden, meadow -> meadow, watermeadow, broadleaf', 'the Narrows gorge', (8960, 2750),
     'a barge horse and its bargee on the towpath; coal barges go down; a heron fishes the confluence; anglers walk up', 'the Lull'),
    ('lullford-bridge', 'Lullford Bridge', 'lull-road', (8960, 4310), 'stone arches on the river island, the toll house and the swing span',
     'meadow, watermeadow, field -> watermeadow, reeds, garden', 'the swing span', (8960, 4310),
     'market carts bound for Neon; the toll keeper on the island; egrets in the shallows; barges wait at the swing span', 'the Lull'),
    ('canal-embankment', 'the canal embankment', 'delta-road', (9450, 4680), 'the raised towpath along the Lull Cut, with a lock',
     'watermeadow, broadleaf, carr -> garden, meadow, broadleaf', 'the falls and the Harbour Bridge', (10100, 4600),
     'market gardeners take produce in; a lock keeper; reed cutters with bundles come out; gulls follow the canal inland', 'the city'),
    ('headland-stile', 'the Headland stile', 'headland-lane', (6990, 5300), 'the stile in the drystone wall across the neck',
     'meadow, sand, field -> sand, meadow', 'the lighthouse', (7050, 5600),
     'sheep cross the stile to the fold; the lighthouse keeper; a hare from the cliff turf; sea pinks spill over the wall', 'the sea'),
    ('shell-bar', 'the Shell Bar', 'shell-bar', (6900, 5900), 'the bar and its islet, a wreck on the sand',
     'sand, meadow, field -> meadow, sand, field2', 'the wreck', (6930, 5870),
     'cocklers walk out at low tide; seals haul out on the bar; terns nest on the islet', 'the sea'),
]

# Obstacles beside the routes, each with a side path round its far side (plan 5.6).
OBSTACLES = [
    ('high-fells', 'thicket', (6729, 1527)),
    ('high-fells', 'thicket', (7404, 1969)),
    ('foothill-road', 'thicket', (7120, 3276)),
    ('towpath', 'fallen tree', (8384, 3465)),
    ('lull-road', 'thicket', (7407, 3994)),
    ('lull-road', 'marshy pool', (9388, 4288)),
    ('coast-path', 'thicket', (7053, 4974)),
    ('coast-path', 'thicket', (7910, 4971)),
    ('drovers-road', 'thicket', (5491, 3829)),
    ('drovers-road', 'ravine', (3890, 3184)),
    ('canyon-road', 'ravine', (2003, 4419)),
    ('ash-coast', 'boulders', (5165, 4817)),
]

# Secret pockets: a dead-end path of 80 px or more to a clearing (plan 6.4).
POCKETS = [
    ('col-path', 'a view over the land', (6416, 2465)),
    ('col-path', 'a bench under a tree', (6488, 2679)),
    ('drovers-road', 'a hermit at a fire', (5183, 3416)),
    ('drovers-road', 'a story detail: a buried bell', (5444, 3604)),
    ('high-fells', 'a story detail: a buried bell', (7634, 1792)),
    ('high-fells', 'a view down a gorge', (7172, 1964)),
    ('high-fells', 'a hermit at a fire', (6890, 1886)),
    ('foothill-road', 'a resident fishing', (7708, 3083)),
    ('foothill-road', 'a story detail: a buried bell', (7212, 2780)),
    ('foothill-road', 'a story detail: an old grave', (7093, 3405)),
    ('towpath', 'a view down a gorge', (8012, 2908)),
    ('coast-path', 'a view over the land', (8283, 5072)),
    ('coast-path', 'a bench under a tree', (7556, 4823)),
    ('lull-road', 'a story detail: initials cut in a stone', (7712, 4158)),
    ('lull-road', 'a story detail: an old grave', (9799, 4170)),
    ('delta-road', 'a resident fishing', (9188, 4572)),
    ('quay-street', 'a bench under a tree', (10652, 5548)),
    ('cape-road', 'a story detail: an old grave', (10740, 4980)),
    ('drovers-road', 'a view down a gorge', (4759, 3270)),
    ('drovers-road', 'a view over the land', (3927, 2838)),
    ('canyon-road', 'a resident fishing', (2126, 3694)),
    ('lode-track', 'a story detail: initials cut in a stone', (3088, 2026)),
    ('ash-coast', 'a bench under a tree', (3387, 5321)),
    ('ember-way', 'a story detail: an old grave', (2212, 5762)),
    ('ember-way', 'a hermit at a fire', (2500, 5402)),
]


# ---------------------------------------------------------------------------- geometry

def _hash(*parts) -> float:
    """A stable number in [0, 1) from the parts (so the bends never change by accident)."""
    h = hashlib.sha256('|'.join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:6], 'big') / float(1 << 48)


def resample(line, step=STEP):
    """Points every `step` px along a polyline, ends kept."""
    out = [tuple(map(float, line[0]))]
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        seg = math.dist((x0, y0), (x1, y1))
        if seg == 0:
            continue
        acc = math.dist(out[-1], (x0, y0))
        t = step - acc if acc < step else 0.0
        while t <= seg:
            out.append((x0 + (x1 - x0) * t / seg, y0 + (y1 - y0) * t / seg))
            t += step
    if math.dist(out[-1], line[-1]) > 0.5:
        out.append(tuple(map(float, line[-1])))
    return out


def arclen(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + math.dist(a, b))
    return s


def smooth(pts, radius_px):
    """Gaussian smoothing along the line, ends pinned."""
    n = len(pts)
    k = max(1, int(radius_px / STEP))
    w = [math.exp(-0.5 * (i / (k / 2.0)) ** 2) for i in range(-k, k + 1)]
    out = []
    for i in range(n):
        if i == 0 or i == n - 1:
            out.append(pts[i])
            continue
        r = min(k, i, n - 1 - i)   # shrink near the ends so they stay put
        sx = sy = sw = 0.0
        for j in range(-r, r + 1):
            ww = w[j + k]
            sx += pts[i + j][0] * ww
            sy += pts[i + j][1] * ww
            sw += ww
        out.append((sx / sw, sy / sw))
    return out


def normals(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 2)]
        b = pts[min(n - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        out.append((-dy / d, dx / d))
    return out


def project(pts, s, p):
    """The arc length of the point of the line nearest p, and its distance."""
    best = (float('inf'), 0.0)
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - x0) * dx + (p[1] - y0) * dy) / L2))
        q = (x0 + dx * t, y0 + dy * t)
        d = math.dist(q, p)
        if d < best[0]:
            best = (d, s[i] + t * math.sqrt(L2))
    return best[1], best[0]


def at_s(pts, s, si):
    """The point at arc length si."""
    if si <= 0:
        return pts[0]
    for i in range(len(pts) - 1):
        if s[i + 1] >= si:
            seg = s[i + 1] - s[i] or 1.0
            t = (si - s[i]) / seg
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t,
                    pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t)
    return pts[-1]


def heading(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def turn(h0, h1) -> float:
    d = (h1 - h0 + 180) % 360 - 180
    return d


def snap(v) -> int:
    return int(round(v / GRID)) * GRID


def owner(x, y):
    for who, name, (x0, y0, x1, y1) in FOOTPRINTS:
        if x0 <= x < x1 and y0 <= y < y1:
            return who, name
    return BETWEEN, 'the land between'


# ---------------------------------------------------------------------------- the build

def bends(rid, s, total, amp_long, amp_short, quiet):
    """Lateral offsets for the plan's irregular bends: a short bend every 160 to 240 px
    riding a long swing of 450 to 750 px, each wavelength and size varying along the
    route (so no stretch reads as a regular S). `quiet` gives, per sample, how much of
    the bend is allowed (0 on bridges and at the ends)."""
    out = []
    ph_l = _hash(rid, 'long') * 2 * math.pi
    ph_s = _hash(rid, 'short') * 2 * math.pi
    prev = 0.0
    for i, si in enumerate(s):
        ds = si - prev
        prev = si
        k = int(si // 300)
        lam_l = 450 + 300 * _hash(rid, 'lam-long', k)
        lam_s = 160 + 80 * _hash(rid, 'lam-short', int(si // 120))
        ph_l += 2 * math.pi * ds / lam_l
        ph_s += 2 * math.pi * ds / lam_s
        a_l = amp_long * (0.6 + 0.4 * _hash(rid, 'amp-long', k))
        a_s = amp_short * (0.7 + 0.3 * _hash(rid, 'amp-short', int(si // 200)))
        out.append(quiet[i] * (a_l * math.sin(ph_l) + a_s * math.sin(ph_s)))
    return out


def build_route(spec, bumps=()):
    rid, name, kind, frm, to, base_w, (b_walk, b_tiers), (amp_l, amp_s) = spec
    raw = resample(ANCHORS[rid])
    pts = smooth(raw, 96) if len(ANCHORS[rid]) > 2 else raw
    s = arclen(pts)
    total = s[-1]
    base_total = total

    crossings = []
    for (r, ck, cname, at, span, way) in CROSSINGS:
        if r != rid:
            continue
        sc, d = project(pts, s, at)
        if d > 96:
            raise SystemExit(f'{name}: {cname} at {at} is {d:.0f} px from the line')
        crossings.append({'kind': ck, 'name': cname, 'way': way, 's': sc, 'span': span, 'brief': at})
    thresholds = []
    for t in THRESHOLDS:
        if t[2] != rid:
            continue
        st, d = project(pts, s, t[3])
        if d > 96:
            raise SystemExit(f'{name}: threshold {t[1]} at {t[3]} is {d:.0f} px from the line')
        thresholds.append((t, st))

    # how much bend each sample may take: none within 64 px of the ends, none on a
    # crossing's span (bridges, fords and causeways are straight), easing in over 64 px
    def quiet_at(si):
        q = min(1.0, si / 64.0, (total - si) / 64.0)
        for c in crossings:
            half = c['span'] / 2
            d = abs(si - c['s']) - half
            q = min(q, max(0.0, d / 64.0))
        return max(0.0, q)
    quiet = [quiet_at(si) for si in s]

    tier0, legs = TIERS[rid]
    changes = []
    tier = tier0
    for (f0, f1, kinds, tiers) in legs:
        n = len(tiers)
        for i, t_after in enumerate(tiers):
            k = kinds if isinstance(kinds, str) else kinds[i]
            sc = total * (f0 + (f1 - f0) * (i + 0.5) / n)
            changes.append({'s': sc, 'kind': k, 'from': tier, 'to': t_after, 'run': RUN[k]})
            tier = t_after
    # keep the changes off crossings and thresholds, and give each its room
    for c in changes:
        for x in crossings:
            lo, hi = x['s'] - x['span'] / 2 - c['run'] / 2, x['s'] + x['span'] / 2 + c['run'] / 2
            if lo < c['s'] < hi:
                c['s'] = hi if c['s'] > x['s'] else lo
        c['s'] = min(max(c['s'], c['run'] / 2), total - c['run'] / 2)

    off = bends(rid, s, total, amp_l, amp_s, quiet)
    # a bend added where the swings happened to cancel into a straight run (check 16)
    for (sb, sign) in bumps:
        for i, si in enumerate(s):
            u = (si - sb) / 180.0
            if -1 < u < 1:
                off[i] += sign * 14 * math.cos(u * math.pi / 2) ** 2 * quiet[i]
    # a switchback is a short Z across the line
    for c in changes:
        if c['kind'] != 'switchback':
            continue
        for i, si in enumerate(s):
            u = (si - (c['s'] - c['run'] / 2)) / c['run']
            if 0 <= u <= 1:
                off[i] += 20 * math.sin(2 * math.pi * u) * (1 if int(c['to']) % 2 else -1)
    nrm = normals(pts)
    line = [(p[0] + nrm[i][0] * off[i], p[1] + nrm[i][1] * off[i]) for i, p in enumerate(pts)]
    # pin the ends exactly where the brief has them
    line[0] = tuple(map(float, ANCHORS[rid][0]))
    line[-1] = tuple(map(float, ANCHORS[rid][-1]))
    ls = arclen(line)
    scale = ls[-1] / total
    for c in changes:
        c['s'] *= scale
    for c in crossings:
        c['s'] *= scale
    thresholds = [(t, st * scale) for t, st in thresholds]
    total = ls[-1]

    # vertices: every sample whose snapped point is new, thinned to the grid's own steps
    verts = []
    vs = []
    for i, p in enumerate(line):
        q = (snap(p[0]), snap(p[1]))
        if verts and q == verts[-1]:
            continue
        verts.append(q)
        vs.append(ls[i])
    # thin: drop a vertex when its neighbours' straight line passes within 2 px of it and
    # keeps the next vertex within VERTEX_EVERY
    keep = [0]
    for i in range(1, len(verts) - 1):
        a = verts[keep[-1]]
        b = verts[i + 1]
        p = verts[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        dev = abs(dx * (p[1] - a[1]) - dy * (p[0] - a[0])) / L
        if dev > 2.0 or math.dist(a, b) > VERTEX_EVERY:
            keep.append(i)
    keep.append(len(verts) - 1)
    verts = [verts[i] for i in keep]
    vs = arclen(verts)
    scale = vs[-1] / total
    for c in changes:
        c['s'] *= scale
    for c in crossings:
        c['s'] *= scale
    thresholds = [(t, st * scale) for t, st in thresholds]
    total = vs[-1]

    # tiers per vertex
    def tier_at(si):
        t = tier0
        for c in changes:
            if si >= c['s']:
                t = c['to']
        return t

    # widths: base, +8 at bends, junction squares at the ends, +16 at thresholds
    widths = []
    for i, v in enumerate(verts):
        w = base_w
        a = verts[max(0, i - 2)]
        b = verts[min(len(verts) - 1, i + 2)]
        if 0 < i < len(verts) - 1:
            h0 = heading(a, v) if a != v else heading(v, b)
            h1 = heading(v, b) if b != v else h0
            if abs(turn(h0, h1)) > 25:
                w += 8
        si = vs[i]
        if kind in ('road', 'path') and (si < 48 or total - si < 48):
            w = max(w, base_w + 16)
        for (t, st) in thresholds:
            if abs(si - st) < 48:
                w = max(w, base_w + 16)
        if kind == 'bar':
            w = 40 + 8 * int(3 * _hash(rid, 'bar', i // 3))
        w = max(WIDTH_MIN, min(WIDTH_MAX, int(round(w / GRID)) * GRID))
        widths.append(w)

    points = [[v[0], v[1], widths[i], tier_at(vs[i])] for i, v in enumerate(verts)]

    out_changes = []
    for c in changes:
        p = at_s(verts, vs, c['s'])
        out_changes.append({'at': [snap(p[0]), snap(p[1])], 's': round(c['s']), 'kind': c['kind'],
                            'from': c['from'], 'to': c['to'], 'run': c['run']})
    out_cross = []
    for c in crossings:
        p = at_s(verts, vs, c['s'])
        out_cross.append({'kind': c['kind'], 'name': c['name'], 'way': c['way'],
                          'at': [snap(p[0]), snap(p[1])], 's': round(c['s']), 'span': c['span']})
    out_thr = []
    for (t, st) in thresholds:
        p = at_s(verts, vs, st)
        before = owner(*at_s(verts, vs, max(0, st - 200)))
        after = owner(*at_s(verts, vs, min(total, st + 200)))
        out_thr.append({
            'id': t[0], 'name': t[1], 'route': rid, 'at': [snap(p[0]), snap(p[1])], 's': round(st),
            'brief': list(t[3]), 'object': t[4], 'band': t[5], 'landmark': t[6], 'landmarkAt': list(t[7]),
            'residents': t[8], 'radiatesFrom': t[9], 'sides': [before[0], after[0]],
            'objectBy': BETWEEN, 'bandFade': 160,
        })

    # meeting cells: where the line passes from one owner's land into another's
    meets = []
    prev = owner(*verts[0])
    for i in range(1, len(verts)):
        a, b = verts[i - 1], verts[i]
        cur = owner(*b)
        if cur[0] == prev[0] and cur[1] == prev[1]:
            continue
        # find the crossing between a and b at 1 px
        n = max(1, int(math.dist(a, b)))
        q = b
        for j in range(1, n + 1):
            x = a[0] + (b[0] - a[0]) * j / n
            y = a[1] + (b[1] - a[1]) * j / n
            if owner(x, y) != prev:
                q = (x, y)
                break
        sq = vs[i - 1] + math.dist(a, q)
        meets.append({
            'route': rid, 'from': prev[0], 'fromPart': prev[1], 'to': cur[0], 'toPart': cur[1],
            'at': [snap(q[0]), snap(q[1])], 'cell': [snap(q[0]) // GRID, snap(q[1]) // GRID],
            's': round(sq), 'tier': tier_at(sq), 'width': widths[i],
            'heading': round(heading(a, b)),
        })
        prev = cur

    out = {
        'id': rid, 'name': name, 'kind': kind, 'from': frm, 'to': to,
        'length': round(total), 'walkS': round(total / WALK_PX_S, 1),
        'blockout': {'walkS': b_walk, 'tierChanges': b_tiers},
        'points': points, 'changes': out_changes, 'crossings': out_cross,
        'thresholds': out_thr, 'meets': meets,
    }
    out['_scale'] = total / base_total
    out['sidePaths'] = side_paths(rid, verts, vs)
    out['pockets'] = pocket_paths(rid, verts, vs)
    return out


def side_paths(rid, verts, vs):
    """A side path round each obstacle: off the road at a shallow Y about 300 px before,
    round the far side with two gentle bends, back at a Y after (plan 5.6)."""
    out = []
    for (r, what, at) in OBSTACLES:
        if r != rid:
            continue
        so, d = project(verts, vs, at)
        total = vs[-1]
        s0, s1 = max(16, so - 300), min(total - 16, so + 300)
        p0, p1 = at_s(verts, vs, s0), at_s(verts, vs, s1)
        pc = at_s(verts, vs, so)
        # the far side: the obstacle stands between the road and the side path
        vx, vy = at[0] - pc[0], at[1] - pc[1]
        dv = math.hypot(vx, vy)
        if dv < 1:
            hx, hy = p1[0] - p0[0], p1[1] - p0[1]
            hd = math.hypot(hx, hy) or 1.0
            vx, vy, dv = -hy / hd, hx / hd, 1.0
        ux, uy = vx / dv, vy / dv
        reach = max(dv, 0) + 72 + 24 * _hash(rid, what, 'reach')   # past the obstacle
        a = at_s(verts, vs, s0 + 0.28 * (s1 - s0))
        b = at_s(verts, vs, s0 + 0.72 * (s1 - s0))
        mid1 = (a[0] + ux * reach * 0.85, a[1] + uy * reach * 0.85)
        mid2 = (b[0] + ux * reach, b[1] + uy * reach)
        path = resample([p0, mid1, mid2, p1], 8)
        path = smooth(path, 64)
        pts = []
        for p in path:
            q = [snap(p[0]), snap(p[1])]
            if not pts or q != pts[-1]:
                pts.append(q)
        pts = pts[::max(1, len(pts) // 12)] + ([pts[-1]] if pts[-1] != pts[::max(1, len(pts) // 12)][-1] else [])
        out.append({'obstacle': what, 'at': list(at), 'leaves': [snap(p0[0]), snap(p0[1])],
                    'rejoins': [snap(p1[0]), snap(p1[1])], 'points': pts, 'width': 24})
    return out


def pocket_paths(rid, verts, vs):
    """A dead-end path to each secret pocket, leaving the route at its nearest point,
    with one gentle bend, ending in a clearing (80 px or more long, plan 6.4)."""
    out = []
    for (r, holds, at) in POCKETS:
        if r != rid:
            continue
        so, d = project(verts, vs, at)
        p0 = at_s(verts, vs, so)
        mx, my = (p0[0] + at[0]) / 2, (p0[1] + at[1]) / 2
        dx, dy = at[0] - p0[0], at[1] - p0[1]
        L = math.hypot(dx, dy) or 1.0
        bend = (0.12 + 0.1 * _hash(rid, holds, at)) * L * (1 if _hash(rid, holds) > 0.5 else -1)
        mid = (mx - dy / L * bend, my + dx / L * bend)
        path = resample([p0, mid, at], 8)
        pts = []
        for p in path[:: max(1, len(path) // 8)] + [path[-1]]:
            q = [snap(p[0]), snap(p[1])]
            if not pts or q != pts[-1]:
                pts.append(q)
        out.append({'holds': holds, 'clearing': list(at), 'leaves': pts[0], 'points': pts,
                    'length': round(arclen(pts)[-1]), 'width': 24, 'clearingRadius': 40})
    return out


# ---------------------------------------------------------------------------- the checks

def straight_runs(points, built=(), where=False):
    """The longest stretch whose heading stays within 6 degrees of where it started,
    measured on headings over 32 px (so the grid's own steps don't count as bends).
    `built` lists (s from, s to) stretches that are built straight (a bridge, a ford, a
    causeway, with 64 px either side to ease in); a run ends where one begins."""
    pts = [(p[0], p[1]) for p in points]
    rs = resample(pts, 8)
    hs = []
    for i in range(len(rs) - 4):
        si = i * 8.0 + 16
        hs.append(None if any(lo <= si <= hi for lo, hi in built) else heading(rs[i], rs[i + 4]))
    best = 0.0
    mid = 0.0
    i = 0
    while i < len(hs):
        if hs[i] is None:
            i += 1
            continue
        j = i
        while j + 1 < len(hs) and hs[j + 1] is not None and abs(turn(hs[i], hs[j + 1])) <= 6:
            j += 1
        if (j - i + 4) * 8.0 > best:
            best = (j - i + 4) * 8.0
            mid = (i + j + 4) / 2 * 8.0
        i = j + 1
    return (best, mid) if where else best


def check(routes):
    problems = []
    for r in routes:
        pts = r['points']
        for x, y, w, t in pts:
            if x % GRID or y % GRID:
                problems.append(f"{r['name']}: vertex ({x}, {y}) off the grid")
            if not (0 <= x <= CANVAS[0] and 0 <= y <= CANVAS[1]):
                problems.append(f"{r['name']}: vertex ({x}, {y}) off the canvas")
            if not (WIDTH_MIN <= w <= WIDTH_MAX) or w % GRID:
                problems.append(f"{r['name']}: width {w} at ({x}, {y})")
        for a, b in zip(pts, pts[1:]):
            if math.dist(a[:2], b[:2]) > VERTEX_EVERY + 8:
                problems.append(f"{r['name']}: {math.dist(a[:2], b[:2]):.0f} px between vertices")
            if abs(a[3] - b[3]) > 1:
                problems.append(f"{r['name']}: tier jumps {a[3]} to {b[3]}")
        tiers0 = TIERS[r['id']][0]
        if pts[0][3] != tiers0:
            problems.append(f"{r['name']}: starts at tier {pts[0][3]}")
        prev_end = -1e9
        for c in r['changes']:
            lo = c['s'] - c['run'] / 2
            if lo < prev_end - 0.5:
                problems.append(f"{r['name']}: tier changes overlap at s {c['s']}")
            prev_end = c['s'] + c['run'] / 2
            if lo < -0.5 or prev_end > r['length'] + 0.5:
                problems.append(f"{r['name']}: a {c['kind']} at s {c['s']} runs off the route")
            for x in r['crossings']:
                if abs(c['s'] - x['s']) < (x['span'] + c['run']) / 2 - 1:
                    problems.append(f"{r['name']}: a {c['kind']} on {x['name']}")
        if r['kind'] in ('road', 'path', 'bar') and r['length'] > 300:
            built = [(x['s'] - x['span'] / 2 - 64, x['s'] + x['span'] / 2 + 64) for x in r['crossings']]
            run = straight_runs(pts, built)
            if run > 240:
                problems.append(f"{r['name']}: a straight run of {run:.0f} px (check 16: at most 240)")
    return problems


def gate_check(routes):
    """Open the ways in order (W1 to W8); at each step flood the route graph from the hut's
    valley and record which places are reached. A route is cut at each crossing that has a
    way not yet open. Returns [(way, sorted places)]."""
    # a route's places: its two ends, and any stop its line passes within 96 px of
    route_stops = {}
    for r in routes:
        verts = [(p[0], p[1]) for p in r['points']]
        vs = arclen(verts)
        on = [(0.0, r['from']), (vs[-1], r['to'])]
        for sid, (_, at) in STOPS.items():
            if sid in (r['from'], r['to']):
                continue
            so, d = project(verts, vs, at)
            if d <= 96:
                on.append((so, sid))
        route_stops[r['id']] = sorted(on)
    steps = []
    for k in range(0, 9):
        open_ways = {f'W{i}' for i in range(1, k + 1)}
        adj = {sid: set() for sid in STOPS}
        for r in routes:
            cuts = [x['s'] for x in r['crossings'] if x['way'] and x['way'] not in open_ways]
            on = route_stops[r['id']]
            for (s0, a), (s1, b) in zip(on, on[1:]):
                if not any(s0 < c < s1 for c in cuts):
                    adj[a].add(b)
                    adj[b].add(a)
        for group in SAME_PLACE:
            for a in group:
                adj[a].update(x for x in group if x != a)
        for (_, a, b, way) in LINKS:
            if way in open_ways:
                adj[a].add(b)
                adj[b].add(a)
        seen = {HOME}
        todo = [HOME]
        while todo:
            n = todo.pop()
            for m in adj[n]:
                if m not in seen:
                    seen.add(m)
                    todo.append(m)
        steps.append(('start' if k == 0 else f'W{k}', sorted(seen)))
    return steps


# ---------------------------------------------------------------------------- the outputs

def export_ts(routes, steps, path):
    meets = [m for r in routes for m in r['meets']]
    thresholds = [t for r in routes for t in r['thresholds']]
    footprints = [{'owner': w, 'part': n, 'box': list(b)} for (w, n, b) in FOOTPRINTS]
    stops = {k: {'name': v[0], 'at': list(v[1])} for k, v in STOPS.items()}
    links = [{'name': n, 'from': a, 'to': b, 'way': w} for (n, a, b, w) in LINKS]
    body = {
        'routes': [{k: v for k, v in r.items() if k not in ('meets', 'thresholds')} for r in routes],
        'thresholds': thresholds,
        'meets': meets,
        'footprints': footprints,
        'stops': stops,
        'links': links,
        'gates': [{'open': w, 'reached': s} for w, s in steps],
    }
    def js(v):
        return json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    lines = [
        '/**',
        ' * The routes between the regions, as data on the world canvas (lane G).',
        ' * Generated by scripts/art/world_routes.py; do not edit by hand. World px on the',
        ' * v5.3 canvas (11264 x 6912, 8 px cells, a tier is a 32 px face). Not read by the',
        ' * game yet: the region lanes build up to it. Checked by lib/world-routes.test.ts.',
        ' */',
        '',
        "export type RouteKind = 'road' | 'path' | 'bar' | 'bridge' | 'causeway';",
        "export type TierChangeKind = 'stair' | 'ramp' | 'switchback';",
        "export type CrossingKind = 'ford' | 'bridge' | 'ferry' | 'causeway' | 'bar' | 'stile' | 'step';",
        'export type LaneId = string;',
        '/** A vertex: x, y (world px, on the 8 px grid), width (px), tier. */',
        'export type RoutePoint = readonly [number, number, number, number];',
        'export interface TierChange { at: readonly [number, number]; s: number; kind: TierChangeKind; from: number; to: number; run: number }',
        'export interface Crossing { kind: CrossingKind; name: string; way: string | null; at: readonly [number, number]; s: number; span: number }',
        'export interface SidePath { obstacle: string; at: readonly [number, number]; leaves: readonly [number, number]; rejoins: readonly [number, number]; points: readonly (readonly [number, number])[]; width: number }',
        'export interface PocketPath { holds: string; clearing: readonly [number, number]; leaves: readonly [number, number]; points: readonly (readonly [number, number])[]; length: number; width: number; clearingRadius: number }',
        'export interface WorldRoute {',
        '  id: string; name: string; kind: RouteKind; from: string; to: string;',
        '  length: number; walkS: number; blockout: { walkS: number | null; tierChanges: number };',
        '  points: readonly RoutePoint[]; changes: readonly TierChange[]; crossings: readonly Crossing[];',
        '  sidePaths: readonly SidePath[]; pockets: readonly PocketPath[];',
        '}',
        'export interface Threshold {',
        '  id: string; name: string; route: string; at: readonly [number, number]; s: number; brief: readonly [number, number];',
        '  object: string; band: string; landmark: string; landmarkAt: readonly [number, number]; residents: string;',
        '  radiatesFrom: string; sides: readonly [LaneId, LaneId]; objectBy: LaneId; bandFade: number;',
        '}',
        'export interface RouteMeet {',
        '  route: string; from: LaneId; fromPart: string; to: LaneId; toPart: string;',
        '  at: readonly [number, number]; cell: readonly [number, number]; s: number; tier: number; width: number; heading: number;',
        '}',
        'export interface Footprint { owner: LaneId; part: string; box: readonly [number, number, number, number] }',
        'export interface RouteStop { name: string; at: readonly [number, number] }',
        'export interface RouteLink { name: string; from: string; to: string; way: string }',
        'export interface GateStep { open: string; reached: readonly string[] }',
        '',
        f'export const ROUTE_CANVAS = {js(list(CANVAS))} as const;',
        f'export const ROUTE_GRID = {GRID};',
        f'export const ROUTE_TIER_PX = {TIER_PX};',
        f'export const ROUTE_WALK_PX_S = {WALK_PX_S};',
        f'export const ROUTE_WIDTH = {js({"min": WIDTH_MIN, "max": WIDTH_MAX})} as const;',
        f'export const ROUTE_VERTEX_EVERY = {VERTEX_EVERY};',
        f'export const TIER_CHANGE_RUN = {js(RUN)} as const;',
        f"export const ROUTES_BETWEEN = '{BETWEEN}';",
        f"export const ROUTES_HOME = '{HOME}';",
        f'export const worldRoutes: readonly WorldRoute[] = {js(body["routes"])};',
        f'export const worldThresholds: readonly Threshold[] = {js(body["thresholds"])};',
        f'export const worldRouteMeets: readonly RouteMeet[] = {js(body["meets"])};',
        f'export const routeFootprints: readonly Footprint[] = {js(body["footprints"])};',
        f'export const routeStops: Readonly<Record<string, RouteStop>> = {js(body["stops"])};',
        f'export const routeLinks: readonly RouteLink[] = {js(body["links"])};',
        f'export const routeGates: readonly GateStep[] = {js(body["gates"])};',
        '',
    ]
    with open(path, 'w') as f:
        f.write('\n'.join(lines))


LANE_NAMES = {
    'claude-c': 'C (the isles)', 'claude-d': 'D (Sunstone Reach)', 'claude-e': 'E (the home valley)',
    'claude-f': 'F (the Frostline, the massif and the Brackens)', 'claude-g': 'G (the land between)',
    'claude-h': 'H (Cogsworth and the coal hills)', 'claude-i': 'I (Neon Harbour and the Lull belt)',
}


def export_md(routes, steps, path):
    L = []
    L.append('# Where the routes meet each lane\n')
    L.append('Generated by `scripts/art/world_routes.py` (lane G); do not edit by hand. World px on the v5.3 canvas; a cell is 8 px, so cell (x, y) is world px (8x, 8y). Tier n is n x 32 px above the sea.\n')
    L.append('Inside your footprint you paint the route\'s surface to the line, width and tier in `lib/world-routes.ts`, with your own kits; between the footprints the route and its land are lane G\'s, and so is every threshold object. Meet each route at the cell, tier and width below. If you need a different tier or a nudge of the line, post a note to claude-g on the crew board and lane G changes `world_routes.py`.\n')
    by_lane = {}
    for r in routes:
        for m in r['meets']:
            if m['from'] == m['to']:
                continue   # between two parts of one lane's land: that lane's own business
            for lane in (m['from'], m['to']):
                if lane != BETWEEN:
                    by_lane.setdefault(lane, []).append(m)
    for lane in sorted(by_lane):
        L.append(f'## Lane {LANE_NAMES.get(lane, lane)}\n')
        L.append('| Route | Crossing | Cell | World px | Tier | Width | Heading |')
        L.append('| ----- | -------- | ---- | -------- | ---- | ----- | ------- |')
        for m in sorted(by_lane[lane], key=lambda m: (m['route'], m['s'])):
            name = next(r['name'] for r in routes if r['id'] == m['route'])
            L.append(f"| {name} | {m['fromPart']} to {m['toPart']} | ({m['cell'][0]}, {m['cell'][1]}) | ({m['at'][0]}, {m['at'][1]}) | {m['tier']} | {m['width']} | {m['heading']} |")
        L.append('')
    L.append('## The routes\n')
    L.append('| Route | Kind | From | To | Length (px) | Walk (s) | Brief walk (s) | Tier changes | Brief tier changes | Ways |')
    L.append('| ----- | ---- | ---- | -- | ----------- | -------- | -------------- | ------------ | ------------------ | ---- |')
    for r in routes:
        ways = ', '.join(sorted({c['way'] for c in r['crossings'] if c['way']})) or '-'
        bw = r['blockout']['walkS']
        L.append(f"| {r['name']} | {r['kind']} | {STOPS[r['from']][0]} | {STOPS[r['to']][0]} | {r['length']} | {r['walkS']} | {bw if bw is not None else '-'} | {len(r['changes'])} | {r['blockout']['tierChanges']} | {ways} |")
    L.append('')
    L.append('## The thresholds\n')
    L.append('| Threshold | Route | At | Sides | Object (lane G) |')
    L.append('| --------- | ----- | -- | ----- | --------------- |')
    for r in routes:
        for t in r['thresholds']:
            L.append(f"| {t['name']} | {r['name']} | ({t['at'][0]}, {t['at'][1]}) | {t['sides'][0]} / {t['sides'][1]} | {t['object']} |")
    L.append('')
    L.append('## The gate check\n')
    L.append('The ways opened one at a time in road order, flooding the routes from the valley; the places each step adds (journeys count once their way is open, settlements are joined by their own streets). Nothing behind a closed way is reached.\n')
    L.append('| Open | Places it adds |')
    L.append('| ---- | -------------- |')
    seen = set()
    for w, s in steps:
        new = [x for x in s if x not in seen]
        seen.update(s)
        L.append(f"| {w} | {', '.join(STOPS[x][0] for x in new) or '(nothing on foot: the rocket and the lander are journeys)'} |")
    L.append('')
    with open(path, 'w') as f:
        f.write('\n'.join(L))


def preview(routes, path, scale=8):
    from PIL import Image, ImageDraw
    W, H = CANVAS[0] // scale, CANVAS[1] // scale
    im = Image.new('RGB', (W, H), (24, 26, 34))
    d = ImageDraw.Draw(im)
    colours = {'claude-c': (40, 120, 130), 'claude-d': (150, 110, 50), 'claude-e': (70, 130, 60),
               'claude-f': (150, 160, 190), 'claude-h': (120, 80, 60), 'claude-i': (70, 90, 160)}
    for who, name, (x0, y0, x1, y1) in FOOTPRINTS:
        d.rectangle([x0 // scale, y0 // scale, x1 // scale - 1, y1 // scale - 1], outline=colours[who])
        d.text((x0 // scale + 3, y0 // scale + 2), f'{who[-1].upper()} {name}', fill=colours[who])
    for r in routes:
        pts = [(p[0] / scale, p[1] / scale) for p in r['points']]
        for i in range(len(pts) - 1):
            t = r['points'][i][3]
            c = (min(255, 120 + t * 8), min(255, 200 - t * 3), 90)
            d.line([pts[i], pts[i + 1]], fill=c, width=max(1, r['points'][i][2] // 16))
        for sp in r['sidePaths'] + r['pockets']:
            d.line([(p[0] / scale, p[1] / scale) for p in sp['points']], fill=(200, 200, 200), width=1)
        for c in r['changes']:
            x, y = c['at'][0] / scale, c['at'][1] / scale
            d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=(255, 255, 255))
        for c in r['crossings']:
            x, y = c['at'][0] / scale, c['at'][1] / scale
            col = (255, 80, 80) if c['way'] else (80, 200, 255)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=col)
            if c['way']:
                d.text((x + 4, y - 10), c['way'], fill=col)
        for m in r['meets']:
            x, y = m['at'][0] / scale, m['at'][1] / scale
            d.rectangle([x - 2, y - 2, x + 2, y + 2], outline=(255, 230, 0))
        x, y = pts[len(pts) // 2]
        d.text((x + 4, y + 2), r['name'], fill=(235, 235, 235))
    im.save(path)


def build():
    routes = []
    for spec in ROUTES:
        bumps = []
        r = build_route(spec)
        # where the long swing and the short bend cancel into a run straighter than check
        # 16 allows, add a bend there (at most four, deterministic) and build again
        while r['kind'] in ('road', 'path', 'bar') and len(bumps) < 4:
            built = [(x['s'] - x['span'] / 2 - 64, x['s'] + x['span'] / 2 + 64) for x in r['crossings']]
            run, at = straight_runs(r['points'], built, where=True)
            if run <= 240:
                break
            bumps.append((at / r['_scale'], 1 if len(bumps) % 2 == 0 else -1))
            r = build_route(spec, bumps)
        del r['_scale']
        routes.append(r)
    problems = check(routes)
    if problems:
        raise SystemExit('world_routes: ' + '\n  '.join(['problems:'] + problems))
    steps = gate_check(routes)
    return routes, steps


def main():
    routes, steps = build()
    ts = os.path.join(worlds.ROOT, 'lib', 'world-routes.ts')
    md = os.path.join(worlds.ROOT, 'docs', 'vision', 'regions', 'route-meets.md')
    os.makedirs(os.path.dirname(md), exist_ok=True)
    export_ts(routes, steps, ts)
    export_md(routes, steps, md)
    try:
        subprocess.run(['npx', 'oxfmt', '--write', ts, md], cwd=worlds.ROOT, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:  # formatting is cosmetic; the check reads the data
        print('world_routes: oxfmt skipped:', e)
    if os.environ.get('ROUTES_PREVIEW'):
        preview(routes, os.environ['ROUTES_PREVIEW'])
    n_meets = sum(len(r['meets']) for r in routes)
    print(f'world_routes: {len(routes)} routes, {sum(r["length"] for r in routes)} px, '
          f'{sum(len(r["changes"]) for r in routes)} tier changes, {n_meets} meeting cells')


if __name__ == '__main__':
    main()
