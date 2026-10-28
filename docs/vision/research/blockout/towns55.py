"""v55's settlement footprints (Matt's brief of 27 Oct, layout step 1), drawn at overview scale on the v55 canvas.

Each town is laid out from a street skeleton (its routes, plus the side streets, back lanes, quays and squares written
here per town) and filled with discrete buildings at the size guide's footprints (size-guide.md 4: a cottage stands on
80 x 48, a two-storey house 64 to 96 wide, a shop 64 to 88, a workshop 80 to 112, a warehouse 112 to 160, a city
building 64 to 96 on 48 to 64), each on one tier, set back from its street with a garden or yard behind. A building is
counted as Matt defines it: homes, shops, workshops and public buildings, enterable or not; market stalls, sheds and the
separate doors of one apartment building are not counted (they are not placed as buildings at all).

What a town's surroundings are for (the fields, orchards, corrals, railyards, quays, kilns) is painted round it as its
working outskirts, so the overview shows why the town is there. Steps 5 to 7 (gameplay-scale building, residents, animals
and props, and the journey checks) are a plan in README.md, "v55", for the lanes and the world editor.

Called by geo55.py (lay_all); not run on its own."""
import math
import numpy as np
from scipy import ndimage as ndi
import geo5 as g
from geo5 import CELL

H = W = None                      # set by geo55.set_dims
PX = PY = None

# footprints in world px (size-guide.md 4); (w range, d range): w along the street, d back from it
BLD = {'cottage': ((56, 80), (40, 48)), 'house': ((80, 104), (48, 64)), 'farmhouse': ((104, 128), (56, 64)), 'shop': ((64, 88), (48, 56)),
       'inn': ((112, 144), (64, 80)), 'workshop': ((88, 120), (56, 72)), 'public': ((88, 136), (56, 72)), 'warehouse': ((112, 160), (64, 88)),
       'townhouse': ((40, 56), (48, 56)), 'tenement': ((88, 128), (48, 64)), 'office': ((96, 144), (72, 96)), 'stilt': ((48, 64), (40, 48)),
       'boathouse': ((72, 104), (56, 64)), 'barn': ((112, 144), (64, 80)), 'mill': ((80, 104), (56, 72)), 'station': ((112, 160), (48, 56)),
       'chapel': ((64, 104), (48, 80)), 'keep': ((112, 160), (80, 112)), 'hall': ((104, 160), (48, 80)), 'tower': ((64, 80), (64, 80)),
       'hangar': ((128, 176), (80, 96)), 'lodge': ((88, 112), (56, 64)),
       # the forms that give each town its own grain (a form is drawn and sized as itself, counted as its type)
       'oldhouse': ((40, 56), (32, 40)), 'aptrow': ((96, 144), (32, 40)), 'longwarehouse': ((176, 224), (64, 88)), 'slab': ((144, 208), (88, 120)),
       'bigtower': ((96, 128), (96, 128)), 'adobe': ((40, 56), (32, 40)), 'depot': ((176, 224), (56, 72)), 'frontshop': ((80, 104), (48, 64)),
       'saloon': ((104, 136), (64, 72)), 'terrace': ((96, 160), (32, 40)), 'barracks': ((96, 128), (48, 64)),
       'skyport': ((176, 224), (88, 112)), 'forge': ((88, 112), (48, 64)),
       # a continuous frontage (Matt's Eastward street, 28 Oct): one record a block of fronts sharing walls, its bays 3 to 8 cells
       'row_tenement': ((24, 192), (24, 56)), 'row_house': ((24, 192), (24, 56)), 'row_shop': ((24, 192), (24, 64)),
       # Highgarth, an old post town on the pass road (Matt, 28 Oct): its own forms
       'machiya': ((24, 64), (40, 56)), 'honjin': ((56, 104), (48, 80)), 'temple_hall': ((96, 128), (64, 80)), 'pagoda': ((32, 40), (32, 40)),
       'watchkeep': ((48, 64), (48, 64)), 'minka_thatched': ((56, 88), (48, 72)), 'kura': ((32, 48), (32, 40)), 'bathhouse': ((64, 96), (48, 64)),
       'machiya_row': ((24, 144), (32, 56)), 'shed': ((32, 48), (24, 40))}
TYPE_OF = {'oldhouse': 'townhouse', 'aptrow': 'tenement', 'longwarehouse': 'warehouse', 'slab': 'office', 'bigtower': 'tower', 'adobe': 'cottage',
           'depot': 'station', 'frontshop': 'shop', 'saloon': 'inn', 'terrace': 'townhouse', 'barracks': 'public', 'skyport': 'station',
           'forge': 'workshop', 'row_tenement': 'tenement', 'row_house': 'townhouse', 'row_shop': 'shop', 'machiya': 'townhouse', 'honjin': 'inn',
           'temple_hall': 'public', 'pagoda': 'tower', 'watchkeep': 'keep', 'minka_thatched': 'farmhouse', 'kura': 'barn', 'bathhouse': 'public',
           'machiya_row': 'townhouse', 'shed': 'barn'}
FALSE_FRONT = {'frontshop', 'saloon', 'depot'}
KIND_OF = {'warehouse': 'warehouse', 'office': 'tower', 'tower': 'tower', 'hangar': 'hangar', 'keep': 'keep', 'station': 'terminal'}
# ground a building, yard or street may be laid on (natural ground and v54's settlement paint, never water, rock or a barrier)
BUILDABLE = {'meadow', 'watermeadow', 'steppe', 'scrub', 'desert', 'broadleaf', 'conifer', 'sand', 'alpine', 'barren', 'ash', 'blacksand',
             'yard', 'lavastone', 'fireweed', 'basalt', 'deadwood', 'garden', 'badland', 'scroll', 'carr', 'heath', 'field', 'field2',
             'orchard', 'hedge', 'fallow', 'plaza', 'clearing', 'lawn', 'gorse', 'wild', 'building', 'lane', 'airfield', 'apron', 'tor',
             'boulders', 'thicket', 'felltree', 'bramble', 'scree', 'wash', 'reeds', 'trail', 'boulevard', 'arcade', 'quay', 'warehouse',
             'tower', 'neon', 'retain', 'stall', 'fishmarket', 'hangar', 'terminal', 'pad', 'dock', 'crane'}
STREETABLE = BUILDABLE | {'path', 'road', 'stair', 'bridge'}
ROUTE = {'path', 'road', 'bridge', 'stair', 'bar', 'trail', 'viaduct'}
# street classes and widths in cells (size-guide.md 0: a town street 48 px frontage to frontage, a road 32 or more, a lane 24, a
# footpath 16); an arrival keeps its route's own width
CLASS_W = {'main': 6, 'side': 4, 'lane': 3, 'close': 2}


def _review():
    import os, sys
    root = os.environ.get('REPO_ROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    p = os.path.join(root, 'scripts', 'review')
    if p not in sys.path:
        sys.path.insert(0, p)
    import town_plan
    return town_plan


def orth(pts, wc):
    """A polyline squared onto the soft grid: x and y runs on cell lines (on a cell's edge for an even width, its middle for
    an odd one), a nearly straight leg as one run, a slanting leg as a Z of three runs; runs shorter than two cells merged."""
    return _review().orth(pts, wc)


def band_mask(line, wc, metric):
    """The cells a street covers, on the whole canvas (the checker's own rule, scripts/review/town_plan.py)."""
    m = np.zeros((H, W), bool)
    xs = [p[0] for p in line]; ys = [p[1] for p in line]
    hw = wc * CELL / 2 + CELL
    c0, c1 = max(0, int((min(xs) - hw) // CELL)), min(W, int((max(xs) + hw) // CELL) + 1)
    r0, r1 = max(0, int((min(ys) - hw) // CELL)), min(H, int((max(ys) + hw) // CELL) + 1)
    m[r0:r1, c0:c1] = _review().band(line, wc, metric, (c0, r0, c1 - c0, r1 - r0))
    return m


def split_laid(line, laid, wc=None):
    """The parts of a street's centre line that were laid (cell runs of at least three cells), as polylines."""
    x, y, al, tot = g.densify(line, 4)
    if len(x) < 2:
        return []
    r = np.clip((np.asarray(y) // CELL).astype(int), 0, H - 1); c = np.clip((np.asarray(x) // CELL).astype(int), 0, W - 1)
    on = laid[r, c]
    out, cur = [], []
    verts = [tuple(p) for p in line]
    vat = [0.0]
    for (a0, b0), (a1, b1) in zip(verts, verts[1:]):
        vat.append(vat[-1] + math.hypot(a1 - a0, b1 - b0))
    for i in range(len(x)):
        if on[i]:
            cur.append(i)
        elif cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    pieces = []
    for run in out:
        a0, a1 = al[run[0]], al[run[-1]]
        if a1 - a0 < 3 * CELL:
            continue
        pts = [(float(x[run[0]]), float(y[run[0]]))] + [verts[j] for j in range(len(verts)) if a0 < vat[j] < a1] + [(float(x[run[-1]]), float(y[run[-1]]))]
        if wc is not None:                                   # a soft-grid street's ends on its cell lines
            off = 0 if wc % 2 == 0 else CELL // 2
            pts = [(round((p[0] - off) / CELL) * CELL + off, round((p[1] - off) / CELL) * CELL + off) for p in pts]
            pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
            if len(pts) < 2:
                continue
        pieces.append([[round(p[0] * 2) / 2, round(p[1] * 2) / 2] for p in pts])
    return pieces


def C(x, y):
    return int(y // CELL), int(x // CELL)


class Town:
    """One settlement: its streets, squares, buildings, yards and working outskirts."""

    def __init__(self, T, name, centre, size, target, purpose, setting, neighbourhoods=(), gathering=(), seed=None):
        self.T = T; self.name = name; self.centre = centre; self.size = size; self.target = target
        self.purpose = purpose; self.setting = setting; self.neighbourhoods = list(neighbourhoods); self.gathering = list(gathering)
        self.buildings = []; self.streets = []; self.spaces = []; self.outskirts = []
        self.rng = np.random.default_rng(g.stable_name_seed(name, 2 ** 31) if seed is None else seed)
        self.level = 1; self.slope_max = 0.016
        self.cap = target[1] if isinstance(target, (tuple, list)) else target

    # -------------------------------------------------------------------------------------- the masks
    def free(self, a, b, c, d, kinds=BUILDABLE):
        T = self.T; K = T['K']
        if a < 1 or b < 1 or c >= H - 1 or d >= W - 1:
            return False
        blk = K[a:c, b:d]
        if not np.isin(blk, list(kinds)).all():
            return False
        if getattr(self, '_hand', False):                            # by hand: the footprint itself must be clear, nothing more
            if T['taken'][a:c, b:d].any() or T['street'][a:c, b:d].any() or T['keepout'][a:c, b:d].any():
                return False
            return True
        if T['taken'][a - 1:c + 1, b - 1:d + 1].any() or T['street'][a:c, b:d].any() or T['barrier'][a:c, b:d].any():
            return False
        tt = T['tiers_pre'][a:c, b:d]
        if tt.max() - tt.min() > self.level:                       # a footprint lies on one tier (size-guide.md 2): at most
            return False                                           # `level` tiers are levelled under it (put() terraces it)
        if T['slope'][a:c, b:d].max() > self.slope_max:
            return False
        if T['keepout'][a:c, b:d].any():
            return False
        return True

    # -------------------------------------------------------------------------------------- streets and squares
    def street(self, pts, width='lane', kind='lane', name=None, smooth=None, route=None):
        """A street on the soft grid (ground-rules.md 4: straight runs on cells along x or y, one width, turns at least two
        cells apart): its class gives its width (CLASS_W, size-guide.md 0), its line is squared to x and y runs (orth), and it
        is painted walkable where the ground allows (never over water, a barrier, a building or a keep-out; small water is a
        bridge). route: the street is that regional route's own line through the town (widened to the class, not squared).
        The parts actually laid are kept as its pieces (the plan's streets)."""
        T = self.T; K = T['K']
        cls = width if isinstance(width, str) else {24: 'lane', 32: 'side', 40: 'main', 48: 'main', 16: 'close'}[int(width)]
        wc = CLASS_W[cls]
        if route:
            line = [(float(x), float(y)) for x, y in pts]; metric = 'euclid'
        else:
            line = orth(pts, wc); metric = 'cheb'
        if len(line) < 2:
            return line
        m = band_mask(line, wc, metric)
        hw_c = int(math.ceil(wc / 2))
        water = np.isin(K, ['river', 'creek', 'channel', 'canal'])
        cl = band_mask(line, 1, metric) & water                      # where the centre line crosses water: a bridge as wide as the street
        cross = ndi.binary_dilation(cl, structure=np.ones((3, 3), bool), iterations=hw_c) & m if cl.any() else np.zeros_like(m)
        wet = cross & water & ~T['hardbar'] & ~T['taken']
        bank = ndi.binary_dilation(wet, iterations=1) & ~T['hardbar']          # a bridge's abutments: the bank beside it may be laid
        ok = m & np.isin(K, list(STREETABLE)) & (~T['barrier'] | bank) & ~T['keepout'] & ~T['taken']
        blocked = m & (T['taken'] | (T['barrier'] & ~bank & ~np.isin(K, list(ROUTE))) | (water & ~wet))   # a building, barrier or water alongside: cut there
        paint = ok & ~np.isin(K, list(ROUTE))
        K[paint] = kind; K[wet] = 'bridge'
        T['street'] |= ok | wet
        T['used'] |= ok | wet
        laid = ok | wet | np.isin(K, list(ROUTE)) & m
        if blocked.any():
            laid &= ~ndi.binary_dilation(blocked, structure=np.ones((3, 3), bool), iterations=hw_c)
        pieces = split_laid(line, laid, wc if metric == 'cheb' else None)
        self.streets.append({'name': name, 'kind': kind, 'cls': cls, 'width_cells': wc, 'width_px': wc * CELL, 'route': route, 'metric': metric,
                             'pts': [[int(round(x)), int(round(y))] for x, y in line], 'pieces': pieces})
        return line

    def street_rec(self, pts):
        p0 = [int(round(pts[0][0])), int(round(pts[0][1]))]
        for s_ in self.streets:
            if s_['pts'] and (s_['pts'][0] == p0 or (s_['route'] and abs(s_['pts'][0][0] - p0[0]) + abs(s_['pts'][0][1] - p0[1]) < 24)):
                return s_
        return None

    def frontage(self, pts, sides=(1, -1), form='row_house', block=(96, 176), depth=(32, 40), alley=(0, 0, 8), stair_every=0,
                 roofs=('flat', 'tin', 'tile'), props=('sign', 'awning', 'potted plants'), false_front=False, limit=None, plot=None, why=None):
        """A continuous frontage along a street (Matt's Eastward street, 28 Oct): blocks of fronts sharing their walls, built to the
        street's edge with no setback, separated by an alley of one cell at most, or by a stair alley of two cells (a street) every
        stair_every blocks; each block's bays 3 to 8 cells wide with their own roofs and storeys; frontage props at the bays."""
        T = self.T; K = T['K']; r = self.rng
        rec = self.street_rec(pts)
        hw = (rec['width_px'] if rec else 24) / 2
        if rec is not None:
            rec['frontage'] = 'continuous'; rec['max_gap_cells'] = 1; rec.setdefault('frontage_props', [])
            rec['frontage_reason'] = why or FRONTAGE_WHY.get(self.name, 'a dense core where land on the street is dear')
        segs = []
        P_ = [tuple(map(float, q)) for q in (_rdp_pts([tuple(q) for q in pts], 6) if (rec and rec.get('route')) else pts)]
        for (ax, ay), (bx, by) in zip(P_, P_[1:]):
            L = math.hypot(bx - ax, by - ay)
            if L < 48:
                continue
            if abs(by - ay) <= 0.36 * abs(bx - ax):                  # an east-west stretch (a route's gentle curve taken as straight)
                segs.append(('x', min(ax, bx), max(ax, bx), (ay + by) / 2))
            elif abs(bx - ax) <= 0.36 * abs(by - ay):
                segs.append(('y', min(ay, by), max(ay, by), (ax + bx) / 2))
        placed = 0; nblock = 0
        for side in sides:
            for (ax_, a0, a1, c) in segs:
                pos = math.ceil((a0 + 8) / CELL) * CELL
                while pos < a1 - 24:
                    if limit is not None and placed >= limit:
                        return placed
                    L = min(int(r.integers(block[0] // CELL, block[1] // CELL + 1)) * CELL, int((a1 - 8 - pos) // CELL) * CELL)
                    if L < 24:
                        break
                    d = int(r.integers(depth[0] // CELL, depth[1] // CELL + 1)) * CELL
                    edge = math.ceil((c + hw) / CELL) * CELL if side > 0 else math.floor((c - hw) / CELL) * CELL   # the street's edge, on a cell line
                    if ax_ == 'x':
                        x, y, w, h = pos, (edge if side > 0 else edge - d), L, d
                    else:
                        x, y, w, h = (edge if side > 0 else edge - d), pos, d, L
                    ok = False
                    for dd in range(d, 23, -8):                          # shallower first, then narrower: the row stays unbroken
                        for shrink in range(0, L - 16, 8):
                            if L - shrink < 24:
                                break
                            if ax_ == 'x':
                                xx, yy, ww, hh = x, (edge if side > 0 else edge - dd), L - shrink, dd
                            else:
                                xx, yy, ww, hh = (edge if side > 0 else edge - dd), y, dd, L - shrink
                            if self.hand(xx, yy, ww, hh, form, plot=plot):
                                ok = True; L -= shrink; d = dd; break
                            self.T.get('hand_fail', []) and self.T['hand_fail'].pop()
                        if ok:
                            break
                    if not ok:
                        pos += CELL; continue
                    b = self.buildings[-1]
                    bays, left = [], L
                    while left >= 24:
                        bw = min(left, int(r.integers(3, 9)) * CELL)
                        if 0 < left - bw < 24:
                            bw = left
                        bays.append({'w_cells': bw // CELL, 'storeys': int(r.integers(1, 4)), 'roof': roofs[int(r.integers(0, len(roofs)))],
                                     **({'false_front': True} if false_front else {})})
                        left -= bw
                    b['bays'] = bays; b['frontage'] = rec['name'] if rec else None
                    at = pos
                    for bay in bays:                                     # one or two frontage props at each bay's front
                        for k in range(int(r.integers(1, 3))):
                            kind = props[int(r.integers(0, len(props)))]
                            u = at + (k + 0.5) * bay['w_cells'] * CELL / 2
                            xy = (u, edge + side * 4) if ax_ == 'x' else (edge + side * 4, u)
                            if rec is not None:
                                rec['frontage_props'].append({'kind': kind, 'at_px': [int(xy[0]), int(xy[1])]})
                        at += bay['w_cells'] * CELL
                    placed += 1; nblock += 1
                    pos += L
                    if stair_every and nblock % stair_every == 0:      # a stair alley two cells wide climbs between the blocks
                        ca = pos + CELL
                        far = edge + side * (d + 24)
                        line = [(ca, edge - side * 2), (ca, far)] if ax_ == 'x' else [(edge - side * 2, ca), (far, ca)]
                        self.street(line, 'close', kind='stair', name=None)
                        self.streets[-1]['alley'] = True
                        pos += 2 * CELL
                    else:
                        pos += int(alley[int(r.integers(0, len(alley)))])
        self._close_gaps(segs, sides, hw, form)
        if rec is not None and placed < 2:                           # not a row after all: the street stays detached
            rec['frontage'] = 'detached'; rec.pop('max_gap_cells', None); rec['frontage_props'] = []
        return placed

    def _close_gaps(self, segs, sides, hw, form):
        """Gaps left in a continuous frontage (two to six cells, between two fronts or a front and a cross street): filled with a
        narrow front where it stands, else the neighbouring front is widened over it."""
        T = self.T; K = T['K']
        for side in sides:
            for (ax_, a0, a1, c) in segs:
                edge = math.ceil((c + hw) / CELL) * CELL if side > 0 else math.floor((c - hw) / CELL) * CELL
                line_rc = int(edge // CELL) if side > 0 else int(edge // CELL) - 1
                lo, hi = int(a0 // CELL) + 1, int(a1 // CELL) - 1
                for it in range(3):
                    cells = T['taken'][line_rc, lo:hi] if ax_ == 'x' else T['taken'][lo:hi, line_rc]
                    stops = (T['street'][line_rc, lo:hi] if ax_ == 'x' else T['street'][lo:hi, line_rc]) & ~cells
                    idx = np.nonzero(cells)[0]
                    if len(idx) < 2:
                        break
                    i = idx[0]; changed = False
                    while i < idx[-1]:
                        if cells[i]:
                            i += 1; continue
                        j = i
                        while j < len(cells) and not cells[j] and not stops[j]:
                            j += 1
                        n = int(j - i)
                        if 2 <= n <= 6:
                            g0 = (lo + i) * CELL
                            for dd in (40, 32, 24):
                                if ax_ == 'x':
                                    xx, yy, ww, hh = g0, (edge if side > 0 else edge - dd), n * CELL, dd
                                else:
                                    xx, yy, ww, hh = (edge if side > 0 else edge - dd), g0, dd, n * CELL
                                if n >= 3 and self.hand(xx, yy, ww, hh, form):
                                    self.buildings[-1]['bays'] = [{'w_cells': n, 'storeys': 1 + n % 3, 'roof': 'flat'}]
                                    changed = True; break
                                if T.get('hand_fail'):
                                    T['hand_fail'].pop()
                                # widen the front before the gap over it
                                prev = next((b for b in self.buildings[::-1] if b.get('bays') and
                                             ((ax_ == 'x' and b['x'] + b['w'] == g0 and b['y'] < line_rc * CELL + CELL and b['y'] + b['h'] > line_rc * CELL) or
                                              (ax_ == 'y' and b['y'] + b['h'] == g0 and b['x'] < line_rc * CELL + CELL and b['x'] + b['w'] > line_rc * CELL))), None)
                                if prev is not None:
                                    if ax_ == 'x':
                                        a_, b_, c_, e_ = prev['y'] // CELL, (prev['x'] + prev['w']) // CELL, (prev['y'] + prev['h']) // CELL, (prev['x'] + prev['w']) // CELL + n
                                    else:
                                        a_, b_, c_, e_ = (prev['y'] + prev['h']) // CELL, prev['x'] // CELL, (prev['y'] + prev['h']) // CELL + n, (prev['x'] + prev['w']) // CELL
                                    blk = K[a_:c_, b_:e_]
                                    if blk.size and np.isin(blk, list(BUILDABLE)).all() and not T['taken'][a_:c_, b_:e_].any() and not T['street'][a_:c_, b_:e_].any():
                                        K[a_:c_, b_:e_] = KIND_OF.get(prev['use'], 'building'); T['taken'][a_:c_, b_:e_] = True
                                        if ax_ == 'x':
                                            prev['w'] += n * CELL
                                        else:
                                            prev['h'] += n * CELL
                                        if n >= 3:
                                            prev['bays'].append({'w_cells': n, 'storeys': 1 + n % 3, 'roof': prev['bays'][-1]['roof']})
                                        else:
                                            prev['bays'][-1]['w_cells'] += n
                                        changed = True
                                break
                        i = max(j, i + 1)
                    if not changed:
                        break

    def S(self, name):
        """A street's laid line, by name."""
        return next(s_['pts'] for s_ in self.streets if s_['name'] == name)

    def to_route(self, x, y, route, cls='lane', name=None):
        """A street from (x, y) straight to the nearest point of a route (closing a loop through the town)."""
        p = np.asarray(self.T['route_px'][route], float)
        i = int(np.argmin(np.hypot(p[:, 0] - x, p[:, 1] - y)))
        return self.street([(x, y), (float(p[i, 0]), float(p[i, 1]))], cls, name=name)

    def main(self, route_name, box, cls='main', name=None):
        """A regional route's part through the town as its main street (widened to the class along the route's own line)."""
        pts = route_part(self.T, route_name, box)
        if len(pts) >= 2:
            self.street(pts, cls, name=name or route_name, route=route_name)
        return pts

    def square(self, cx, cy, rx, ry, kind='plaza', name=None, rough=None):
        """A square (or a green): a rectangle on whole cells round (cx, cy), paved or grassed where the ground allows."""
        T = self.T; K = T['K']
        x0, y0 = int(round((cx - rx) / CELL)), int(round((cy - ry) / CELL)); x1, y1 = int(round((cx + rx) / CELL)), int(round((cy + ry) / CELL))
        for _ in range(12):                                          # shrunk off any building it would cover
            tk = T['taken'][y0:y1, x0:x1]
            if not tk.any() or x1 - x0 < 3 or y1 - y0 < 3:
                break
            cand = {'n': tk[0].sum(), 's': tk[-1].sum(), 'w': tk[:, 0].sum(), 'e': tk[:, -1].sum()}
            side = max(cand, key=cand.get)
            if cand[side] == 0:
                rr, cc = np.nonzero(tk); side = 'n' if rr.mean() < tk.shape[0] / 2 else 's'
            if side == 'n': y0 += 1
            elif side == 's': y1 -= 1
            elif side == 'w': x0 += 1
            else: x1 -= 1
        if T['taken'][y0:y1, x0:x1].any():
            return
        m = np.zeros((H, W), bool); m[y0:y1, x0:x1] = True
        m &= np.isin(K, list(STREETABLE)) & ~T['barrier'] & ~T['keepout'] & ~T['taken'] & ~np.isin(K, ['bridge'])
        K[m & ~np.isin(K, ['road', 'path', 'stair'])] = kind
        T['street'] |= m; T['used'] |= m
        self.spaces.append({'kind': 'square' if kind == 'plaza' else ('green' if kind == 'garden' else kind), 'name': name, 'x': int(cx), 'y': int(cy),
                            'rx': int(rx), 'ry': int(ry), 'cells': [x0, y0, x1 - x0, y1 - y0]})

    # -------------------------------------------------------------------------------------- buildings
    def put(self, x0, y0, w, d, use, counted=True, behind=None):
        """One building at (x0, y0) of w x d world px (snapped to the 8 px grid); behind: (dx, dy, depth) of its plot."""
        if counted and self.count() >= self.cap:
            return False
        x0 = int(round(x0 / CELL)) * CELL; y0 = int(round(y0 / CELL)) * CELL
        w = max(CELL, int(round(w / CELL)) * CELL); d = max(CELL, int(round(d / CELL)) * CELL)
        a, b = C(x0, y0); c, e = a + d // CELL, b + w // CELL
        if not self.free(a, b, c, e):
            return False
        T = self.T; K = T['K']
        tt = T['tiers_pre'][a:c, b:e]
        if tt.max() != tt.min():                                   # levelled: the footprint's ground set to its middle tier
            lo = int(np.median(tt)); T['tiers_pre'][a:c, b:e] = lo
            T['h'][a:c, b:e] = (lo + 0.5) / 30.0
            T.setdefault('levelled', []).append([int(x0), int(y0), int(w), int(d)])
        K[a:c, b:e] = KIND_OF.get(TYPE_OF.get(use, use), 'building')
        T['taken'][a:c, b:e] = True; T['used'][a - 1:c + 1, b - 1:e + 1] = True
        self.buildings.append({'x': x0, 'y': y0, 'w': w, 'h': d, 'use': TYPE_OF.get(use, use), 'form': use, 'counted': bool(counted)})
        if behind:                                                  # the plot: a garden or yard behind, where it is free
            dx, dy, dep, kind = behind
            if dy:
                ya, yb = (c, c + dep // CELL) if dy > 0 else (a - dep // CELL, a)
                xa, xb = b, e
            else:
                xa, xb = (e, e + dep // CELL) if dx > 0 else (b - dep // CELL, b)
                ya, yb = a, c
            ya, yb, xa, xb = max(1, ya), min(H - 1, yb), max(1, xa), min(W - 1, xb)
            sub = K[ya:yb, xa:xb]
            ok = np.isin(sub, list(BUILDABLE - {'building', 'warehouse', 'tower', 'keep', 'hangar', 'terminal'} - ROUTE)) & ~T['taken'][ya:yb, xa:xb] \
                & ~T['street'][ya:yb, xa:xb] & ~T['barrier'][ya:yb, xa:xb] & ~T['keepout'][ya:yb, xa:xb]
            sub[ok] = kind; T['used'][ya:yb, xa:xb] |= ok
            if ok.any():
                rr, cc = np.nonzero(ok)
                self.buildings[-1]['plot'] = [int(xa + cc.min()), int(ya + rr.min()), int(cc.max() - cc.min() + 1), int(rr.max() - rr.min() + 1), kind]
                T.setdefault('authored_protected_cells', []).append(self.buildings[-1]['plot'][:4])
        return True

    def place(self, cx, cy, use, w=None, d=None, r=96, plot=None, counted=True, within=None):
        """A principal building (a keep, a hall, a chapel) near (cx, cy): its ground levelled under it, searched outward."""
        (w0, w1), (d0, d1) = BLD[use]
        w = w or (w0 + w1) / 2; d = d or (d0 + d1) / 2
        lv, sm = self.level, self.slope_max
        self.level, self.slope_max = 40, 1.0
        try:
            for rr in range(0, r + 1, 8):
                for k in range(max(1, rr // 4)):
                    a = 2 * math.pi * k / max(1, rr // 4)
                    x_, y_ = cx + rr * math.cos(a) - w / 2, cy + rr * math.sin(a) - d / 2
                    if within is not None:
                        a_, b_ = C(round(x_ / CELL) * CELL, round(y_ / CELL) * CELL)
                        if not within[a_:a_ + int(round(d / CELL)), b_:b_ + int(round(w / CELL))].all():
                            continue
                    if self.put(x_, y_, w, d, use, counted, plot):
                        return True
        finally:
            self.level, self.slope_max = lv, sm
        return False

    def hand(self, x, y, w, d, form, plot=None, counted=True):
        """A building placed by hand (a hand-authored plan): its ground levelled under it; a failure is logged, not hidden."""
        lv, sm = self.level, self.slope_max
        self.level, self.slope_max, self._hand = 40, 1.0, True
        try:
            ok = self.put(x, y, w, d, form, counted, plot)
        finally:
            self.level, self.slope_max, self._hand = lv, sm, False
        if not ok:
            self.T.setdefault('hand_fail', []).append((self.name, form, x, y, w, d))
        return ok

    def adopt(self, packet):
        """Append source-authored proposals using the existing placement forms.

        Metadata travels explicitly to town_plans; no generated JSON is read.
        Authored terrain, access and identity failures stop regeneration.
        """
        import copy
        import town_plans
        town_plans.validate_authored_packet(packet, town_plans.slug(self.name))
        if hasattr(self, 'authored_plan'):
            raise ValueError(f'{self.name}: duplicate authored packet')
        protected = np.zeros(self.T['K'].shape, dtype=bool)
        uses = list(self.T.get('authored_protected_cells', []))
        uses += [b['plot'][:4] for b in self.buildings if b.get('plot')]
        uses += [[o['box'][0] // CELL, o['box'][1] // CELL,
                  (o['box'][2] - o['box'][0]) // CELL, (o['box'][3] - o['box'][1]) // CELL]
                 for o in self.outskirts]
        for c, r, w, h in uses:
            protected[max(0, r):r + h, max(0, c):c + w] = True
        reserved = np.zeros(self.T['K'].shape, dtype=bool)
        wc, wr, ww, wh = packet['terrain_box_cells']
        for rec in packet['buildings']:
            c, r, w, h = rec['footprint_cells']
            if r + h > H or c + w > W:
                raise ValueError(f"{rec['id']}: authored footprint leaves the real terrain")
            if not (wc <= c and wr <= r and c + w <= wc + ww and r + h <= wr + wh):
                raise ValueError(f"{rec['id']}: authored footprint leaves its terrain window")
            sl = (slice(r, r + h), slice(c, c + w))
            if not np.isin(self.T['K'][sl], list(BUILDABLE)).all() or any(
                    self.T[key][sl].any() for key in ('taken', 'street', 'barrier', 'keepout')) or reserved[sl].any() or protected[sl].any():
                raise ValueError(f"{rec['id']}: authored footprint overlaps blocked ground or another use")
            tiers = self.T['tiers_pre'][sl]
            if tiers.max() != tiers.min():
                raise ValueError(f"{rec['id']}: authored footprint needs an unapproved terrain-tier change")
            reserved[sl] = True
            if 'plot_cells' in rec:
                pc, pr, pw, ph = rec['plot_cells']
                ps = (slice(pr, pr + ph), slice(pc, pc + pw))
                if not (wc <= pc and wr <= pr and pc + pw <= wc + ww and pr + ph <= wr + wh):
                    raise ValueError(f"{rec['id']}: authored plot leaves its terrain window")
                if pr + ph > H or pc + pw > W or not np.isin(self.T['K'][ps], list(BUILDABLE - ROUTE)).all() or any(
                        self.T[key][ps].any() for key in ('taken', 'street', 'barrier', 'keepout')) or reserved[ps].any() or protected[ps].any():
                    raise ValueError(f"{rec['id']}: authored plot is clipped or overlaps another use")
                reserved[ps] = True
        # The existing JSON convention excludes landmarks and groups joined fronts.
        # put() predates that convention and caps raw records instead; retain its
        # geometry checks while checking authored capacity by the actual convention.
        def contribution(raw):
            if not raw['counted'] or raw.get('form') in town_plans.LANDMARK_FORMS or raw['use'] in town_plans.LANDMARK_TYPES:
                return 0
            n = len(raw.get('bays', [])) or 1
            return (n + 4) // 5 if n >= 3 else 1
        if sum(contribution(b) for b in self.buildings) + sum(b['counts_as'] for b in packet['buildings']) > self.cap:
            raise ValueError(f'{self.name}: authored buildings exceed the existing count guide')
        self.authored_plan = copy.deepcopy(packet)
        for rec in packet['buildings']:
            x, y, w, h = rec['rect_px']
            a, b = C(x, y); c, d = a + h // CELL, b + w // CELL
            tiers = self.T['tiers_pre'][a:c, b:d]
            if tiers.size != w * h // (CELL * CELL) or tiers.max() != tiers.min():
                raise ValueError(f"{rec['id']}: authored footprint needs an unapproved terrain-tier change")
            if self.T['barrier'][a:c, b:d].any():
                raise ValueError(f"{rec['id']}: authored footprint intersects a barrier")
            behind = None
            if 'plot_cells' in rec:
                pc, pr, pw, ph = rec['plot_cells']
                if pc + pw == x // CELL and pr == y // CELL and ph == h // CELL:
                    behind = (-1, 0, pw * CELL, rec['plot'])
                elif pc == (x + w) // CELL and pr == y // CELL and ph == h // CELL:
                    behind = (1, 0, pw * CELL, rec['plot'])
                elif pr + ph == y // CELL and pc == x // CELL and pw == w // CELL:
                    behind = (0, -1, ph * CELL, rec['plot'])
                elif pr == (y + h) // CELL and pc == x // CELL and pw == w // CELL:
                    behind = (0, 1, ph * CELL, rec['plot'])
                else:
                    raise ValueError(f"{rec['id']}: plot is not an existing rectangular rear-plot form")
            cap = self.cap
            self.cap = max(cap, self.count() + int(rec['counted']))
            try:
                placed = self.hand(x, y, w, h, rec['form'], plot=behind, counted=rec['counted'])
            finally:
                self.cap = cap
            if not placed:
                raise ValueError(f"{rec['id']}: authored placement failed")
            raw = self.buildings[-1]
            if 'plot_cells' in rec and raw.get('plot') != rec['plot_cells'] + [rec['plot']]:
                raise ValueError(f"{rec['id']}: authored plot was clipped")
            raw['authored_id'] = rec['id']
            raw['door'] = list(rec['door_cells'])
            raw['faces'] = rec['faces']

    def row(self, pts, uses, gap=(8, 24), setback=None, sides=(1, -1), plot=(40, 'garden'), counted=True, limit=None, jitter=8, start=20, reach=88):
        """Buildings along a street, on its sides, each fronting it (axis-aligned, as the game's buildings are)."""
        if setback is None:                                         # clear of the street's band: half its width and a step
            setback = 16
            if len(pts):
                p0 = [int(round(pts[0][0])), int(round(pts[0][1]))]
                for s_ in self.streets:
                    if s_['pts'] and (s_['pts'][0] == p0 or (s_['route'] and abs(s_['pts'][0][0] - p0[0]) + abs(s_['pts'][0][1] - p0[1]) < 24)):
                        setback = max(setback, s_['width_px'] // 2 + 4)
        x, y, al, tot = g.densify(pts, 4)
        placed = 0
        for side in sides:
            a = start + self.rng.uniform(0, 12)
            k = 0
            while a < tot - 20:
                if limit is not None and placed >= limit:
                    return placed
                i = int(np.argmin(np.abs(al - a)))
                j, k_ = min(i + 3, len(x) - 1), max(i - 3, 0)
                tx, ty = x[j] - x[k_], y[j] - y[k_]; L = math.hypot(tx, ty) or 1; tx, ty = tx / L, ty / L
                use = uses[k % len(uses)] if isinstance(uses, (list, tuple)) else uses
                (w0, w1), (d0, d1) = BLD[use]
                w = self.rng.uniform(w0, w1); d = self.rng.uniform(d0, d1)
                nx, ny = -ty * side, tx * side                       # the side's normal
                ew = abs(tx) >= abs(ty)                              # the street runs east-west: the building's width along x
                bw, bh = (w, d) if ew else (d, w)
                off = setback + (bh if ew else bw) / 2 + self.rng.uniform(0, jitter)
                cx_, cy_ = x[i] + nx * off, y[i] + ny * off
                ok = False
                for shift, slide in [(sh, 0) for sh in range(0, reach, 8)] + [(sh, sl) for sl in (-16, 16) for sh in range(0, min(64, reach), 16)]:
                    sx_, sy_ = cx_ + nx * shift + tx * slide, cy_ + ny * shift + ty * slide
                    beh = None
                    if plot:
                        dep, kind = plot
                        beh = (0, int(np.sign(ny)) or 1, dep, kind) if ew else (int(np.sign(nx)) or 1, 0, dep, kind)
                    if self.put(sx_ - bw / 2, sy_ - bh / 2, bw, bh, use, counted, beh):
                        ok = True; break
                if ok:
                    placed += 1; k += 1
                    a += w + self.rng.uniform(*gap)
                else:
                    a += 24
        return placed

    def cluster(self, cx, cy, r, uses, n, counted=True, plot=(32, 'yard')):
        """Buildings scattered on free ground near a point (farmsteads, works, a hamlet's houses)."""
        placed = 0
        for t in range(n * 120):
            if placed >= n:
                break
            ang = self.rng.uniform(0, 2 * math.pi); rr = r * math.sqrt(self.rng.uniform(0, 1))
            use = uses[placed % len(uses)]
            (w0, w1), (d0, d1) = BLD[use]
            w = self.rng.uniform(w0, w1); d = self.rng.uniform(d0, d1)
            if self.put(cx + rr * math.cos(ang) - w / 2, cy + rr * math.sin(ang) - d / 2, w, d, use, counted,
                        (0, 1, plot[0], plot[1]) if plot else None):
                placed += 1
        return placed

    def fill(self, target, r0, uses=('house', 'cottage', 'house', 'workshop'), reach=150, centre=None, plot=(32, 'yard'), box=None):
        """Infill to the target count: buildings behind and between the streets (courtyards, workshops behind shops, homes in
        the back lanes), each within reach px of a street or route so it can be reached, nearest the centre first."""
        T = self.T; cx, cy = centre or self.centre
        acc = ndi.distance_transform_edt(~(T['street'] | np.isin(T['K'], list(ROUTE)))) * CELL
        cand = []
        for k in range(1, 4):
            r = r0 * (1 + 0.35 * (k - 1))
            for t in range(900):
                ang = self.rng.uniform(0, 2 * math.pi); rr = r * math.sqrt(self.rng.uniform(0, 1))
                cand.append((rr, cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        cand.sort()
        n = 0
        for rr, x, y in cand:
            if self.count() >= target:
                break
            a, b = C(x, y)
            if not (0 <= a < H and 0 <= b < W) or acc[a, b] > reach or acc[a, b] < 20:
                continue
            if box is not None and not (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
                continue
            use = uses[n % len(uses)]
            (w0, w1), (d0, d1) = BLD[use]
            w = self.rng.uniform(w0, w1); d = self.rng.uniform(d0, d1)
            if self.put(x - w / 2, y - d / 2, w, d, use, True, (0, 1, plot[0], plot[1]) if plot else None):
                n += 1
        return n

    def fixed(self, rects, use='house'):
        """Buildings already placed by a zone plan (Crossroads): counted, not redrawn on the ground."""
        for r_ in rects:
            (x0, y0, w, d, u), door = r_[:5], (r_[5] if len(r_) > 5 else None)
            self.buildings.append({'x': x0, 'y': y0, 'w': w, 'h': d, 'use': u, 'counted': True, 'plan': True})
            if door is not None:
                self.buildings[-1]['zone_door'] = door
            a, b = C(x0, y0); self.T['taken'][a:a + d // CELL, b:b + w // CELL] = True
            sub = self.T['K'][a:a + d // CELL, b:b + w // CELL]; sub[~np.isin(sub, list(ROUTE) + ['river', 'creek'])] = 'building'

    # -------------------------------------------------------------------------------------- the working outskirts
    def fields(self, x0, y0, x1, y1, kinds=('field', 'field2'), hedge=True, size=(96, 176), name=None, why=None, dry=False, p=0.85):
        """A patchwork of fields (or orchards, or vegetable plots) with hedges on their edges, on free flat ground."""
        T = self.T; K = T['K']; r = self.rng
        land_ = ['meadow', 'steppe', 'watermeadow', 'scrub', 'garden', 'heath', 'clearing', 'alpine', 'fireweed', 'lavastone'] + (['desert', 'sand', 'ash'] if dry else [])
        y = y0; n = 0
        while y < y1:
            rh = int(r.integers(size[0] // 2, size[1] // 2 + 1)) // CELL * CELL or CELL
            x = x0
            while x < x1:
                rw = int(r.integers(size[0], size[1] + 1)) // CELL * CELL
                a, b = C(x, y); c, e = min(a + rh // CELL, int(y1 // CELL)), min(b + rw // CELL, int(x1 // CELL))
                if c - a < 2 or e - b < 2:
                    x += rw; continue
                if 1 < a and c < H - 1 and 1 < b and e < W - 1 and r.uniform() < p:
                    blk = K[a:c, b:e]
                    okm = np.isin(blk, land_) & ~T['taken'][a:c, b:e] & ~T['street'][a:c, b:e] & ~T['barrier'][a:c, b:e] & ~T['keepout'][a:c, b:e]
                    if okm.mean() > 0.85 and T['slope'][a:c, b:e].max() < 0.014:
                        blk[okm] = kinds[n % len(kinds)]
                        if hedge:
                            ed = np.zeros(blk.shape, bool); ed[[0, -1], :] = True; ed[:, [0, -1]] = True
                            blk[ed & okm] = 'hedge'
                        T['used'][a:c, b:e] |= okm; n += 1
                x += rw
            y += rh
        if n:
            self.outskirts.append({'kind': kinds[0], 'name': name, 'box': [int(x0), int(y0), int(x1), int(y1)], 'plots': n, 'why': why})
            self.T.setdefault('authored_protected_cells', []).append([int(x0 // CELL), int(y0 // CELL), int((x1 - x0) // CELL), int((y1 - y0) // CELL)])
        return n

    def yard(self, x0, y0, x1, y1, kind='yard', name=None, why=None):
        T = self.T; K = T['K']
        a, b = C(x0, y0); c, e = C(x1, y1)
        sub = K[a:c, b:e]
        ok = np.isin(sub, list(BUILDABLE)) & ~T['taken'][a:c, b:e] & ~T['street'][a:c, b:e] & ~T['barrier'][a:c, b:e] & ~T['keepout'][a:c, b:e]
        sub[ok & ~np.isin(sub, list(ROUTE))] = kind; T['used'][a:c, b:e] |= ok
        self.outskirts.append({'kind': kind, 'name': name, 'box': [int(x0), int(y0), int(x1), int(y1)], 'why': why})
        self.T.setdefault('authored_protected_cells', []).append([int(x0 // CELL), int(y0 // CELL), int((x1 - x0) // CELL), int((y1 - y0) // CELL)])

    # -------------------------------------------------------------------------------------- the record
    def count(self):
        return sum(1 for b in self.buildings if b['counted'])

    def record(self):
        bs = [b for b in self.buildings]
        if bs:
            xs = [b['x'] for b in bs] + [b['x'] + b['w'] for b in bs]; ys = [b['y'] for b in bs] + [b['y'] + b['h'] for b in bs]
            box = [min(xs), min(ys), max(xs), max(ys)]
        else:
            box = None
        uses = {}
        for b in bs:
            if b['counted']:
                uses[b['use']] = uses.get(b['use'], 0) + 1
        homes = sum(v for k, v in uses.items() if k in ('cottage', 'house', 'townhouse', 'tenement', 'farmhouse', 'stilt'))
        return {'size': self.size, 'target': self.target, 'buildings_counted': self.count(), 'by_use': uses, 'homes': homes,
                'centre': [int(self.centre[0]), int(self.centre[1])], 'footprint_box': box, 'purpose': self.purpose, 'setting': self.setting,
                'neighbourhoods': self.neighbourhoods, 'gathering_places': self.gathering, 'squares': self.spaces, 'outskirts': self.outskirts,
                'streets': self.streets, 'buildings': [[b['x'], b['y'], b['w'], b['h'], b['use'], int(b['counted'])] for b in bs]}


def _lm(pts, width):
    """geo5's own line mask (geo52 swaps in a varied-width one for the routes)."""
    import geo52 as G
    return G._orig_line_mask(pts, width)


# ------------------------------------------------------------------------------------------ helpers for skeletons
def route_part(T, name, box):
    """The part of a route's drawn line inside a box (the longest run), to use as a town's main street."""
    x0, y0, x1, y1 = box
    pts = T['route_px'][name]
    runs, cur = [], []
    for (x, y) in pts:
        if x0 <= x <= x1 and y0 <= y <= y1:
            cur.append((x, y))
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return max(runs, key=len) if runs else []


def grid(x0, y0, x1, y1, step_x, step_y, rng, jitter=12):
    """Street lines on a loose grid (jittered, each a separate polyline)."""
    out = []
    ys = np.arange(y0, y1 + 1, step_y); xs = np.arange(x0, x1 + 1, step_x)
    for y in ys:
        pts = [(x, y + rng.uniform(-jitter, jitter)) for x in np.linspace(x0, x1, max(2, int((x1 - x0) // 120) + 2))]
        out.append(pts)
    for x in xs:
        pts = [(x + rng.uniform(-jitter, jitter), y) for y in np.linspace(y0, y1, max(2, int((y1 - y0) // 120) + 2))]
        out.append(pts)
    return out


def prepare(T, keepout_boxes=(), keepout_discs=()):
    """The masks the layout needs: taken (buildings), street, barrier (water and barriers, never built on or crossed),
    the tiers before layout (one tier per footprint) and keep-outs (built zones, the garden, the parks, craters)."""
    import geo52 as G
    K = T['K']
    T['taken'] = np.zeros((H, W), bool); T['street'] = np.zeros((H, W), bool)
    bar = np.zeros((H, W), bool)
    for m in T['barriers'].values():
        bar |= m
    bar |= np.isin(K, ['river', 'rapids', 'creek', 'canal', 'oxbow', 'tarn', 'mere', 'sea', 'surf', 'lava', 'aa', 'fissure', 'crater', 'falls',
                       'channel', 'pool', 'cliff', 'crag', 'wall', 'castlewall', 'shardglass', 'craterrim', 'scorch', 'circle', 'spoil', 'rockfall',
                       'closedroad', 'viaduct', 'viapier', 'mud', 'sandbar'])
    T['barrier'] = ndi.binary_dilation(bar, iterations=1)
    hb = np.zeros((H, W), bool)
    for m in T['barriers'].values():
        hb |= m
    T['hardbar'] = ndi.binary_dilation(hb, iterations=1)
    T['tiers_pre'] = G.tier_field(T)
    ko = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in keepout_boxes:
        ko[int(y0 // CELL):int(y1 // CELL), int(x0 // CELL):int(x1 // CELL)] = True
    for (x, y, r) in keepout_discs:
        ko |= np.hypot(PX - x, PY - y) < r
    ko |= T.get('crater_mask', np.zeros((H, W), bool))
    T['keepout'] = ko


def dry_out(T, x0, y0, x1, y1, keep=64):
    """A desert town's ground: green only along water. Grass, gardens and woods farther than keep px from a river, channel
    or pool go back to the desert (or dry scrub on the gravel)."""
    K = T['K']
    a, b, c, d = int(y0 // CELL), int(x0 // CELL), int(y1 // CELL), int(x1 // CELL)
    sub = K[a:c, b:d]
    wet = np.isin(sub, ['river', 'creek', 'channel', 'canal', 'pool', 'rapids'])
    far = ndi.distance_transform_edt(~wet) * CELL > keep
    green = np.isin(sub, ['meadow', 'watermeadow', 'broadleaf', 'conifer', 'clearing', 'lawn', 'garden', 'wild', 'thicket', 'felltree', 'bramble',
                          'heath', 'gorse', 'carr', 'reeds', 'fireweed'])
    m = green & far & ~T['taken'][a:c, b:d]
    sub[m] = 'desert'
    return int(m.sum())


def clear_paint(T, x0, y0, x1, y1, keep_box=None, kinds=('building', 'yard', 'garden', 'plaza', 'keep', 'lane', 'retain', 'stall', 'hut')):
    """v54's generic houses lifted off a town's ground (back to the natural ground), so v55's layout replaces them."""
    K = T['K']; K0 = T['K0']
    a, b, c, d = int(y0 // CELL), int(x0 // CELL), int(y1 // CELL), int(x1 // CELL)
    sub = K[a:c, b:d]; base = K0[a:c, b:d]
    m = np.isin(sub, list(kinds)) & T['land'][a:c, b:d]
    if keep_box is not None:
        kx0, ky0, kx1, ky1 = keep_box
        yy_, xx_ = np.mgrid[a:c, b:d]
        m &= ~((xx_ * CELL >= kx0) & (xx_ * CELL < kx1) & (yy_ * CELL >= ky0) & (yy_ * CELL < ky1))
    nat = np.where(np.isin(base, ['sea', 'river', 'canal', 'road', 'path', 'bridge', 'stair', 'creek']), 'meadow', base)
    nat = np.where(np.isin(nat, ['wild', 'ancient', 'thicket', 'felltree']), 'broadleaf', nat)   # cleared once: open woods, walkable
    sub[m] = nat[m]
    return int(m.sum())


# ------------------------------------------------------------------------------------------ the towns (v55 world px)
def crossroads_plan(root):
    import json, os
    p = json.load(open(os.path.join(root, 'game', 'data', 'plans', 'crossroads.json')))
    ox, oy = p['origin_on_canvas']
    use = {'hut': 'cottage', 'library': 'public', 'north_cottages': 'house', 'bakery': 'shop', 'herbalist': 'shop', 'smithy': 'workshop',
           'fern_cottage': 'cottage'}
    return [(ox + b['rect'][0], oy + b['rect'][1], b['rect'][2], b['rect'][3], use.get(b['id'], 'house'),
             (ox + b['door'][0], oy + b['door'][1]) if b.get('door') else None) for b in p['buildings']], (ox, oy, ox + p['box'][2], oy + p['box'][3])


def _authored_inputs(authored, allowed):
    """Check deliberate caller input; defaults never consult proposed authoring data."""
    if authored is None:
        return {}
    if not isinstance(authored, dict) or set(authored) - allowed:
        raise ValueError('unknown authored town key for this producer entrypoint')
    if not authored:
        return authored
    import town_plans
    for pid, packet in authored.items():
        town_plans.validate_authored_packet(packet, pid)
    return authored


def _adopt_requested(town, authored, pid):
    """Dispatch only a selected packet; Town.adopt verifies its actual target and ground."""
    if not authored:
        return
    import town_plans
    if town_plans.slug(town.name) != pid:
        raise ValueError('authored dispatch target town mismatch')
    if pid in authored:
        town.adopt(authored[pid])


def lay_all(T, X, *, authored=None):
    """Every settlement's footprint, in the order of Matt's allocation, then the smaller places. X: the geo55 module."""
    authored = _authored_inputs(authored, {'cinderwick', 'hearthold'})
    towns = {}
    rng = np.random.default_rng(55)

    # ---------------------------------------------------------------- Crossroads (large): the market town at the routes' hub
    plan, pbox = crossroads_plan(X.ROOT)
    clear_paint(T, 5700, 3150, 7000, 4300)
    t = Town(T, 'Crossroads', (6296, 3536), 'large', (30, 45),
             'the market and meeting point of the valley: four lanes and two roads meet here; the farms round it bring grain, wool and '
             'fruit to its market, and the halt, the mill and the smithy serve the whole valley',
             'the valley floor either side of the Sleepwater, on its flat terraces; the woodland and the stone circle to the north-west',
             neighbourhoods=[('the square (built)', 'the zone as built: the square, the well, the bakery, the herbalist, the smithy, the library', 6296, 3536),
                             ('Mill End', 'south along the Sleepwater: the mill, the granary, millers\' and carters\' cottages', 6330, 3990),
                             ('Halt Road', 'south-west down the lane to the halt: cottages with long gardens, the halt and its goods shed', 5930, 3900),
                             ('Eastgate', 'east where the Foothill Road and the Lull Road leave: the drovers\' market, the inn, the farrier', 6740, 3560),
                             ('West Lane', 'a short row on the woodland\'s skirt, foresters\' and hurdle-makers\' cottages', 5900, 3600)],
             gathering=[('the square', 6296, 3536), ("the drovers' market", 6710, 3530), ('the mill green', 6360, 3900), ('the halt yard', 5880, 4075)],
             seed=101)
    t.cap = 40
    t.fixed(plan)
    import json as _j, os as _o
    zp = _j.load(open(_o.path.join(X.ROOT, 'game', 'data', 'plans', 'crossroads.json')))
    zx, zy = zp['origin_on_canvas']
    for r_ in zp['routes']:                                         # the zone's own roads and lanes, as built
        t.street([(zx + a, zy + b) for a, b in r_['points']], 'side' if r_['kind'] == 'road' else 'lane', kind='lane', name=r_['id'].replace('_', ' '),
                 route='the Crossroads zone plan')
    for q in zp['places']:                                          # the zone's square and green, as built
        if q['kind'] in ('square', 'green'):
            x_, y_, w_, h_ = q['rect']
            t.square(zx + x_ + w_ / 2, zy + y_ + h_ / 2, w_ / 2, h_ / 2, kind='plaza' if q['kind'] == 'square' else 'garden',
                     name=f"the {q['id']} (the zone as built)")
    straighten(T, 'Valley lane south', (6100, 3780, 6500, 4300), 24, 'path')   # Mill Street: a planned street through the old core
    mill = route_part(T, 'Valley lane south', (6100, 3800, 6500, 4300))
    halt = route_part(T, 'Valley lane west', (5800, 3760, 6000, 4120))
    east = route_part(T, 'Valley lane east', (6600, 3330, 6800, 3520)) + route_part(T, 'Foothill Road', (6760, 3300, 6880, 3420))
    lull = route_part(T, 'Valley lane to the Lull Road', (6600, 3580, 6780, 3800)) + route_part(T, 'Lull Road', (6760, 3700, 6960, 3900))
    t.street([(6300, 3975), (6420, 3972), (6540, 3985)], 'side', name='Granary Row')
    t.street([(6305, 4100), (6420, 4110), (6520, 4130)], 24, name='Weir Lane')
    t.street([(5975, 3560), (5900, 3585), (5830, 3605)], 24, name='West Lane')
    t.street([(6650, 3420), (6660, 3540), (6655, 3640)], 'side', name='Market Lane')
    t.street(mill, 'main', name='Mill Street (Valley lane south)', route='Valley lane south')
    t.street(east, 'side', name='Eastgate (Valley lane east)', route='Valley lane east')
    t.to_route(6540, 3985, 'Valley lane south', 'lane', name='Granary Row (east end)')
    t.street([(6520, 4130), (6540, 3985)], 'lane', name='Orchard Lane')
    t.square(6712, 3532, 56, 40, name="the drovers' market")
    t.square(5880, 4078, 48, 30, name='the halt yard')
    t.square(6365, 3905, 40, 28, kind='garden', name='the mill green')
    t.cluster(6200, 3905, 40, ['mill'], 1)
    t.cluster(5835, 4040, 60, ['station'], 1)
    cp = ('sign', 'bench', 'potted plants', 'planter tree', 'water butt')
    t.frontage(t.S('Granary Row'), sides=(-1,), form='row_house', block=(80, 144), depth=(40, 48), props=cp, roofs=('tile', 'thatch', 'tile'), limit=3)
    t.row(mill, ['cottage', 'house', 'cottage', 'shop'], limit=9, start=10, plot=(16, 'garden'))
    t.row(t.S('Granary Row'), ['cottage', 'house', 'barn'], limit=4)
    t.row(t.S('Weir Lane'), ['cottage', 'house'], limit=3)
    t.row(halt, ['cottage', 'house', 'cottage'], limit=6, plot=(56, 'garden'), start=10)
    t.row(east, ['inn', 'house', 'workshop', 'shop', 'cottage'], limit=6, start=10)
    t.row(lull, ['house', 'cottage', 'shop', 'cottage'], limit=6, start=10)
    t.row(t.S('Market Lane'), ['shop', 'house'], limit=3)
    t.row(t.S('West Lane'), ['cottage'], limit=3, plot=(48, 'garden'))
    for pts in (mill, lull, halt, east):
        if t.count() < 38:
            t.row(pts, ['cottage', 'house'], limit=38 - t.count(), start=60, setback=24)
    t.fields(5700, 3950, 6150, 4350, ('field', 'field2', 'orchard'), name='the halt farms', why='grain, hay and apples for the market')
    t.fields(6450, 3900, 6950, 4300, ('field', 'orchard', 'field2'), name='the mill farms', why='wheat for the mill, orchards on the river terrace')
    towns['Crossroads'] = t

    # ---------------------------------------------------------------- Dust Gulch (large): the railhead, the mine's town
    clear_paint(T, 2050, 2150, 3000, 2800)
    dry_out(T, 2000, 2050, 3100, 2850)
    t = Town(T, 'Dust Gulch', (2478, 2420), 'large', (30, 45),
             "the desert line's railhead and the Lode's ore yard: ore comes down the mule track to the depot, goods and water go out "
             'along the line; repair shops, the assay office and the corrals for the caravans; the Amber gives it water',
             'where the Amber leaves the mountains, on the gravel fan either side of the river; desert all round, the Glass field to the west',
             neighbourhoods=[('Front Street', 'the frontier main street: the saloon, the store, the sheriff (Pendle), the assay office', 2600, 2455),
                             ('the Depot', 'the platform, the goods yard and sheds, the repair shop and the water tower', 2720, 2335),
                             ('Water Street', 'homes along the river and its gardens, behind the main street', 2470, 2570),
                             ('West Row', 'homes and the chapel on the west bank', 2300, 2350),
                             ('the corrals', 'pens and stables for the caravans and the mule trains, east of town', 2900, 2450)],
             gathering=[('the depot square', 2640, 2395), ('the well square', 2380, 2445), ('the chapel yard', 2290, 2380)], seed=102)
    front = route_part(T, "Drover's Road", (2560, 2380, 2960, 2560))
    t.street([(2575, 2458), (2440, 2448), (2300, 2442), (2170, 2452)], 'main', name='Front Street (west)')
    t.street([(2560, 2335), (2700, 2338), (2880, 2340)], 'side', name='Depot Street')
    t.street([(2300, 2330), (2295, 2470), (2300, 2620)], 24, name='Chapel Street')
    t.street([(2665, 2345), (2662, 2480), (2668, 2620)], 24, name='Mesa Street')
    t.street([(2790, 2465), (2795, 2600)], 24, name='Corral Lane')
    t.street([(2190, 2565), (2320, 2562), (2440, 2568)], 24, name='Water Street (west)')
    t.street([(2540, 2575), (2670, 2578), (2800, 2580)], 24, name='Water Street')
    t.street([(2180, 2338), (2300, 2334), (2420, 2338)], 24, name='West Row')
    t.street(front, 'main', name="Front Street (Drover's Road)", route="Drover's Road")
    t.square(2640, 2392, 52, 30, name='the depot square')
    t.square(2380, 2446, 36, 26, name='the well square')
    yd = (24, 'yard')                                               # sand and adobe yards behind, not gardens
    t.level, t.slope_max = 2, 0.03                                  # the gravel fan, in low terraces
    # the frontier main street: the saloon, the store and the false-fronted shops face Front Street from both sides
    fs = t.S('Front Street (west)'); fy = fs[0][1]
    t.frontage(fs, sides=(-1, 1), form='row_shop', block=(96, 176), depth=(48, 56), false_front=True, plot=None,
               props=('sign', 'awning', 'hitching rail', 'water barrel', 'bench'), roofs=('flat', 'tin', 'flat'))
    t.row(front, ['saloon', 'frontshop', 'frontshop', 'public', 'frontshop', 'frontshop'], limit=8, start=8, plot=yd, gap=(4, 10))
    t.row(t.streets[0]['pts'], ['frontshop', 'public', 'frontshop', 'frontshop', 'house'], limit=8, plot=yd, gap=(4, 10))
    t.row(t.S('Depot Street'), ['depot', 'warehouse', 'workshop', 'adobe'], limit=4, plot=yd)
    for k_, uses in ((2, ['adobe', 'chapel', 'adobe']), (3, ['adobe', 'workshop']), (5, ['adobe', 'house']), (6, ['adobe', 'house']),
                     (7, ['adobe', 'adobe', 'house']), (4, ['workshop', 'barn'])):
        t.row(t.streets[k_]['pts'], uses, limit=4, plot=yd)
    for pts in (t.streets[5]['pts'], t.streets[6]['pts'], t.streets[2]['pts'], t.streets[3]['pts']):
        if t.count() < 38:
            t.row(pts, ['adobe', 'adobe', 'house'], limit=38 - t.count(), start=50, setback=24, plot=yd)
    t.yard(2840, 2390, 2980, 2530, name='the corrals', why='pens and stables for the caravans and the mule trains')
    t.yard(2580, 2235, 2880, 2312, name='the goods yard', why="the desert line's sidings and the ore bins")
    t.yard(2600, 2120, 2700, 2210, name='the ore yard', why="the Lode's ore, down the mule track, waiting for the train")
    t.fields(2330, 2600, 2580, 2780, ('orchard', 'field2'), name='the river gardens', why='irrigated from the Amber: vegetables, figs, fodder', dry=True, size=(64, 128))
    t.fill(38, 260, ('adobe', 'adobe', 'workshop', 'adobe', 'house'))
    towns['Dust Gulch'] = t

    # ---------------------------------------------------------------- Palm Spring (medium): the oasis
    clear_paint(T, 2950, 2550, 3650, 3100)
    dry_out(T, 2950, 2500, 3650, 3150, keep=48)
    pool = g.shape(3282, 2738, 48, 34, 3301, 0.2) & T['land'] & ~np.isin(T['K'], list(ROUTE))
    T['K'][pool] = 'pool'; T['barrier'] |= ndi.binary_dilation(pool, iterations=1)
    t = Town(T, 'Palm Spring', (3282, 2760), 'medium', (14, 22),
             'the first water in the dry country: the Willow Run comes up again in the spring; irrigated gardens, date and fig orchards, '
             "the caravans' rest on the Drover's Road, and the diviner (Mirra) who keeps the spring",
             'round the spring pool and along its two channels, on the gravel where the Willow Run resurfaces; scrub and steppe round it',
             neighbourhoods=[('Spring Row', 'houses round the pool under the palms', 3282, 2680),
                             ('the caravanserai', "the inn, stables and stores on the Drover's Road", 3420, 2830),
                             ('Channel Row', 'gardeners\' houses along the south-west channel', 3170, 2900),
                             ('Palm Row', 'along the south-east channel to the orchards', 3400, 2900)],
             gathering=[('the spring square', 3350, 2780), ('the pool steps', 3282, 2700)], seed=103)
    t.street([(3172, 2806), (3172, 2668), (3388, 2668), (3388, 2806)], 24, name='Spring Row')
    t.to_route(3172, 2806, "Drover's Road", name='Spring Row (west end)')
    t.to_route(3388, 2806, "Drover's Road", name='Spring Row (east end)')
    t.street([(3255, 2830), (3170, 2900), (3080, 2975)], 24, name='Channel Row')
    t.street([(3320, 2835), (3400, 2890), (3470, 2950)], 24, name='Palm Row')
    road = route_part(T, "Drover's Road", (3050, 2650, 3550, 2950))
    t.street(road, 'main', name="the Caravan Road (Drover's Road)", route="Drover's Road")
    t.square(3352, 2782, 38, 24, name='the spring square')
    t.row(road, ['inn', 'shop', 'house', 'shop', 'workshop'], limit=6, start=8, plot=(24, 'yard'))
    t.row(t.S('Spring Row'), ['house', 'public', 'house', 'cottage'], limit=6, sides=(1,), plot=(24, 'yard'))
    t.row(t.S('Channel Row'), ['adobe', 'house'], limit=4, plot=(24, 'yard'))
    t.row(t.S('Palm Row'), ['adobe', 'house'], limit=4, plot=(24, 'yard'))
    t.fields(3080, 2880, 3480, 3080, ('orchard', 'field2', 'orchard'), name='the date gardens', why='date palms, figs and vegetables on the channels', dry=True, size=(64, 128))
    t.fields(3150, 2560, 3420, 2640, ('orchard',), name='the north grove', why='palms along the Willow Run', dry=True, size=(64, 112), hedge=False)
    t.fill(18, 170, ('adobe', 'house', 'adobe'), plot=(24, 'yard'))
    towns['Palm Spring'] = t

    # ---------------------------------------------------------------- Fernhollow (medium): the timber town in the Fern hills
    clear_paint(T, 6900, 2850, 7500, 3350)
    t = Town(T, 'Fernhollow', (7180, 3080), 'medium', (14, 22),
             "timber from the Fern hills' wet woods: the sawmill, the wood yards and the joiners; charcoal for Cogsworth; its own green, "
             'school and chapel, on the Foothill Road halfway between Crossroads and Cogsworth',
             'a clearing in the woods of the Fern hills, where the Foothill Road crosses Fern Lane',
             neighbourhoods=[('the Green', 'houses round the village green, the chapel and the school', 7230, 3070),
                             ('the Yards', 'the sawmill and the wood yards, joiners and coopers', 7380, 2980),
                             ('Fern Lane', 'cottages down the lane to the Lull Road', 7200, 3200)],
             gathering=[('the green', 7230, 3075), ('the sawmill yard', 7400, 2975)], seed=104)
    foot = route_part(T, 'Foothill Road', (7030, 2900, 7470, 3200))
    fern = route_part(T, 'Fern Lane', (7120, 3100, 7260, 3380))
    t.street([(7090, 3040), (7200, 3015), (7320, 3000)], 'side', name='Green Lane')
    t.street([(7240, 3160), (7340, 3150), (7430, 3120)], 24, name='Cooper Lane')
    t.to_route(7090, 3040, 'Foothill Road', name='Chapel Lane')
    t.to_route(7320, 3000, 'Foothill Road', name='School Lane')
    t.to_route(7430, 3120, 'Foothill Road', name='Cooper Lane (east end)')
    t.to_route(7240, 3160, 'Fern Lane', name='Cooper Lane (west end)')
    t.street(foot, 'main', name='Fernhollow Street (Foothill Road)', route='Foothill Road')
    t.square(7232, 3078, 46, 30, kind='garden', name='the green')
    t.row(foot, ['house', 'shop', 'cottage', 'inn', 'cottage', 'workshop'], limit=8, start=8)
    t.row(t.streets[0]['pts'], ['chapel', 'cottage', 'public', 'cottage'], limit=4)
    t.row(fern, ['cottage', 'house'], limit=3, start=40)
    t.row(t.streets[1]['pts'], ['workshop', 'cottage'], limit=3)
    t.cluster(7400, 2975, 60, ['mill'], 1)
    t.yard(7340, 2920, 7470, 2960, name='the wood yards', why="the Fern hills' timber, seasoning in stacks")
    t.fields(7020, 3180, 7140, 3320, ('field2', 'field'), name='the clearing fields', why='oats and hay in the clearing', size=(64, 112))
    t.fill(16, 200, ('cottage', 'house', 'workshop'), box=(7020, 2860, 7520, 3400))
    towns['Fernhollow'] = t

    # ---------------------------------------------------------------- Cogsworth (medium, room to grow): works and railway
    clear_paint(T, 7850, 2250, 8520, 2900)
    t = Town(T, 'Cogsworth', (8130, 2520), 'medium (room to become large)', (14, 45),
             'coal and iron from the coal hills, the fast Cog for power (the Millrace), and the railway out: the foundry, the mills, '
             'the engine works and the terminus; brick terraces for the workers between the works and the pits',
             "the Cog's east bank where the valley opens, between the river and the coal hills; the pits and spoil heaps above it",
             neighbourhoods=[('Foundry Row', 'the foundry, the mills on the Millrace, workshops by the river', 8130, 2560),
                             ('Engine Street', 'shops and the works offices on the towpath road down to the terminus', 8260, 2680),
                             ('the Terraces', "brick workers' terraces climbing toward the pits", 8300, 2520),
                             ('the Platform', "the platform, the station square and the Garth Road's start", 8080, 2410)],
             gathering=[('the station square', 8095, 2405), ('the works gate', 8230, 2610)], seed=105)
    tow = route_part(T, 'Towpath', (8100, 2500, 8420, 2860))
    garth = route_part(T, 'the Garth Road', (7990, 2280, 8070, 2400))
    t.street([(8040, 2450), (8130, 2545), (8235, 2680), (8310, 2780)], 'side', name='Foundry Row')
    t.street([(8160, 2420), (8280, 2530), (8400, 2670)], 24, name='Pit Row')
    t.street([(8070, 2410), (8160, 2405), (8240, 2400)], 'side', name='Platform Street')
    t.street([(8125, 2565), (8230, 2535), (8340, 2510)], 24, name='Engine Lane')
    t.street([(8230, 2705), (8330, 2680), (8430, 2650)], 24, name='Terrace Lane')
    t.street([(8240, 2400), (8340, 2400), (8340, 2512)], 'lane', name='Station Lane')
    t.street([(8340, 2512), (8340, 2690)], 'lane', name='Chapel Street')
    t.street(tow, 'main', name='Engine Street (Towpath)', route='Towpath')
    t.square(8098, 2402, 36, 22, name='the station square')
    t.row(tow, ['shop', 'townhouse', 'public', 'townhouse', 'shop'], limit=7, start=8)
    t.row(t.streets[0]['pts'], ['workshop', 'mill', 'workshop', 'terrace'], limit=6)
    t.row(t.streets[1]['pts'], ['terrace'], limit=6, gap=(4, 8))
    t.row(t.streets[2]['pts'], ['station', 'shop', 'inn'], limit=3)
    t.row(t.streets[3]['pts'], ['terrace'], limit=4, gap=(4, 8))
    t.row(t.streets[4]['pts'], ['terrace'], limit=4, gap=(4, 8))
    t.yard(8300, 2770, 8470, 2860, name='the railway yard', why='the terminus sidings, the engine shed and the coal stage')
    t.fields(8360, 2430, 8520, 2560, ('field2',), name='the allotments', why="the terraces' vegetable plots", size=(48, 80))
    t.fill(26, 260, ('terrace', 'workshop', 'townhouse', 'house'), box=(7900, 2250, 8560, 2900))
    towns['Cogsworth'] = t

    towns['Hearthold'] = hearthold(T, X, authored={k: v for k, v in authored.items() if k == 'hearthold'})

    # ---------------------------------------------------------------- Cinderwick (medium): the black-sand cove
    clear_paint(T, 2250, 5700, 2750, 5960)
    t = Town(T, 'Cinderwick', (2478, 5860), 'medium', (14, 22),
             "the fire country's harbour: fishing boats and the coaster that calls for Hearthold's goods; charcoal kilns and a "
             "black-sand glassworks; the quay is the region's way to the sea",
             'a black-sand cove between the flows, the young flow steaming to the east; the Ash Coast path and the Ember Way meet here',
             neighbourhoods=[('the Strand', "fishers' houses and net lofts along the beach", 2450, 5885),
                             ('Kiln Lane', 'the kilns, the glassworks and the coopers', 2520, 5795),
                             ('the Quay', 'the stone quay, the chandler and the harbour office', 2470, 5920)],
             gathering=[('the quay', 2470, 5915), ('the kiln yard', 2640, 5795)], seed=107)
    t.level, t.slope_max = 2, 0.03                                # the cove's slope, terraced
    north = (PY < 5724) & (PX > 1980) & (PX < 2900) & (PY > 5300) & ~T['keepout']   # the fields between it and Hearthold stay open
    T['keepout'] |= north
    t.street([(2290, 5872), (2450, 5868), (2610, 5878)], 'side', name='the Strand')
    t.street([(2370, 5790), (2500, 5798), (2620, 5806)], 24, name='Kiln Lane')
    t.street([(2440, 5800), (2450, 5860)], 24, name='Quay Lane')
    t.street([(2270, 5800), (2330, 5760), (2400, 5730)], 24, name='Back Lane')
    t.street([(2420, 5752), (2530, 5745), (2640, 5758)], 24, name='Kiln Row')
    t.street([(2624, 5760), (2624, 5880)], 'lane', name='Kiln Steps')
    t.row(t.streets[0]['pts'], ['cottage', 'townhouse', 'shop', 'cottage', 'workshop'], limit=9, plot=None, gap=(2, 8))
    t.row(t.streets[1]['pts'], ['workshop', 'townhouse', 'cottage'], limit=7, plot=None, gap=(2, 8))
    t.row(route_part(T, 'Ember Way', (2200, 5700, 2420, 5860)), ['cottage', 'house'], limit=3, start=10)
    t.yard(2620, 5760, 2720, 5840, name='the kilns', why='charcoal from the dead forest; black-sand glass')
    t.row(t.streets[3]['pts'], ['cottage', 'house'], limit=4)
    t.row(t.streets[4]['pts'], ['cottage', 'house', 'workshop'], limit=4)
    t.row(route_part(T, 'Ash Coast', (2480, 5760, 2760, 5900)), ['cottage', 'house'], limit=3, start=10)
    t.fill(17, 380, ('cottage', 'boathouse', 'townhouse', 'workshop'), box=(1990, 5725, 2880, 6040), reach=260, plot=None)
    T['keepout'] &= ~north
    _adopt_requested(t, authored, 'cinderwick')
    towns['Cinderwick'] = t

    # ---------------------------------------------------------------- Lagoon Landing (medium): the isles' town on its lagoon
    clear_paint(T, 6350, 6350, 6900, 6620)
    t = Town(T, 'Lagoon Landing', (6600, 6490), 'medium', (14, 22),
             "the isles' town: boats, fishing and the diving trade off the reef wrecks (Brine), the naturalist's house, net and sail "
             "lofts, the boatyard; the ferry to Driftwood and the boats to the other isles leave from here",
             "the neck of the main isle between the ferry pier on the open north shore and the sheltered lagoon (a drowned crater)",
             neighbourhoods=[('the Lagoon front', 'boathouses and stilt houses on the lagoon', 6620, 6560),
                             ('Net Row', 'net and sail lofts, the chandler', 6620, 6460),
                             ('the Pier', 'the ferry pier, the harbour office and the inn', 6500, 6420)],
             gathering=[('the lagoon steps', 6600, 6555), ('the pier head', 6490, 6415)], seed=108)
    py_ = 6420
    while py_ > 6200 and T['K'][int(py_ // CELL), int(6488 // CELL)] not in ('sea', 'surf'):
        py_ -= CELL
    t.street([(6488, py_ + 2 * CELL), (6488, 6420)], 'side', name='the Pier')
    t.street([(6488, 6420), (6522, 6480), (6560, 6545)], 24, name='Pier Lane')
    t.street([(6440, 6552), (6600, 6560), (6800, 6570)], 'side', name='Lagoon Front')
    t.street([(6470, 6468), (6620, 6462), (6770, 6465)], 24, name='Net Row')
    t.street([(6700, 6345), (6660, 6410), (6630, 6460)], 24, name='Bar Lane')
    t.street([(6604, 6462), (6604, 6556)], 'lane', name='Slip Lane')
    t.street([(6800, 6568), (6968, 6568), (6968, 6812), (6840, 6812)], 'lane', name='the East Strand')
    t.street([(6968, 6690), (7120, 6690)], 'lane', name='Reef Lane')
    t.row(t.S('Lagoon Front'), ['boathouse', 'stilt', 'cottage', 'boathouse', 'stilt'], limit=6, sides=(-1,))
    t.row(t.S('Net Row'), ['cottage', 'shop', 'house', 'cottage'], limit=7)
    t.row(t.S('Pier Lane'), ['inn', 'public'], limit=2)
    t.row(t.S('Lagoon Front'), ['cottage', 'house'], limit=3, sides=(1,))
    t.row(t.S('the East Strand'), ['boathouse', 'cottage', 'stilt', 'house', 'cottage'], limit=8, start=10)
    t.row(t.S('Reef Lane'), ['cottage', 'house'], limit=3, start=10)
    t.yard(6760, 6500, 6860, 6545, name='the boatyard', why='hulls on the slip, the repair shed')
    t.fill(18, 220, ('cottage', 'house', 'boathouse'), reach=180)
    towns['Lagoon Landing'] = t

    towns['Highgarth'] = highgarth(T, X)
    towns.update(neon(T, X, rng))
    towns.update(smaller(T, X))
    return towns


HEARTHOLD_WALL = (2176, 5064, 2464, 5424)                         # the town wall's outer edge, two cells thick
HEARTHOLD_GATE = (2296, 2328)                                      # the main gate in the south wall (x), four cells
HEARTHOLD_POSTERN = (5224, 5240)                                   # the postern in the west wall (y): walled up, opens later


def hearthold(T, X, *, authored=None):
    """Hearthold, authored by hand: the walled town on the rock between the lava flows, its gate, Gate Street down to the gate
    market, Smiths' Row against the cooled lava, and the home streets as terraces stepping down the slope (Matt's brief; Claude
    A's review of 28 Oct). Every coordinate is in world px on the soft grid."""
    authored = _authored_inputs(authored, {'hearthold'})
    K = T['K']
    clear_paint(T, 1900, 5000, 2700, 5760, kinds=('building', 'yard', 'garden', 'plaza', 'lane', 'retain', 'stall', 'hut'))
    old = np.isin(K, ['castlewall', 'keep']) & (PX > 1850) & (PX < 2500) & (PY > 4950) & (PY < 5500)
    K[old] = np.where(np.isin(T['K0'][old], ['sea', 'river']), 'steppe', T['K0'][old])
    t = Town(T, 'Hearthold', (2312, 5300), 'large', (30, 45),
             "the fire country's town of knights and crafts: the castle on its rock commands the only stable ground between the lava "
             'flows; armourers, smiths, potters and vintners under the walls; the lower town on the flat ground below, toward the springs and the coast',
             "a rock between two lava flows below the crater, ringed by its town wall; the old flow's weathered ash below it farmed",
             neighbourhoods=[('the Castle', "inside the wall: the keep, the hall, the barracks and drill yard, the chapel, the knights' houses", 2312, 5250),
                             ("Smiths' Row", 'forges and armourers against the cooled lava, east of the gate market', 2480, 5500),
                             ('Gate Street', 'the gate market, the inn and the shops below the gate', 2200, 5470),
                             ('Ash Lane', "potters', vintners' and smiths' terraces stepping down the slope", 2340, 5660)],
             gathering=[('the inner square', 2388, 5224), ('the gate market', 2312, 5492), ('the drill yard', 2388, 5380)], seed=106)
    t.fort = {'wall_px': [[2176, 5064], [2464, 5064], [2464, 5424], [2176, 5424], [2176, 5064]], 'thick_cells': 2,
              'towers_px': [[2176, 5064], [2464, 5064], [2464, 5424], [2176, 5424], [2176, 5244], [2464, 5244], [2280, 5424], [2344, 5424]],
              'gates': [{'name': 'the gate', 'x_px': [HEARTHOLD_GATE[0], HEARTHOLD_GATE[1]], 'y_px': [5408, 5424], 'side': 'south', 'open': True}],
              'postern': {'name': 'the west postern', 'x_px': [2176, 2192], 'y_px': list(HEARTHOLD_POSTERN), 'side': 'west', 'open': False,
                          'opens': 'after the knights accept you (a later shortcut to the Forge Stair)'}}
    # the wall: a ring of cells two thick on the rock, towers at the corners, the gate and the gate towers, the postern walled up
    x0, y0, x1, y1 = HEARTHOLD_WALL
    a0, b0, a1, b1 = y0 // CELL, x0 // CELL, y1 // CELL, x1 // CELL
    ring = np.zeros_like(T['taken'])
    ring[a0:a1, b0:b1] = True; ring[a0 + 2:a1 - 2, b0 + 2:b1 - 2] = False
    for (tx, ty) in t.fort['towers_px']:
        r, c = int(ty // CELL), int(tx // CELL)
        ring[r - 2:r + 2, c - 2:c + 2] = True
    gate = np.zeros_like(ring); gate[a1 - 4:a1 + 2, HEARTHOLD_GATE[0] // CELL:HEARTHOLD_GATE[1] // CELL] = True
    ring &= ~gate
    rd = np.isin(K, list(ROUTE))
    K[ring & ~rd] = 'castlewall'
    T['barrier'] |= ndi.binary_dilation(ring & ~rd, iterations=1) & ~gate
    T['taken'] |= ring
    inner = np.zeros_like(ring); inner[a0 + 2:a1 - 2, b0 + 2:b1 - 2] = True
    hv = T['h'][inner]                                               # three terraces inside the wall: the keep's, the hall's, the barracks'
    T['h'][inner] = np.where(PY[inner] < 5184, np.percentile(hv, 85), np.where(PY[inner] < 5296, np.percentile(hv, 50), np.percentile(hv, 15)))
    T['tiers_pre'][inner] = np.round(T['h'][inner] * 30 - 0.5).astype(T['tiers_pre'].dtype)
    # inside the wall
    t.street([(2312, 5440), (2312, 5200)], 'side', kind='lane', name='Castle Street')
    t.street([(2208, 5284), (2432, 5284)], 'lane', kind='lane', name='Chapel Row')
    t.hand(2248, 5096, 128, 80, 'keep')
    t.hand(2192, 5192, 104, 56, 'hall')
    t.hand(2192, 5304, 64, 56, 'chapel', plot=None)
    t.hand(2336, 5304, 104, 48, 'barracks')
    for (hx, hy, hw, hd) in ((2192, 5096, 48, 40), (2392, 5096, 48, 40), (2192, 5144, 48, 40), (2392, 5144, 48, 40), (2256, 5304, 40, 48), (2256, 5360, 40, 48)):
        t.hand(hx, hy, hw, hd, 'townhouse')
    t.square(2388, 5224, 52, 32, name='the inner square')
    t.yard(2336, 5352, 2440, 5408, kind='yard', name='the drill yard', why="the knights' and the guard's training ground, beside the barracks")
    t.yard(x0 + 16, y0 + 16, x1 - 16, y1 - 16, kind='plaza', name='the castle yard', why='basalt setts inside the wall')
    # the lower town
    t.street([(2312, 5456), (2312, 5716)], 'main', kind='lane', name='Gate Street')
    t.square(2312, 5492, 56, 28, name='the gate market')
    t.street([(2256, 5492), (1996, 5492)], 'lane', kind='lane', name='Market Street')
    t.street([(2368, 5504), (2760, 5504)], 'side', kind='lane', name="Smiths' Row")
    t.street([(2124, 5596), (2604, 5596)], 'lane', kind='lane', name='Ash Lane')
    t.street([(2124, 5716), (2760, 5716)], 'lane', kind='lane', name="Potters' Lane")
    t.street([(2124, 5492), (2124, 5716)], 'lane', kind='lane', name='Well Lane')
    t.street([(2604, 5504), (2604, 5716)], 'lane', kind='lane', name='Vine Lane')
    # the gate market: the inn and the shops
    t.hand(2136, 5512, 112, 64, 'inn')
    for sx in (2016, 2088, 2192):
        t.hand(sx, 5432, 64, 48, 'shop', plot=(0, -1, 24, 'yard'))
    t.hand(2368, 5440, 72, 48, 'shop')
    # Smiths' Row: forges both sides, the east ones against the cooled lava
    t.hand(2488, 5440, 104, 48, 'forge')
    t.hand(2632, 5440, 104, 48, 'forge')
    for fx in (2376, 2488, 2632):
        t.hand(fx, 5520, 104, 56, 'forge', plot=(0, 1, 8, 'yard'))
    # the home streets: continuous brick-and-basalt terraces stepping down the slope
    fp = ('sign', 'potted plants', 'woodpile', 'water butt', 'lamp')
    # the lower town's home streets: detached houses with their yards (Matt, 28 Oct 11:26), not wall to wall
    t.row(t.S('Ash Lane'), ['house', 'cottage', 'house', 'workshop', 'cottage'], limit=6, plot=(16, 'yard'), reach=32)
    t.row(t.S("Potters' Lane"), ['cottage', 'house', 'workshop', 'house', 'cottage'], limit=7, plot=(16, 'yard'), reach=32)
    t.hand(2248, 5520, 40, 48, 'townhouse')                             # the gate market's corner house
    t.hand(2632, 5600, 120, 40, 'terrace')                               # Vine Lane's terrace above the lava
    # a calm ground: the lower town's leftover rough ground made plain yard, its terraces stepping down in three levels
    lo = (PX > 1990) & (PX < 2770) & (PY > 5424) & (PY < 5784) & ~T['taken'] & ~T['street']
    K[lo & np.isin(K, ['ash', 'lavastone', 'basalt', 'scree', 'scrub', 'deadwood', 'fireweed', 'steppe', 'boulders', 'tor', 'desert', 'meadow'])] = 'yard'
    box_ = (PX > 1990) & (PX < 2770) & (PY > 5424) & (PY < 5784)
    hv = T['h'][box_]
    T['h'][box_] = np.where(PY[box_] < 5590, np.percentile(hv, 70), np.where(PY[box_] < 5700, np.percentile(hv, 45), np.percentile(hv, 20)))
    # the edges: the vines on the cooled ash east of the wall, the lower fields between the town and Cinderwick
    t.fields(2480, 5120, 2620, 5400, ('orchard',), name='the vines', why="vines on the cooled ash of the rock's warm east side", size=(64, 112), hedge=False)
    t.fields(2140, 5744, 2600, 5800, ('field', 'field2'), name='the lower fields', why='barley and beans between the town and the cove', size=(80, 144))
    _adopt_requested(t, authored, 'hearthold')
    return t


HIGHGARTH_STYLE = {'name': 'old_japanese_post_town', 'after': 'a mountain highway post town, in our own style: no real script, invented signs, no modern '
                   'elements (no power lines, poles or vending machines)',
                   'forms': {'machiya': 'dark weathered timber townhouse, two storeys, wall to wall, lattice front, low deep eaves with a second small eave '
                                        'over the shopfront, hanging lanterns',
                             'honjin': 'a post-town inn (lodgings for travellers on the pass road)', 'temple_hall': 'the main hall: heavy tiled hipped roof, white '
                             'plaster and timber frame, on a stone plinth', 'pagoda': 'a five-storey pagoda, the landmark seen from the ways in; vermilion '
                             'trim', 'watchkeep': "a small black keep on a battered stone base with a tarn in front, snow on its roofs: the lord's watch on "
                             'the pass, smaller than Hearthold\'s keep', 'minka_thatched': 'a steep thatched farmhouse built for snow, on the upper '
                             'terraces', 'kura': 'a storehouse with white plaster walls and a tiled roof', 'bathhouse': 'the small hot spring bathhouse'},
                   'colour': 'dark roofs and timber, white plaster lines; vermilion only on the temple gate and the pagoda trim',
                   'ground': 'grey stone paving on Garth Street, raked gravel in the temple court, moss, stone steps, snow above the town'}


def highgarth(T, X):
    """Highgarth, authored by hand as an old post town on the pass road (Matt, 28 Oct): Garth Street, the post road, wall to wall
    with machiya and two post inns; the temple precinct on its stone plinth above the town with the pagoda; the shrine path of
    timber gates climbing toward the closed pass; the lord's small black keep watching the pass behind its tarn; thatched
    farmhouses on the upper terraces, the terraced fields below, the quarry, the sawmill and a small hot spring bathhouse."""
    K = T['K']
    t = Town(T, 'Highgarth', X.HIGHGARTH, 'medium', (24, 36),
             "an old post town on the pass road: lodgings, stores and the lord's watch on the north pass; slate from its quarry, wool from the "
             "summer pastures and timber from the valley's larches go down to Cogsworth. Its trade over the pass stopped when the Starfall "
             'brought the rockfall down, and the lord sealed the pass: the road beyond waits for a later region',
             "a sheltered valley on the upper Cog inside the range: Garth Street along the valley floor, the temple on its plinth up the east "
             'slope, terraces stepping down to the river, snow on the peaks round it',
             neighbourhoods=[('Garth Street', 'the post road: machiya wall to wall, the two post inns, the post square', 7920, 1150),
                             ('the temple', 'the main hall, the pagoda and the gravel court on their plinth; the pine grove and the shrine path', 8064, 990),
                             ('the upper terraces', 'thatched farmhouses and storehouses up the east slope; the slate quarry', 8150, 1200),
                             ('Mill Lane', 'the sawmill by the Cog, the bathhouse and the moon-viewing terrace', 7750, 1260)],
             gathering=[('the post square', 7976, 1188), ('the temple court', 8060, 1040), ('the moon-viewing terrace', 7736, 1296)], seed=109)
    t.style = HIGHGARTH_STYLE
    t.cap = 40
    # the post road through the town: the Garth Road and the Northway laid on the soft grid with one slight bend on the contour
    set_route(T, 'the Garth Road', (7800, 996, 8000, 1344), [(7928, 1336), (7928, 1172), (7912, 1172)], 24, 'path')
    set_route(T, 'the Northway', (7800, 996, 8000, 1344), [(7912, 1172), (7912, 1000)], 24, 'path')
    t.street([(7912, 1000), (7912, 1172), (7928, 1172), (7928, 1336)], 'side', kind='lane', name='Garth Street')
    t.street([(7928, 1132), (8320, 1132)], 'lane', kind='lane', name='Quarry Lane')
    t.street([(7912, 1252), (7704, 1252)], 'lane', kind='lane', name='Mill Lane')
    t.street([(7928, 1004), (8000, 1004)], 'lane', kind='stair', name='Temple Steps')
    t.street([(8124, 1132), (8124, 1336)], 'lane', kind='lane', name='High Lane')
    t.street([(7944, 1324), (8124, 1324)], 'lane', kind='lane', name='Terrace Lane')
    t.street([(8064, 920), (8064, 648)], 'close', kind='stair', name='the shrine path')
    t.street([(7868, 700), (7904, 700)], 'close', kind='stair', name='Keep Steps')
    t.square(7972, 1172, 28, 28, name='the post square')
    # the temple on its stone plinth: the hall, the pagoda, the gravel court; the temple gate where the steps arrive
    plinth = np.zeros_like(T['taken']); plinth[928 // CELL:1072 // CELL, 8000 // CELL:8128 // CELL] = True
    ring = plinth & ~ndi.binary_erosion(plinth, iterations=1)
    ring[992 // CELL:1016 // CELL, 8000 // CELL:8008 // CELL] = False
    K[ring & np.isin(K, list(BUILDABLE))] = 'retain'; T['taken'] |= ring
    t.hand(8024, 944, 96, 64, 'temple_hall')
    t.hand(8088, 1024, 32, 32, 'pagoda')
    t.yard(8008, 936, 8120, 1064, kind='yard', name='the temple court', why='raked gravel, stone lanterns and the bell')
    # the lord's watch keep on its battered stone base, the tarn in front
    base = np.zeros_like(T['taken']); base[664 // CELL:736 // CELL, 7904 // CELL:7976 // CELL] = True
    bring = base & ~ndi.binary_erosion(base, iterations=1); bring[688 // CELL:712 // CELL, 7904 // CELL:7912 // CELL] = False
    K[bring & np.isin(K, list(BUILDABLE))] = 'retain'; T['taken'] |= bring
    t.hand(7912, 672, 56, 56, 'watchkeep')
    tarn = np.zeros_like(T['taken']); tarn[744 // CELL:776 // CELL, 7904 // CELL:7976 // CELL] = True
    tarn &= np.isin(K, list(BUILDABLE)) & ~T['street'] & ~T['taken']
    K[tarn] = 'tarn'; T['barrier'] |= ndi.binary_dilation(tarn, iterations=1)
    # the post inns, the upper terraces' farmhouses and storehouses, the bathhouse and the sawmill
    t.hand(7840, 1040, 56, 72, 'honjin', plot=(-1, 0, 16, 'yard'))
    t.hand(7944, 1216, 56, 80, 'honjin', plot=(1, 0, 16, 'yard'))
    for (hx, hy, hw, hd) in ((8144, 1060, 64, 64), (8224, 1060, 64, 64), (8136, 1148, 56, 72), (8136, 1228, 56, 72)):
        t.hand(hx, hy, hw, hd, 'minka_thatched')
    for (hx, hy) in ((8232, 1004), (8064, 1148), (8064, 1196)):
        t.hand(hx, hy, 40, 40 if hx > 8200 else 32, 'kura')
    # the upper terraces filled: more farmhouses and storehouses on every terrace above the post road (Matt, 28 Oct 11:26)
    for (hx, hy, hw, hd, f) in ((8224, 1256, 56, 64, 'minka_thatched'), (8040, 1240, 56, 64, 'minka_thatched'),
                                (8144, 1004, 64, 48, 'minka_thatched'), (8296, 1004, 32, 40, 'kura'),
                                (7744, 1016, 64, 56, 'minka_thatched'), (7744, 1088, 40, 32, 'kura'), (7744, 1128, 56, 48, 'minka_thatched')):
        t.hand(hx, hy, hw, hd, f)
    t.hand(7768, 1264, 72, 48, 'bathhouse')
    t.hand(7712, 1184, 88, 56, 'mill')
    # Garth Street wall to wall on both sides: blocks of machiya fronts, each front 3 to 6 cells
    t.frontage(t.S('Garth Street'), sides=(-1, 1), form='machiya_row', block=(72, 128), depth=(40, 48), alley=(0,),
               props=('hanging lantern', 'stone lantern', 'noren curtain', 'invented sign board', 'potted pine', 'water barrel'),
               roofs=('tile', 'tile', 'tile'), limit=None)
    # the second machiya lane: Mill Lane down to the stream, its own short rows on both sides
    t.frontage(t.S('Mill Lane'), sides=(-1, 1), form='machiya_row', block=(72, 112), depth=(40, 40), alley=(0,),
               props=('hanging lantern', 'noren curtain', 'water barrel', 'potted pine'), roofs=('tile', 'tile', 'tile'), limit=4,
               why="the lane from the post road down to the mill and the footbridge: craftsmen's machiya wall to wall")
    t.frontage(t.S('High Lane'), sides=(-1,), form='machiya_row', block=(72, 112), depth=(40, 40), alley=(0,),
               props=('hanging lantern', 'potted pine'), roofs=('tile', 'tile', 'tile'), limit=3,
               why='the upper street along the terrace edge: a short row of machiya facing the farmhouses')
    for b in t.buildings:
        for q in b.get('bays', []):
            q['w_cells'] = q['w_cells']                                # (fronts already 3 to 8 cells)
    # the terraces: retaining walls of stone along the contours (the town steps up from the stream to the temple), the
    # stream's stone embankment, and the ground stepped tier by tier
    walls = [[(7832, 1000), (7832, 1236)], [(8016, 1076), (8016, 1300)], [(8104, 1140), (8104, 1340)]]
    for wl in walls:
        (x0_, y0_), (x1_, y1_) = wl
        c_ = int(x0_ // CELL); seg = K[int(y0_ // CELL):int(y1_ // CELL), c_]
        free_ = ~T['taken'][int(y0_ // CELL):int(y1_ // CELL), c_] & ~T['street'][int(y0_ // CELL):int(y1_ // CELL), c_] & np.isin(seg, list(BUILDABLE))
        seg[free_] = 'retain'
    box_ = (PX > 7600) & (PX < 8330) & (PY > 990) & (PY < 1350)
    hv = T['h'][box_]; base_h = float(np.percentile(hv, 30))
    step = 1.0 / 30
    T['h'][box_ & (PX < 7832)] = base_h
    T['h'][box_ & (PX >= 7832) & (PX < 8016)] = base_h + step
    T['h'][box_ & (PX >= 8016) & (PX < 8104)] = base_h + 2 * step
    T['h'][box_ & (PX >= 8104)] = base_h + 3 * step
    T['h'][plinth] = base_h + 3 * step
    T['tiers_pre'][box_] = np.round(T['h'][box_] * 30 - 0.5).astype(T['tiers_pre'].dtype)
    river = np.isin(K, ['river', 'rapids'])
    bank = ndi.binary_dilation(river, iterations=1) & ~river & (PY > 990) & (PY < 1350) & (PX > 7560) & (PX < 7800) & np.isin(K, list(BUILDABLE)) \
        & ~T['taken'] & ~T['street']
    K[bank] = 'retain'                                                # the stream's stone embankment
    # the footbridge over the Cog on Mill Lane (a crossing for walkers: tried as a real bridge; see the plan's features)
    fb_ = np.zeros_like(T['taken']); fb_[1248 // CELL:1264 // CELL, 7600 // CELL:7720 // CELL] = True
    fb_ &= np.isin(K, ['river', 'rapids', 'creek'])
    K[fb_] = 'bridge'
    t.footbridge = {'name': 'the Mill Lane footbridge', 'xy_px': [7680, 1256], 'over': 'the Cog', 'foot_only': True, 'counts_as_way': False,
                    'cells': int(fb_.sum())}
    # the ground and the details
    t.yard(7712, 1272, 7760, 1320, kind='plaza', name='the moon-viewing terrace', why="facing the beam over the valley; the bathhouse's pools hold the moon's light")
    grove = np.zeros_like(T['taken']); grove[864 // CELL:928 // CELL, 7968 // CELL:8056 // CELL] = True
    K[grove & np.isin(K, ['meadow', 'alpine', 'scree', 'boulders', 'bramble', 'thicket'])] = 'conifer'
    t.outskirts.append({'kind': 'conifer', 'name': 'the pine grove', 'box': [7968, 864, 8056, 928], 'why': "the shrine's pines on the slope"})
    t.yard(8208, 1148, 8304, 1236, name='the slate quarry', why='slate for the roofs of Cogsworth and the valley')
    t.yard(7840, 860, 7940, 950, name='the folds', why='sheepfolds below the summer pastures')
    # the terraced paddies: stepped strips on stone walls down the lower slope, every other one flooded
    water = np.zeros_like(T['taken'])
    for i, y_ in enumerate(range(1384, 1600, 40)):
        a_, c_ = y_ // CELL, (y_ + 40) // CELL
        sub = K[a_:c_, 7744 // CELL:8064 // CELL]
        ok_ = np.isin(sub, ['meadow', 'alpine', 'field', 'field2', 'hedge', 'scrub', 'broadleaf', 'clearing']) & ~T['street'][a_:c_, 7744 // CELL:8064 // CELL] \
            & ~T['FRAME'][a_:c_, 7744 // CELL:8064 // CELL]
        sub[ok_] = 'field' if i % 2 == 0 else 'field2'
        sub[0, ok_[0]] = 'retain'
        if i % 2 == 0:
            water[a_ + 1:c_, 7744 // CELL:8064 // CELL] |= ok_[1:]
        hh = T['h'][a_:c_, 7744 // CELL:8064 // CELL]; hh[ok_] = base_h - (i + 1) * step / 2
    T['paddy_water'] = water
    t.outskirts.append({'kind': 'field', 'name': 'the terraced paddies', 'box': [7744, 1384, 8064, 1600], 'why': 'rice stepping down the valley on stone walls, every other terrace flooded'})
    # the snow line just above the town
    snow = (PY < 944) & (PX > 7600) & (PX < 8330) & (PY > 600) & np.isin(K, ['alpine', 'meadow', 'scree', 'scree2', 'boulders', 'bramble', 'thicket', 'felltree']) \
        & ~T['taken'] & ~T['street'] & ~T['FRAME']
    K[snow] = 'snow'
    set_route(T, 'the Northway', (7800, 780, 8000, 999), [(7912, 992), (7880, 952), (7904, 904), (7876, 860), (7888, 800)], 24, 'path')
    WK = list(g.WALK)
    fr_ = T['FRAME'] & np.isin(K, WK) & ~np.isin(T['K0'], WK)
    K[fr_] = T['K0'][fr_]                                             # nothing walkable-looking painted onto the frame
    t.gates_on_path = [[8064, y_] for y_ in range(900, 650, -36)]  # the timber gates along the shrine path
    t.shrine_path = [[8064, 928], [8064, 648]]
    return t


def arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]


FRONTAGE_WHY = {   # why a street is wall to wall (Matt, 28 Oct 11:26: only where a real town would build that way)
    'Neon Harbour: the old waterfront': 'the old port town packed behind the quays: land by the water is dear, houses share walls',
    'Neon Harbour: the Lanes': 'the crowded city core between the docks and the Heights: apartment rows wall to wall',
    'Neon Harbour: the Heights': 'terraces cut into the steep slope: each contour street has room for one built row',
    'Highgarth': 'the old post road: inns and merchants\' houses crowd the road the travellers walk, as in a post town',
    'Crossroads': 'the market core: shops and granaries crowd the market street where the trade is',
    'Dust Gulch': "the frontier main street: every business wants a front on the one street the wagons use"}


def set_route(T, rn, box, pts, width=24, kind='path'):
    """A regional route's part inside a box laid by hand (pts in its own direction): the old line's ground back to its
    natural cover, the new one painted; it joins the route where it leaves the box."""
    K = T['K']; K0 = T['K0']
    old = [tuple(p) for p in T['route_px'][rn]]
    x0, y0, x1, y1 = box
    ins = [i for i, (x, y) in enumerate(old) if x0 <= x <= x1 and y0 <= y <= y1]
    if not ins:
        return 0
    i0, i1 = ins[0], ins[-1]
    new = ([old[i0 - 1]] if i0 > 0 else []) + [tuple(map(float, p)) for p in pts] + ([old[i1 + 1]] if i1 < len(old) - 1 else [])
    om = _lm(old[max(0, i0 - 1):i1 + 2], width + 16)
    wetk = ['river', 'creek', 'channel', 'canal', 'sea', 'bridge', 'pool', 'falls', 'rapids']
    nm = _lm(new, width)
    oldc = om & np.isin(K, ['road', 'path', 'trail']) & ~nm
    nat = np.where(np.isin(K0, ['sea', 'river', 'canal', 'road', 'path', 'bridge', 'stair', 'creek', 'trail']), 'meadow', K0)
    nat = np.where(np.isin(nat, ['wild', 'ancient', 'thicket', 'felltree']), 'broadleaf', nat)
    K[oldc] = nat[oldc]
    K[nm & ~np.isin(K, wetk)] = kind
    xs, ys, al, tot = g.densify(new, 6)
    T['route_px'][rn] = old[:max(0, i0 - 1)] + list(zip(xs.tolist(), ys.tolist())) + old[i1 + 2:]
    return 1


def straighten(T, rn, box, width=40, kind='road'):
    """A regional route's part inside a city laid out as planned streets: each stretch on land between its water crossings
    squared into x and y runs on the cells, where the squared line stays on land; the crossings (its bridges) are kept as they
    were. The old line's ground goes back to its natural cover, the new line is painted as the route."""
    K = T['K']; K0 = T['K0']
    pts = [tuple(p) for p in T['route_px'][rn]]
    x0, y0, x1, y1 = box
    wetk = ['river', 'creek', 'channel', 'canal', 'sea', 'surf', 'bridge', 'pool', 'falls', 'rapids']
    def wetp(p):
        r, c = int(p[1] // CELL), int(p[0] // CELL)
        return not (0 <= r < H and 0 <= c < W) or K[r, c] in wetk or K0[r, c] in wetk
    out, i, changed = [], 0, 0
    while i < len(pts):
        p = pts[i]
        if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1) or wetp(p):
            out.append(p); i += 1; continue
        j = i
        while j < len(pts) and x0 <= pts[j][0] <= x1 and y0 <= pts[j][1] <= y1 and not wetp(pts[j]):
            j += 1
        seg = pts[i:j]

        def square(seg, depth):
            nonlocal changed
            L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(seg, seg[1:]))
            if L < 96 or len(seg) < 3:
                return list(seg)
            key = _rdp_pts(seg, 44)
            new = orth(key, width // CELL)
            new = ([tuple(seg[0])] + [q for q in new if q != tuple(seg[0]) and q != tuple(seg[-1])] + [tuple(seg[-1])]) if len(new) >= 2 else list(seg)
            nm = band_mask(new, width // CELL, 'cheb')
            om = _lm(seg, width + 16)
            bad = nm & ~om & (np.isin(K, wetk + ['cliff', 'crag', 'wall', 'castlewall', 'fence', 'craterrim', 'shardglass']) | T.get('keepout', np.zeros_like(nm)))
            if bad.any():                                            # the terrain forces a curve here: try the halves
                if depth >= 3:
                    return list(seg)
                k = len(seg) // 2
                return square(seg[:k + 1], depth + 1)[:-1] + square(seg[k:], depth + 1)
            old = om & np.isin(K, ['road', 'path', 'trail']) & ~nm
            nat = np.where(np.isin(K0, ['sea', 'river', 'canal', 'road', 'path', 'bridge', 'stair', 'creek', 'trail']), 'meadow', K0)
            nat = np.where(np.isin(nat, ['wild', 'ancient', 'thicket', 'felltree']), 'broadleaf', nat)
            K[old] = nat[old]
            K[nm & ~np.isin(K, wetk)] = kind
            xs, ys, al, tot = g.densify(new, 6)
            changed += 1
            return list(zip(xs.tolist(), ys.tolist()))
        out += square(seg, 0); i = j
    T['route_px'][rn] = out
    return changed


def _rdp_pts(pts, eps):
    if len(pts) < 3:
        return list(pts)
    a, b = np.array(pts[0], float), np.array(pts[-1], float); ab = b - a; L = np.hypot(*ab) or 1e-9
    d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / L for p in pts[1:-1]]
    k = int(np.argmax(d)) + 1
    if d[k - 1] > eps:
        return _rdp_pts(pts[:k + 1], eps)[:-1] + _rdp_pts(pts[k:], eps)
    return [pts[0], pts[-1]]


def neon(T, X, rng):
    """Neon Harbour, clearly the largest place in the world: five districts that blend into one another round the ria, the
    east coast and the Heights, with inhabited outskirts on its approaches (provisional 60 to 90 buildings)."""
    out = {}
    K = T['K']
    # the regional roads through the city become its planned streets: straight runs the districts hang off, curving only at the water
    T.setdefault('straightened', {})
    for rn, bx in (('Quay Street', (10950, 4380, 11600, 5600)), ('Old Bridges', (10450, 4300, 11150, 4520)), ('Cape Road', (11400, 5000, 12300, 5800)),
                   ('Lull Road', (9650, 4250, 10560, 4580)), ('Delta Road', (9780, 4380, 10400, 5700))):
        T['straightened'][rn] = straighten(T, rn, bx, 40 if g.ROUTES[rn][1] == 'road' else 24, g.ROUTES[rn][1] if g.ROUTES[rn][1] in ('road', 'path') else 'road')
    # ------------------------------------------------ 1. the old waterfront: the Falls Rock and the old quays round the ria's head
    t = Town(T, 'Neon Harbour: the old waterfront', (10950, 4470), 'city district', (12, 18),
             'the city\'s first streets, round the ria\'s head where the Glint falls gave the first crossing: narrow lanes, old houses, '
             'small businesses (chandlers, cafes, pawn shops, a ferry office) and the Bridgefoot square',
             'the rock between the Glint\'s falls and the old quays at the head of the ria', seed=201,
             neighbourhoods=[('the Falls Rock', 'the oldest houses between the falls', 10760, 4430), ('the old quays', 'the first quays, now cafes and small trade', 11120, 4600)],
             gathering=[('Bridgefoot', 11135, 4462), ('the falls steps', 10760, 4500)])
    for pts in grid(10600, 4300, 11240, 4700, 128, 104, rng, 0):
        t.street(pts, 24, name=None)
    t.cap = 22
    t.square(11135, 4462, 44, 30, name='Bridgefoot')
    t.cap = 26
    for s_ in list(t.streets):                                       # wall-to-wall old houses along every street (Matt's Eastward street)
        if s_['name'] is None:
            t.frontage(s_['pts'], sides=(-1, 1), form='row_house', block=(64, 160), depth=(32, 40), alley=(0, 0, 8),
                       props=('sign', 'awning', 'potted plants', 'planter tree', 'pipes', 'AC unit'), roofs=('tile', 'tin', 'flat'))
    out['Neon Harbour: the old waterfront'] = t
    # ------------------------------------------------ 3. the residential lanes and the east shore
    t = Town(T, 'Neon Harbour: the Lanes and the East Shore', (11480, 4480), 'city district', (14, 20),
             'closely packed homes and flats with courtyards, washing over the lanes, pot plants, corner shops and a school; the East '
             'Shore\'s terraces face the open sea', 'between the old waterfront and the Company district, and along the east coast',
             seed=203,
             neighbourhoods=[('the Lanes', 'flats round courtyards, corner shops', 11470, 4480), ('the East Shore', 'terraces along the sea front, the lido', 12100, 5150)],
             gathering=[('Courtyard Square', 11470, 4470), ('the sea front', 12200, 5150)])
    # the Lanes: a dense block of narrow lanes between the old waterfront and the Company district, apartment rows along them
    t.level, t.slope_max = 2, 0.03
    for y in (4316, 4396, 4476, 4556, 4636):
        t.street([(11276, y), (11556, y)], 'lane', name=None)
    for x in (11276, 11416, 11556):
        t.street([(x, 4300), (x, 4700)], 'lane', name=None)
    # the East Shore: one sea-front road and two cross streets, terraces facing the sea
    t.street([(12196, 4940), (12196, 5380)], 'side', name='Shore Road')
    t.street([(11980, 5060), (12196, 5060)], 'lane', name='Lido Lane')
    t.street([(11980, 5260), (12196, 5260)], 'lane', name='Terrace Lane')
    t.cap = 22
    t.square(11470, 4470, 30, 22, name='Courtyard Square')
    for s_ in list(t.streets):
        if s_['name'] is None and s_['pts'][0][1] == s_['pts'][-1][1]:   # the Lanes: wall-to-wall apartment fronts, stair alleys between
            t.frontage(s_['pts'], sides=(-1,), form='row_tenement', block=(96, 144), depth=(32, 40), stair_every=2, alley=(0, 8),
                       props=('sign', 'awning', 'AC unit', 'pipes', 'gas tank', 'potted plants', 'planter tree'), roofs=('flat', 'tin', 'flat'))
        elif s_['name'] is not None:
            t.row(s_['pts'], ['terrace', 'aptrow', 'terrace'], plot=(8, 'yard'), gap=(0, 4), limit=4, sides=(1, -1))
    out['Neon Harbour: the Lanes and the East Shore'] = t
    # ------------------------------------------------ 2. the working docks: the ria's deep east side, quays, warehouses, yards
    t = Town(T, 'Neon Harbour: the docks', (11320, 5050), 'city district', (12, 18),
             'warehouses, boats, repair yards, workshops and cargo handling: the deep water of the ria\'s east side, the steamer pier, '
             'the fish market, the cranes and the slip', 'the ria\'s east shore from the old quays down to its mouth', seed=202,
             neighbourhoods=[('Quayside', 'the long quay, the cranes and the bonded warehouses', 11250, 4950), ('the slip', 'the repair yard and the boat slip near the mouth', 11380, 5420)],
             gathering=[('the fish market', 11230, 5080), ('the dock gate', 11400, 4790)])
    shore = T['land'] & ndi.binary_dilation(T['sea'], iterations=4) & ~ndi.binary_dilation(T['sea'], iterations=0) & (PX > 11120) & (PX < 11420) & (PY > 4700) & (PY < 5480)
    shore &= np.isin(K, list(BUILDABLE)) & ~np.isin(K, list(ROUTE))
    K[shore] = 'quay'; T['street'] |= shore; T['used'] |= shore
    t.spaces.append({'kind': 'quay', 'name': 'the long quay', 'x': 11220, 'y': 5000, 'rx': 120, 'ry': 380})
    for pts in ([(11330, 4760), (11370, 5000), (11390, 5250), (11400, 5470)], [(11220, 4860), (11330, 4865), (11460, 4870)],
                [(11240, 5180), (11360, 5185), (11480, 5190)], [(11250, 5380), (11380, 5390), (11500, 5400)]):
        t.street(pts, 32, name=None)
    t.square(11228, 5078, 36, 26, name='the fish market')
    qs = route_part(T, 'Quay Street', (11100, 4600, 11450, 5520))
    t.cap = 13
    t.row(qs, ['longwarehouse', 'longwarehouse', 'workshop', 'longwarehouse', 'office'], sides=(-1,), plot=None, gap=(4, 12), limit=7)
    for s_ in t.streets:
        t.row(s_['pts'], ['longwarehouse', 'workshop', 'warehouse'], plot=(24, 'yard'), gap=(4, 12), limit=3)
    t.fill(13, 420, ('longwarehouse', 'workshop', 'warehouse'), plot=(24, 'yard'), box=(11080, 4640, 11600, 5560), reach=200)
    for qy in range(4760, 5440, 95):                                       # piers out into the deep water
        ys = qy // CELL; row = K[ys]
        xs_ = [x for x in range(11120 // CELL, 11320 // CELL) if row[x] == 'quay']
        if xs_:
            x0 = min(xs_) * CELL
            m = _lm([(x0, qy), (x0 - 130, qy)], 12) & T['sea']; K[m] = 'pier'
            K[ys, max(xs_) - 1:max(xs_) + 1] = 'crane'
    t.yard(11420, 5380, 11540, 5480, name='the slip', why='boats hauled out for repair')
    out['Neon Harbour: the docks'] = t
    # ------------------------------------------------ 4. the Company district: the maglev terminus, offices, the Company's yard
    t = Town(T, 'Neon Harbour: the Company district', (11850, 4560), 'city district', (12, 18),
             'larger buildings, offices, the Company\'s tower and the maglev terminus; deliveries and concentrated street activity; the '
             'Company crater fenced in its yard to the north, its light sold as neon', 'the flats east of the old town, round the terminus', seed=204,
             neighbourhoods=[('Terminus Square', 'the maglev terminus and its square', 11640, 4560), ('Neon Row', 'offices, arcades and the neon boulevard', 11980, 4560),
                             ("the Company's yard", 'the fenced crater and its works', 11780, 4170)],
             gathering=[('Terminus Square', 11650, 4565), ('Neon Square', 12050, 4700)])
    bl = t.street([(11570, 4528), (11800, 4535), (12050, 4550), (12320, 4565)], 'main', kind='boulevard', name='Neon Row')
    for pts in ([(11800, 4310), (11800, 4560), (11805, 4860)], [(12060, 4320), (12060, 4580), (12065, 4870)], [(11590, 4720), (11850, 4725), (12310, 4740)],
                [(11620, 4380), (11850, 4385), (12300, 4390)]):
        t.street(pts, 32, kind='boulevard', name=None)
    t.square(11650, 4565, 60, 38, name='Terminus Square')
    t.square(12050, 4700, 44, 30, name='Neon Square')
    for s_ in t.streets:
        t.row(s_['pts'], ['slab', 'bigtower', 'slab', 'office'], plot=None, gap=(4, 16), limit=4, setback=28)
    t.fill(14, 360, ('slab', 'bigtower', 'office'), plot=None, box=(11540, 4300, 12330, 4880))
    cx_, cy_ = X.V.CRATERS['the Company crater'][:2]
    yard = g.shape(cx_, cy_, 190, 140, 3701, 0.15) & T['land'] & ~np.isin(K, list(ROUTE) + ['river', 'sea']) & ~T['taken'] & ~T['street']
    K[yard] = 'yard'
    bowl = g.shape(cx_, cy_, 85, 72, 3702, 0.2) & yard; rim = g.shape(cx_, cy_, 104, 90, 3702, 0.2) & yard & ~bowl
    K[rim] = 'craterrim'; K[bowl] = 'shardglass'
    fence = yard & ~ndi.binary_erosion(yard, iterations=1)
    fence &= ~(np.hypot(PX - cx_, PY - (cy_ + 135)) < 48)              # the yard's gate, toward the district's streets
    K[fence & ~np.isin(K, list(ROUTE))] = 'fence'
    t.outskirts.append({'kind': 'yard', 'name': "the Company's yard", 'box': [int(cx_ - 190), int(cy_ - 140), int(cx_ + 190), int(cy_ + 140)],
                        'why': 'the Company crater, fenced; its shard light pumped to the neon'})
    out['Neon Harbour: the Company district'] = t
    # ------------------------------------------------ 5. the Heights and the Skyport
    t = Town(T, 'Neon Harbour: the Heights and the Skyport', (10050, 5050), 'city district', (12, 20),
             'terraces, stairs and elevated walks over the city; the funicular up from the canal basin; the Skyport\'s mooring masts on '
             'the crown, where the airships ride above the roofs; views over the ria, the docks and the sea',
             'the headland west of the ria, over three knolls', seed=205,
             neighbourhoods=[('the crown', 'the Skyport: its masts, the terminal and the hangar', 10040, 4900), ('the terraces', 'houses on the contours, stairs between', 10120, 5250),
                             ('Funicular foot', 'the canal basin and the funicular station', 10074, 4935)],
             gathering=[('the Skyport terminal', 10060, 4840), ('the belvedere', 10200, 5420)])
    t.level, t.slope_max = 2, 0.03
    t.cap = 18
    ap = g.shape(10030, 4905, 120, 90, 3801, 0.12) & T['land'] & ~np.isin(K, list(ROUTE))
    K[ap] = 'apron'; T['street'] |= ap
    for (mx, my) in ((9960, 4880), (10040, 4950), (10110, 4870)):
        a, b = C(mx, my); K[a - 1:a + 2, b - 1:b + 2] = 'tower'; T['taken'][a - 2:a + 3, b - 2:b + 3] = True
    t.spaces.append({'kind': 'apron', 'name': 'the Skyport', 'x': 10030, 'y': 4905, 'rx': 120, 'ry': 90})
    t.place(10030, 4752, 'skyport', w=208, d=96, r=120)               # the Skyport: one big terminal on the crown, the landmark
    # the terraces: contour streets stepping down the headland, stair streets between them, rows of houses on retaining walls
    contours = (5016, 5096, 5176, 5256, 5336, 5416, 5496)
    for y in contours:
        t.street([(9852, y + 4), (10268, y + 4)], 'lane', kind='lane', name=None)
    for x in (9940, 10164):
        t.street([(x + 4, 5000), (x + 4, 5520)], 'lane', kind='stair', name=None)
    for s_ in list(t.streets):
        if s_['pts'][0][1] == s_['pts'][-1][1]:                       # the contour streets: houses on their uphill (north) side
            t.frontage(s_['pts'], sides=(-1,), form='row_house', block=(96, 176), depth=(32, 40), stair_every=2, alley=(0, 8),
                       props=('potted plants', 'planter tree', 'AC unit', 'sign', 'washing line'), roofs=('tile', 'flat', 'tin'))
    ret = np.zeros_like(T['taken'])                                    # the retaining wall at each terrace's foot (its street's south kerb)
    for y in contours:
        r = int((y + 4 + 16) // CELL)
        ret[r, int(9852 // CELL):int(10268 // CELL)] = True
    ret &= np.isin(K, list(BUILDABLE)) & ~T['taken'] & ~T['street'] & ~np.isin(K, list(ROUTE))
    K[ret] = 'retain'
    out['Neon Harbour: the Heights and the Skyport'] = t
    # ------------------------------------------------ the outskirts: Canalside, Glintside, Halcyon Row; Launch Cape
    t = Town(T, 'Canalside', (10000, 4430), 'outskirts', (6, 12),
             "market gardens and the carters' and bargees' houses on the Lull Road where it comes into the city beside the Lull Cut",
             'the flat land between the Lull Road and the canal, west of the old town', seed=206)
    lr = route_part(T, 'Lull Road', (9700, 4300, 10500, 4520))
    t.street(lr, 'main', name='Canal Road (Lull Road)', route='Lull Road')
    t.row(lr, ['cottage', 'house', 'workshop', 'house'], limit=10, start=10, plot=(40, 'garden'), reach=32)
    t.fields(9700, 4470, 10350, 4660, ('field2', 'field', 'orchard'), name='the market gardens', why="vegetables and flowers for the city's markets", size=(64, 128))
    out['Canalside'] = t
    t = Town(T, 'Glintside', (11120, 4150), 'hamlet', (3, 6),
             'a village of mill houses and laundries along the Glint above the falls, now the city\'s northern edge, where the maglev comes in',
             'the Glint\'s banks north of the old town', seed=207)
    t.level, t.slope_max = 2, 0.03
    t.street([(10952, 4404), (10952, 4320)], 'lane', name='Glint Steps')
    t.street([(10860, 4320), (11060, 4320), (11260, 4320)], 'side', name='Mill Street')
    t.street([(11152, 4320), (11152, 4120)], 'lane', name='Weir Lane')
    t.street([(10968, 4296), (11152, 4296)], 'lane', name='Mill Row')
    t.street([(11260, 4320), (11260, 4420)], 'lane', name='Laundry Lane')
    t.square(11000, 4372, 40, 20, kind='garden', name='the mill green')
    for s_ in t.streets:
        t.row(s_['pts'], ['house', 'cottage', 'mill', 'house'], limit=5, plot=(32, 'garden'), reach=32)
    cands = [(x_, 4240) for x_ in range(10968, 11140, 72)] + [(x_, 4312) for x_ in range(10968, 11140, 72)] + \
            [(11168, y_) for y_ in range(4128, 4280, 48)] + [(11072, y_) for y_ in range(4128, 4280, 48)] + \
            [(x_, y_) for y_ in range(4112, 4272, 40) for x_ in range(10904, 11280, 48)]
    for (cx_, cy_) in cands:                                         # cottages on Mill Row and Weir Lane, by hand, up to five
        if t.count() >= 5:
            break
        a_, b_ = C(cx_, cy_)
        if not T['street'][max(0, a_ - 3):a_ + 8, max(0, b_ - 3):b_ + 11].any():
            continue                                                  # only beside a street
        t.hand(cx_, cy_, 64, 40, 'cottage', plot=None)
    t.fields(10950, 3980, 11400, 4120, ('field2', 'orchard'), name='the allotments', why="the city's allotments by the Glint", size=(64, 112))
    out['Glintside'] = t
    t = Town(T, 'Halcyon Row', (12020, 5590), 'outskirts', (8, 14),
             "the launch staff's houses at the cape's neck, named for the Company's station overhead: the canteen, the store, the clinic; "
             'a heath buffer of more than 800 px between it and the pad', 'the neck of Launch Cape, behind the dunes', seed=208)
    cr = route_part(T, 'Cape Road', (11700, 5300, 12250, 5800))
    t.street(cr, 'side', name='Halcyon Row (Cape Road)', route='Cape Road')
    t.street([(11930, 5468), (12140, 5468), (12140, 5660)], 'lane', name='Canteen Lane')
    t.row(cr, ['house', 'house', 'shop', 'house', 'public'], limit=10, start=10, plot=(32, 'garden'), reach=32)
    t.row(t.S('Canteen Lane'), ['house', 'cottage', 'house'], limit=10 - t.count() if t.count() < 10 else 0, plot=(32, 'garden'), reach=32)
    out['Halcyon Row'] = t
    return out


def charcoal_hollow(T, X):
    """The foresters' and charcoal burners' hamlet in its clearing in the old forest (Matt, 28 Oct): a lane off the Old Forest
    Trail, four huts and the kilns."""
    t = Town(T, 'Charcoal Hollow', (8470, 2440), 'hamlet', (6, 8), "foresters and charcoal burners: charcoal for Cogsworth's forges, "
             "timber the old way, by hand", 'a clearing in the old forest, on the trail from the Towpath', seed=310)
    rp = route_part(T, 'the Old Forest Trail', (8380, 2340, 8560, 2560))
    if len(rp) > 4:
        i0 = len(rp) // 2; x0_, y0_ = rp[i0]
        t.street([(x0_ + 12, y0_), (x0_ + 120, y0_)], 'lane', name='Kiln Lane')
        t.row(t.streets[-1]['pts'], ['cottage', 'shed', 'workshop', 'cottage', 'shed', 'cottage'], limit=6, plot=(16, 'yard'), reach=32)
    t.row(rp, ['cottage', 'shed', 'workshop', 'cottage'], limit=max(0, 8 - t.count()), plot=(16, 'yard'), reach=32)
    # more huts and sheds on the open ground near the trail (6 to 8, Matt 28 Oct 11:26): free, buildable, within 40 px of the way
    K = T['K']; way = np.isin(K, list(ROUTE)) | T['street']
    near = ndi.binary_dilation(way, iterations=5)
    kinds = ['cottage', 'shed', 'cottage', 'shed', 'cottage', 'shed']
    for hy in range(2296, 2584, 16):
        for hx in range(8320, 8600, 16):
            if t.count() >= 7:
                break
            f = kinds[t.count() % len(kinds)]
            w_, d_ = (48, 40) if f == 'cottage' else (32, 32)
            a_, b_ = C(hx, hy); c_, e_ = a_ + d_ // CELL, b_ + w_ // CELL
            win = (slice(a_ - 2, c_ + 2), slice(b_ - 2, e_ + 2))
            if not near[a_:c_, b_:e_].any() or T['taken'][win].any() or T['street'][win].any() or T['barrier'][win].any() \
                    or not np.isin(K[win], list(BUILDABLE)).all():
                continue
            t.hand(hx, hy, w_, d_, f, plot=None)
    t.yard(8500, 2460, 8580, 2500, name='the kiln yard', why='charcoal burning in earth clamps, the charcoal bagged for Cogsworth')
    t.yard(8440, 2340, 8500, 2370, name='the log stacks', why="cordwood seasoning by the lane before it goes into the clamps")
    return {'Charcoal Hollow': t}


def launch_cape(T, X, *, authored=None):
    """Launch Cape's facility: the pad at the headland's tip with its service apron, the assembly hall, workshops and stores
    near the cape's middle, a heath buffer round the pad, the road down the cape."""
    authored = _authored_inputs(authored, {'launch-cape'})
    K = T['K']
    t = Town(T, 'Launch Cape', X.PAD, 'facility', (4, 8),
             "the Company's launch site: rockets go up over open sea, away from people (W8); the assembly hall, the workshops and the "
             "propellant stores in the cape's middle, the pad at its tip; a buffer of open heath between the pad and every house",
             'the headland past the city, exposed to the sea on three sides', seed=209,
             neighbourhoods=[('the pad', 'the launch pad, its tower and the service apron', X.PAD[0], X.PAD[1]),
                             ('the works', 'the assembly hall, workshops, stores and the control bunker', 12060, 6080)],
             gathering=[('the works gate', 12000, 5960)])
    t.level, t.slope_max = 4, 0.04
    pad = g.shape(X.PAD[0], X.PAD[1], 72, 60, 3901, 0.1) & T['land']
    apron = g.shape(X.PAD[0] - 20, X.PAD[1] - 70, 130, 100, 3902, 0.15) & T['land'] & ~pad
    K[apron & ~np.isin(K, list(ROUTE))] = 'apron'; K[pad] = 'pad'
    a, b = C(X.PAD[0] + 40, X.PAD[1] - 30); K[a - 3:a + 1, b - 1:b + 1] = 'tower'
    T['street'] |= pad | apron; T['used'] |= pad | apron
    t.spaces.append({'kind': 'pad', 'name': 'the pad', 'x': X.PAD[0], 'y': X.PAD[1], 'rx': 72, 'ry': 60})
    t.cluster(12060, 6090, 170, ['hangar', 'workshop', 'warehouse', 'workshop', 'public', 'warehouse'], 6, plot=(16, 'yard'))
    t.yard(11960, 5960, 12250, 6000, name='the works yard', why='carts and the transporter road to the pad')
    _adopt_requested(t, authored, 'launch-cape')
    return {'Launch Cape': t}


def smaller(T, X):
    """The places that stay smaller (Driftwood, Lullford, Gullwick, Cinder Springs, the Lode, the Ember forge): enough houses
    to read as what they are."""
    out = {}
    specs = [('Lullford', (8860, 4350), 'town', (10, 16), "the lowest bridging place of the Lull: the swing bridge, the toll house, bargees' "
              'inns and the mill on the island', 'gravel terraces either side of the river', 'Lull Road', (8560, 4230, 9100, 4480), 14),
             ('Driftwood', (6440, 5080), 'village', (8, 12), "the valley's landing place: fishers' cottages, the lighthouse keeper's house, the "
              'ferry pier', "the cove at the Sleepwater's mouth under the Headland", 'Valley lane south', (6300, 4880, 6700, 5120), 10),
             ('Gullwick', (8045, 5200), 'village', (6, 10), 'a fishing cove on the open coast: boats on the beach, net lofts', 'the cove west of the delta',
              'Gull Lane', (7950, 4980, 8150, 5200), 8),
             ('Cinder Springs', (1860, 5600), 'hamlet', (4, 8), 'hot springs where the sea seeps into the warm flank: the bath house and lodgings',
              "the volcano's warm south-west flank", 'Ember Way', (1780, 5450, 2000, 5760), 6),
             ('the Lode', (2820, 1690), 'hamlet', (3, 6), 'the iron and copper mine: the mine house, the smithy, the miners\' bunkhouse', 'the massif foothills above Dust Gulch',
              'Lode Track', (2700, 1600, 2900, 1820), 4),
             ('Ember forge', (2140, 4985), 'facility', (3, 5), "the forge at the caldera lip, using the crater's heat: the forge hall, the ore store",
              "the caldera's lip above Hearthold", 'Forge Stair', (2040, 4900, 2260, 5100), 3)]
    for i, (nm, c, size, tgt, purpose, setting, rn, box, n) in enumerate(specs):
        t = Town(T, nm, c, size, tgt, purpose, setting, seed=300 + i)
        if nm in ('Ember forge', 'the Lode'):
            t.level, t.slope_max = 4, 0.04
        rp = route_part(T, rn, box)
        pl = (24, 'yard') if nm == 'the Lode' else (32, 'garden')
        t.row(rp, ['cottage', 'house', 'shop', 'cottage', 'workshop'], limit=n, start=8, plot=pl, reach=88 if size in ('town', 'facility') else 32)
        if t.count() < n and len(rp) > 4:                            # a lane off the road, houses on both its sides
            for frac, sgn in ((0.5, 1), (0.5, -1), (0.3, 1), (0.7, -1)):
                if t.count() >= n:
                    break
                i0 = int(len(rp) * frac); (ax, ay), (bx, by) = rp[max(0, i0 - 3)], rp[min(len(rp) - 1, i0 + 3)]
                L = math.hypot(bx - ax, by - ay) or 1
                nx, ny = -(by - ay) / L * sgn, (bx - ax) / L * sgn
                x0_, y0_ = rp[i0]
                ln = t.street([(x0_ + nx * 12, y0_ + ny * 12), (x0_ + nx * 150, y0_ + ny * 150)], 'lane', name=f'{nm} Lane' if sgn > 0 else f'{nm} Back Lane')
                if len(ln) >= 2 and t.streets[-1]['pieces']:
                    t.row(t.streets[-1]['pts'], ['cottage', 'house', 'workshop'], limit=n - t.count(), start=4, plot=pl, reach=32)
        if nm == 'the Lode':
            dry_out(T, box[0] - 100, box[1] - 100, box[2] + 100, box[3] + 100)
        pl = (24, 'yard') if nm == 'the Lode' else (32, 'garden')
        t.fill(n, 160, ('cottage', 'house', 'workshop'), reach=160 if size in ('town', 'facility') else 48, box=(box[0] - 60, box[1] - 60, box[2] + 60, box[3] + 60), plot=pl)
        out[nm] = t
    return out


# Exact, UNAPPROVED Y15 inputs. These source pins identify the separately reviewed proposals;
# regeneration never reads its generated JSON as authoring input. Matt must approve placement.
PROPOSED_ADOPTIONS = {'cinderwick': {'status': 'proposal',
                'source': {'commit': '4669140421d7d8c69482fc90b78fea0a50d1d4bc',
                           'blob': '9cacbd0833c090c5365d3a9afea84a15ac9c5977',
                           'path': 'docs/vision/research/blockout/towns/cinderwick.json'},
                'baseline': {'commit': '4984438d09b5fe1333d3e6ea6e6ee82be2bdc908',
                             'blob': 'b1a6b82b71ba055bf6dc351f81a58766775bf1c4',
                             'path': 'docs/vision/research/blockout/towns/cinderwick.json'},
                'terrain_box_cells': [232, 701, 144, 70],
                'buildings': [{'id': 'cinderwick-b014',
                               'type': 'cottage',
                               'form': 'cottage',
                               'footprint_cells': [301, 719, 8, 6],
                               'rect_px': [2408, 5752, 64, 48],
                               'faces': 'cinderwick-s02',
                               'door_cells': [305, 725],
                               'purpose': 'a detached fishing cottage',
                               'occupants': "a fisher's household",
                               'district': 'cinderwick-d-the-quay',
                               'counted': True,
                               'counts_as': 1,
                               'plot_cells': [301, 717, 8, 2],
                               'plot': 'yard'},
                              {'id': 'cinderwick-b015',
                               'type': 'cottage',
                               'form': 'cottage',
                               'footprint_cells': [306, 727, 7, 5],
                               'rect_px': [2448, 5816, 56, 40],
                               'faces': 'cinderwick-s02',
                               'door_cells': [305, 729],
                               'purpose': 'a detached fishing cottage',
                               'occupants': "a fisher's household",
                               'district': 'cinderwick-d-the-quay',
                               'counted': True,
                               'counts_as': 1,
                               'plot_cells': [306, 725, 7, 2],
                               'plot': 'yard'},
                              {'id': 'cinderwick-b016',
                               'type': 'barn',
                               'form': 'shed',
                               'footprint_cells': [300, 736, 4, 3],
                               'rect_px': [2400, 5888, 32, 24],
                               'faces': 'cinderwick-s01',
                               'door_cells': [302, 735],
                               'purpose': 'a net shed by the boatyard',
                               'occupants': 'work storage only; resident roles deferred to X3',
                               'district': 'cinderwick-d-the-quay',
                               'counted': False,
                               'counts_as': 0},
                              {'id': 'cinderwick-b017',
                               'type': 'barn',
                               'form': 'shed',
                               'footprint_cells': [306, 736, 4, 3],
                               'rect_px': [2448, 5888, 32, 24],
                               'faces': 'cinderwick-s01',
                               'door_cells': [308, 735],
                               'purpose': 'a net shed by the boatyard',
                               'occupants': 'work storage only; resident roles deferred to X3',
                               'district': 'cinderwick-d-the-quay',
                               'counted': False,
                               'counts_as': 0}],
                'districts': [],
                'district_descriptions': {'cinderwick-d-the-quay': {'declared': 'the existing stone quay with '
                                                                                'detached fishing cottages, net '
                                                                                'sheds and a working boatyard',
                                                                    'function': 'docks and transport with homes'}},
                'open_uses': [{'id': 'cinderwick-o01',
                               'name': 'the boatyard work apron',
                               'kind': 'yard',
                               'cells': [294, 736, 6, 5]},
                              {'id': 'cinderwick-o02',
                               'name': 'the boatyard net-shed frontage',
                               'kind': 'yard',
                               'cells': [300, 736, 11, 3]}],
                'site_authored': 'existing generated layout with Y15 Cinderwick-only authored additions (issue149 '
                                 'comment6471345306)'},
 'hearthold': {'status': 'proposal',
               'source': {'commit': '59f3722d1b39050cc81709fa5933d4c9c093ee98',
                          'blob': '51fad9db44e2a9be22d2bbb5b007249ae9ecebce',
                          'path': 'docs/vision/research/blockout/towns/hearthold.json'},
               'baseline': {'commit': '4984438d09b5fe1333d3e6ea6e6ee82be2bdc908',
                            'blob': 'f19a9108cf07a3b8140ba136c04149a8c0ddd31d',
                            'path': 'docs/vision/research/blockout/towns/hearthold.json'},
               'terrain_box_cells': [234, 622, 129, 119],
               'buildings': [{'id': 'hearthold-b033',
                              'type': 'house',
                              'form': 'house',
                              'footprint_cells': [253, 706, 10, 6],
                              'rect_px': [2024, 5648, 80, 48],
                              'faces': 'hearthold-s09',
                              'door_cells': [263, 708],
                              'purpose': 'a detached lower-town house',
                              'occupants': 'household; individual residents and routines not yet authored',
                              'district': 'hearthold-d-ash-lane',
                              'counted': True,
                              'plot_cells': [251, 706, 2, 6],
                              'plot': 'yard',
                              'counts_as': 1},
                             {'id': 'hearthold-b034',
                              'type': 'cottage',
                              'form': 'cottage',
                              'footprint_cells': [254, 698, 9, 6],
                              'rect_px': [2032, 5584, 72, 48],
                              'faces': 'hearthold-s09',
                              'door_cells': [263, 700],
                              'purpose': 'a detached lower-town cottage',
                              'occupants': 'household; individual residents and routines not yet authored',
                              'district': 'hearthold-d-ash-lane',
                              'counted': True,
                              'plot_cells': [252, 698, 2, 6],
                              'plot': 'yard',
                              'counts_as': 1},
                             {'id': 'hearthold-b035',
                              'type': 'workshop',
                              'form': 'workshop',
                              'footprint_cells': [343, 690, 11, 7],
                              'rect_px': [2744, 5520, 88, 56],
                              'faces': 'hearthold-s06',
                              'door_cells': [345, 689],
                              'purpose': 'a craft workshop; specific trade not yet authored',
                              'occupants': 'craft workers; individual workers and routines not yet authored',
                              'district': 'hearthold-d-smiths-row',
                              'counted': True,
                              'plot_cells': [343, 697, 11, 2],
                              'plot': 'yard',
                              'counts_as': 1}],
               'districts': [],
               'district_descriptions': {},
               'open_uses': []},
 'launch-cape': {'status': 'proposal',
                 'source': {'commit': '9276174000e47858e92a25803e606fb9dea1fc87',
                            'blob': '9aab428f54a898b2c19049857bc092fe39d6e009',
                            'path': 'docs/vision/research/blockout/towns/launch-cape.json'},
                 'baseline': {'commit': '4984438d09b5fe1333d3e6ea6e6ee82be2bdc908',
                              'blob': '06faf55d311d78016966c977bedcc7598348b817',
                              'path': 'docs/vision/research/blockout/towns/launch-cape.json'},
                 'terrain_box_cells': [1467, 726, 79, 104],
                 'buildings': [{'id': 'launch-cape-b007',
                                'type': 'cottage',
                                'form': 'cottage',
                                'footprint_cells': [1494, 727, 8, 6],
                                'rect_px': [11952, 5816, 64, 48],
                                'faces': 'launch-cape-a1',
                                'door_cells': [1502, 729],
                                'purpose': 'a detached staff cottage',
                                'occupants': 'staff; individual residents and routines not yet authored',
                                'district': 'launch-cape-d-staff-homes',
                                'counted': True,
                                'plot_cells': [1492, 727, 2, 6],
                                'plot': 'garden',
                                'counts_as': 1},
                               {'id': 'launch-cape-b008',
                                'type': 'cottage',
                                'form': 'cottage',
                                'footprint_cells': [1510, 729, 8, 6],
                                'rect_px': [12080, 5832, 64, 48],
                                'faces': 'launch-cape-a1',
                                'door_cells': [1509, 731],
                                'purpose': 'a detached staff cottage',
                                'occupants': 'staff; individual residents and routines not yet authored',
                                'district': 'launch-cape-d-staff-homes',
                                'counted': True,
                                'plot_cells': [1518, 729, 2, 6],
                                'plot': 'garden',
                                'counts_as': 1},
                               {'id': 'launch-cape-b009',
                                'type': 'workshop',
                                'form': 'workshop',
                                'footprint_cells': [1509, 737, 13, 7],
                                'rect_px': [12072, 5896, 104, 56],
                                'faces': 'launch-cape-a1',
                                'door_cells': [1508, 739],
                                'purpose': 'a staff settlement workshop',
                                'occupants': 'staff; individual workers and routines not yet authored',
                                'district': 'launch-cape-d-the-works',
                                'counted': True,
                                'plot_cells': [1522, 737, 2, 7],
                                'plot': 'yard',
                                'counts_as': 1}],
                 'districts': [{'id': 'launch-cape-d-staff-homes',
                                'name': 'the staff homes',
                                'centre_px': [12048, 5848],
                                'declared': 'two detached staff cottages with gardens at the northern entrance, '
                                            'away from the pad',
                                'town': 'Launch Cape',
                                'function': 'homes'}],
                 'district_descriptions': {'launch-cape-d-the-works': {'function': 'docks and transport'}},
                 'open_uses': []}}
