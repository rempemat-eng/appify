"""The woodland's layout: the first finished screen at density 2 (docs/vision/first-screen.md).

Pure data in world px (320 x 576, the soft grid's 8 px cell). The library in scripts/art/native/
turns it into pictures, the walk grid and the zone's objects; the biome file
(scripts/art/biomes/woodland.json) holds the palette, the plant set and the numbers. Game
function is kept from the 1x woodland (valley_zones.woodland): the same stands, ports and the
forager's round.

The story of the place: the Hollow's escarpment stands above the north edge; at its foot a
wooded shelf (32 px up) runs across the zone in three stepped reaches. The Hollow's falls land on
the shelf at x 84 and run as a brook to its lip, fall its cobble face into a plunge pool, and run
on south past the glade to the spring pool, from where the stream leaves east to the garden. The
hollow oak stands in a sunlit glade under the shelf, the forester keeps a woodpile beside it, the
stone circle sits in its ring of trodden earth in the south-west, and the lane comes in from the
garden's orchard walk.
"""
from __future__ import annotations

NAME = 'woodland'
BIOME = 'woodland'
W, H = 320, 576
SEED = 21
TOP = 48              # plan rows above the screen for the raised tier (cliff core)

# ---- game function, kept exactly -----------------------------------------------------------------
STANDS = {'garden': (304, 456), 'clearing': (110, 160), 'spring': (100, 316), 'stones': (78, 414)}
START = 'garden'
ROUND = ((180, 172), (214, 168))      # the forager's walk (lib/resident-routes.ts): kept open

# ---- height: the shelf at z 32 under the Hollow (cliff core Plan.mound boxes: the top as seen) -----
# masses that step forward and back by whole cells (Matt, 13:37: "the structure of the terrain in
# the old version is much better"): outcrop columns (x 24..48, 104..128, 184..208), recesses, and a
# bay (x 64..104) whose back face the brook falls down into its pool; the east end at x 264
MOUNDS = [(32, -8, -48, 24, 64), (32, 24, -48, 48, 80), (32, 48, -48, 64, 64), (32, 64, -48, 104, 40),
          (32, 104, -48, 128, 72), (32, 128, -48, 184, 48), (32, 184, -48, 208, 64), (32, 208, -48, 240, 48),
          (32, 240, -48, 264, 56)]
SPUR_Z = 32

# ---- water: source, brook, fall, pools, stream ---------------------------------------------------
# reaches (x0, x1, y0, y1): straight within a cell run, moving only at cell lines, 1.5 to 2.5
# cells wide; corners rounded at texel radius (terrain.WATER_ROUND)
BROOK = [(78, 92, -48, 16), (76, 90, 16, 48)]                  # on the shelf, from the Hollow's falls
LOW_BROOK = [(76, 90, 84, 136), (70, 84, 136, 192), (72, 88, 192, 240), (64, 78, 240, 276)]
POND = (48, 268, 100, 306)        # the spring pool, where the brook turns east
STREAM_X0 = 92
STREAM_MATCH = 304    # from here east the garden's own rows
STILL = [POND]        # still water: glints and lapping, no current (animate.water)

# ---- paths: whole cells (x0, y0, x1, y1), rounded corners; every one ends somewhere ----------------
PATHS = [
    (88, 448, 320, 464),      # the lane: the garden's orchard walk on the same rows, to the circle
    (120, 312, 136, 456),     # south of the footbridge
    (120, 176, 136, 288),     # north of it, to the glade
    (112, 168, 144, 184),     # the path's end widening into the glade
    (88, 312, 120, 328),      # the spur to the pool seat (the spring stand)
    (80, 432, 96, 456),       # into the stone circle
]
BRIDGE = (118, 138)           # the footbridge's x span over the stream (the north path's line)

# ---- places --------------------------------------------------------------------------------------
GLADE = (100, 100, 196, 200)      # sunlit grass round the hollow oak (an organic patch)
RING = (40, 392, 120, 440)        # the stone circle's trodden earth ring
RING_IN = (56, 400, 104, 432)     # its grass
FAIRY = (158, 150, 16, 8)         # the fairy ring of toadstools (centre, radii)
SUN = [(108, 108, 188, 192), (196, 470, 236, 494)]   # sun pools (boxes): the glade, one on the lane
SEAT = (40, 312, 96, 336)         # the cosy corner by the spring pool (kept clear of trees)

# ---- objects: (id, kind, foot x, foot y, params) ---------------------------------------------------
OBJECTS = [
    # the glade: the hollow oak, a stump
    ('oak', 'veteran_oak', 150, 114, dict(seed=3)),
    ('stump-1', 'stump', 180, 198, dict(seed=5)),
    # the pool seat: a stone seat, a lantern on a post, a mossy stone
    ('seat', 'stone_seat', 66, 326, dict(seed=7)),
    ('lantern', 'lantern_post', 90, 322, dict(seed=8, side=-1)),
    ('stone-p', 'mossy_stone', 110, 282, dict(seed=9, w=12, h=8)),
    # the forester's yard: a woodpile under a lean-to, a chopping block with an axe
    ('woodpile', 'woodpile', 216, 148, dict(seed=11)),
    ('block', 'chopping_block', 188, 156, dict(seed=12)),
    # the stone circle: seven standing stones on the ring
    ('stone-1', 'standing_stone', 66, 396, dict(seed=31, h=30, w=16)),
    ('stone-2', 'standing_stone', 96, 398, dict(seed=32, h=26, w=15)),
    ('stone-3', 'standing_stone', 116, 418, dict(seed=33, h=20, w=14)),
    ('stone-4', 'standing_stone', 104, 440, dict(seed=34, h=28, w=16)),
    ('stone-5', 'standing_stone', 54, 440, dict(seed=35, h=30, w=16)),
    ('stone-6', 'standing_stone', 40, 420, dict(seed=36, h=20, w=14)),
    ('stone-7', 'standing_stone', 44, 400, dict(seed=37, h=22, w=14)),
    # the footbridge over the stream
    ('bridge', 'footbridge', 128, 314, dict(seed=13)),
    # a fallen log by the lane
    ('log-1', 'log', 252, 438, dict(seed=14, length=44)),
]

# ---- the wood: belts and clumps (library: screen.scatter) ------------------------------------------
# (box x0, y0, x1, y1 in world px, spacing in world px, kind weights, tier z the feet stand on)
TREE_MIX = {'oak': 3, 'beech': 2, 'pine': 3, 'birch': 2}
BELTS = [
    ((-14, 4, 268, 52), 15, {'pine': 3, 'oak': 2, 'beech': 2, 'birch': 1}, 32),   # the shelf's wood
    ((268, 6, 330, 110), 16, TREE_MIX, 0),                                        # its east end
    ((-14, 104, 58, 270), 15, TREE_MIX, 0),                                       # the west belt
    ((-14, 340, 34, 392), 15, TREE_MIX, 0),
    ((-14, 470, 110, 590), 15, TREE_MIX, 0),                                      # the south belt, west
    ((236, 486, 334, 590), 15, TREE_MIX, 0),                                      # and east of the gap
    ((232, 112, 334, 268), 16, TREE_MIX, 0),                                      # the clump east of the yard
    ((150, 214, 232, 272), 18, {'oak': 2, 'birch': 2, 'beech': 1}, 0),           # a clump north of the stream
    ((196, 334, 334, 426), 17, TREE_MIX, 0),                                      # the south-east clump
]
UNDER = {'bush': 3, 'bramble': 2, 'holly': 1, 'sapling': 2}    # undergrowth at the belts' edges
# open ground the ports need, and the places, kept clear of tree feet
KEEP_OPEN = [(288, 436, 330, 476), (112, 500, 236, 590), (40, 384, 124, 452), (92, 296, 140, 334)]

DRESS_EVERY = 26     # world px between dressing clumps on open floor (Matt, 13:37: no empty lawn)
FERNS = [(26, 286), (110, 292), (150, 120), (196, 200), (236, 284), (8, 380), (36, 456), (122, 480), (244, 392),
         (292, 280), (176, 548), (284, 432), (60, 520), (196, 116), (96, 96), (58, 110), (110, 244), (100, 210)]
FLOWERS = [(30, 346, 'white', 4), (84, 342, 'yellow', 3), (120, 136, 'white', 5), (178, 128, 'violet', 3),
           (80, 424, 'white', 3), (60, 404, 'yellow', 3), (216, 300, 'blue', 3), (164, 462, 'yellow', 3),
           (196, 486, 'violet', 3), (176, 222, 'white', 3), (104, 190, 'yellow', 3)]
MUSHROOMS = [(184, 204), (36, 352), (110, 452), (268, 414), (206, 160)]


# ---- the stream's line (the garden's own, garden_meadow.stream_centre, so the seam matches) -------
def stream_centre(x):
    import garden_meadow as meadow
    return meadow.stream_centre(x - meadow.W)


def stream_half(x):
    """Out of the spring pool at the half-width of the brook (8), widening to the garden
    stream's half-width (9, with its own slow wobble) by x 216."""
    import garden_meadow as meadow
    from pixel import smooth_noise
    full = 9 + (smooth_noise(x - meadow.W, 0, 13, 91) - 0.5) * 2.4
    t = min(1.0, max(0.0, (x - STREAM_X0) / 124))
    return full * t + 7 * (1 - t)
