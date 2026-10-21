"""The c-tiles swatch: a summer highland laid only from the 16 px autotiles plus decals.

The map is a plan height grid (16 px cells; heights in tiles: meadow 0, ledge 2, upper tier 4,
summit 6). A cell at plan row p and height h shows its top at screen row p - h; where its
south neighbour is d tiles lower, its face hangs over the d screen rows below. Each height
is laid on its own layer (tops, faces, stairs), lowest first, and each layer throws an 8 px
shadow east onto what lies below it. Decals go on last, by their foot.

    python3 scene.py      writes swatch.png, swatch-3x.png, tileset.png, compare.png,
                          bar.txt (detail_bar numbers)
"""

import numpy as np
from scipy import ndimage as ndi

from .. import ctx
from . import decals as DC
from . import tiles as TL
from ..palette import C, FI, is_fam, step
from ..ctx import D as DEN, TT, P

PLAN = ctx.PLAN
_T = PLAN['terrain']
_W = PLAN['water']


def _cells(v):
    return {tuple(c) for c in v}

# r6 style constants (the 2x kit reads these)
POOL_SOFT = 1.8      # r6: the pool outline's smoothing (world px)
_WS = ctx.BIOME.get('style', {}).get('water', {})
POOL_SOFT_R7 = _WS.get('pool_soft', 3.0)   # r7: the pool's shoreline smoothing for its depth bands and its neck (world px)
POOL_BANDS = [(k, f, t, i) for k, (f, t, i) in enumerate(_WS.get('pool_bands', [['water', 0, 2.2], ['water_cool', 1, 4.2], ['water', 1, 6.2]]))]  # r7: dark bands, inset (world px)
BROOK_HW = tuple(_WS.get('brook_half_width', (2.5, 5.0)))  # r7: the brook's half width breathes between these (5 to 10 world px wide)
BROOK_BANK_RUN = _WS.get('brook_bank_run', 3.0)   # r7: world px per run of the earth bank line (grass breaks it between runs)
BROOK_STONES = tuple(_W.get('brook_stones', ()))   # r7: midstream stones (arc length along the brook, world px; plan data)

T = TT                # a tile in art px at this density (16 world px)
TW = _T['tile']       # a tile in world px
COLS, ROWS = _T['cols'], _T['rows']
MARGIN = _T['margin']   # extra tile rows above the screen for tiers that start above it

# per column: the summit's last screen row (or None), the upper tier's last screen row, ledge rows
COLSPEC = {int(c): tuple(v) for c, v in _T['colspec'].items()}
PLAN_ROWS = ROWS + MARGIN + _T['plan_rows_extra']
POOL = _cells(_W['pool_cells'])
SNOW = _cells(_T['snow_cells'])
SNOW6 = _cells(_T['snow_cells_summit'])
TRAIL = _cells(_T['trail_cells'])
TRAIL_C = {}
FIX = True            # the pilot's logic fixes (always on in the kit)
# the pool drains by a brook that runs south, then east out of the picture
STREAM = _cells(_W['stream_cells'])
# the flights, each 40 world px of treads in a three-cell cut (ledge, then plateau)
STAIRS = [dict(st, cols=tuple(st['cols']), rows=tuple(st['rows'])) for st in _T['stairs']]
STAIR = {(c, r) for st in STAIRS for c in range(st['cols'][0], st['cols'][1] + 1) for r in range(st['rows'][0], st['rows'][1] + 1)}
WET = POOL | STREAM     # cells kept clear of dressing (the brook is drawn by brook2)


def plan():
    """Plan heights hp[p][c] (tiles). Plan row p = screen row + h + MARGIN."""
    hp = np.zeros((PLAN_ROWS, COLS), int)
    for c, (se, ue, L) in COLSPEC.items():
        for p in range(PLAN_ROWS):
            s0 = p - MARGIN   # screen row of a meadow cell at this plan row
            hp[p, c] = 0
        p_summit_end = se + 6 + MARGIN if se is not None else -1
        p_upper_end = ue + 4 + MARGIN
        p_ledge_end = p_upper_end + L
        for p in range(PLAN_ROWS):
            if p <= p_summit_end:
                hp[p, c] = 6
            elif p <= p_upper_end:
                hp[p, c] = 4
            elif p <= p_ledge_end:
                hp[p, c] = 2
            else:
                hp[p, c] = 0
    return hp


def H(hp, p, c):
    p = min(max(p, 0), PLAN_ROWS - 1)
    c = min(max(c, 0), COLS - 1)
    return hp[p, c]


def material(h, c, s):
    return _T['tier_materials'][str(h)]


def build():
    hp = plan()
    SR = ROWS + MARGIN          # screen rows in the canvas (margin above)
    levels = [0, 2, 4, 6]
    occ = {h: {} for h in levels}   # (c, s_canvas) -> ('top', p) | ('face', p, k, d) | ('stair',)
    for p in range(PLAN_ROWS):
        for c in range(COLS):
            h = hp[p, c]
            s = p - h       # canvas row (margin included)
            if 0 <= s < SR:
                occ[h][(c, s)] = ('top', p)
            hs = H(hp, p + 1, c) if p + 1 < PLAN_ROWS else h
            if hs < h:
                d = h - hs
                for k in range(d):
                    ss = s + 1 + k
                    if 0 <= ss < SR:
                        occ[h][(c, ss)] = ('face', p, k, d)
    if FIX:
        for i, st in enumerate(STAIRS):
            for c in range(st['cols'][0], st['cols'][1] + 1):
                for r in range(st['rows'][0], st['rows'][1] + 1):
                    occ[st['h']][(c, r + MARGIN)] = ('stair', i)
    else:
        for (c, s) in STAIR:
            occ[2][(c, s + MARGIN)] = ('stair',)
    # ghosts: a tier's ground carried on under the higher tiers that stand on it (only in
    # columns where that tier exists), so a rounded end of a higher face opens onto the
    # ground it rises from, never onto nothing
    ghosts = {h: {} for h in levels}
    for c in range(COLS):
        have = {h for h in levels if (hp[:, c] == h).any()}
        for p in range(PLAN_ROWS):
            for h in levels:
                if h in have and hp[p, c] > h:
                    s = p - h
                    if 0 <= s < SR and (c, s) not in occ[h]:
                        ghosts[h][(c, s)] = ('ghost', p)
    return hp, occ, ghosts


def end_type(occ, h, c, s, side):
    n = (c + side, s)
    if not (0 <= n[0] < COLS):
        return 'cont'
    me = occ[h].get(n)
    if me and me[0] == 'face':
        return 'cont'
    if me and me[0] == 'stair':
        return 'inner'
    for hh in occ:
        if hh >= h and occ[hh].get(n):
            return 'inner'
    for hh in occ:
        v = occ[hh].get(n)
        if hh < h and v and v[0] in ('face', 'stair'):
            return 'edge'     # a lower face beside: shade the turn, do not open it
    return 'outer'


def ground_beside(occ, h, c, s, side):
    """Is the cell beside at this screen row the open top of a lower tier (so a side band
    may open onto it)?"""
    n = (c + side, s)
    if not (0 <= n[0] < COLS):
        return False
    for hh in occ:
        v = occ[hh].get(n)
        if v and hh >= h:
            return False
        if v and hh < h and v[0] != 'top':
            return False
    return True


def render():
    hp, occ, ghosts = build()
    SR = ROWS + MARGIN
    Hc, Wc = SR * T, COLS * T
    layers = {}
    tops = {}
    for h in sorted(occ):
        lay = np.full((Hc, Wc), -1, np.int32)
        back = np.full((Hc, Wc), -1, np.int32)
        ltop = np.zeros((Hc, Wc), bool)
        lgh = np.zeros((Hc, Wc), bool)
        for (c, s), v in ghosts[h].items():
            p = v[1]
            nb = [[1 if H(hp, p + i, c + j) >= h else 0 for j in (-1, 0, 1)] for i in (-1, 0, 1)]
            t = TL.top(material(h, c, s - MARGIN), nb, c * T, (s - MARGIN) * T)
            lay[s * T:(s + 1) * T, c * T:(c + 1) * T] = t
            if FIX:     # r3: ground under a face is ground (its foot's contact shade falls on it)
                ltop[s * T:(s + 1) * T, c * T:(c + 1) * T] = t >= 0
                lgh[s * T:(s + 1) * T, c * T:(c + 1) * T] = t >= 0
        # tops first
        for (c, s), v in occ[h].items():
            if v[0] != 'top':
                continue
            p = v[1]
            nb = [[1 if H(hp, p + i, c + j) >= h else 0 for j in (-1, 0, 1)] for i in (-1, 0, 1)]
            if FIX and h in (2, 4):
                # logic fix: the stair's head is flush with the ledge floor (no brink across it)
                for j in (-1, 0, 1):
                    if (c + j, s - MARGIN + 1) in STAIR:
                        nb[2][j + 1] = 1
            mat = material(h, c, s - MARGIN)
            wx, wy = c * T, (s - MARGIN) * T
            cw, ce = ground_beside(occ, h, c, s, -1), ground_beside(occ, h, c, s, 1)
            if FIX:
                cw, ce = True, True     # r2: a side band's edge follows its lumps everywhere (no ruled line)
            t = TL.top(mat, nb, wx, wy, cut=(cw, ce))
            back[s * T:(s + 1) * T, c * T:(c + 1) * T] = TL.top(mat, nb, wx, wy, cut=False)
            sc = (c, s - MARGIN)
            if h == 4 and sc in SNOW:
                pass
            if h in (4, 6):
                SN = SNOW if h == 4 else SNOW6
                nb2 = [[1 if (c + j, s - MARGIN + i) in SN else 0 for j in (-1, 0, 1)] for i in (-1, 0, 1)]
                if any(map(any, nb2)):
                    t = TL.over(t, 'snow', nb2, wx, wy)
            if h == 0:
                nb2 = [[1 if ((c + j, s - MARGIN + i) in TRAIL or (FIX and i < 0 and (c + j, s - MARGIN + i) in STAIR
                                                                    and (c + j, s - MARGIN) in TRAIL)) else 0
                         for j in (-1, 0, 1)] for i in (-1, 0, 1)]
                if any(map(any, nb2)):
                    t = TL.over(t, 'trail', nb2, wx, wy)
                nb3 = [[1 if (c + j, s - MARGIN + i) in POOL else 0 for j in (-1, 0, 1)] for i in (-1, 0, 1)]
                if any(map(any, nb3)):
                    t = TL.over(t, 'water', nb3, wx, wy)
            # the foot of a face above (any higher level) gets the contact line and scree
            above = None
            for hh in occ:
                a = occ[hh].get((c, s - 1))
                if hh > h and a and a[0] == 'face' and a[2] == a[3] - 1:
                    above = a
            if above is not None and (c, s - MARGIN) not in POOL:
                t = TL.foot(t, wx, wy, 1.0 if h == 0 else 0.6, key_extra=(h,))
            tops[(h, c, s)] = t
            sl = (slice(s * T, (s + 1) * T), slice(c * T, (c + 1) * T))
            lay[sl] = np.where((t >= 0) | (t < -1), t, lay[sl])
            ltop[sl] = np.where(t >= 0, True, ltop[sl])
        # faces and stairs
        for (c, s), v in occ[h].items():
            wx, wy = c * T, (s - MARGIN) * T
            if v[0] == 'face':
                p, k, d = v[1], v[2], v[3]
                lt = end_type(occ, h, c, s, -1)
                rt = end_type(occ, h, c, s, 1)
                if FIX:
                    # r3: beside the pool the face stands straight in the water (no cut end
                    # opening onto the hidden ground); the bank line gets its wobble later
                    if (c - 1, s - MARGIN) in POOL:
                        lt = 'cont'
                    if (c + 1, s - MARGIN) in POOL:
                        rt = 'cont'
                fringe = None
                if k == 0:
                    above = tops.get((h, c, s - 1))
                    if above is not None:
                        row = above[T - 1]
                        fr = []
                        for x in range(T):
                            cc = row[x:x + 1]
                            if cc[0] < 0:
                                fr.append(None)
                            elif is_fam(cc, 'grass')[0] or is_fam(cc, 'leaf')[0]:
                                fr.append('g')
                            elif is_fam(cc, 'snow')[0]:
                                fr.append('s')
                            elif is_fam(cc, 'path')[0]:
                                fr.append('p')
                            else:
                                fr.append(None)
                        fringe = tuple(fr)
                deep = any(h == f['tier'] and f['cols'][0] <= c <= f['cols'][1] for f in _T['deep_lips'])
                wet = next((tuple(f['x']) for f in _T['wet_faces'] if h == f['tier'] and c == f['col']), None)
                t = TL.face(wx, wy, k, d, lt, rt, fringe, deep=deep, snowy=False, wet=wet)
                bk = TL.face_backing(wx, wy, k, d, fringe, deep=deep, snowy=False, wet=wet)
                back[s * T:(s + 1) * T, c * T:(c + 1) * T] = bk
            elif v[0] == 'stair' and len(v) > 1:
                st = STAIRS[v[1]]
                k = (s - MARGIN) - st['rows'][0]
                t = TL.stair2(wx, wy, k, st['rows'][1] - st['rows'][0] + 1, c - st['cols'][0],
                              st['cols'][1] - st['cols'][0] + 1, st['x0'], st['x1'], st['seed'])
            elif v[0] == 'stair':
                k = (s - MARGIN) - 11
                t = TL.stair(4 * T, wy, k, 2, c - 4)
            else:
                continue
            tops[(h, c, s, 'f')] = t
            sl = (slice(s * T, (s + 1) * T), slice(c * T, (c + 1) * T))
            lay[sl] = np.where((t >= 0) | (t < -1), t, lay[sl])
            ltop[sl] = np.where(t >= 0, False, ltop[sl])
        layers[h] = (lay, back, ltop, lgh)
    # composite, lowest first; each layer throws an 8 px shadow east on what is below it
    canvas = np.full((Hc, Wc), -1, np.int32)
    holes = np.zeros((Hc, Wc), np.int32)
    ctop = np.zeros((Hc, Wc), bool)
    cgh = np.zeros((Hc, Wc), bool)
    for h in sorted(layers):
        lay, back, ltop, lgh = layers[h]
        a = lay >= 0
        holes[a] = 0
        side = (lay == -4) | (lay == -5)
        holes[side] = lay[side]
        hole = (lay < 0) & (canvas < 0) & (back >= 0)
        lay = np.where(hole, back, lay)
        a = lay >= 0
        sh = np.zeros_like(a)
        if FIX:
            # r3: the cast shadow goes down and right along the light (as the props' shadows),
            # so its edge follows the tier's own silhouette, and its outer rim is one tone
            rim = np.zeros_like(a)
            for dx in range(1, P(8) + 1):
                dy = int(round(dx * 0.48))
                tgt = sh if dx <= P(8) - P(2) else rim
                if dy:
                    tgt[dy:, dx:] |= a[:-dy, :-dx]
                else:
                    tgt[:, dx:] |= a[:, :-dx]
            rim &= ~sh
            for m_ in (sh, rim):
                m_ &= ~a & (canvas >= 0) & ctop
            canvas[sh] = step(canvas[sh], -2)
            canvas[rim] = step(canvas[rim], -1)
        else:
            for dx in range(1, P(8) + 1):
                sh[:, dx:] |= a[:, :-dx]
            sh &= ~a & (canvas >= 0)
            # only what is lower than the caster: everything on the canvas so far is
            canvas[sh] = step(canvas[sh], -2)
        # contact: the ground right under a tier's lowest pixels, two tones then one down
        c1 = np.zeros_like(a)
        c1[1:] = a[:-1]
        c1 &= ~a & (canvas >= 0)
        c2 = np.zeros_like(a)
        for k in range(2, 2 + P(1)):
            c2[k:] |= a[:-k]
        c2 &= ~a & ~c1 & (canvas >= 0)
        canvas[c1] = step(canvas[c1], -2)
        canvas[c2] = step(canvas[c2], -1)
        canvas[a] = lay[a]
        ctop[a] = ltop[a]
        cgh[a] = lgh[a]
    # a side cut at a rounded end opens onto its neighbour's ground: carry that on
    ys, xs = np.nonzero(holes)
    for y, x in zip(ys, xs):
        dx = -T if holes[y, x] == -4 else T
        if FIX and cgh[y, x]:
            X = x + dx
            if 0 <= X < Wc and canvas[y, X] // 8 in (FI['water'], FI['water_warm'], FI['water_cool']):
                v = canvas[y, X]
                canvas[y, x] = v if v % 8 <= 2 else v // 8 * 8 + 2
                continue
        for k in (1, 2):
            X = x + dx * k
            if FIX and 0 <= X < Wc and ctop[y, X] and ctop[y, x] and not cgh[y, x] and canvas[y, x] >= 0 and \
                    canvas[y, X] // 8 not in (FI['water'], FI['water_warm'], FI['water_cool']):
                break       # r3: ground beside, and the lower tier's own ground (in its contact shade) is here
            if 0 <= X < Wc and holes[y, X] == 0 and canvas[y, X] >= 0 and \
                    canvas[y, X] // 8 not in (FI['water'], FI['water_warm'], FI['water_cool']):
                canvas[y, x] = canvas[y, X]
                break
    if FIX:
        # r1: the ground right under a face's foot is in its contact shade wherever it shows
        # (also where the foot follows the lumps and a strip of the tier's ground peeps out)
        facepx = (~ctop) & (canvas >= 0) & np.isin(canvas // 8, [FI['crag'], FI['crag_warm'], FI['crag_cool']])
        below = np.zeros_like(facepx)
        below[1:] = facepx[:-1]
        below &= ctop & (canvas >= 0) & (canvas % 8 >= 3)
        canvas[below] = step(canvas[below], -3)
        b2 = np.zeros_like(below)
        b2[1:] = below[:-1]
        b2 &= ctop & (canvas >= 0) & ~below & (canvas % 8 >= 3)
        canvas[b2] = step(canvas[b2], -2)
        prev = b2
        done = below | b2
        for _ in range(P(3) - 2):
            b3 = np.zeros_like(below)
            b3[1:] = prev[:-1]
            b3 &= ctop & (canvas >= 0) & ~done & (canvas % 8 >= 3)
            canvas[b3] = step(canvas[b3], -1)
            done |= b3
            prev = b3
    if FIX:
        # r1: where a floor (path top) meets a face rising to its east along a straight line,
        # the face shows its west side: a lit band 1 to 3 world px wide on a wobble, closed by
        # a broken dark line on the floor side (eastward-edges 3.3)
        isface = (~ctop) & (canvas >= 0) & np.isin(canvas // 8, [FI['crag'], FI['crag_warm'], FI['crag_cool']])
        isfloor = np.isin(canvas // 8, [FI['path'], FI['path_warm'], FI['path_cool']])
        Hh, Ww = canvas.shape
        for y in range(Hh):
            xs_ = np.nonzero(isfloor[y, :-1] & isface[y, 1:])[0]
            for x in xs_:
                # only long straight runs: the same boundary x over at least 6 rows around y
                run = sum(1 for dy in range(-3, 4) if 0 <= y + dy < Hh and isfloor[y + dy, x] and isface[y + dy, x + 1])
                if run < 6:
                    continue
                wv = int(round(DEN * (1.8 + 0.9 * np.sin(y / (5.5 * DEN)) + 0.4 * np.sin(y / (2.3 * DEN) + 1.3))))
                if x + 1 < Ww and canvas[y, x + 1] % 8 >= 6:
                    canvas[y, x + 1] = C('crag', 2)
                for k in range(max(1, wv)):
                    X = x - k
                    if X >= 0 and isfloor[y, X]:
                        canvas[y, X] = C('crag', 3) if k < max(1, wv) - 1 else C('crag_warm', 3)
                X = x - max(1, wv)
                if X >= 0 and isfloor[y, X]:
                    canvas[y, X] = C('crag', 6)
            # the mirror case: a face to the floor's west shows its east side, in shade
            xs_ = np.nonzero(isface[y, :-1] & isfloor[y, 1:])[0]
            for x in xs_:
                run = sum(1 for dy in range(-3, 4) if 0 <= y + dy < Hh and isface[y + dy, x] and isfloor[y + dy, x + 1])
                if run < 6:
                    continue
                wv = int(round(DEN * (1.6 + 0.8 * np.sin(y / (5.0 * DEN) + 2.0) + 0.4 * np.sin(y / (2.1 * DEN)))))
                if canvas[y, x] % 8 >= 6:
                    canvas[y, x] = C('crag', 1)
                for k in range(1, max(1, wv) + 1):
                    X = x + k
                    if X < Ww and isfloor[y, X]:
                        canvas[y, X] = C('crag', 1) if k < max(1, wv) else C('crag_cool', 1)
                X = x + max(1, wv) + 1
                if X < Ww and isfloor[y, X]:
                    canvas[y, X] = C('crag', 6)
    if FIX:
        # r5: a floor's rim over a face below wobbles: in runs of 3 to 10 world px the floor
        # reaches one world px further and the face's lit top row starts below it
        isface = (~ctop) & (canvas >= 0) & np.isin(canvas // 8, [FI['crag'], FI['crag_warm'], FI['crag_cool']])
        isfloor = ctop & np.isin(canvas // 8, [FI['path'], FI['path_warm'], FI['path_cool']])
        Hh, Ww = canvas.shape
        stair_m = np.zeros_like(isface)
        for (c_, r_) in STAIR:
            stair_m[(r_ + MARGIN) * T - P(2):(r_ + MARGIN + 1) * T, c_ * T:(c_ + 1) * T] = True
        rim = np.zeros_like(isface)
        rim[1:] = isfloor[:-1] & isface[1:]
        rim &= ~stair_m
        ys_, xs_ = np.nonzero(rim)
        if DEN > 1:
            # r7: the rim wanders 0 to 3 art px in one-px steps (runs of 2 to 6 world px), and its
            # lit row breaks now and then, so neither reads as a ruled line
            _rr = np.random.default_rng(27)
            walk = np.zeros(Ww + 1, int)
            _x, _v = 0, 1
            while _x <= Ww:
                _w = P(float(_rr.uniform(2, 6)))
                walk[_x:_x + _w] = _v
                _v = int(np.clip(_v + _rr.choice([-1, 1]), 0, P(1.5)))
                _x += _w
            for y, x in zip(ys_, xs_):
                sh = int(walk[x])
                for r_ in range(y + sh - 1, y - P(4) - 1, -1):
                    if sh and r_ - sh >= 0 and r_ < Hh and isfloor[r_ - sh, x]:
                        canvas[r_, x] = canvas[r_ - sh, x]
                Y = y + sh
                if Y < Hh and isface[Y, x]:
                    brk = ((int(x / DEN) // 4) * 2654435761 >> 7) % 6 == 0
                    canvas[Y, x] = C('crag', 3) if brk else C('crag_warm', 4)
            ys_, xs_ = [], []
        for y, x in zip(ys_, xs_):
            wq = int(x / DEN)
            seg = (wq + ((wq * 7) // 5) % 4) // 6
            if ((seg * 2654435761) >> 9) % 5 < 2:
                # shift the floor's last rows (its dark brink row with them) down by one world px
                for r_ in range(y + P(1) - 1, y - P(4) - 1, -1):
                    if r_ - P(1) >= 0 and r_ < Hh and (isfloor[r_ - P(1), x]):
                        canvas[r_, x] = canvas[r_ - P(1), x]
                Y = y + P(1)
                if Y < Hh and isface[Y, x]:
                    canvas[Y, x] = C('crag_warm', 4)
    if FIX:
        # r4: a straight run of face foot (6 world px or more on one row) gets half-buried toe
        # stones straddling it, every 8 to 14 world px: round, lit at the upper left, dark below,
        # a contact shade under each; no foot stays a ruled line
        isface = (~ctop) & (canvas >= 0) & np.isin(canvas // 8, [FI['crag'], FI['crag_warm'], FI['crag_cool']])
        iswat = np.isin(canvas // 8, [FI['water'], FI['water_warm'], FI['water_cool']])
        Hh, Ww = canvas.shape
        foot = isface.copy()
        foot[:-1] &= ctop[1:] & (canvas[1:] >= 0) & ~iswat[1:]
        foot[-1] = False
        for (c_, r_) in STAIR:          # no toe stones across a flight's foot
            foot[(r_ + MARGIN) * T:(r_ + MARGIN + 2) * T, max(0, c_ * T - P(3)):(c_ + 1) * T + P(3)] = False
        rngt = np.random.default_rng(4242)
        stones = []
        # a foot that wobbles by a pixel or two is still one straight run: find runs on the foot
        # widened by one world px up and down, and set each stone on the foot found there
        footw = foot.copy()
        for k_ in range(1, P(1) + 1):
            footw[k_:] |= foot[:-k_]
            footw[:-k_] |= foot[k_:]
        used = np.zeros_like(foot)
        for y in range(MARGIN * T, Hh):
            row = footw[y] & ~used[y]
            if FIX:
                used[max(0, y - P(1)):y + P(1) + 1] |= row[None, :]
            if not row.any():
                continue
            xs_ = np.nonzero(row)[0]
            runs = np.split(xs_, np.nonzero(np.diff(xs_) > 1)[0] + 1)
            for r in runs:
                if len(r) < P(6):
                    continue
                x = r[0] + P(rngt.uniform(1.0, 5.0))
                while x < r[-1] - P(1.5):
                    xi = int(x)
                    fy = np.nonzero(foot[max(0, y - P(1)):y + P(1) + 1, xi])[0]
                    yy0 = (max(0, y - P(1)) + fy[-1]) if len(fy) else y
                    stones.append((yy0, x, rngt.uniform(2.2, 3.6), rngt.uniform(1.5, 2.3), int(rngt.integers(0, 3))))
                    x += P(rngt.uniform(8.0, 14.0))
        # the same on a straight vertical side (a face's end standing on open ground): stones
        # straddle the side every 8 to 14 world px
        for side in (-1, 1):
            sidem = isface.copy()
            if side > 0:
                sidem[:, :-1] &= ctop[:, 1:] & (canvas[:, 1:] >= 0) & ~iswat[:, 1:]
                sidem[:, -1] = False
            else:
                sidem[:, 1:] &= ctop[:, :-1] & (canvas[:, :-1] >= 0) & ~iswat[:, :-1]
                sidem[:, 0] = False
            for (c_, r_) in STAIR:
                sidem[(r_ + MARGIN) * T:(r_ + MARGIN + 2) * T, max(0, c_ * T - P(4)):(c_ + 1) * T + P(4)] = False
            sidem[:MARGIN * T] = False
            for x in range(Ww):
                col = sidem[:, x]
                if not col.any():
                    continue
                ys_ = np.nonzero(col)[0]
                runs = np.split(ys_, np.nonzero(np.diff(ys_) > 1)[0] + 1)
                for r in runs:
                    if len(r) < P(6):
                        continue
                    y = r[0] + P(rngt.uniform(2.0, 5.0))
                    while y < r[-1] - P(1.0):
                        stones.append((y, x + side * P(0.6), rngt.uniform(1.8, 2.8), rngt.uniform(1.6, 2.4), int(rngt.integers(0, 3))))
                        y += P(rngt.uniform(7.0, 11.0))
        for (y, x, rx, ry, k) in stones:
            fam = ('crag', 'crag_warm', 'crag')[k]
            cy = y / DEN + ry * 0.25
            cx = x / DEN
            shade = []
            for Y in range(P(cy - ry - 1, 0), P(cy + ry + 1, 0) + 1):
                for X in range(P(cx - rx - 1, 0), P(cx + rx + 1, 0) + 1):
                    if not (0 <= Y < Hh and 0 <= X < Ww) or iswat[Y, X]:
                        continue
                    vy, vx = (Y / DEN + 0.5 / DEN - cy) / ry, (X / DEN + 0.5 / DEN - cx) / rx
                    r2 = (abs(vx) ** 2.2 + abs(vy) ** 2.2) ** (1 / 2.2)
                    if r2 <= 1.0:
                        edge = r2 > 1 - 1.0 / (min(rx, ry) * DEN)
                        if edge and (vy > 0.15 or vx > 0.5):
                            c = C('crag', 0)
                        elif vy < -0.25 and vx < 0.3:
                            c = C(fam, 4)
                        elif vy > 0.35 or vx > 0.55:
                            c = C('crag', 1)
                        else:
                            c = C(fam, 3) if vx < 0.1 else C('crag', 2)
                        canvas[Y, X] = c
                    elif r2 <= 1.0 + 1.6 / (ry * DEN + 1) and vy > 0.2 and ctop[Y, X] and canvas[Y, X] >= 0 \
                            and not np.isin(canvas[Y, X] // 8, [FI['crag'], FI['crag_warm'], FI['crag_cool']]):
                        shade.append((Y, X))
            for (Y, X) in shade:
                canvas[Y, X] = step(canvas[Y:Y + 1, X:X + 1], -2)[0, 0]
            # r6: a pebble or two rolled out from it onto the ground
            if k != 1 and DEN > 1:
                for (ox_, oy_) in ((rx + 1.6, ry * 0.9), (-rx - 1.2, ry * 1.1))[:1 + (k == 2)]:
                    Yp, Xp = P(cy + oy_, 0), P(cx + ox_, 0)
                    for (dy, dx, t_) in ((0, 0, 3), (0, 1, 2), (1, 0, 1), (1, 1, 1)):
                        Y, X = Yp + dy, Xp + dx
                        if 0 <= Y < Hh and 0 <= X < Ww and ctop[Y, X] and not iswat[Y, X] and \
                                not np.isin(canvas[Y, X] // 8, [FI['crag'], FI['crag_warm'], FI['crag_cool']]):
                            canvas[Y, X] = C('stone', t_)
    if FIX:
        # r3: where a face stands in the pool, its waterline wobbles by one world px in runs of
        # 2 to 6 (no ruled bank on the cell line); the rock right at the water is wet and dark
        iswat = np.isin(canvas // 8, [FI['water'], FI['water_warm'], FI['water_cool']])
        isface = (~ctop) & (canvas >= 0) & np.isin(canvas // 8, [FI['crag'], FI['crag_warm'], FI['crag_cool']])
        Hh, Ww = canvas.shape
        for side in (-1, 1):
            ys_, xs_ = np.nonzero(isface[:, max(0, -side):Ww - max(0, side)] &
                                  iswat[:, max(0, side):Ww - max(0, -side) if side < 0 else Ww])
            for y, x in zip(ys_, xs_):
                if side < 0:
                    x = x + 1           # face at x, water at x - 1
                yq = int((y - MARGIN * T) / DEN)
                seg = (yq + ((yq * 7) // 5) % 3) // 4
                h_ = ((seg * 2654435761) ^ (x // T) * 977) & 0xff
                wv = P(1) if h_ % 3 == 0 else 0
                wtr = canvas[y, x + side]
                for k in range(wv):
                    X = x - side * k
                    if 0 <= X < Ww and isface[y, X]:
                        canvas[y, X] = wtr // 8 * 8 + min(2, wtr % 8)
                X = x - side * wv
                if 0 <= X < Ww and isface[y, X]:
                    canvas[y, X] = C('crag_cool', 0) if canvas[y, X] % 8 < 6 else canvas[y, X]
    global TOPM
    TOPM = ctop[MARGIN * T:]
    return canvas[MARGIN * T:], hp, occ


TOPM = None
# r1: a worn branch from the main path to the bench and lantern nook, the worn track on the
# plateau from the upper flight's head, and the herb bed the fence encloses (world px, canvas)
WORN = [[tuple(p) for p in w] for w in PLAN['places']['worn_paths']]
BED = tuple(PLAN['places']['herb_bed'])
# r2: no dressing peeps out at the rim of a tree crown (canvas world px boxes of the crowns)
CROWNS = [tuple(b) for b in PLAN['places']['crown_boxes']]


def _curve(pts, step_w=0.25):
    pts = np.array(pts, float)
    out = []
    P_ = np.vstack([pts[0], pts, pts[-1]])
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n = max(2, int(np.hypot(*(p2 - p1)) / step_w))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    out = np.array(out)
    seg = np.hypot(*np.diff(out, axis=0).T)
    sarc = np.concatenate([[0], np.cumsum(seg)])
    return out, sarc


def worn2(cv, pts, hw0=3.6):
    """A worn footpath (grade 3): trodden dirt about 7 world px wide with a frayed grass edge,
    grass islands left in its middle, a damp darker row along the margin."""
    from scipy.spatial import cKDTree
    H, W = cv.shape
    cp, sarc = _curve(pts)
    tree = cKDTree(cp)
    ys = np.arange(max(0, P(cp[:, 1].min() - 10, 0)), min(H, P(cp[:, 1].max() + 10, 0)))
    xs = np.arange(max(0, P(cp[:, 0].min() - 10, 0)), min(W, P(cp[:, 0].max() + 10, 0)))
    YY, XX = np.meshgrid(ys, xs, indexing='ij')
    wy, wx = YY / DEN + 0.5 / DEN, XX / DEN + 0.5 / DEN
    dist, idx = tree.query(np.stack([wx.ravel(), wy.ravel()], 1))
    dist = dist.reshape(wx.shape); idx = idx.reshape(wx.shape)
    sa = sarc[idx]
    Xw, Yw = wx.astype(int), wy.astype(int)
    hsh = ((Xw * 73856093) ^ (Yw * 19349663) ^ 0x2545F491) & 0xffff
    from . import noise as TN
    fray = (TN.vnoise(wx, wy, 5.0, 41) - 0.5) * 2.2
    hw = hw0 + 0.5 * np.sin(sa / 9.0) + fray
    # a fillet where it leaves the main path, a small apron at its end (the bench front)
    hw = hw + 5.5 * np.exp(-sa / 5.0) + 1.6 * np.exp(-((sarc[-1] - sa) - 3.0) ** 2 / 30.0)   # r3: a real fillet
    hw = hw * np.clip((sarc[-1] - sa + 2.0) / 5.0, 0.3, 1.0)
    cur = cv[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    grassy = is_fam(cur, 'grass') | is_fam(cur, 'leaf')
    sheet = TL.SHEETS['trail']
    fill = sheet[np.ix_(ys % sheet.shape[0], xs % sheet.shape[1])]
    island = np.zeros_like(dist, bool)     # r3: no grass islands (they read as holes)
    dirt = grassy & (dist <= hw) & ~island
    out = cur.copy()
    out[dirt] = step(fill[dirt], -1)
    damp = dirt & (dist > hw - 1.0)
    out[damp] = step(out[damp], -1)
    cv[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] = out


def herb_bed(cv):
    """The herb bed inside the fence: tilled earth in ridges and furrows, herbs on the ridges
    (two kinds, lit top-left), a dark rim where the bed meets the grass."""
    x0, y0, x1, y1 = BED
    H, W = cv.shape
    for Y in range(P(y0, 0), P(y1, 0)):
        for X in range(P(x0, 0), P(x1, 0)):
            wy, wx = Y / DEN, X / DEN
            # rounded corners, radius 3
            cx = min(max(wx, x0 + 3), x1 - 3); cy = min(max(wy, y0 + 3), y1 - 3)
            if (wx - cx) ** 2 + (wy - cy) ** 2 > 9:
                continue
            r = (wy - y0) % 5.0
            if r < 1.0:
                c = C('earth_warm', 3)
            elif r < 3.0:
                c = C('earth', 2)
            else:
                c = C('earth', 1)
            edge = (wx - x0 < 1) or (x1 - wx <= 1) or (wy - y0 < 1) or (y1 - wy <= 1)
            if edge:
                c = C('earth', 0)
            cv[Y, X] = c
    k = 0
    for ry in np.arange(y0 + 3.0, y1 - 2.0, 5.0):
        for rx in np.arange(x0 + 4.0 + (k % 2) * 3.0, x1 - 4.0, 6.0):
            fam = 'leaf' if k % 2 else 'grass_cool'
            for dy in range(P(-2.5, 0), P(0.5, 0) + 1):
                for dx in range(P(-2.0, 0), P(2.0, 0) + 1):
                    vy, vx = dy / DEN / 2.2, dx / DEN / 2.0
                    if vx * vx + (vy + 0.1) ** 2 > 1:
                        continue
                    Y, X = P(ry, 0) + dy, P(rx, 0) + dx
                    if 0 <= Y < H and 0 <= X < W:
                        t = 4 if (vy < -0.2 and vx < 0.2) else (2 if (vy > 0.3 or vx > 0.5) else 3)
                        cv[Y, X] = C(fam, t)
            k += 1


def bank_stone(cv, cx, cy, rx, ry, fam='stone', seed=0):
    """A bank stone: a chunky rounded block, its top plane lit (a tone-5 glint at the upper-left
    edge), the body a tone down, the lower right two down, an outline in the stone's own edge
    tone on the lower right only."""
    H, W = cv.shape
    if FIX and DEN > 1:
        # r6: the shared pixel-art stone (no plane facets)
        dec = DC.lump_px(max(3, P(2 * rx)), max(3, P(2 * ry)), seed, fams=(fam,), outline=(fam, 0))
        DC.paste(cv, dec, P(cx - rx, 0), P(cy - ry, 0))
        return
    rng = np.random.default_rng(seed)
    chips = [(rng.uniform(0, 2 * np.pi), rng.uniform(0.12, 0.22)) for _ in range(2)]
    for Y in range(P(cy - ry - 1, 0), P(cy + ry + 1, 0) + 1):
        for X in range(P(cx - rx - 1, 0), P(cx + rx + 1, 0) + 1):
            if not (0 <= Y < H and 0 <= X < W):
                continue
            vy, vx = (Y / DEN + 0.5 / DEN - cy) / ry, (X / DEN + 0.5 / DEN - cx) / rx
            r = (abs(vx) ** 2.6 + abs(vy) ** 2.6) ** (1 / 2.6)
            ang = np.arctan2(vy, vx)
            for (a0, cut) in chips:
                if abs((ang - a0 + np.pi) % (2 * np.pi) - np.pi) < 0.35:
                    r += cut
            if r > 1:
                continue
            edge = r > 1 - 1.0 / (min(rx, ry) * DEN)
            if vy < -0.15 and vx < 0.35:
                t = 4
            elif vy > 0.35 or vx > 0.55:
                t = 2
            else:
                t = 3
            if edge and (vy > 0.1 or vx > 0.3):
                c = C(fam, 6)
            elif edge and t == 4 and vx < -0.2:
                c = C(fam, 5)
            else:
                c = C(fam, t)
            cv[Y, X] = c


def bank_run(cv, x0, y0, x1, y1, n, nx, ny, seed):
    """r7: a run of n bank stones, each overlapping the one before (the lower one in front),
    their water side under the waterline: the submerged half a dark shape in the water, a light
    lap line where the stone meets the surface."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    for k in range(n):
        f = (k + rng.uniform(-0.3, 0.3)) / max(1, n - 1)   # r8: uneven spacing
        big = k % 3 == 0                                   # r8: one large, two small
        jit = (1.6 if k % 2 else -0.9) + rng.uniform(-0.5, 0.5)   # r8: staggered in and out (2 to 4 px)
        cx = x0 + (x1 - x0) * f + jit * nx + rng.uniform(-0.4, 0.4) * ny
        cy = y0 + (y1 - y0) * f + jit * ny + rng.uniform(-0.6, 0.6)
        rx, ry = (rng.uniform(2.6, 3.8), rng.uniform(2.0, 2.8)) if big else (rng.uniform(1.6, 2.2), rng.uniform(1.3, 1.8))
        dec = DC.lump_px(max(3, P(2 * rx)), max(3, P(2 * ry)), seed + k, fams=('stone', 'stone_warm', 'stone'),
                         outline=('stone_cool', 0))
        X0, Y0 = P(cx - rx, 0), P(cy - ry, 0)
        wl = rng.uniform(0.05, 0.3)                        # the water level on the stone (share of ry)
        for yy_ in range(dec.shape[0]):
            for xx_ in range(dec.shape[1]):
                c = dec[yy_, xx_]
                Y, X = Y0 + yy_, X0 + xx_
                if c < 0 or not (0 <= Y < H and 0 <= X < W):
                    continue
                # the water level cuts the stone low down (a contour, not a wall): where the stone
                # stands in water, its foot is under the surface, with a light lap line
                sd = ((Y + 0.5) / DEN - cy) / ry - 0.12 * np.sin((X + 0.5) / DEN * 1.7 + k)
                if sd > wl and cv[Y, X] // 8 in (FI['water'], FI['water_cool'], FI['water_warm']):
                    cv[Y, X] = C('water', 4) if sd <= wl + 0.55 / ry else C('water_cool', 1)
                    continue
                cv[Y, X] = c


def soften_pool(cv):
    """r6: the pool and the brook's mouth as one organic body: the water's outline is smoothed
    (stair-steps and right-angled corners round off), water lost at the edge becomes wet dark
    rock beside a face or damp earth on open ground, water gained spreads only over open
    ground; a damp band of earth in clumps round the open banks; shallows a tone lighter along
    the south and west banks; the dark band under the cliff stays."""
    if not FIX:
        return
    H, W = cv.shape
    y0, y1, x0, x1 = P(160, 0), P(250, 0), P(150, 0), P(240, 0)
    sub = cv[y0:y1, x0:x1]
    fam = sub // 8
    isw = np.isin(fam, [FI['water'], FI['water_warm'], FI['water_cool']])
    isrock = np.isin(fam, [FI['crag'], FI['crag_warm'], FI['crag_cool'], FI['stone'], FI['stone_warm'], FI['stone_cool']])
    isopen = np.isin(fam, [FI['grass'], FI['grass_warm'], FI['grass_cool'], FI['leaf'], FI['earth'], FI['earth_warm'],
                           FI['earth_cool'], FI['path'], FI['path_warm'], FI['path_cool']])
    sm = ndi.gaussian_filter(isw.astype(float), POOL_SOFT * DEN) > 0.5
    lost = isw & ~sm
    gain = sm & ~isw & isopen
    nearrock = ndi.binary_dilation(isrock, iterations=max(1, P(1.5)))
    out = sub.copy()
    out[lost & nearrock] = C('crag_cool', 1)
    out[lost & ~nearrock] = C('earth', 2)
    if gain.any():
        idx = ndi.distance_transform_edt(~isw, return_distances=False, return_indices=True)
        src = sub[idx[0], idx[1]]
        out[gain] = np.where(src[gain] % 8 > 2, src[gain] // 8 * 8 + 2, src[gain])
    w2 = (isw & ~lost) | gain
    # the damp band round open banks, in clumps
    ring = ndi.binary_dilation(w2, iterations=max(1, P(1.2))) & ~w2 & isopen
    ring &= (np.mgrid[0:sub.shape[0], 0:sub.shape[1]][0] + y0) < P(_W['pool_bottom'] + 3, 0)   # r8: the pool's own banks, not the brook's
    yy, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
    # r7: the damp band in runs (3 world px clumps, two in five left as grass), not a ruled line
    cl = ((((xx // max(1, P(3.0))) * 73856093) ^ ((yy // max(1, P(3.0))) * 19349663)) & 0xff)
    keep = cl % 5 >= 2
    out[ring & keep] = np.where(cl[ring & keep] % 3 == 0, C('earth_warm', 2), C('earth', 2))
    # shallows: a tone lighter just inside the south and west banks of the pool (not the brook)
    dist = ndi.distance_transform_edt(w2)
    _, (iy, ix) = ndi.distance_transform_edt(w2, return_indices=True)
    vy, vx = iy - yy, ix - xx
    pool_zone = (yy + y0) < P(226, 0)
    shal = w2 & pool_zone & (dist <= P(2.2)) & (dist > P(0.6)) & ((vy > 0) | (vx < 0)) & (out % 8 == 2)
    out[shal] = out[shal] + 1
    cv[y0:y1, x0:x1] = out


def pool_bands(cv):
    """r7: the pool's depth bands traced from its smoothed shoreline (the auditors: the bands
    stepped with the tiles). The shoreline is smoothed once more (which also rounds the neck
    under the fall); under rock banks the water darkens in three bands at a 2 to 6 world px
    inset (narrower on the side banks), their edges wandering so no run is straight; along the
    open banks a light waterline and shallows. The pool's tones end at a ragged line inside the
    outlet, so the brook's own tones begin unevenly."""
    if not (FIX and DEN > 1):
        return
    y0, y1, x0, x1 = P(176.5, 0), P(238, 0), P(160, 0), P(240, 0)
    sub = cv[y0:y1, x0:x1]
    h_, w_ = sub.shape
    fam = sub // 8
    wf = [FI['water'], FI['water_warm'], FI['water_cool']]
    rockf = [FI[n] for n in ('crag', 'crag_warm', 'crag_cool', 'stone', 'stone_warm', 'stone_cool')]
    isw = np.isin(fam, wf)
    isrock = np.isin(fam, rockf)
    yy, xx = np.mgrid[0:h_, 0:w_]
    rng = np.random.default_rng(717)
    nz = ndi.gaussian_filter(rng.random((h_, w_)), 1.6 * DEN)
    nz = (nz - nz.mean()) / (nz.std() + 1e-6)
    # the pool ends at a ragged line in the outlet
    xw = (xx + x0) / DEN
    end = _W['pool_bottom'] + 2.5 + 2.0 * np.sin(xw / 2.3) + 1.5 * np.sin(xw / 1.1 + 0.7)
    zone = (yy + y0) / DEN < end
    pz = isw & zone
    sm = ndi.gaussian_filter(pz.astype(float), POOL_SOFT_R7 * DEN) > 0.5
    deep_bay = (yy + y0) / DEN < _W['pool_bottom'] - 6
    gain = sm & ~pz & zone & ((isrock & deep_bay) | np.isin(fam, wf))
    lost = pz & ~sm & ((yy + y0) / DEN < _W['pool_bottom'] - 2)
    out = sub.copy()
    nearrock = ndi.binary_dilation(isrock, iterations=max(1, P(1.5)))
    out[lost & nearrock] = C('crag_cool', 1)
    out[lost & ~nearrock] = C('earth', 2)
    wat = (pz & ~lost) | gain
    allw = wat | (isw & ~zone)
    dist, (iy, ix) = ndi.distance_transform_edt(allw, return_indices=True)
    rockpx = ~allw & (isrock | (lost & nearrock) | ~np.isin(out // 8, [FI[n] for n in (
        'grass', 'grass_warm', 'grass_cool', 'leaf', 'earth', 'earth_warm', 'earth_cool', 'path', 'path_warm', 'path_cool')]))
    dr = ndi.distance_transform_edt(~rockpx) / DEN          # to the nearest rock bank
    dop = ndi.distance_transform_edt(rockpx | allw) / DEN   # to the nearest open bank
    # the bands are widest under the north bank and narrow smoothly down the side banks
    yw = (yy + y0) / DEN
    s = np.clip(1.0 - (yw - 196.0) / 16.0 * 0.45, 0.55, 1.0)
    body = C('water', 2)
    keep = np.isin(sub % 8, (4, 5)) & isw & (dist > DEN)     # the fall's foam streaks and glints stay
    t = np.full((h_, w_), body)
    for (_k, f_, tone, inset) in reversed(POOL_BANDS):
        t[dr <= inset * s + 0.8 * nz] = C(f_, tone)
    _, (oy, ox) = ndi.distance_transform_edt(rockpx | allw, return_indices=True)
    south_west = ((oy - yy) > 0) | ((ox - xx) < 0)
    opn = dr > 2.0 + 0.5 * nz
    t[opn & (dop <= 2.2 + 0.6 * nz) & south_west] = C('water', 3)
    t[opn & (dop <= 0.5 + 0.01)] = C('water', 4)
    sel = wat & ~keep
    out[sel] = t[sel]
    cv[y0:y1, x0:x1] = out


def landing(cv):
    """r6 (the jetty removed): the shore track ends on a tidy dirt landing at the pond's south-east
    bank, with a flat sitting stone at the water's edge."""
    L_ = _W['landing']
    bank_stone(cv, *L_['at'], *L_['r'], L_['fam'], seed=L_['seed'])


def reeds(cv):
    """A few reed clumps at the pond's still edges: thin blades, dark at the root and lit at
    the tip, one seed head per clump; a dark ring on the water at their feet."""
    H, W = cv.shape
    rng = np.random.default_rng(77)
    for (cx_, cy_, n) in [tuple(r) for r in _W['reeds']]:
        for b_ in range(n):
            bx = cx_ + (b_ - n / 2) * 1.1 + rng.uniform(-0.3, 0.3)
            hgt = rng.uniform(4.5, 7.0)
            lean = rng.uniform(-0.25, 0.25)
            for k in range(P(hgt, 0)):
                t_ = k / max(1, P(hgt, 0) - 1)
                X, Y = P(bx + lean * hgt * t_, 0), P(cy_, 0) - k
                if 0 <= Y < H and 0 <= X < W:
                    cv[Y, X] = C('leaf', 1) if t_ < 0.25 else (C('grass', 3) if t_ < 0.7 else C('grass_warm', 4))
            if b_ == n // 2:
                X0, Y0 = P(bx + lean * hgt, 0), P(cy_, 0) - P(hgt, 0)
                for Y in range(Y0, Y0 + P(2.2)):
                    for X in range(X0, X0 + max(1, P(1))):
                        if 0 <= Y < H and 0 <= X < W:
                            cv[Y, X] = C('timber', 2 if X == X0 else 1)


def _foot_ok(cv, x, yf, w=6):
    """A plant's foot must stand on open top ground (never on a face, a stair or water)."""
    if TOPM is None:
        return True
    H, W = cv.shape
    Y = P(yf, 0) - 1
    for fx in (x + 1, x + w / 2, x + w - 1):
        X = P(fx, 0)
        if not (0 <= Y < H and 0 <= X < W):
            continue
        if not TOPM[Y, X]:
            return False
        f = cv[Y, X] // 8
        if f in (FI['water'], FI['water_warm'], FI['water_cool'], FI['crag'], FI['crag_warm'], FI['crag_cool']):
            return False
        if f in (FI['earth'], FI['earth_warm'], FI['earth_cool']):
            return False
        if yf > _T['plants_off_paths_below'] and f in (FI['path'], FI['path_warm'], FI['path_cool']):
            return False
    return True


def soften_lip(cv, box):
    """r7: round a lip's right-angle steps inside a box (canvas world px): the turf's outline is
    smoothed; turf lost shows the face beside it, turf gained takes the turf from further in,
    and the new brink gets the lip's dark row with a shaded px of face under it."""
    x0, y0, x1, y1 = (P(v, 0) for v in box)
    sub = cv[y0:y1, x0:x1]
    gf = [FI[n] for n in ('grass', 'grass_warm', 'grass_cool', 'leaf')]
    rf = [FI[n] for n in ('crag', 'crag_warm', 'crag_cool')]
    G = np.isin(sub // 8, gf)
    R = np.isin(sub // 8, rf)
    if not G.any() or not R.any():
        return
    h_, w_ = sub.shape
    yy, xx = np.mgrid[0:h_, 0:w_]
    edge = np.minimum.reduce([yy, xx, h_ - 1 - yy, w_ - 1 - xx]) / DEN
    wgt = np.clip((edge - 1.0) / 3.0, 0, 1)            # feathered to nothing at the box's edge
    sm = ndi.gaussian_filter(G.astype(float), 2.4 * DEN)
    Gs = np.where(wgt > 0, sm > 0.5 + 0.5 * (1 - wgt), G)
    out = sub.copy()
    inner = ndi.binary_erosion(G, iterations=P(3))
    if inner.any():
        _, (iy, ix) = ndi.distance_transform_edt(~inner, return_indices=True)
        gain = Gs & ~G & R
        out[gain] = sub[iy[gain], ix[gain]]
    _, (ry, rx) = ndi.distance_transform_edt(~(R & ~Gs), return_indices=True)
    lost = G & ~Gs
    out[lost] = sub[ry[lost], rx[lost]]
    Gn = (G & ~lost) | (Gs & ~G & R)
    below = np.zeros_like(Gn)
    below[:-1] = ~Gn[1:] & np.isin(out[1:] // 8, rf)
    brink = Gn & below & (wgt > 0)
    out[brink] = C('grass', 2)
    sh = np.zeros_like(Gn)
    sh[1:] = brink[:-1]
    sh &= np.isin(out // 8, rf)
    out[sh] = step(out[sh], -1)
    cv[y0:y1, x0:x1] = out


def tidy_edge(cv, box):
    """r8: inside a box (canvas world px), the floor's straight vertical edge against a face walks
    1 to 3 px (the floor reaches into the face or the face into the floor, row by row in runs),
    and thick dark wedges (crag tone 0, more than a crevice) take the rock beside them."""
    x0, y0, x1, y1 = (P(v, 0) for v in box)
    sub = cv[y0:y1, x0:x1]
    h_, w_ = sub.shape
    pf = [FI[n] for n in ('path', 'path_warm', 'path_cool')]
    rf = [FI[n] for n in ('crag', 'crag_warm', 'crag_cool')]
    out = sub.copy()
    rng = np.random.default_rng(int(box[0] * 31 + box[1]))
    v_, left = 0, 0
    for y in range(h_):
        if left <= 0:
            v_ = int(np.clip(v_ + rng.choice([-1, 1]), -P(1), P(1.5)))
            left = P(float(rng.uniform(2, 6)))
        left -= 1
        row = sub[y] // 8
        for x in range(1, w_):
            if row[x - 1] in pf and row[x] in rf:          # the floor's east edge in this row
                if v_ > 0:
                    out[y, x:min(w_, x + v_)] = sub[y, max(0, x - 1 - v_):x - 1][:min(w_, x + v_) - x] if x - 1 - v_ >= 0 else sub[y, x - 1]
                    if x + v_ < w_:
                        out[y, x + v_] = C('crag', 0)
                elif v_ < 0:
                    out[y, max(0, x + v_):x] = C('crag', 0)
                break
    dark = np.isin(out // 8, rf) & (out % 8 == 0)
    thick = ndi.binary_opening(dark, structure=np.ones((3, 3)))
    if thick.any():
        rock = np.isin(out // 8, rf) & (out % 8 > 0)
        if rock.any():
            _, (iy, ix) = ndi.distance_transform_edt(~rock, return_indices=True)
            fill = out[iy, ix]
            out[thick] = np.where(fill[thick] % 8 > 1, fill[thick] - 1, fill[thick])
    cv[y0:y1, x0:x1] = out


def place_decals(cv):
    """Hand-placed story pieces, then hashed dressing."""
    Hc, Wc = cv.shape
    if FIX and DEN > 1:
        for box in _W.get('soften_lips', []):
            soften_lip(cv, box)
        for box in _T.get('tidy_edges', []):
            tidy_edge(cv, box)
    if FIX:
        for pts in WORN:
            worn2(cv, pts)
        herb_bed(cv)
    base = cv.copy()
    meadow_ok = is_fam(base, 'grass')
    # the rill on the upper tier and the trickle down the bay face into the pool
    if FIX:
        rill2(cv)
        fall2(cv)
        brook2(cv)
        soften_pool(cv)
        pool_bands(cv)
        # bank stones on the pool's east shore and one on the west, straddling the waterline
        isw = lambda Y, X: 0 <= Y < Hc and 0 <= X < Wc and cv[Y, X] // 8 in (FI['water'], FI['water_cool'])
        # the pool's surface: a soft patch of sky in the south half, glints in pairs
        # r3: the sky lies on the water as a few soft horizontal streaks (no dithered oval)
        for (sx0, sx1, sy) in _W['sky_streaks']:
            Y = P(sy, 0)
            for X in range(P(sx0, 0), P(sx1, 0) + 1):
                for dy_ in range(max(1, P(0.5))):
                    if isw(Y + dy_, X) and cv[Y + dy_, X] % 8 == 2:
                        cv[Y + dy_, X] = C('water', 3)
        # ripple arcs spreading from the foam at the fall's foot, broken, fading outwards
        fx_, fy_ = _W['ripples']['at']
        for rr, tone, gap in _W['ripples']['rings']:
            for k in range(int(rr * 9 * DEN)):
                th = np.pi * (0.12 + 0.76 * k / (rr * 9 * DEN))
                if (np.sin(th * 7.0 + gap * 3.0) > 0.35):
                    continue
                X, Y = P(fx_ + np.cos(th) * rr * 1.5, 0), P(fy_ + np.sin(th) * rr * 0.75, 0)
                if isw(Y, X) and cv[Y, X] % 8 in (1, 2):
                    cv[Y, X] = C('water', tone if cv[Y, X] % 8 == 2 else 2)
        # glints in pairs: a dash and a dot beside it
        for (gx_, gy_) in _W['glints']:
            for k in range(P(2)):
                if isw(P(gy_, 0), P(gx_, 0) + k):
                    cv[P(gy_, 0), P(gx_, 0) + k] = C('water', 5)
            if isw(P(gy_ + 1.0, 0), P(gx_ + 3.0, 0)):
                cv[P(gy_ + 1.0, 0), P(gx_ + 3.0, 0)] = C('water', 5)
        for (x0_, y0_, x1_, y1_, n_, nx_, ny_, sd_) in (_W.get('bank_runs', []) if DEN > 1 else []):
            bank_run(cv, x0_, y0_, x1_, y1_, n_, nx_, ny_, sd_)
        for k_, (bx, by, brx, bry) in enumerate(_W['bank_stones'] if not (DEN > 1 and 'bank_runs' in _W) else []):
            bank_stone(cv, bx, by, brx, bry, 'stone_warm' if k_ % 2 else 'stone', seed=300 + k_)
            # its reflection: a darker band in the water just below it
            for Y in range(P(by + bry * 0.6, 0), P(by + bry + 2.6, 0)):
                for X in range(P(bx - brx * 0.9, 0), P(bx + brx * 0.9, 0) + 1):
                    if isw(Y, X) and cv[Y, X] % 8 >= 2:
                        cv[Y, X] = C('water', 1)
        # stepping stones: the shore track crosses the brook to the east meadow
        for k_, (bx, by, brx, bry) in enumerate(_W['stepping_stones']):
            # the waterline round each stone, light; a foam pixel on its upstream (north) side
            for Y in range(P(by - bry - 1.0, 0), P(by + bry + 1.0, 0) + 1):
                for X in range(P(bx - brx - 1.0, 0), P(bx + brx + 1.0, 0) + 1):
                    if 0 <= Y < Hc and 0 <= X < Wc and cv[Y, X] // 8 == FI['water']:
                        vy, vx = (Y / DEN - by) / (bry + 0.9), (X / DEN - bx) / (brx + 0.9)
                        if vx * vx + vy * vy <= 1:
                            cv[Y, X] = C('water', 4) if vy < 0.2 else C('water', 1)
            bank_stone(cv, bx, by, brx, bry, 'stone', seed=320 + k_)
            Y, X = P(by - bry - 0.6, 0), P(bx - 0.5, 0)
            if 0 <= Y < Hc and 0 <= X < Wc and cv[Y, X] // 8 == FI['water']:
                cv[Y, X] = C('snow', 5)
        # r3: the crossing leads to a small fishing jetty on the far bank, reaching into the pond
        landing(cv)      # r6: the jetty did not read (a ladder in the pond); a landing instead
        reeds(cv)
        bx0, by0, bx1, by1, byl = _W['bay_rock_west']
        for Y in range(P(by0, 0), P(by1, 0)):
            for X in range(P(bx0, 0), P(bx1, 0)):
                if (is_fam(cv[Y:Y + 1, X:X + 1], 'grass')[0, 0] or is_fam(cv[Y:Y + 1, X:X + 1], 'leaf')[0, 0]) and Y < P(byl, 0):
                    cv[Y, X] = C('crag', 1) if (X // max(1, P(3)) + Y // max(1, P(2))) % 4 else C('crag', 2)
        # the fall's bay: no turf beside the splash, wet dark rock down to the pool
        bx0, by0, bx1, by1 = _W['bay_rock_fall']
        for Y in range(P(by0, 0), P(by1, 0)):
            for X in range(P(bx0, 0), P(bx1, 0)):
                if (is_fam(cv[Y:Y + 1, X:X + 1], 'grass')[0, 0] or is_fam(cv[Y:Y + 1, X:X + 1], 'leaf')[0, 0]):
                    cv[Y, X] = C('crag', 1) if (X + Y) % 5 else C('crag', 0)
    T = TW               # item positions below are in world px (drawn at x density)
    items = [tuple(_tup(v) for v in it) for it in PLAN['decals']['hand']]
    # hashed dressing: flowers and tufts on open grass, away from the trail and pool
    kinds = PLAN['decals']['flower_kinds']
    for s in range(0, ROWS):
        for c in range(COLS):
            hsh = (c * 2654435761 ^ s * 40503) & 0xffff
            y0, x0 = s * T, c * T
            patch = meadow_ok[P(y0, 0):P(y0 + T, 0), P(x0, 0):P(x0 + T, 0)]
            if patch.mean() < 0.95:
                continue
            if (c, s) in TRAIL or (c, s) in WET:
                continue
            if hsh % 5 == 0:
                items.append((y0 + 6 + hsh % 7, 'flowers', x0 + hsh % 7, y0 + hsh % 7, hsh, kinds[hsh % 6]))
            elif hsh % 5 == 1:
                items.append((y0 + 8, 'tuft', x0 + (hsh >> 3) % 9, y0 + 4 + (hsh >> 5) % 6, hsh, None))
    if FIX and TOPM is not None:
        # r6: a few flowers where the meadow meets a cliff foot (spaced well apart)
        fam_ = cv // 8
        face_ = np.isin(fam_, [FI['crag'], FI['crag_warm'], FI['crag_cool']]) & ~TOPM
        gr_ = np.isin(fam_, [FI['grass'], FI['grass_warm'], FI['grass_cool']]) & TOPM
        footp = np.zeros_like(gr_)
        footp[P(5):] = face_[:-P(5)] & gr_[P(5):]
        ys_, xs_ = np.nonzero(footp)
        picked = []
        kinds_ = ['white', 'yellow', 'violet']
        for k_ in np.random.default_rng(55).permutation(len(ys_)):
            fx, fy = xs_[k_] / DEN, ys_[k_] / DEN
            if fy < 60 or any((fx - a_) ** 2 + (fy - b_) ** 2 < 45 ** 2 for a_, b_ in picked):
                continue
            picked.append((fx, fy))
            items.append((fy + 2, 'flowers', fx - 3, fy - 4, 970 + len(picked), kinds_[len(picked) % 3]))
            if len(picked) >= 7:
                break
    if FIX:
        # boulders laid over the seams where faces of one tier meet out of step
        items += [tuple(_tup(v) for v in it) for it in PLAN['decals']['laid']]
        out = []
        for it in items:
            yf, kind, x, y, seed, extra = it
            if kind in ('tuft', 'flowers', 'fern', 'bush'):
                w = extra[0] if kind == 'bush' else (13 if kind == 'fern' else 6)
                if not _foot_ok(cv, x, yf, w):
                    continue
                bx0, by0, bx1, by1 = BED
                if bx0 - 3 <= x + w / 2 <= bx1 + 3 and by0 - 3 <= yf <= by1 + 6:
                    continue
                if any(c0 - 4 <= x + w / 2 <= c1 + 4 and r0 - 4 <= yf <= r1 for (c0, r0, c1, r1) in CROWNS):
                    continue
            out.append(it)
        items = out
    items.sort(key=lambda t: t[0])
    return items


PLANTS = []     # at densities above 1 the plants are drawn by the kit's sprites (compose.py)


def _tup(v):
    return tuple(v) if isinstance(v, list) else v


def draw_items(cv, items, fig_at=None):
    for it in items:
        yf, kind, x, y, seed, extra = it
        X, Y = P(x, -10 ** 6), P(y, -10 ** 6)
        if (DEN != 1 and kind in ('bush', 'fern', 'tuft', 'flowers')) or (FIX and DEN == 1 and kind == 'bush'):
            # r3: with the fixes the 1x bushes are drawn by the pilot's kit too (one lit dome)
            PLANTS.append({'kind': kind, 'x': x, 'y': y, 'foot': yf, 'seed': int(seed), 'extra': extra})
            continue
        if kind == 'ivy':
            if FIX:
                dec = DC.ivy2(seed, P(extra[0]), P(extra[1]), DEN)
            else:
                dec = DC.ivy(seed, *extra) if DEN == 1 else DC.ivy_d(seed, P(extra[0]), P(extra[1]), DEN)
            DC.paste(cv, dec, X, Y)
        elif kind == 'b32':
            DC.paste(cv, DC.boulder32(seed) if DEN == 1 else DC.boulder32_d(seed, DEN), X, Y, shadow=True,
                     shadow_dx=P(4), shadow_dy=P(2))
        elif kind == 'lump':
            DC.paste(cv, DC.lump(P(extra[0]), P(extra[1]), seed), X, Y, shadow=True, shadow_dx=P(2), shadow_dy=P(1))
        elif kind == 'lumpd' and DEN != 1:
            DC.paste(cv, DC.lump(P(extra[0]), P(extra[1]), seed, fams=('crag_warm',)), X, Y, shadow=True,
                     shadow_dx=P(2), shadow_dy=P(1))
        elif kind == 'fern':
            DC.paste(cv, DC.fern(seed), X, Y, shadow=True, shadow_dx=2, shadow_dy=1)
        elif kind == 'bush':
            DC.paste(cv, DC.bush(extra[0], extra[1], seed), X, Y, shadow=True, shadow_dx=4, shadow_dy=2)
        elif kind == 'tuft':
            DC.paste(cv, DC.tuft(seed), X, Y)
        elif kind == 'flowers':
            DC.paste(cv, DC.flowers(seed, extra), X, Y)
        elif kind == 'snowrock':
            DC.paste(cv, DC.snowrock(seed) if DEN == 1 else DC.snowrock_d(seed, DEN), X, Y, shadow=True,
                     shadow_dx=P(2), shadow_dy=P(1))
        elif kind == 'crack' and FIX and DEN > 1:
            pass            # r6: no thin crack lines on the pixel-art stone at 1.5x and 2x
        elif kind == 'crack':
            DC.paste(cv, DC.crack(seed) if DEN == 1 else DC.crack_d(seed, DEN), X, Y)


# --- the rill and its fall, redrawn (pilot logic fixes, 21 Oct) ----------------------------------
LIP_Y = _W['lip_row'] * TW     # the upper tier's brink above the bay (world px, canvas)
POOL_Y = _W['pool_row'] * TW   # the pool's top


def _rill_x(yw):
    return _W['rill_x'] + 2.6 * np.sin(yw / 13.0 + 0.6) + 1.4 * np.sin(yw / 5.7)


def _rill_hw(yw):
    return 2.3 + 0.6 * np.sin(yw / 8.0) + max(0.0, (yw - 92) / 20.0) * 1.4


def rill2(cv):
    """The rill on the upper tier in a natural bed: water 4 to 6 world px wide on a gentle
    meander, a shaded west bank and a lit east bank of earth, the grass lip lit on the east,
    a few bed stones, the current as short lit dashes with glints in pairs. It widens towards the
    brink, where it spills over the lip into the fall."""
    H, W = cv.shape
    rng = np.random.default_rng(7)
    stones = [(yw, -1 if k % 2 else 1) for k, yw in enumerate(range(9, LIP_Y - 8, 13))]
    for Y in range(0, P(LIP_Y, 0) + P(1)):
        yw = Y / DEN
        cx, hw = _rill_x(yw), _rill_hw(yw)
        x0, x1 = int((cx - hw - 3) * DEN) - 1, int((cx + hw + 3) * DEN) + 2
        for X in range(max(0, x0), min(W, x1)):
            u = X / DEN + 0.5 / DEN - cx          # world offset from the centre
            c0 = cv[Y, X]
            if not (is_fam(cv[Y:Y + 1, X:X + 1], 'grass')[0, 0] or is_fam(cv[Y:Y + 1, X:X + 1], 'leaf')[0, 0]
                    or c0 // 8 in (FI['water'], FI['earth'], FI['earth_warm'], FI['earth_cool'])):
                continue
            a = abs(u)
            if a <= hw:
                t = 3
                if u < -hw + 1.2:
                    t = 2                          # shade under the west bank
                if u > hw - 0.8:
                    t = 4 if yw < LIP_Y - 3 else 3   # light off the east bank
                c = C('water', t)
                # the current: lit dashes over their own shadow, staggered down the bed
                # r4: hashed streaks of irregular length on two lanes, most of the bed plain
                lane = int(np.floor((u + 4.0) / 2.0))
                cell = int(np.floor((yw + lane * 2.7) / 6.0))
                hh = ((lane * 73856093) ^ (cell * 19349663)) & 0xffff
                ln = 1.5 + (hh // 100 % 6) * 0.45
                ph = yw + lane * 2.7 - cell * 6.0 - (hh % 100) / 100.0 * 2.0
                if hh % 8 < 3 and abs(u) < hw - 1.0 and t == 3:
                    if 0 <= ph < ln:
                        c = C('water', 4)
                    elif ln <= ph < ln + 0.6 / DEN + 0.01:
                        c = C('water', 2)
                cv[Y, X] = c
            elif a <= hw + 1.0:
                cv[Y, X] = C('earth', 1) if u < 0 else C('earth_warm', 3)   # the banks
            elif a <= hw + 1.0 + 1.0 / DEN + 0.001:
                cv[Y, X] = C('grass', 2) if u < 0 else C('grass', 4)      # grass lip: dark west, lit east
    # bed stones: small lumps at the water's edge, lit top-left, dark underside
    for (yw, side) in stones:
        cx, hw = _rill_x(yw), _rill_hw(yw)
        sx = cx + side * (hw - 0.6)
        for Y in range(P(yw - 1.2, 0), P(yw + 1.3, 0)):
            for X in range(P(sx - 1.6, 0), P(sx + 1.6, 0)):
                if 0 <= Y < H and 0 <= X < W and cv[Y, X] // 8 in (FI['water'], FI['earth'], FI['earth_warm']):
                    ry = (Y / DEN - yw) / 1.25
                    rx = (X / DEN - sx) / 1.6
                    if rx * rx + ry * ry <= 1:
                        cv[Y, X] = C('stone', 4 if (ry < -0.2 and rx < 0.3) else (2 if ry > 0.45 else 3))
    # glints in pairs
    for yw in range(5, LIP_Y - 4, 17):
        cx = _rill_x(yw)
        Y, X = P(yw, 0), P(cx - 0.5, 0)
        for k in range(P(2)):
            if 0 <= Y < H and 0 <= X + k < W and cv[Y, X + k] // 8 == FI['water']:
                cv[Y, X + k] = C('water', 5)


# the brook's centre line (world px, canvas): out of the pool's south shore, a little south,
# then bending east and out of the picture past the boulders
BROOK = [tuple(p) for p in _W['brook']]


def _brook_curve(step_w=0.25):
    pts = np.array(BROOK)
    # Catmull-Rom through the points, sampled densely
    out = []
    P_ = np.vstack([pts[0], pts, pts[-1]])
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n = max(2, int(np.hypot(*(p2 - p1)) / step_w))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out = np.array(out)
    seg = np.hypot(*np.diff(out, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    tan = np.gradient(out, axis=0)
    tan /= np.maximum(1e-6, np.hypot(tan[:, 0], tan[:, 1]))[:, None]
    return out, s, tan


def _brook_hw(s):
    # wide where it leaves the pool, then a brook 6 to 8 world px wide that breathes along its run
    # (r6: a little more breathing, so it is no canal)
    lo, hi = BROOK_HW
    mid, amp = (lo + hi) / 2, (hi - lo) / 2
    # r7: 5 to 10 world px wide, breathing irregularly (two incommensurate waves), wide at the mouth
    return mid + amp * (0.62 * np.sin(s / 10.5 + 0.4) + 0.38 * np.sin(s / 4.1 + 1.0)) + 3.0 * np.exp(-s / 6.0)


def brook2(cv):
    """The pool's outlet: a brook in a natural bed (not a channel). Its banks are earth, lit where
    they face the light (south and east banks) and shaded where they face away; the grass lip
    follows; the water is shaded under the north/west bank; the current runs as lit dashes along
    the flow; a few bed stones sit at the edges and glints come in pairs."""
    H, W = cv.shape
    pts, sarc, tan = _brook_curve()
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    ymin, ymax = pts[:, 1].min() - 12, pts[:, 1].max() + 12
    Ys = np.arange(max(0, P(ymin, 0)), min(H, P(ymax, 0)))
    Xs = np.arange(max(0, P(pts[:, 0].min() - 12, 0)), W)
    YY, XX = np.meshgrid(Ys, Xs, indexing='ij')
    wy = YY / DEN + 0.5 / DEN
    wx = XX / DEN + 0.5 / DEN
    dist, idx = tree.query(np.stack([wx.ravel(), wy.ravel()], 1))
    dist = dist.reshape(wx.shape); idx = idx.reshape(wx.shape)
    tx, ty = tan[idx, 0], tan[idx, 1]
    nx_, ny_ = ty, -tx                     # left normal of the flow
    ox, oy = wx - pts[idx, 0], wy - pts[idx, 1]
    u = ox * nx_ + oy * ny_                # signed offset across the flow
    sa = sarc[idx]
    hw = _brook_hw(sa)
    # which side faces the light: a bank whose outward offset points south/east is lit
    side_lit = (ox + oy) > 0
    a = np.abs(u)
    cur = cv[Ys[0]:Ys[-1] + 1, Xs[0]:Xs[-1] + 1]
    fam = cur // 8
    okfam = np.isin(fam, [FI[n] for n in ('grass', 'grass_warm', 'grass_cool', 'leaf', 'water', 'water_warm', 'water_cool',
                                          'earth', 'earth_warm', 'earth_cool', 'path', 'path_warm', 'path_cool')])
    in_pool = np.isin(fam, [FI['water'], FI['water_warm'], FI['water_cool']]) & (wy < _W['pool_bottom'])
    water = (a <= hw) & okfam & (dist < 20)
    bank = (a > hw) & (a <= hw + 1.0) & okfam & ~in_pool
    lip = (a > hw + 1.0) & (a <= hw + 1.0 + 1.0 / DEN + 0.001) & okfam & ~in_pool
    out = cur.copy()
    t = np.full(cur.shape, 3)
    # r7: which side is the outside of a bend: the curvature vector points to the bend's centre
    dtan = np.gradient(tan, axis=0) / np.maximum(1e-6, np.gradient(sarc))[:, None]
    kap = ndi.gaussian_filter1d(dtan[:, 0] * tan[:, 1] - dtan[:, 1] * tan[:, 0], 12)   # along the left normal
    kk = kap[idx]
    outside = (np.sign(u) == -np.sign(kk)) & (np.abs(kk) > 0.012)
    inside = (np.sign(u) == np.sign(kk)) & (np.abs(kk) > 0.03)
    t[(a > hw - 1.2) & ~side_lit] = 2      # shade under the north/west bank
    t[(a > hw - 0.8) & outside] = 4        # r7: the light lane only on the outside of a bend
    # r7: shallows, a tone lighter, on the inside of the sharper bends, in a few broken patches
    shq = np.floor(sa / 4.0).astype(int)
    t[(a > hw - 2.4) & (a <= hw) & inside & ((((shq * 40503) >> 4) & 3) != 0)] = 4
    t[(a < hw - 2.8) & (sa > 10)] = 2      # the deeper middle a tone darker
    # the mouth: the pool's own calm body runs on into the brook (one body of water)
    # r4: the pool's calm body runs on into the brook and the brook's own tones begin at a
    # ragged line (a different place on each narrow lane), not on one row
    lane0 = np.floor((u + 6) / 0.9).astype(int)
    thr = 6.0 + 7.0 * ((((lane0 * 2654435761) >> 7) & 0xff) / 255.0)
    t[sa < thr] = 2
    t[(sa < thr + 4) & (a < hw * 0.5)] = 2
    # the current: streaks of irregular length (1.5 to 4 world px) lying with the flow, each over
    # its own 1 px shadow, on lanes 2.2 world px apart, about a quarter of the cells lit, so most
    # of the channel stays plain (no regular hatch)
    lane = np.floor((u + 6) / 2.2).astype(int)
    cell = np.floor((sa + lane * 2.9) / 6.5).astype(int)
    hh = ((lane * 73856093) ^ (cell * 19349663)) & 0xffff
    off = (hh % 100) / 100.0 * 2.5
    ln = 1.5 + (hh // 100 % 6) * 0.5
    pos = sa + lane * 2.9 - cell * 6.5 - off
    on = (hh % 9 < (2 if FIX else 3)) & (a < hw - 0.9) & (sa > thr + 2)   # r7: fewer streaks
    t[on & (pos >= 0) & (pos < ln)] = 4
    t[on & (pos >= ln) & (pos < ln + 1.0 / DEN + 0.01)] = 1
    wcode = np.vectorize(lambda k: C('water', int(k)))(t)
    out[water & ~in_pool] = wcode[water & ~in_pool]
    if FIX and DEN > 1:
        # r6: natural banks, no ruled outline: damp earth in clumps of two tones, broken in runs
        # by grass hanging over the water's edge; the grass lip is the lawn's own edge
        # r7: the bank line in runs (2 to 6 world px), the grass between runs hanging over the edge
        sq = np.floor(sa / BROOK_BANK_RUN + 0.8 * np.sin(sa / 5.3) + np.sign(u)).astype(int)
        hb = ((sq * 2654435761) ^ (np.sign(u).astype(int) + 3) * 40503) & 0xff
        # r8: the earth line shows on at most a quarter of the bank and never on the inside of a
        # bend; between its runs the grass hangs over the edge or the bank is a damp green patch
        earth_run = (hb % 4 == 0) & ~inside
        over = ~earth_run & (hb % 4 != 3)
        dampg = ~earth_run & (hb % 4 == 3)
        Xw, Yw = (XX / DEN).astype(int), (YY / DEN).astype(int)
        cl = (((Xw // 2) * 73856093) ^ ((Yw // 2) * 19349663)) & 0xff
        damp = np.where(side_lit, np.where(cl % 3 == 0, C('earth_warm', 3), C('earth_warm', 2)),
                        np.where(cl % 3 == 0, C('earth', 2), C('earth_cool', 2)))
        bnk = bank & earth_run
        out[bnk] = damp[bnk]
        dg = bank & dampg
        out[dg] = np.where(side_lit[dg], C('grass_cool', 2), C('leaf', 2))
        out[bank & over] = np.where(side_lit[bank & over], C('grass', 3), C('grass', 2))
        lipg = lip & ~over
        out[lipg] = np.where(side_lit[lipg], cur[lipg], step(cur[lipg], -1))
    else:
        out[bank & ~side_lit] = C('earth', 1)
        out[bank & side_lit] = C('earth_warm', 3)
        out[lip & ~side_lit] = C('grass', 2)
        out[lip & side_lit] = C('grass', 4)
    cv[Ys[0]:Ys[-1] + 1, Xs[0]:Xs[-1] + 1] = out
    # bed stones at the water's edge, lit high-left, dark beneath
    rng = np.random.default_rng(23)
    for k, sv in enumerate(np.arange(16, sarc[-1] - 8, 15.5)):
        i = int(np.searchsorted(sarc, sv))
        side = -1 if k % 2 else 1
        cx = pts[i, 0] + side * (_brook_hw(sv) - 0.4) * tan[i, 1]
        cy = pts[i, 1] - side * (_brook_hw(sv) - 0.4) * tan[i, 0]
        rx, ry = rng.uniform(1.4, 2.1), rng.uniform(1.0, 1.4)
        for Y in range(P(cy - ry, 0), P(cy + ry, 0) + 1):
            for X in range(P(cx - rx, 0), P(cx + rx, 0) + 1):
                if 0 <= Y < H and 0 <= X < W and cv[Y, X] // 8 in (FI['water'], FI['earth'], FI['earth_warm']):
                    vy = (Y / DEN + 0.5 / DEN - cy) / ry
                    vx = (X / DEN + 0.5 / DEN - cx) / rx
                    if vx * vx + vy * vy <= 1:
                        cv[Y, X] = C('stone', 4 if (vy < -0.2 and vx < 0.3) else (2 if vy > 0.45 else 3))
    # r7: two or three stones in the stream, a foam crescent on their upstream side, a dark wake below
    if FIX and DEN > 1:
        for k, sv in enumerate(BROOK_STONES):
            i = int(np.searchsorted(sarc, sv))
            off_ = (0.9 if k % 2 else -1.1)
            cx = pts[i, 0] + off_ * tan[i, 1]
            cy = pts[i, 1] - off_ * tan[i, 0]
            rx, ry = 2.5 - 0.3 * k, 1.6 - 0.1 * k
            tx_, ty_ = tan[i]
            for Y in range(P(cy - ry - 2.5, 0), P(cy + ry + 2.5, 0) + 1):
                for X in range(P(cx - rx - 2.5, 0), P(cx + rx + 2.5, 0) + 1):
                    if not (0 <= Y < H and 0 <= X < W) or cv[Y, X] // 8 != FI['water']:
                        continue
                    vy = (Y / DEN + 0.5 / DEN - cy)
                    vx = (X / DEN + 0.5 / DEN - cx)
                    al = vx * tx_ + vy * ty_            # along the flow
                    r = (vx / rx) ** 2 + (vy / ry) ** 2
                    if r <= 1:
                        cv[Y, X] = C('stone', 4 if (vy < -0.25 * ry and vx < 0.3 * rx) else (1 if (vy > 0.5 * ry or vx > 0.7 * rx) else 3))
                    elif r <= 2.0 and al < -0.1:
                        cv[Y, X] = C('snow', 5) if (r <= 1.5 and al < -0.5) else C('water', 4)
                    elif r <= 2.6 and al > 0.6 and abs(vx * ty_ - vy * tx_) < rx * 0.8:
                        cv[Y, X] = C('water', 2)
    # glints in pairs on the current
    for sv in np.arange(9, sarc[-1], 19.0):
        i = int(np.searchsorted(sarc, sv))
        Y, X = P(pts[i, 1], 0), P(pts[i, 0] - 0.5, 0)
        for k in range(P(2)):
            if 0 <= Y < H and 0 <= X + k < W and cv[Y, X + k] // 8 == FI['water']:
                cv[Y, X + k] = C('water', 5)


def fall2(cv):
    """The fall: a sheet about 8 world px wide spilling over the lip (a lit curl, a dark line
    under it), lit on its west edge and shaded on its east, broken white streaks running down; it
    strikes a rock step about halfway (a white plume, spray in pairs) and drops again a little
    narrower into the pool, where it foams and rings out. The rock beside it is dark and wet."""
    H, W = cv.shape
    cxl = _rill_x(LIP_Y - 1)
    y_top, y_mid, y_bot = LIP_Y - 1.0, LIP_Y + 30.0, POOL_Y + 2.0
    rng = np.random.default_rng(11)
    streak_x = [-2.7, -1.6, -0.4, 0.8, 1.9, 2.8]
    gaps = {sx: [(rng.uniform(0, 60), rng.uniform(2, 7)) for _ in range(4)] for sx in streak_x}
    for Y in range(P(y_top, 0), P(y_bot, 0)):
        yw = Y / DEN
        upper = yw < y_mid
        cx = cxl + (0.0 if upper else 0.8)
        seg0 = y_top if upper else y_mid
        hw = (3.6 if upper else 3.0) + (yw - seg0) / 26.0          # the sheet spreads as it falls
        if upper and yw < y_top + 3:
            hw = 3.6 + (y_top + 3 - yw) * 0.45      # a touch wider where it leaves the lip
        hl = hw + 0.55 * np.sin(yw / 3.3)          # the edges waver
        hr = hw + 0.55 * np.sin(yw / 2.7 + 1.0)
        for X in range(max(0, P(cx - hw - 2.5, 0)), min(W, P(cx + hw + 2.5, 0) + 1)):
            u = X / DEN + 0.5 / DEN - cx
            if -hl <= u <= hr:
                if u < -hl + 1.0:
                    t = 4                           # lit west edge
                elif u > hr - 1.0:
                    t = 1                           # shaded east edge
                elif u > hr - 2.2:
                    t = 2
                else:
                    t = 3
                c = C('water', t)
                for sx in streak_x:
                    if abs(u - sx) < 0.5 and t in (2, 3):
                        broken = any(g0 <= (yw - y_top) % 60 < g0 + gl for (g0, gl) in gaps[sx])
                        if not broken:
                            c = C('snow', 4) if sx < 1 else C('water', 4)
                lipw = 1.5 + 0.9 * abs(np.sin(u * 1.9 + 0.7)) + 0.5 * abs(np.sin(u * 4.3))
                if upper and yw < y_top + lipw:
                    c = C('snow', 5) if u < hw - 1.2 else C('snow', 4)      # white water breaking over the lip
                elif upper and yw < y_top + lipw + 1.0 / DEN + 0.01:
                    c = C('water', 4) if u < 0 else C('water', 2)           # the curl's underside
                cv[Y, X] = c
            elif -hl - 2.0 <= u <= hr + 2.0 and cv[Y, X] // 8 in (FI['crag'], FI['crag_warm'], FI['crag_cool']) and                     cv[Y, X] % 8 not in (0, 6, 7):
                cv[Y, X] = step(cv[Y:Y + 1, X:X + 1], -1)[0, 0]             # wet rock beside it
    # r3: the rock shelf the first drop strikes: a chipped lip of the face's own rock standing
    # out 2 world px west and 4 east of the water, its top lit (a glint at the upper left), its
    # front a tone down, a dark line under it and shade on the face below; the second drop
    # pours from its front edge with white running down at each side
    hw2 = 3.0
    for Y in range(P(y_mid - 0.5, 0), P(y_mid + 8.0, 0)):
        yw = Y / DEN
        for X in range(P(cxl - 7.5, 0), P(cxl + 9.5, 0) + 1):
            if not (0 <= Y < H and 0 <= X < W):
                continue
            u = X / DEN + 0.5 / DEN - cxl
            ext = (2.4 if u < 0 else 4.6)            # how far it stands out past the water
            e = max(0.0, abs(u) - hw2) / ext         # 0 at the water's edge, 1 at the tip
            if e > 1.0:
                continue
            # a lens of rock: its top drops and its underside rises towards the rounded tip
            top = y_mid + 0.6 + 1.6 * e ** 2 + 0.25 * np.sin(u * 3.1)
            bot = y_mid + 4.9 - 2.4 * e ** 1.6 - 0.35 * abs(np.sin(u * 2.3 + 0.4))
            if yw < top or yw > bot + 2.0:
                continue
            onrock = cv[Y, X] // 8 in (FI['crag'], FI['crag_warm'], FI['crag_cool'])
            if abs(u) < hw2 - 0.6:
                continue                         # the second drop itself
            if yw > bot:
                if onrock and cv[Y, X] % 8 > 1:  # its shade on the face below
                    cv[Y, X] = step(cv[Y:Y + 1, X:X + 1], -2 if yw < bot + 1.0 else -1)[0, 0]
                continue
            rr = (yw - top) / max(0.5, bot - top)
            if abs(u) < hw2 + 0.6 and rr < 0.85:
                # the spill: white running down over the front at each side of the drop
                cv[Y, X] = C('snow', 5) if (u < 0 or rr < 0.3) else C('snow', 4)
                continue
            if rr < 0.2:
                c = C('crag_warm', 5) if (u < 0 and e < 0.7) else C('crag_warm', 4)
                if DEN == 1 and (e > 0.55 or X % 3 == 1):
                    c = C('crag', 3)                 # r4: at 1x a chipped lit edge, not a tan bar
            elif rr < 0.78:
                c = C('crag_warm', 3) if (u < 0 or rr < 0.4) else C('crag', 3)
                if e > 0.55 and rr > 0.5:
                    c = C('crag', 2)
                if abs(np.sin(u * 5.1 + yw * 3.3)) > 0.95:
                    c = C('crag', 1)             # a chip
            else:
                c = C('crag', 0)
            cv[Y, X] = c
    # the plume where it strikes the step, and the foam where it meets the pool
    blobs = []
    for (yc, wide, tall) in ((y_mid - 0.6, 4.4, 2.0), (y_bot - 0.5, 7.5, 2.6)):
        cx = cxl + 0.4
        parts = [(cx + rng.uniform(-0.6, 0.6) * wide, yc + rng.uniform(-0.4, 0.4) * tall, wide * rng.uniform(0.35, 0.55),
                  tall * rng.uniform(0.6, 0.95)) for _ in range(5)]
        for Y in range(P(yc - tall * 1.5, 0), P(yc + tall * 1.5, 0) + 1):
            for X in range(P(cx - wide * 1.4, 0), P(cx + wide * 1.4, 0) + 1):
                if not (0 <= Y < H and 0 <= X < W):
                    continue
                r = min(((X / DEN - px) / pw) ** 2 + ((Y / DEN - py) / ph) ** 2 for (px, py, pw, ph) in parts)
                v = (Y / DEN - yc) / tall
                if r <= 1.0:
                    if v < -0.2 and r < 0.75:
                        cv[Y, X] = C('snow', 5)
                    elif r < 0.75:
                        cv[Y, X] = C('snow', 4)
                    else:
                        cv[Y, X] = C('water', 4)
    # spray in pairs beside the plumes
    for (yc, cx0) in ((y_bot - 3, cxl),):
        for k in range(8):
            side = -1 if k % 2 else 1
            dist = 4.5 + (k // 2) * 1.6 + rng.uniform(0, 0.8)
            sx = cx0 + side * dist
            sy = yc - (k // 2) * 0.9 - rng.uniform(0, 0.6)
            Y, X = P(sy, 0), P(sx, 0)
            if 0 <= Y < H and 0 <= X < W:
                cv[Y, X] = C('snow', 5) if k < 4 else C('water', 4)

