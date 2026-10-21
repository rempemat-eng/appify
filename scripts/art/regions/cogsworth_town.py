"""Cogsworth, the town: its ground, walls, water, ways and buildings, painted from the plan.

Lane H (Claude H). The plan is cogsworth_plan.py (the brief as data, PR #176); this paints the
town's box (704 x 960 at world 7624, 1968) from it with the kits, so every surface is a kit's:

- the city kit (Claude C, #169, on the coast kit #162): setts, flagstones, kerbs, brick
  retaining walls, railings, and the coast kit's dressed masonry, stairs and ramps for the
  quay and canal walls; the house kits (#121): every front, in Cogsworth's brick and iron;
- water drawn here in the house style: the Cog fast and dark, streaked with the flow; the
  Millrace quick in its stone leat; the canal and its basin still, with the walls' dark
  reflection along them; the lock's chamber a step lower than the canal;
- the town's own ground (what no kit has): cinder lanes and the gasworks' yard, the railway
  (ballast, sleepers, rails, the platform's coping), the brick towpath, the allotments.

The soft grid (verticality.md, eastward-edges.md) comes from the plan's tiers: the cells
are laid by the coast kit's autotiler (`lattice`) into a Relief with tops at 0 (the Cog),
16 (the canal and the leat, half a tier down), 32 (the street) and 64 (the bench and Gasworks
Hill); every south face hangs as tall as its drop, the side bands are 5 px, every tier
throws its 8 px shadow. Biome: city masonry (Matt, 21 Oct 10:08: each biome draws its own
edges on one grammar): brick for the railway cutting and the hill, dressed stone for the
water's walls.

Nothing in the game reads this yet: `chunk()` returns the town as a world-canvas Chunk (its
ground, blocked pixels, tiers, stands, areas), which the region's painter registers once
Claude A has said how a v5 chunk joins the build.

    python3 scripts/art/regions/cogsworth_town.py [OUT_DIR]
writes OUT_DIR/town.png (1x), town-2x.png (with residents for scale), town-night.png,
compare.png (crops beside Eastward's town screens at the same character height, when the
screenshots are in REF_DIR) and the buildings' heights and logic; `--audit` also runs the
world audit on the town as a chunk (audit-heat.png and the red cells by check). Default OUT_DIR: napattack-cogsworth-town in the system's temp
folder, never the repository.
"""
from __future__ import annotations

import os
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ART)

import cogsworth_plan as plan  # noqa: E402
import coast_kit as ck  # noqa: E402
import city_kit as cy  # noqa: E402
from coast_kit import (IDX, Plot, Relief, lattice, hash01, fbm, shift, stamp, base, texture,  # noqa: E402
                       SMALL, DOMINOES, paste, setts, masonry, stair, ramp_along, stepped_tread, bands,
                       tier_shadows, cast, _from_canvas, Sprite)

W, H = plan.TOWN_W, plan.TOWN_H
GRID = 8
E_TOWN = [0, 16, 32, 64]            # the tops: the Cog, canal and leat, the street, the bench and hill
WATER = ('cog', 'race', 'canal', 'lock')


# --- the plan on the grid -----------------------------------------------------------------------
def kind_cells():
    """The plan's ground at 8 px cells: tier and kind of every cell (bridges left out: they are
    decks painted over the water)."""
    rows, cols = H // GRID, W // GRID
    C = np.zeros((rows, cols), np.int16)
    K = np.full((rows, cols), '', object)
    for gid, k, t, poly, wk in plan.GROUND:
        m = plan._poly_mask(poly, W, H, GRID)
        C[m], K[m] = t, k
    return C, K


def kind_pixels(K, T):
    """Each pixel's ground kind: the cell's kind, followed to the lattice's stepped outline
    (where the autotiler moved a corner to the next tier, the kind of a neighbouring cell on
    that tier is taken)."""
    yy, xx = np.mgrid[0:H, 0:W]
    k = K[np.clip(yy // GRID, 0, K.shape[0] - 1), np.clip(xx // GRID, 0, K.shape[1] - 1)]
    return k


# --- water ------------------------------------------------------------------------------------
def cog_water(p: Plot, m, seed=0, along='y'):
    """The Cog: fast, dark water off the coal hills in soft patches stretched along its flow,
    darker against its walls, with sparse strokes of light and foam lying with the current.
    Returns the mask."""
    m = np.asarray(m, bool)
    d = ck.dist_to(~m, 40)
    water_base(p, m, seed + 9, 'fast', BASE_SCALE['fast'], (2.5, 0.5) if along == 'y' else (0.5, 2.5))
    under = m & (d <= 3)
    p.step(under, -1, lo=0)
    water_marks(p, m, seed + 5, 'fast', along, every=8, share=0.45, lmin=3, thick=1)
    ck.despeckle(p, m, 3)
    p.wet |= m
    p.hazard |= m
    p.walk &= ~m
    p.solid &= ~m
    return m


def still_water(p: Plot, m, seed=0):
    """The canal and the basin: still water in soft patches, the north wall's dark reflection
    in the first rows under it, and sparse ripple strokes (Matt, 21 Oct 10:52: calm, clean
    planes, as Eastward's)."""
    m = np.asarray(m, bool)
    water_base(p, m, seed + 9, 'still', BASE_SCALE['still'], (0.6, 1.8))
    north = m & ~shift(m, 0, 3, True)          # the first rows under the north wall: its reflection
    p.put(north, 'water_cool', 1)
    water_marks(p, m, seed + 5, 'still', 'x', every=9, share=0.35, lmin=3, thick=1)
    ck.despeckle(p, m, 3)
    p.wet |= m
    p.hazard |= m
    p.walk &= ~m
    p.solid &= ~m
    return m


BASE_SCALE = {'still': 32.0, 'fast': 48.0}
WATER_BASE = {
    'still': [('water_cool', 1), ('water_cool', 2), ('water', 2), ('water_warm', 2), ('water', 3), ('lagoon_cool', 2)],
    'fast': [('water_cool', 1), ('water', 1), ('water_cool', 2), ('water', 2), ('water_warm', 2), ('water_cool', 3)],
}


def water_base(p: Plot, m, seed=0, kind='still', scale=11.0, stretch=(1.0, 1.0)):
    """The water's body: soft patches of depth and of the sky's colour in it, six tones of the
    water ramps laid by a slow noise (stretched along the flow), large and calm, so the marks
    on top read as marks."""
    m = np.asarray(m, bool)
    cols = WATER_BASE[kind]
    n = fbm(p.x * stretch[0], p.y * stretch[1], scale, seed)
    lo, hi = np.quantile(n[m], 0.03), np.quantile(n[m], 0.97)
    k = np.clip(((n - lo) / max(1e-6, hi - lo) * len(cols)).astype(int), 0, len(cols) - 1)
    fam = np.array([IDX[c[0]] for c in cols])[k]
    tone = np.array([c[1] for c in cols])[k]
    p.f[m], p.t[m] = fam[m], tone[m]


WATER_MARKS = {
    # (ramp, tone) the marks on water take: light caught on ripples, the sky's reflection, the
    # dark under each ripple, a glint, a drowned leaf; chosen per kind of water
    'still': [('water', 3), ('water', 4), ('water_warm', 3), ('water_warm', 4), ('water_cool', 0), ('water_cool', 3),
              ('sky_cool', 4), ('sky', 4), ('water', 1), ('lagoon_cool', 3), ('water_cool', 4), ('leaf_cool', 2),
              ('sky_cool', 3), ('lagoon', 3), ('water_warm', 1), ('dusk_cool', 2), ('water', 0), ('sky', 3)],
    'fast': [('water', 3), ('water', 4), ('water_cool', 3), ('water_cool', 4), ('snow_cool', 4), ('snow_cool', 3),
             ('water', 0), ('water_cool', 0), ('water_warm', 3), ('sky_cool', 4), ('water_warm', 1), ('earth_cool', 1),
             ('water_warm', 4), ('snow', 4), ('sky_cool', 3), ('lagoon_cool', 3), ('dusk_cool', 1), ('stone_cool', 2)],
}


def water_marks(p: Plot, m, seed=0, kind='still', along='x', every=4, share=0.85, lmin=2, lspan=4, thick=1):
    """The marks that make water read at Eastward's detail: one small stroke (2 to 5 px,
    lying along the flow, or across a still surface as ripples do) on a 4 px lattice cell,
    each a tone or a sibling of the water round it, a dark row under the light ones; never a
    single pixel. They sit on the calm planes laid first, so the water stays one surface."""
    m = np.asarray(m, bool)
    inner = m & (ck.dist_to(~m, 6) >= 2)
    cols = WATER_MARKS[kind]
    gy, gx = p.y // every, p.x // every
    on = hash01(gx, gy, seed) < share
    pick = (hash01(gx, gy, seed + 1) * len(cols)).astype(int)
    ln = lmin + (hash01(gx, gy, seed + 2) * lspan).astype(int)
    ox = (hash01(gx, gy, seed + 3) * every).astype(int)
    oy = (hash01(gx, gy, seed + 4) * every).astype(int)
    u = (p.x - gx * every - ox) if along == 'x' else (p.y - gy * every - oy)
    v = (p.y - gy * every - oy) if along == 'x' else (p.x - gx * every - ox)
    mark = inner & on & (u >= 0) & (u < ln) & (v >= 0) & (v < thick)
    fam = np.array([IDX[c[0]] for c in cols])[pick]
    tone = np.array([c[1] for c in cols])[pick]
    p.f[mark], p.t[mark] = fam[mark], tone[mark]
    under = shift(mark, 0, 1, False) & inner & ~mark & (tone >= 3) if along == 'x' else \
        shift(mark, 1, 0, False) & inner & ~mark & (tone >= 3)
    p.step(under, -1, lo=0)


# --- the town's own ground ---------------------------------------------------------------------
def cinder(p: Plot, m, seed=0):
    """Cinder and packed earth, the coal town's lanes and yards: dark ash and earth in calm
    patches, clinker in small clusters, a cart's ruts worn paler, weeds where feet don't go."""
    m = np.asarray(m, bool)
    base(p, m, [('earth_cool', 0.7), ('stone_cool', 0.3)], seed, 26, tone=3, light=0.82, dark=0.14)
    texture(p, m, seed + 1, swaps=0.02, ups=0.006, downs=0.008, shapes=SMALL)
    clinker = m & (fbm(p.x, p.y, 30, seed + 2) > 0.7)
    stamp(p, clinker, 0.03, seed + 3, SMALL, ramp='soot', tone=2, same_family=False)
    edge = m & (ck.dist_to(~m, 8) <= 3)
    stamp(p, edge & (fbm(p.x, p.y, 20, seed + 4) > 0.55), 0.08, seed + 5, SMALL, ramp='grass_cool', same_family=False)
    p.walk |= m & ~p.hazard
    p.solid &= ~m


def heath(p: Plot, m, seed=0):
    """The coal-hill bench: rough grass gone dark and sooty, tussocks, patches of heather out of
    flower (a dull plum, never pink), bare peat where the path wears it; calm, so the trees and
    spoil standing on it read."""
    m = np.asarray(m, bool)
    base(p, m, [('grass_cool', 0.55), ('leaf_cool', 0.25), ('grass', 0.2)], seed, 12, tone=2, light=0.7, dark=0.3)
    texture(p, m, seed + 1, swaps=0.08, ups=0.02, downs=0.02)
    heather = m & (fbm(p.x, p.y, 18, seed + 2) > 0.62)
    stamp(p, heather, 0.18, seed + 3, SMALL, ramp='dusk_cool', tone=2, same_family=False)
    peat = m & (fbm(p.x, p.y, 24, seed + 4) < 0.22)
    base(p, peat, [('earth_cool', 0.7), ('soot', 0.3)], seed + 5, 6, tone=2)
    stamp(p, m & ~peat, 0.03, seed + 6, ck.SMALL, ramp='grass', tone=3, same_family=False)
    p.walk |= m & ~p.hazard


def rails(p: Plot, m, seed=0, gauge=12):
    """A railway along x: ballast (grey-brown stone in small clusters), timber sleepers every
    6 px lit on top, two rails polished on top with their shadow side, a second track where
    the bed is wide enough."""
    m = np.asarray(m, bool)
    base(p, m, [('stone_cool', 0.5), ('earth_cool', 0.3), ('slate', 0.2)], seed, 6, tone=2, light=0.7, dark=0.3)
    stamp(p, m, 0.12, seed + 1, SMALL, dt=1)
    stamp(p, m, 0.08, seed + 2, DOMINOES, dt=-1)
    ys = np.nonzero(m.any(1))[0]
    if not len(ys):
        return
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    tracks = [y0 + 6] if y1 - y0 < 26 else [y0 + 4, y0 + 18]
    for ty in tracks:
        sl = m & (p.y >= ty - 2) & (p.y < ty + gauge + 3)
        sleeper = sl & (((p.x + int(hash01(ty, 0, seed) * 6)) % 6) < 3)
        p.put(sleeper, 'timber_cool', 2)
        p.put(sleeper & (p.y == ty - 2), 'timber', 3)
        p.put(sleeper & (p.y == ty + gauge + 2), 'timber_cool', 1)
        for ry in (ty, ty + gauge):
            p.put(m & (p.y == ry), 'iron', 4)
            p.put(m & (p.y == ry + 1), 'iron', 1)
            p.put(m & (p.y == ry) & (hash01(p.x // 12, ry, seed + 3) < 0.3), 'iron_cool', 5)
    p.walk &= ~m
    return tracks


def platform(p: Plot, m, seed=0):
    """The platform: flagstones with a coping of long pale stones along the track edge (its
    nose lit, a dark row under it where it overhangs the ballast)."""
    m = np.asarray(m, bool)
    cy.flags(p, m, seed, course=6, ramps=('ashlar', 'stone_warm', 'ashlar_cool', 'concrete_warm'))
    north = m & ~shift(m, 0, 4, True)
    p.put(north, 'ashlar_warm', 4)
    p.put(north & ~shift(m, 0, 1, True), 'ashlar_warm', 5)
    p.put(north & (((p.x + 7) // 24) != ((p.x + 8) // 24)), 'ashlar', 2)
    under = shift(north & ~shift(north, 0, -1, False), 0, 1, False) & ~m
    p.step(under & ~p.solid, -1, lo=0)
    p.walk |= m


def towpath(p: Plot, m, seed=0):
    """The towpath: blue engineering bricks on edge in courses of 4, worn in a band where the
    horse walks, a ridge of grass along the hedge side."""
    m = np.asarray(m, bool)
    cy.flags(p, m, seed, course=4, ramps=('slate', 'iron_warm', 'slate_cool', 'stone_cool'))
    worn = m & (fbm(p.x, p.y, 20, seed + 1) > 0.55)
    p.step(worn & (p.t < 4), 1)
    p.walk |= m


def allotments(p: Plot, m, seed=0):
    """Allotments: beds of dug earth in rows (leeks, cabbages, beans on canes), grass paths
    between them, a water butt and a shed at the end."""
    m = np.asarray(m, bool)
    base(p, m, [('grass', 0.5), ('grass_cool', 0.5)], seed, 10, tone=3)
    texture(p, m, seed + 1, swaps=0.08)
    xs = np.nonzero(m.any(0))[0]
    if not len(xs):
        return
    x0 = int(xs.min())
    bed = m & (((p.x - x0) % 40) >= 4) & (((p.x - x0) % 40) < 34) & (ck.dist_to(~m, 8) >= 3)
    base(p, bed, [('earth', 0.6), ('earth_warm', 0.4)], seed + 2, 6, tone=2)
    rows_ = bed & ((p.y % 6) == 0)
    p.step(rows_, 1)
    plant = bed & ((p.y % 6) == 3) & (hash01(p.x // 3, p.y // 6, seed + 3) < 0.55)
    crop = (hash01((p.x - x0) // 40, 0, seed + 4) * 3).astype(int)
    p.put(plant & (crop == 0), 'leaf', 3)
    p.put(plant & (crop == 1), 'leaf_cool', 4)
    p.put(plant & (crop == 2), 'grass_warm', 4)
    p.put(shift(plant, 0, 1, False) & bed & ~plant, 'leaf_cool', 2)
    p.walk |= m & ~bed


GROUND_PAINT = {
    'cinder': cinder, 'yard': lambda p, m, s=0: cinder(p, m, s + 50), 'heath': heath, 'setts': setts,
    'flags': lambda p, m, s=0: cy.flags(p, m, s), 'platform': platform, 'towpath': towpath,
    'allotment': allotments, 'quay': lambda p, m, s=0: setts(p, m, s, ramps=('stone', 'stone_cool', 'slate', 'stone_warm'), course=5),
}


def girder_bridge(p: Plot, x0, x1, y0, y1, seed=0):
    """The railway over the Cog: a deck of sleepers and rails between two plate girders,
    each girder a lit top flange, a web of riveted plates with stiffeners every 8 px, a dark
    bottom flange; its shadow on the water down and to the right."""
    box = (p.x >= x0) & (p.x < x1) & (p.y >= y0) & (p.y < y1)
    wet = p.wet.copy()
    cast(p, shift(box, 3, 6, False) & ~box & wet, 2)
    p.put(box, 'timber_cool', 2)
    sl = box & ((p.x % 6) < 3)
    p.put(sl, 'timber', 3)
    for gy in (y0, y1 - 6):
        g = box & (p.y >= gy) & (p.y < gy + 6)
        p.put(g, 'iron_cool', 2)
        p.put(g & (p.y == gy), 'iron', 4)
        p.put(g & (p.y == gy + 5), 'iron_cool', 0)
        p.put(g & (((p.x - x0) % 8) == 0) & (p.y > gy) & (p.y < gy + 5), 'iron', 3)
        p.put(g & (p.y == gy + 1) & (((p.x - x0) % 3) == 0), 'iron', 5)
    for ry in (y0 + 10, y0 + 22):
        p.put(box & (p.y == ry), 'iron', 4)
        p.put(box & (p.y == ry + 1), 'iron', 1)
    p.wet &= ~box
    p.hazard |= box
    p.walk &= ~box
    p.solid |= box


def _rows(R, y0, y1):
    """A view of the Relief whose faces are only those between rows y0 and y1, so a stair or
    ramp is cut through the one face the plan meant."""
    import copy
    Rw = copy.copy(R)
    rows = np.zeros(R.face.shape, bool)
    rows[max(0, y0):max(0, y1)] = True
    Rw.face = R.face & rows
    return Rw


# --- buildings ---------------------------------------------------------------------------------
# Each building's front, laid out as a house-kits LAYOUT (#121) at its own width: the kit's own
# walls, roofs, doors, windows and dressing, so the wide works and the station are the same
# brick and iron as the street's houses. Doors stand where the plan puts them (its door x is
# the door's middle); w and the storeys set the picture, which stands on the plan's foot line.
def _door(x_mid, v=0, x0=0):
    w = 22 if v == 3 else 14
    return ('door', v, x_mid - x0 - w // 2)


def layouts():
    B = {b[0]: b for b in plan.BUILDINGS}

    def doors(bid, vs):
        x0 = B[bid][3][0]
        return [_door(dx, v, x0) for (dx, _dy), v in zip(B[bid][5], vs)]
    L = {
        'station': dict(wall='ashlar', roof='slate', shape='ridge', storeys=2, items=[
            *doors('station', (3, 3)), ('clock', 52, 33), ('win', 1, 6, 'up'), ('win', 1, 24, 'up'), ('win', 1, 72, 'up'),
            ('win', 1, 92, 'up'), ('lantern', 8), ('lantern', 60), ('downpipe', 111)]),
        'engine-shed': dict(wall='brick_soot', roof='slate', shape='gable', gable='brick_soot', items=[
            *doors('engine-shed', (3,)), ('win', 2, 4), ('win', 2, 52)]),
        'mill-1': dict(wall='brick_soot', roof='slate', shape='gable', gable='brick_soot', storeys=2, items=[
            ('chimney', 8), *doors('mill-1', (1,)), ('win', 2, 4, 'up'), ('win', 2, 23, 'up'), ('win', 2, 42, 'up'),
            ('win', 0, 6), ('win', 0, 46), ('tie', 31)]),
        'mill-2': dict(wall='brick', roof='slate', shape='gable', gable='brick', storeys=2, items=[
            ('chimney', 46), *doors('mill-2', (1,)), ('win', 2, 4, 'up'), ('win', 2, 23, 'up'), ('win', 2, 42, 'up'),
            ('win', 0, 6), ('win', 0, 46), ('tie', 31)]),
        'workshop-row-1': dict(wall='brick', roof='copper', shape='ridge', storeys=2, items=[
            ('fascia', 0, 34, 30), *doors('workshop-row-1', (1, 2)), ('shopwin', 37, 25), ('win', 0, 6, 'up'), ('win', 0, 30, 'up'),
            ('win', 0, 58, 'up'), ('win', 0, 82, 'up')]),
        'workshop-row-2': dict(wall='stock', roof='slate', shape='ridge', storeys=2, items=[
            ('chimney', 8), ('fascia', 1, 6, 76), ('shopwin', 8, 28), ('shopwin', 40, 16), *doors('workshop-row-2', (0,)),
            ('win', 1, 8, 'up'), ('win', 1, 36, 'up'), ('win', 1, 64, 'up'), ('downpipe', 2)]),
        'warehouse': dict(wall='brick_soot', roof='slate', shape='gable', gable='brick_soot', storeys=2, items=[
            *doors('warehouse', (3,)), ('win', 3, 8), ('win', 3, 64), ('win', 2, 8, 'up'), ('win', 2, 35, 'up'), ('win', 2, 62, 'up'),
            ('tie', 43), ('downpipe', 79)]),
        'retort-house': dict(wall='brick_soot', roof='slate', shape='ridge', items=[
            ('chimney', 10), ('chimney', 88), *doors('retort-house', (3,)), ('win', 2, 56), ('win', 2, 80),
            ('downpipe', 2)]),
        'foundry': dict(wall='brick_soot', roof='slate', shape='ridge', storeys=2, items=[
            ('chimney', 20), ('chimney', 112), *doors('foundry', (3, 3)), ('win', 2, 6, 'up'), ('win', 2, 30, 'up'), ('win', 2, 54, 'up'),
            ('win', 2, 78, 'up'), ('win', 2, 102, 'up'), ('win', 2, 122, 'up'), ('win', 2, 6), ('win', 2, 120), ('win', 2, 66),
            ('tie', 72)]),
        'row-south': dict(wall='brick', roof='slate', shape='ridge', storeys=2, items=[
            ('chimney', 62), ('fascia', 3, 4, 56), ('shopwin', 6, 22), *doors('row-south', (2,)), ('win', 0, 60),
            ('win', 0, 8, 'up'), ('win', 0, 34, 'up'), ('win', 0, 58, 'up')]),
        'terminus': dict(wall='ashlar', roof='glass', shape='ridge', storeys=2, items=[
            *doors('terminus', (3, 3)), ('clock', 96, 33), ('fascia', 3, 76, 56), ('win', 1, 8, 'up'), ('win', 1, 30, 'up'),
            ('win', 1, 150, 'up'), ('win', 1, 172, 'up'), ('win', 1, 10), ('win', 1, 88), ('win', 1, 108),
            ('win', 1, 172), ('lantern', 34), ('lantern', 188), ('downpipe', 2), ('downpipe', 199)]),
        'pump-house': dict(wall='brick', roof='slate', shape='gable', gable='brick', items=[
            ('chimney', 54), *doors('pump-house', (1,)), ('win', 1, 6), ('win', 1, 48)]),
        'allotment-shed': dict(wall='stock', roof='slate', shape='gable', gable='stock', items=[('win', 3, 10)]),
    }
    return L


def gasholder(w=112, seed=0):
    """The gasholder on Gasworks Hill, seen from the south and above: the bell, a riveted
    iron drum (plates in courses of 6, each lit along its top, the drum lit on its west third
    and shaded east), its crown a shallow dome of plates with a lit crescent at the upper
    left and a ring of guide rollers; round it, eight cast-iron columns (the near five in
    front of the drum, the far three behind it), joined at the top and at mid height by
    lattice girders. The bell stands in its tank, a brick ring at the foot, half full: the
    gas is on (a ladder up the side, a valve house's pipe)."""
    h = 112
    sp = Sprite(w, h, w // 2, h - 1)
    cx = w / 2.0
    rx, ry = w / 2.0 - 10, 14.0              # the drum's ellipse
    top_y, foot = 34, h - 14                 # the crown's centre line and the tank's rim
    yy, xx = sp.y, sp.x
    u = (xx - cx) / rx                       # -1 .. 1 across the drum
    inside = np.abs(u) <= 1
    yc = np.sqrt(np.clip(1 - u * u, 0, 1)) * ry
    # the tank: a brick ring at the foot (its near half)
    tank = inside & (yy >= foot - 2 + yc * 0.0) & (yy <= foot + yc + 6) & (yy >= foot + yc - 2)
    ring = tank
    brick_r = ((yy // 3) % 2) * 4
    sp.put(ring, 'clay', 3)
    sp.put(ring & (((xx + brick_r) % 8) == 7), 'clay_cool', 1)
    sp.put(ring & ((yy % 3) == 2), 'clay_cool', 2)
    sp.put(ring & (yy == (foot + yc - 2).astype(int)), 'ashlar_warm', 4)
    # the drum's side: from the crown's front edge down into the tank, painted green
    side = inside & (yy >= top_y + yc) & (yy < foot + yc - 2)
    lam = np.where(u < -0.55, 4, np.where(u < -0.1, 3, np.where(u < 0.45, 2, 1)))
    sp.put(side, 'copper_cool', 2)
    sp.t[side] = lam[side]
    sp.put(side & (u < -0.78), 'copper_cool', 3)
    course = ((yy - (top_y + yc).astype(int)) % 7 == 0) & side
    sp.t[course] = np.clip(sp.t[course] - 1, 0, 5)
    sp.t[shift(course, 0, 1, False) & side & ~course & (u < 0.2)] += 0
    seam = side & ((((xx - cx) / np.sqrt(np.clip(1 - u * u, 0.15, 1))).astype(int) % 16) == 0)
    sp.t[seam] = np.clip(sp.t[seam] - 1, 0, 5)
    riv = side & ((yy - (top_y + yc).astype(int)) % 7 == 2) & ((xx % 6) == 0) & (u < 0.3)
    sp.t[riv] = np.clip(sp.t[riv] + 1, 0, 5)
    rust = side & (fbm(xx, yy, 6, seed + 3) > 0.74) & ((yy - (top_y + yc)) > 6)
    sp.put(rust & (sp.t >= 2), 'clay_cool', 2)
    # the crown: a shallow dome of plates, lit at its upper left
    crown = inside & (yy >= top_y - yc) & (yy < top_y + yc)
    v = (yy - top_y) / ry
    lit = -(u * 0.8) - v * 0.7
    sp.put(crown, 'copper_cool', 2)
    sp.t[crown & (lit > -0.2)] = 3
    sp.t[crown & (lit > 0.45)] = 4
    sp.t[crown & (lit > 0.95)] = 5
    rings = crown & (np.abs(np.sqrt(u * u + v * v) - 0.55) < 0.05)
    sp.t[rings] = np.clip(sp.t[rings] - 1, 0, 5)
    cap = crown & (np.sqrt(u * u + v * v) < 0.12)
    sp.put(cap, 'iron', 3)
    rim = inside & (np.abs(yy - (top_y + yc)) < 1)
    sp.put(rim, 'copper', 4)
    sp.put(inside & (np.abs(yy - (top_y + yc) - 1) < 1), 'copper_cool', 0)
    # the guide frame: columns and two girder rings
    cols = [(-1.0, True), (-0.6, True), (0.0, True), (0.6, True), (1.0, True), (-0.45, False), (0.45, False)]
    ctop = 8
    for cu, near in cols:
        x = int(round(cx + cu * (rx + 6)))
        base_y = int(foot + (np.sqrt(max(0.0, 1 - cu * cu)) * ry if near else -np.sqrt(max(0.0, 1 - cu * cu)) * ry)) + 2
        col = (xx >= x - 2) & (xx < x + 2) & (yy >= ctop) & (yy <= base_y)
        if not near:
            col &= ~sp.m
        sp.put(col, 'iron', 3)
        sp.put(col & (xx == x - 2), 'iron', 4)
        sp.put(col & (xx == x + 1), 'iron', 1)
        sp.put((xx >= x - 3) & (xx < x + 3) & (yy >= ctop - 2) & (yy < ctop), 'iron', 4)   # the capital
    for gy in (ctop + 2, ctop + 40):
        g = (yy >= gy) & (yy < gy + 4) & (xx >= cx - rx - 8) & (xx <= cx + rx + 8)
        lat = g & ((((xx + yy) % 6) == 0) | (((xx - yy) % 6) == 0) | (yy == gy) | (yy == gy + 3))
        sp.put(lat & ~sp.m | (lat & (yy == gy)), 'iron', 3)
        sp.put(lat & (yy == gy), 'iron', 4)
    # a ladder up the drum's west side and the inlet pipe on the east
    lad = (np.abs(xx - (cx - rx * 0.62)) < 2) & (yy > top_y + 6) & (yy < foot + 4)
    sp.put(lad & ((xx == int(cx - rx * 0.62) - 1) | (xx == int(cx - rx * 0.62) + 1)), 'iron', 4)
    sp.put(lad & ((yy % 3) == 0), 'iron', 3)
    pipe = (xx >= int(cx + rx * 0.5)) & (xx < int(cx + rx * 0.5) + 4) & (yy >= foot + 4) & (yy < h - 1)
    sp.put(pipe, 'iron_cool', 2)
    sp.put(pipe & (xx == int(cx + rx * 0.5)), 'iron', 4)
    sp.fx, sp.fy = w // 2, h - 2
    return sp


def fence(p: Plot, x0, x1, y, seed=0):
    """An iron railing along a platform's edge: a top rail lit on its upper edge 7 px above
    the foot, a lower rail, square balusters every 3 px, a post with a ball cap every 24,
    its shadow a tone down on the ground to the south-east."""
    run = (p.x >= x0) & (p.x < x1)
    top, low = run & (p.y == y - 7), run & (p.y == y - 2)
    bal = run & (p.y > y - 7) & (p.y <= y) & (((p.x - x0) % 3) == 0)
    post = run & (p.y >= y - 9) & (p.y <= y) & (((p.x - x0) % 24) < 2)
    shadow = shift(top | bal | post, 2, 2, False) & ~(top | bal | post | low) & ~p.solid
    p.step(shadow & (p.y > y), -1, lo=0)
    p.put(bal, 'iron', 2)
    p.put(low, 'iron', 2)
    p.put(top, 'iron', 4)
    p.put(post, 'iron', 3)
    p.put(post & (((p.x - x0) % 24) == 1), 'iron', 1)
    p.put(post & (p.y == y - 9), 'iron', 5)
    p.walk &= ~(run & (p.y >= y - 2) & (p.y <= y))
    p.solid |= top | bal | post | low


def lock_gates(p: Plot, x0, x1, y0, y1, seed=0):
    """The lock at the canal's west end, where it steps down to the Cog: the chamber between
    two pairs of mitre gates (oak leaves with iron straps, their tops a walkway with a
    handrail), the upper gate holding the canal's water a step above the chamber's (the
    canal's plane lit, the chamber's dark), each leaf with its balance beam lying back onto
    the lockside, white-painted at its end, and a sluice paddle's rack on the upper gate."""
    for gx, step_up in ((x1 - 6, True), (x0 + 2, False)):
        gate = (p.x >= gx) & (p.x < gx + 5) & (p.y >= y0) & (p.y < y1)
        p.put(gate, 'timber', 3)
        p.put(gate & (p.x == gx), 'timber', 4)
        p.put(gate & (p.x == gx + 4), 'timber_cool', 1)
        p.put(gate & ((p.y - y0) % 7 == 3), 'iron', 2)
        mid = (y0 + y1) // 2
        p.put(gate & (np.abs(p.y - mid) < 1), 'timber_cool', 1)          # where the leaves meet
        rail = (p.x == gx + 2) & (p.y >= y0) & (p.y < y1) & ((p.y % 4) == 0)
        p.put(rail, 'iron', 4)
        for by, dy in ((y0 - 2, -1), (y1 + 1, 1)):                       # the balance beams on the lockside
            beam = (p.x >= gx - (16 if step_up else -1)) & (p.x < gx + (5 if step_up else 22)) & (p.y >= by) & (p.y < by + 3)
            p.put(beam, 'timber', 3)
            p.put(beam & (p.y == by), 'timber', 4)
            p.put(beam & (p.y == by + 2), 'timber_cool', 1)
            end = beam & ((p.x < gx - 12) if step_up else (p.x >= gx + 18))
            p.put(end, 'plaster', 4)
            p.walk &= ~beam
            p.solid |= beam
        if step_up:
            rack = (p.x >= gx + 1) & (p.x < gx + 4) & (p.y >= y0 + 4) & (p.y < y0 + 8)
            p.put(rack, 'iron', 3)
            p.put(rack & (p.y == y0 + 4), 'iron', 5)
        p.walk &= ~gate
        p.solid |= gate
        p.wet &= ~gate
    chamber = (p.x >= x0 + 7) & (p.x < x1 - 6) & (p.y >= y0) & (p.y < y1) & p.wet
    p.step(chamber, -1, lo=0)                                            # the chamber's water lies lower, in shade


def kit_sprite(draw, w, h, fx=None, fy=None):
    """A small standing thing drawn with a house-kits piece (a lamp, a bench, a trough...),
    outlined in its edge tones, as a kit Sprite with its foot at (fx, fy)."""
    from pixel import Canvas
    from style_sheet import outline
    cv = Canvas(w + 2, h + 2)
    draw(cv)
    outline(cv)
    sp = _from_canvas(cv)
    sp.fx = fx if fx is not None else (w + 2) // 2
    sp.fy = fy if fy is not None else h
    return sp


def props(p: Plot, seed=0):
    """The town's dressing from the house kits: gas lamps along the streets and the platform,
    benches, troughs, barrels and crates at the doors and on the wharf, where the plan's slots
    and the logic of each place put them."""
    import house_kits as hk
    lamp = kit_sprite(lambda cv: hk.lamp(cv, 4, 34, 30), 10, 34, 5, 33)
    bench = kit_sprite(lambda cv: hk.bench(cv, 1, 13), 24, 13, 12, 12)
    trough = kit_sprite(lambda cv: hk.trough(cv, 1, 8), 22, 8, 11, 7)
    barrel = kit_sprite(lambda cv: hk.barrel(cv, 1, 13), 12, 13, 6, 12)
    crate = kit_sprite(lambda cv: hk.crate(cv, 1, 11), 14, 11, 7, 10)
    things = {'lamp': lamp, 'bench': bench, 'trough': trough, 'barrel': barrel, 'crate': crate}
    placed = []
    for name, x, y in PROPS:
        sp = things[name]
        if p.solid[y, x] or not p.walk[y, x]:
            continue
        paste(p, sp, x, y, shadow=sp.thrown(0.45), block=sp.m & (sp.y >= sp.fy - 2))
        placed.append((name, x, y))
    return placed


def ring(p: Plot, x0, y0, x1, y1, seed=0):
    """The sparring ring in the square: a floor of rolled earth inside a kerb of setts set on
    edge, an octagon (a mason's shape, not a circle), four iron posts with a rope between them
    sagging a pixel, chalk lines worn at its middle."""
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx, ry = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    u, v = np.abs(p.x + 0.5 - cx) / rx, np.abs(p.y + 0.5 - cy) / ry
    octo = (u <= 1) & (v <= 1) & (u + v <= 1.45)
    inner = (u <= 0.9) & (v <= 0.88) & (u + v <= 1.3)
    kerb = octo & ~inner
    p.put(kerb, 'stone', 3)
    p.put(kerb & (p.y < cy), 'stone', 4)
    p.put(kerb & (((p.x + p.y) % 6) == 0), 'stone_cool', 2)
    base(p, inner, [('earth', 0.6), ('earth_warm', 0.4)], seed, 18, tone=3, light=0.8, dark=0.15)
    chalk = inner & (np.abs(p.x + 0.5 - cx) < 1) & (np.abs(p.y + 0.5 - cy) < ry * 0.5)
    p.put(chalk, 'plaster', 4)
    p.walk |= octo
    # four corner posts and the rope between them along the near (south) side
    posts = [(int(cx - rx * 0.62), int(cy - ry * 0.55)), (int(cx + rx * 0.62), int(cy - ry * 0.55)),
             (int(cx - rx * 0.62), int(cy + ry * 0.62)), (int(cx + rx * 0.62), int(cy + ry * 0.62))]
    for (px_, py_) in posts:
        post = (p.x >= px_ - 1) & (p.x <= px_ + 1) & (p.y >= py_ - 12) & (p.y <= py_)
        p.put(post, 'iron', 3)
        p.put(post & (p.x == px_ - 1), 'iron', 4)
        p.put(post & (p.x == px_ + 1), 'iron', 1)
        p.put(post & (p.y == py_ - 12), 'brass', 4)
        p.walk &= ~((p.x >= px_ - 1) & (p.x <= px_ + 1) & (p.y >= py_ - 2) & (p.y <= py_))
        p.solid |= post
    for (a, b) in ((posts[0], posts[1]), (posts[2], posts[3])):
        for xx in range(a[0] + 2, b[0] - 1):
            sag = int(round(2 * np.sin(np.pi * (xx - a[0]) / (b[0] - a[0]))))
            yy = a[1] - 9 + sag
            p.put((p.x == xx) & (p.y == yy), 'cloth' if 'cloth' in IDX else 'sand_warm', 4)


def trees(p: Plot, seed=0):
    """Street trees: a lime at each corner of the square in an iron grille, an alder by the
    leat, birches on the hill's edge; each from the river and meadow kit (#133)."""
    import river_kit as rk
    spots = [('oak', 252, 236, 0.6), ('alder', 92, 448, 1.0), ('birch', 700, 160, 1.0),
             ('birch', 572, 380, 1.0), ('oak', 96, 840, 0.7)]
    for i, (kind, x, y, sc) in enumerate(spots):
        if kind == 'oak':
            sp, sh = rk.oak(seed + i, sc)
        elif kind == 'alder':
            sp, sh = rk.alder(seed + i)
        else:
            sp, sh = rk.birch(seed + i)
        if not p.walk[y, x] and kind != 'alder':
            continue
        if kind == 'oak':
            cy.tree_pit(p, x, y - 1, seed + i)
        paste(p, sp, x, y, shadow=sh, block=sp.m & (sp.y >= sp.fy - 3) & (np.abs(sp.x - sp.fx) <= 3))


# (thing, foot x, foot y) in box px
PROPS = [
    # the platform's lamps and benches, the square's lamps round the clock tower
    ('lamp', 216, 132), ('lamp', 320, 132), ('lamp', 416, 132), ('bench', 268, 130), ('bench', 372, 130),
    ('lamp', 244, 212), ('lamp', 464, 212), ('lamp', 236, 372), ('lamp', 464, 368),
    ('bench', 300, 214), ('trough', 440, 356), ('bench', 412, 214),
    # Workshop Street and the mills' yards
    ('barrel', 194, 276), ('barrel', 204, 280), ('crate', 196, 410), ('lamp', 226, 300), ('lamp', 226, 452),
    # the wharf, the towpath and the bridges' ends
    ('lamp', 330, 532), ('lamp', 392, 532), ('crate', 480, 520), ('crate', 494, 524), ('barrel', 470, 530),
    ('bench', 560, 532), ('lamp', 330, 620), ('lamp', 392, 620), ('barrel', 140, 524),
    # the south: the foundry's lane, the terminus forecourt, the riverside
    ('lamp', 300, 776), ('trough', 304, 764), ('lamp', 476, 790), ('lamp', 700 - 12, 790), ('bench', 560, 792),
    ('lamp', 160, 868), ('lamp', 320, 868), ('lamp', 480, 868), ('lamp', 640, 868), ('bench', 512, 864),
    # the hill
    ('lamp', 572, 176), ('bench', 528, 236), ('barrel', 690, 480), ('crate', 676, 484),
]


def front(bid, lay, cw=None, w=None):
    """The house kits' front() at this building's width, with its layout, in Cogsworth's
    kit; and its logic check (hk.logic) on the way."""
    import house_kits as hk
    if w is None:
        x0, top, x1, foot = {b[0]: b for b in plan.BUILDINGS}[bid][3]
        w = x1 - x0 - 2
    hk.LAYOUT['cogsworth'].append(lay)
    v = len(hk.LAYOUT['cogsworth']) - 1
    old = hk.W_FRONT
    hk.W_FRONT = w
    try:
        cv = hk.front('cogsworth', v, cw)
        faults = hk.logic('cogsworth', v, cv)
    finally:
        hk.W_FRONT = old
        hk.LAYOUT['cogsworth'].pop()
    return cv, faults


def buildings(p: Plot, seed=0):
    """Every building of the plan stood on its foot line, its shadow thrown down and right;
    the whole picture stops a walker (what is behind a building cannot be reached)."""
    L = layouts()
    out = {}
    cws = iter([1, 0, 2, 3, 0, 2, 1, 3, 2, 0, 3, 1, 0, 2, 1])
    for bid, env, kind, (x0, top, x1, foot), side, doors in plan.BUILDINGS:
        if bid not in L:
            continue
        cv, faults = front(bid, L[bid], next(cws))
        sp = _from_canvas(cv)
        sp.fx, sp.fy = 1, sp.h - 2
        sh = sp.thrown(0.4)
        block = sp.m.copy()
        paste(p, sp, x0, foot, shadow=sh, block=block)
        out[bid] = dict(h=sp.h - 2, faults=faults, top=foot - (sp.h - 2))
    return out


# --- the whole town ----------------------------------------------------------------------------
def town(seed=1):
    C, K = kind_cells()
    T = lattice(C, W, H)
    R = Relief(T, E_TOWN)
    p = Plot(W, H, 'stone', 3)
    p.crossing = np.zeros(p.f.shape, bool)
    p.tier = R.seen().astype(np.int8)
    p.walk[:] = False
    kind = kind_pixels(K, T)
    tops = ~R.face
    # water first (it is the lowest and sets the hazard)
    cog = tops & ((kind == 'cog') | (kind == 'lock')) & (T == 0)
    cog_water(p, cog & (p.y < 860), seed + 1, 'y')
    cog_water(p, cog & (p.y >= 860), seed + 2, 'x')
    race = tops & (kind == 'race')
    cog_water(p, race, seed + 3, 'y')
    canal = tops & (kind == 'canal')
    still_water(p, canal, seed + 4)
    # the grounds on their tops
    for i, (k, fn) in enumerate(GROUND_PAINT.items()):
        m = tops & (kind == k) & ~p.hazard
        if m.any():
            fn(p, m, seed + 10 + i)
    rail_m = tops & (kind == 'rails')
    rails(p, rail_m, seed + 30)
    # the walls: brick for the railway cutting and the hill, dressed stone at the water
    wall3 = R.face & (R.kf == 3)
    cy.brick_wall(p, R, wall3, seed + 40)
    wet = p.wet.copy()
    masonry(p, R, R.face & (R.kf == 2) & (R.kb == 0), seed + 41, ramps=('ashlar', 'ashlar_cool', 'stone_cool', 'ashlar_warm'), water=wet)
    masonry(p, R, R.face & (R.kf == 2) & (R.kb == 1), seed + 42, ramps=('ashlar', 'ashlar_warm', 'stone_warm', 'ashlar_cool'), water=wet)
    masonry(p, R, R.face & (R.kf == 1), seed + 43, ramps=('stone', 'stone_cool', 'ashlar_cool'), water=wet)
    bands(p, R, seed + 44, rocks=('ashlar', 'ashlar', 'ashlar_warm', 'ashlar_cool'))
    tier_shadows(p, R)
    # the ways between the tiers, each through its own face (the plan's rect picks the rows)
    ways = np.zeros(p.f.shape, bool)
    for sid, sk, (x0, y0, x1, y1), lo, hi in plan.STAIRS:
        Rw = _rows(R, y0 - 8, y1 + 8)
        if sk == 'stair':
            ways |= stair(p, Rw, x0 - 4, (x1 - x0) - 0, seed + 50 + x0, k=hi)
        else:
            tr = ramp_along(p, Rw, x0, x1, 24, seed + 60, rising='east', kind='stone', k=hi)
            stepped_tread(p, tr, 'east', seed + 61)
            ways |= tr
    # the bridges: decks of setts between parapets over the water
    bridge_face = np.zeros(p.f.shape, bool)
    for bid, (x0, y0, x1, y1), t in plan.BRIDGES:
        deck = (p.x >= x0) & (p.x < x1) & (p.y >= y0) & (p.y < y1)
        setts(p, deck, seed + 70 + x0, ramps=('stone', 'stone_warm', 'ashlar'), course=4)
        horiz = (x1 - x0) > (y1 - y0)
        for side in ((0, 1) if not horiz else (0, 1)):
            if horiz:
                par = deck & ((p.y < y0 + 3) if side == 0 else (p.y >= y1 - 3))
            else:
                par = deck & ((p.x < x0 + 3) if side == 0 else (p.x >= x1 - 3))
            p.put(par, 'ashlar_warm', 4)
            p.put(par & ((p.x == x1 - 1) | (p.y == y1 - 1)), 'ashlar', 2)
            p.walk &= ~par
            p.solid |= par
        p.wet &= ~deck
        p.hazard &= ~deck
        p.walk |= deck & ~p.solid
        # where the deck ends over water, its south face shows: dressed stone down to the water
        # with the dark of the arch under it (as tall as the deck stands over the water)
        below = (p.x >= x0) & (p.x < x1) & (p.y >= y1) & wet
        if below.any():
            drop = E_TOWN[t] - E_TOWN[int(R.seen()[y1 + 1, (x0 + x1) // 2]) if y1 + 1 < H else 0]
            arch = below & (p.y < y1 + max(0, drop))
            mid, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0 - 4
            u = np.abs(p.x + 0.5 - mid) / max(1.0, half)
            hole = arch & (u < 1) & (p.y - y1 >= drop * (0.35 + 0.4 * u * u))
            p.put(arch, 'ashlar', 3)
            p.put(arch & (p.y == y1), 'ashlar_warm', 4)
            p.put(arch & (((p.x - x0) % 9) == 0), 'ashlar_cool', 2)
            p.put(arch & ((p.y - y1) % 5 == 4), 'ashlar_cool', 2)
            p.put(hole, 'water_cool', 0)
            p.put(hole & (p.y == p.y[hole].max() if hole.any() else hole), 'water_cool', 1)
            p.wet &= ~arch
            p.walk &= ~arch
            p.solid |= arch
            bridge_face |= arch
        cast(p, shift(deck, 4, 1, False) & ~deck & wet, 1)
    girder_bridge(p, 0, 84, 72, 104, seed + 75)
    for rid, (x0, y0, x1, y1) in plan.RAILINGS:
        fence(p, x0, x1, y0 + 2, seed + 76)
    built = buildings(p, seed + 80)
    lock_gates(p, 80, 168, 560, 600, seed + 85)
    gx0, gt, gx1, gfoot = {b[0]: b for b in plan.BUILDINGS}['gasholder'][3]
    gh = gasholder(gx1 - gx0, seed + 90)
    paste(p, gh, gx0 + gh.fx, gfoot, shadow=gh.thrown(0.4), block=gh.m.copy())
    # the clock tower on the square: three storeys of ashlar under a copper cap, the clock on
    # its top storey facing the platform's way down, a door at its foot
    tower, tf = front('clock-tower', dict(wall='ashlar', roof='copper', shape='ridge', storeys=3, items=[
        ('door', 0, 9), ('win', 1, 10, 'up'), ('clock', 9, 28)]), 1, w=32)
    tsp = _from_canvas(tower)
    tsp.fx, tsp.fy = tsp.w // 2, tsp.h - 2
    tx0, ty0, tx1, ty1 = {l[0]: l for l in plan.LANDMARKS}['clock-tower'][2]
    paste(p, tsp, (tx0 + tx1) // 2, ty1, shadow=tsp.thrown(0.35), block=tsp.m & (tsp.y >= tsp.fy - 8))
    built['clock-tower'] = dict(h=tsp.h - 2, faults=tf, top=ty1 - tsp.h + 2)
    ring(p, *{l[0]: l for l in plan.LANDMARKS}['ring'][2], seed=seed + 97)
    trees(p, seed + 98)
    placed = props(p, seed + 95)
    return p, dict(R=R, T=T, C=C, kind=kind, ways=ways, built=built, props=placed, bridge_face=bridge_face)


PATHS = ('setts', 'flags', 'platform', 'towpath', 'quay')


def cell_maps(p: Plot, parts):
    """The town in 4 px walk cells: walk (bool), terrain (world_lint's codes: '~' water,
    '=' path, '.' ground, '^' wall or cliff), the tier digits (the chunk's tiers) and the
    tier map in the audit's code ('f' face, 'b' side band, 's' stair or ramp)."""
    R, kind, ways = parts['R'], parts['kind'], parts['ways']
    c = 4
    rows, cols = H // c, W // c

    def frac(m, k=c):
        r_, c_ = H // k, W // k
        return np.asarray(m, float).reshape(r_, k, c_, k).mean((1, 3))

    def up(a):                                   # an 8 px cell map as 4 px cells
        return np.repeat(np.repeat(a, 2, 0), 2, 1)
    walk = frac(p.walk) >= 0.75
    # the terrain on the soft grid: decided per 8 px cell (so every boundary between kinds lies
    # on the grid's lines, as the plan's are), then read at 4 px
    wet8 = frac(p.wet, 8) >= 0.5
    face8 = frac(R.face, 8) >= 0.5
    solid8 = frac(p.solid & ~p.walk, 8) >= 0.5
    path8 = frac(np.isin(kind, PATHS) & p.walk, 8) >= 0.5
    t8 = np.full((H // 8, W // 8), '.', object)
    t8[path8] = '='
    rails8 = frac(kind == 'rails', 8) >= 0.5
    t8[(face8 | solid8 | rails8) & ~(frac(p.walk, 8) >= 0.5)] = '^'
    t8[wet8] = '~'
    terrain = up(t8)
    face = frac(R.face) >= 0.5
    seen = R.seen()
    tier = np.zeros((rows, cols), int)
    for k in range(int(R.T.max()) + 1):
        tier[frac((seen == k)) >= 0.5] = k
    tier[face] = np.maximum(tier[face], 0)
    # bridge decks stand at their own tier over the water
    for bid, (x0, y0, x1, y1), t in plan.BRIDGES:
        tier[y0 // c:y1 // c, x0 // c:x1 // c] = t
        face[y0 // c:y1 // c, x0 // c:x1 // c] = False
    bf = frac(parts['bridge_face']) >= 0.5
    face = face | bf
    # a stair is the face cells across its whole width (the plan's rect), cheeks included
    st = np.zeros((rows, cols), bool)
    for sid, sk, (x0, y0, x1, y1), lo, hi in plan.STAIRS:
        win = np.zeros((rows, cols), bool)
        win[max(0, (y0 - 8) // c):(y1 + 8) // c, x0 // c:x1 // c] = True
        cut = win & face
        full = cut.sum(1) >= 8                      # rows where the flight is its whole width
        cut[~full] = False
        cut[full] = win[full]
        st |= cut
    code = np.array([[str(v) for v in r] for r in tier], object)
    code[face] = 'f'
    for y in range(rows):
        for x in range(cols - 1):
            a, b = tier[y, x], tier[y, x + 1]
            if a != b and not face[y, x] and not face[y, x + 1]:
                hi = x if a > b else x + 1
                code[y, hi] = 'b'
    code[st] = 's'
    walk = walk | st
    return dict(walk=walk, terrain=[''.join(r) for r in terrain], digits=[''.join(str(v) for v in r) for r in tier],
                audit_tiers=[''.join(r) for r in code])


def chunk(p: Plot = None, parts=None):
    """The town as a world-canvas Chunk at its v5 origin (not registered with the build
    yet; region-canvas.md, 'Painting a chunk directly')."""
    import world_canvas as wc
    if p is None:
        p, parts = town()
    M = cell_maps(p, parts)
    ch = wc.Chunk('cogsworth', W, H, kind='region', plane='continent', origin=plan.TOWN_ORIGIN, margin=0)
    rgb = np.asarray(p.image())
    ch.ground = Image.fromarray(np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]), 'RGBA')
    ys, xs = np.nonzero(~p.walk)
    ch.blocked = set(zip(xs.tolist(), ys.tolist()))
    wy, wx = np.nonzero(p.wet)
    ch.water = set(zip(wx.tolist(), wy.tolist()))
    ch.walk = [''.join('.' if v else '#' for v in r) for r in M['walk']]
    ch.terrain = M['terrain']
    ch.tiers = M['digits']
    ch.stands = {k: tuple(v) for k, v in plan.STANDS.items()}
    ch.areas = [dict(a) for a in plan.AREAS]
    ch.audit_tiers = M['audit_tiers']
    return ch


def audit(ch, out=None, ledger=None):
    """The whole-world audit (world_audit.py) on the town alone, as it will run once the
    chunk is in the build: every 32 px cell, with the tier map. Returns the Audit."""
    import world_audit as wa
    R = wa.Region('steam', 'continent', W, H, plan.TOWN_ORIGIN)   # Cogsworth's region id (lib/world-places.ts)
    R.ground = np.asarray(ch.ground).copy()
    codes = {'-': 0, '.': 1, '=': 2, '~': 3, '!': 4, '^': 5}
    R.terrain = np.array([[codes[c] for c in r] for r in ch.terrain], np.uint8)
    R.walk = np.array([[c == '.' for c in r] for r in ch.walk], bool)
    R.tiers = np.array([[ord(c) for c in r] for r in ch.audit_tiers], np.uint8)
    for a in ch.areas:
        R.add_place(wa.Place(a['id'], 'area', 'steam', 'cogsworth_town', tuple(a['rect'])))
    R.stands = list(ch.stands.values())
    root = os.path.abspath(os.path.join(ART, '..', '..'))
    ctx = wa.make_context(root, ledger)
    ctx['source'], ctx['root'] = 'world', root
    A = wa.Audit(R, ctx).run()
    if out:
        wa.heat(A).save(os.path.join(out, 'audit-heat.png'))
    return A


ROOT = os.path.abspath(os.path.join(ART, '..', '..'))
PEOPLE = (('tinkerer', (208, 330)), ('porter', (352, 124)), ('boatwoman', (264, 530)), ('courier', (360, 300)),
          ('stroller', (520, 800)), ('docker', (480, 536)), ('vendor', (300, 778)))


def preview(p, scale=2, people=True):
    """The town at `scale` with residents standing in it for scale (an adult is 25 px)."""
    img = p.image().convert('RGBA')
    if people:
        for name, (x, y) in PEOPLE:
            path = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')  # ledger: compare (residents stand in the preview for scale only)
            if os.path.exists(path):
                r = Image.open(path).convert('RGBA')
                r = r.resize((r.width // 4, r.height // 4), Image.NEAREST)
                img.alpha_composite(r, (x - r.width // 2, y - r.height))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def compare_sheet(p, scale=3, size=(200, 140)):
    """Town crops beside Eastward's town screens (edges and the soft grid are compared with
    Eastward only, Matt 21 Oct 09:23), all at an adult of 25 px; the screenshots come from a
    local REF_DIR (city_kit.REFS) and are never committed."""
    ours = preview(p, 1)
    crops = [('ours: the platform, the square and the clock tower', ours.crop((200, 100, 400, 240))),
             ('ours: workshops on the wharf, the canal and its bridges', ours.crop((220, 400, 420, 540))),
             ('ours: the lock, the Millrace and the Cog', ours.crop((40, 460, 240, 600))),
             ('ours: the terminus, the pump house and the riverside quay', ours.crop((420, 700, 620, 840)))]
    refs = []
    for (name, url, box, adult) in cy.REFS:
        im = ck.ref_image(url, box, adult)
        if im is not None:
            refs.append((name, im.crop((0, 0, min(im.width, size[0]), min(im.height, size[1])))))
    rows = max(len(crops), len(refs))
    cw, chh = size[0] * scale + 16, size[1] * scale + 30
    sheet = Image.new('RGB', (2 * cw + 16, rows * chh + 40), (46, 40, 52))
    ck._label(sheet, 'Cogsworth (left) and Eastward (right), all at an adult of 25 px, shown at 3x', (10, 10), (250, 214, 140))
    for i, (name, im) in enumerate(crops):
        sheet.paste(im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST), (10, 36 + i * chh))
        ck._label(sheet, name, (10, 36 + i * chh + im.height * scale + 2))
    for i, (name, im) in enumerate(refs):
        sheet.paste(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (cw + 16, 36 + i * chh))
        ck._label(sheet, name, (cw + 16, 36 + i * chh + im.height * scale + 2))
    return sheet


def night(img):
    a = np.asarray(img.convert('RGB')).astype(np.float32) * np.array([0.42, 0.45, 0.68])
    return Image.fromarray(a.astype(np.uint8))


def main(argv):
    argv = [a for a in argv if not a.startswith('--')]
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-cogsworth-town')
    os.makedirs(out, exist_ok=True)
    p, parts = town()
    p.image().save(os.path.join(out, 'town.png'))
    preview(p, 2).save(os.path.join(out, 'town-2x.png'))
    night(p.image()).save(os.path.join(out, 'town-night.png'))
    compare_sheet(p).save(os.path.join(out, 'compare.png'))
    for bid, b in parts['built'].items():
        plan_top = {x[0]: x for x in plan.BUILDINGS}.get(bid, (0, 0, 0, (0, b['top'])))[3][1]
        flag = '' if abs(b['top'] - plan_top) <= 2 else f'  (plan top {plan_top})'
        print(f"  {bid:16s} {b['h']:3d} px tall, top {b['top']}{flag}", '; '.join(b['faults']))
    if '--audit' in sys.argv:
        ch = chunk(p, parts)
        A = audit(ch, out)
        import world_audit as wa
        st = A.status if hasattr(A, 'status') else {}
        worst = A.worst if hasattr(A, 'worst') else None
        if worst is not None:
            t = wa.tally(worst)
            print('audit:', t)
        fails = {}
        for chk, a in st.items():
            n = int((a == wa.RED).sum())
            if n:
                fails[chk] = n
        print('red cells by check:', dict(sorted(fails.items(), key=lambda kv: -kv[1])))
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1:])
