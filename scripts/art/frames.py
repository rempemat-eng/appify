"""Where neighbouring places meet (Codex's connected-world contract, PR #23, and
docs/vision/world-ports.md). Two places that touch are joined only at a declared
opening: the shared edge is closed everywhere else by something you can see, a hedge,
a park wall, a belt of trees, rock shoulders, dune ridges, basalt. Both zones draw
their half of the same boundary from world coordinates, so it reads as one hedge or one
belt of trees across the seam, never as two cut edges.

A frame only covers ground that was open; water, cliffs, buildings and props that
already close an edge stay as drawn. Paths that ran to a closed stretch are a fault the
world lint reports (path-to-nowhere); the fix is in the zone's own drawing."""
import math

import materials
from pixel import noise2, smooth_noise

W, H, CELL = 320, 576, 4
DMAX = 30  # how far into a zone a frame can reach, in art px

M = materials.MATERIALS
FRAMES = {
    # kind: ramp (dark to light), feature spacing, feature radius range, core half-depth, ellipse y factor
    'trees': (M['leaf'], 10, (9, 13), 7, 1.0),
    'willows': (['#1F3328', '#34553A', '#4E7647', '#6E9652', '#9DBC70'], 10, (8, 12), 6, 0.9),
    'firs': (['#13221C', '#1D3428', '#2A4A36', '#3B6244', '#557F55'], 8, (7, 10), 6, 1.15),
    'jungle': (['#0E241A', '#183B25', '#24572F', '#367638', '#5C9C45'], 10, (9, 14), 7, 0.95),
    'rocks': (M['stone'], 8, (6, 10), 5, 0.75),
    'snowrocks': (M['stone'], 8, (6, 10), 5, 0.75),
    'basalt': (['#1B1A20', '#2C2930', '#433D47', '#5E5563', '#7D7383'], 8, (6, 10), 5, 0.75),
    'ash': (M['ash'], 8, (6, 9), 5, 0.75),
    'dunes': (M['desert'][:5], 9, (7, 11), 5, 0.7),
    'hedge': (M['leaf'], 0, (0, 0), 6, 1.0),
    'wall': (M['ashlar'][:5], 0, (0, 0), 5, 1.0),
    'quay': (M['slate'], 0, (0, 0), 5, 1.0),
}
BUILT = {'hedge', 'wall', 'quay'}  # straight, made boundaries: a gatepost either side of the way through
SNOW = M['snow']
MOSS = ['#2C4A2E', '#3F6A3A', '#5C8C46']

# Every shared edge, (west or north zone, east or south zone): the opening along the
# edge (art px from the zone's top or left) and what closes the rest. Codex's spans
# where the drawing allows; docs/vision/world-ports.md records each one that differs
# and why. A pair listed with no opening is closed along its whole length.
PORTS = {
    # the home valley (the garden's own side is closed in lib/region-walk.ts and drawn
    # by garden.py; its neighbours draw their half here)
    ('woodland', 'garden'): ((412, 468), 'trees'),
    ('garden', 'riverside'): ((192, 248), 'willows'),
    ('ridge', 'garden'): ((196, 216), 'trees'),
    ('garden', 'town'): ((144, 176), 'hedge'),
    ('woodland', 'halt'): ((120, 184), 'hedge'),
    ('halt', 'town'): ((268, 324), 'hedge'),
    ('riverside', 'park'): ((136, 192), 'willows'),
    ('town', 'park'): ((272, 328), 'wall'),
    ('town', 'harbour'): ((136, 192), 'wall'),
    ('park', 'headland'): ((112, 168), 'hedge'),
    ('harbour', 'headland'): ((88, 144), 'rocks'),
    # the Frostline Highlands
    ('hollow', 'ridge'): ((144, 200), 'firs'),
    ('hollow', 'woodland'): (None, 'rocks'),
    ('snowmelt', 'hollow'): ((120, 148), 'snowrocks'),
    ('snowmelt', 'saddle'): ((404, 436), 'snowrocks'),
    ('saddle', 'ridge'): ((172, 196), 'snowrocks'),
    ('summit', 'saddle'): ((140, 164), 'snowrocks'),
    # Cogsworth, Neon
    ('junction', 'canal'): ((128, 192), 'wall'),
    ('neon', 'skyport'): ((164, 220), 'quay'),
    # Sunstone Reach
    ('oasis', 'gulch'): ((296, 352), 'dunes'),
    ('gulch', 'scorch'): ((356, 412), 'dunes'),
    ('hearthold', 'scorch'): ((140, 188), 'ash'),
    ('caldera', 'hearthold'): ((104, 152), 'basalt'),
    ('caldera', 'springs'): ((264, 320), 'basalt'),
    # the Tidebloom Isles
    ('rainforest', 'headwaters'): ((224, 280), 'jungle'),
    ('rainforest', 'landing'): ((128, 184), 'jungle'),
    ('headwaters', 'cove'): ((192, 248), 'basalt'),
    ('landing', 'cove'): ((352, 408), 'basalt'),
}


def seams_of(name: str, layout: dict):
    """This zone's shared edges: (other zone, side, span, kind, global seam)."""
    region = next(r for r, zs in layout.items() if name in zs)
    zs = layout[region]
    col, row = zs[name]
    at = {pos: z for z, pos in zs.items()}
    out = []
    for side, (dc, dr) in (('west', (-1, 0)), ('east', (1, 0)), ('north', (0, -1)), ('south', (0, 1))):
        other = at.get((col + dc, row + dr))
        if other is None:
            continue
        pair = (other, name) if side in ('west', 'north') else (name, other)
        assert pair in PORTS, f'{pair[0]} and {pair[1]} touch but no port says how they meet (frames.PORTS)'
        span, kind = PORTS[pair]
        a = zs[pair[0]]
        vertical = side in ('west', 'east')
        out.append({'other': other, 'side': side, 'span': span, 'kind': kind, 'vertical': vertical,
                    'below': (col, row + 1) in at,
                    'seam': (a[0] + 1) * W if vertical else (a[1] + 1) * H,
                    't0': a[1] * H if vertical else a[0] * W, 'pair': pair})
    return region, (col, row), out


def _features(s):
    """The crowns or boulders along a seam, in seam coordinates (t, d, r), the same for
    both zones that draw it."""
    ramp, step, (r0, r1), core, _ = FRAMES[s['kind']]
    if not step:
        return []
    seed = sum(ord(c) for c in s['pair'][0] + s['pair'][1])
    feats = []
    L = H if s['vertical'] else W
    k = 0
    for t in range(-step, L + step, step):
        ct = t + (noise2(k, 1, seed) - 0.5) * step * 0.8
        cd = (noise2(k, 2, seed) - 0.5) * 10
        r = r0 + noise2(k, 3, seed) * (r1 - r0)
        k += 1
        if s['span'] and ct + r + 3 > s['span'][0] and ct - r - 3 < s['span'][1]:
            continue  # the way through stays clear, its sides ragged
        feats.append((ct, cd, r))
    return feats


def _inside(s, feats, t, d):
    ramp, step, (_r0, r1), core, ry = FRAMES[s['kind']]
    if abs(d) > core + 3 and abs(d) > r1 * ry + 6:
        return None
    span = s['span']
    margin = 3 if step else 0
    best = None
    for (ct, cd, r) in feats:
        if abs(t - ct) >= r:
            continue
        dt, dd = t - ct, (d - cd) / ry
        if dt * dt + dd * dd < r * r:
            front = ct if s['vertical'] else cd  # the nearer the viewer, the more on top
            if best is None or front > best[0]:
                best = (front, ((ct, cd), dt, dd, r))
    if best:
        return best[1]
    if span and span[0] - margin <= t < span[1] + margin:
        return None
    wob = (smooth_noise(t, 0, 9, 71) - 0.5) * 3 if step else 0
    if abs(d) < core + wob:
        return (None, 0, 0, core)
    return None


def _post(s, t, d):
    """A gatepost either side of the way through a made boundary."""
    if s['kind'] not in BUILT or not s['span']:
        return False
    a, b = s['span']
    return abs(d) < 7 and (a - 5 <= t < a or b <= t < b + 5)


def _colour(s, feats, gx, gy, t, d, hit, inside):
    kind = s['kind']
    ramp = FRAMES[kind][0]
    # light from the upper left, in world coordinates
    if _post(s, t, d):
        st = M['stone']
        edge = not _post(s, t - 1, d) or not _post(s, t + 1, d) or abs(d) >= 6
        return st[1] if edge else st[3] if (gx + gy) % 5 else st[2]
    near_edge = [inside(t + dt, d + dd) is None for (dt, dd) in ((-1, 0), (1, 0), (0, -1), (0, 1))]
    # which neighbours lie outside, in world directions (t runs along the seam)
    if s['vertical']:
        out_l, out_r, out_u, out_dn = near_edge[2], near_edge[3], near_edge[0], near_edge[1]
    else:
        out_l, out_r, out_u, out_dn = near_edge[0], near_edge[1], near_edge[2], near_edge[3]
    if kind in BUILT:
        return _built(kind, ramp, gx, gy, s, d, out_l, out_r, out_u, out_dn)
    centre, dt, dd, r = hit
    if centre is None:  # the core between features: lower, in shade
        tone = 1 + (noise2(gx // 2, gy // 2, 77) > 0.6)
    else:
        # where on the feature: its upper left catches the light
        if s['vertical']:
            ux, uy = dd, dt
        else:
            ux, uy = dt, dd
        lit = -(ux + uy) / (r * 1.3)
        tone = 1 + int((lit + 1) * 1.6 + noise2(gx, gy, 78) * 0.9)
        tone = max(1, min(len(ramp) - 1, tone))
    if out_r or out_dn:
        return ramp[0]
    if out_l or out_u:
        tone = max(1, tone - 1) if kind in ('rocks', 'snowrocks', 'basalt', 'ash', 'dunes') else tone
    c = ramp[tone]
    if kind == 'snowrocks' and centre is not None:
        uy2 = (dt if s['vertical'] else dd)
        if uy2 < -r * 0.15 and noise2(gx // 2, gy // 2, 79) > 0.25:
            c = SNOW[min(3, 1 + int((-(uy2) / r) * 3))]
    elif kind == 'firs' and centre is not None and tone >= 3 and noise2(gx // 2, gy // 2, 80) > 0.55:
        c = SNOW[2 if tone == 3 else 3]
    elif kind == 'basalt' and centre is not None and noise2(gx // 3, gy // 3, 81) > 0.72:
        c = MOSS[min(2, tone // 2)]
    elif kind in ('trees', 'willows', 'jungle') and tone >= 3 and noise2(gx, gy, 82) > 0.86:
        c = ramp[min(len(ramp) - 1, tone + 1)]
    return c


def _built(kind, ramp, gx, gy, s, d, out_l, out_r, out_u, out_dn):
    if kind == 'hedge':
        # clipped leaves: small clumps, the face at the south catches no sun
        if out_r or out_dn:
            return ramp[0]
        if not s['vertical'] and d >= FRAMES[kind][3] - 3:
            return ramp[1] if (gx // 2 + gy) % 3 else ramp[0]
        clump = noise2(gx // 3, gy // 2, 83)
        tone = 2 + (clump > 0.45) + (clump > 0.8)
        if out_l or out_u:
            tone = min(4, tone + 1)
        return ramp[tone]
    # walls and quays: coursed stones, the cap lit, the south face in shade
    course = 4
    row = gy // course
    off = (row % 2) * 4
    joint = (gx + off) % 9 == 0 or gy % course == 0
    if out_r or out_dn:
        return ramp[0]
    if not s['vertical'] and d >= 0:  # the face below the cap
        return ramp[1] if joint else ramp[2] if noise2((gx + off) // 9, row, 84) > 0.5 else ramp[1]
    if out_l or out_u:
        return ramp[4]
    return ramp[1] if joint else ramp[3] if noise2((gx + off) // 9, row, 85) > 0.4 else ramp[2]


# Props that stand along each kind of boundary, on the side where the zone lies
# (tall ones only where their crown rises inside their own zone: the west side of a
# north-south seam, either side of an east-west one... see _place).
PROPS = {
    'trees': (['tree', 'tree_small', 'bush', 'tree_small'], ['bush', 'bush', 'fern']),
    'willows': (['willow', 'bush', 'tree_small'], ['bush', 'reeds', 'bush']),
    'hedge': ([], ['bush']),
    'wall': ([], []),
    'quay': ([], []),
    'firs': (['snowy_pine', 'pine', 'snowy_pine'], ['scree_small', 'stone']),
    'rocks': (['boulder', 'scree', 'scree_b'], ['stone', 'scree_small', 'bush']),
    'snowrocks': (['scree', 'boulder', 'scree_b', 'snowy_pine'], ['scree_small', 'stone']),
    'jungle': (['tree_fern', 'monstera', 'tree_fern', 'hibiscus'], ['monstera', 'fern', 'hibiscus']),
    'basalt': (['black_rock', 'tree_fern', 'black_rock_small'], ['black_rock_small', 'monstera', 'fern']),
    'ash': (['obsidian', 'charred_snag', 'obsidian_small'], ['obsidian_small', 'obsidian']),
    'dunes': (['sandstone_outcrop', 'desert_scrub', 'sandstone_outcrop_b', 'saguaro_small'],
              ['desert_scrub_b', 'sandstone_outcrop_b', 'desert_scrub']),
}
# where a region only has its own props, what stands in for the ones it lacks
STAND_IN = {'black_rock': 'obsidian', 'black_rock_small': 'obsidian_small', 'tree_fern': 'basalt_columns_low',
            'monstera': 'obsidian_small', 'fern': 'obsidian_small', 'boulder': 'obsidian', 'stone': 'obsidian_small'}


def _place(s, name: str, sprites: dict, allowed, objects, stands, walk) -> list:
    """Props along this zone's side of a seam: (id, key, x, y) in sprite pixels."""
    tall, low = PROPS[s['kind']]
    side = s['side']
    # tall props stand where they rise over their own ground: a north-south seam's
    # either side (they grow upwards, along it), an east-west seam's north side
    pool = (tall or low) if side in ('west', 'east', 'south') else low
    if not pool:
        return []
    seed = sum(ord(c) for c in s['pair'][0] + s['pair'][1]) + (7 if side in ('west', 'north') else 0)
    L = H if s['vertical'] else W
    occupied = [(x, y, x + sprites[k].w, y + sprites[k].h) for (_i, k, x, y) in objects]
    out = []
    t = 4 + int(noise2(0, 9, seed) * 10)
    k = 0
    while t < L:
        key = pool[int(noise2(k, 5, seed) * len(pool)) % len(pool)]
        if allowed is not None and key not in allowed:
            key = STAND_IN.get(key, key)
            if key not in allowed:
                t += 10
                k += 1
                continue
        sp = sprites[key]
        j = int(noise2(k, 6, seed) * 5)
        along = sp.w if not s['vertical'] else max(10, sp.h // 3)
        if s['vertical']:
            foot = t
            x = W - sp.w - j if side == 'east' else j
            y = foot - sp.h
            t0, t1 = y + sp.h - 14, y + sp.h
        else:
            x = t - sp.w // 2
            y = (H - sp.h - j) if side == 'south' else (2 + j)
            t0, t1 = x, x + sp.w
            if side == 'north' and y < 0:
                y = 0
        t += max(8, int(along * (0.7 + noise2(k, 7, seed) * 0.4)))
        k += 1
        span = s['span']
        if span and t1 > span[0] - 8 and t0 < span[1] + 8:
            continue  # the way through stays clear
        if x < 0 or x + sp.w > W or y + sp.h > H or y < 0:
            continue
        if s.get('below') and y + sp.h > H - 52:
            continue  # (the zone below may raise a tall prop over this corner)
        box = (x + 2, y + sp.h - 10, x + sp.w - 2, y + sp.h)
        if any(box[0] < o[2] and box[2] > o[0] and box[1] < o[3] and box[3] > o[1] - 6 for o in occupied):
            continue
        # its foot on ground that was open, away from every stand
        fx0, fx1, fy = (x + 3) // CELL, (x + sp.w - 3) // CELL, (y + sp.h - 2) // CELL
        if not (0 <= fy < len(walk)) or any(walk[fy][c] != '.' for c in range(max(0, fx0), min(len(walk[0]), fx1 + 1))):
            continue
        if any(x - 6 <= sx <= x + sp.w + 6 and y + sp.h - 24 <= sy <= y + sp.h + 10 for (sx, sy) in stands.values()):
            continue
        occupied.append((x, y, x + sp.w, y + sp.h))
        out.append((f'frame-{s["other"]}-{len(out)}', key, x, y))
    return out


def apply(cv, name: str, layout: dict, walk: list[str], is_water) -> set:
    """Draw this zone's half of each boundary it shares and return the ground it closes."""
    region, (col, row), seams = seams_of(name, layout)
    closed = set()
    for s in seams:
        feats = _features(s)

        def inside(t, d, s=s, feats=feats):
            return _inside(s, feats, t, d)

        for i in range(DMAX):
            for j in range(H if s['vertical'] else W):
                if s['side'] == 'west':
                    x, y = i, j
                elif s['side'] == 'east':
                    x, y = W - 1 - i, j
                elif s['side'] == 'north':
                    x, y = j, i
                else:
                    x, y = j, H - 1 - i
                gx, gy = col * W + x, row * H + y
                t = (gy - s['t0']) if s['vertical'] else (gx - s['t0'])
                d = (gx - s['seam']) if s['vertical'] else (gy - s['seam'])
                d += 0.5
                hit = inside(t, d)
                post = _post(s, t, d)
                if hit is None and not post:
                    # a soft shadow cast down and right of the boundary, on open ground
                    if (inside(t - (0 if s['vertical'] else 1), d - (1 if s['vertical'] else 0)) is not None or
                            inside(t - (1 if s['vertical'] else 0), d - (0 if s['vertical'] else 1)) is not None) \
                            and walk[y // CELL][x // CELL] == '.' and not is_water(x, y):
                        r, g, b = cv.get(x, y)[:3]
                        cv.set(x, y, '#%02X%02X%02X' % (int(r * 0.78), int(g * 0.78), int(b * 0.82)))
                    continue
                if walk[y // CELL][x // CELL] != '.' or is_water(x, y):
                    continue
                cv.set(x, y, _colour(s, feats, gx, gy, t, d, hit, inside))
                closed.add((x, y))
    return closed


def check(built: dict, layout: dict):
    """Every port is open on both sides; every other stretch of a shared edge is closed
    on at least one side. The walk grids are the authority."""
    bad = []
    for (a, b), (span, kind) in PORTS.items():
        if a not in built or b not in built:
            continue
        region = next(r for r, zs in layout.items() if a in zs)
        (ca, ra), (cb, rb) = layout[region][a], layout[region][b]
        vertical = cb == ca + 1
        assert vertical or rb == ra + 1, f'{a} and {b} do not touch'
        wa, wb = built[a]['walk'], built[b]['walk']
        n = (H if vertical else W) // CELL
        for k in range(n):
            if vertical:
                oa, ob = wa[k][-1] == '.', wb[k][0] == '.'
            else:
                oa, ob = wa[-1][k] == '.', wb[0][k] == '.'
            p = k * CELL
            if span and span[0] + CELL <= p < span[1] - CELL:
                if not (oa and ob):
                    bad.append(f'{a}|{b}: the way through is shut at {p}')
            elif (not span or p < span[0] or p >= span[1]) and oa and ob:
                bad.append(f'{a}|{b}: open outside the way through at {p}')
    assert not bad, 'ports: ' + '; '.join(bad)


def export() -> dict:
    """The ports for lib/zone-maps.ts (the route checks read them)."""
    return {f'{a}|{b}': {'span': list(span) if span else None, 'frame': kind}
            for (a, b), (span, kind) in PORTS.items()}


def place(name: str, layout: dict, sprites: dict, allowed, objects, stands, walk) -> list:
    """The props standing along every boundary this zone shares."""
    _region, _pos, seams = seams_of(name, layout)
    out = []
    for s in seams:
        out += _place(s, name, sprites, allowed, list(objects) + out, stands, walk)
    return out
