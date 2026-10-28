"""Town plans: the soft-grid street rules and the checker for docs/vision/research/blockout/towns/*.json.

Each town plan (schema "mygame.town_plan/1", written by geo55.py through town_plans.py) holds a settlement's site, its
streets by class on the 8 px cells, its squares, districts and buildings, the arrivals from the regional routes, the game
layout (arrival, first view, landmark, loops, later shortcuts, quiet corners), the ground, a terrain grid of the town's box
and empty residents and routines for Codex (X3).

    python3 scripts/review/town_plan.py                  # check every plan, print one line per town and the failures
    python3 scripts/review/town_plan.py --town hearthold # one plan, every finding

What it checks, per plan (ground-rules.md 4 and 5, size-guide.md 0, Matt's brief of 27 Oct):
  cells       every footprint on whole cells; every street (not an arrival) in x and y runs on the soft grid at its class width
  off_streets no building on a street, square or arrival
  off_water   no building on water or a barrier; a street crosses water only on a bridge
  reach       every building has a door within three cells of the street it faces (a close two cells wide if it is set back)
  count       the counted buildings within the town's range
  arrivals    every arrival lies on its regional route (blockout-v55.json) or at its station (a ferry)
  orphans     every street is joined to an arrival through the street network
  districts   a large town has three or more districts with two or more functions and two or more gathering places
  layout      a landmark within two screens (40 x 22.5 cells each) of every entry; a medium or large town has a loop
  bridges     wherever a street (not a regional route) and water overlap, the cells are a bridge
  blocks      each block between the streets is at least half plots, buildings or a named open use (park, yard, square)
  sizes       each building within its form's footprint range (size_table_px); a medium or large town has four forms or more
  outskirts   an outskirt, hamlet or village's houses stand on its streets (no close longer than eight cells)
  planned     a city's regional roads inside it (within six cells of its buildings) run in x and y runs (75% of their length), curving
              only at the water
  dry         a desert town is green only along its water (green more than 8 cells from water at most 3%)
The insets' labels are checked where they are drawn (map55.town_inset): no two label boxes overlap.
It reports (not fails): dead ends, the town's size in screens and the number of street blocks (loops).

The functions orth() and band() are the generator's own rules too (towns55.py imports them), so the plan and the check
cannot drift apart."""
import json
import math
import os
import sys

import numpy as np

CELL = 8
SCREEN = (40, 22.5)                       # cells per screen, landscape phone (size-guide.md 0)
WATER = set('~')
BARRIER = set('#')


# ------------------------------------------------------------------------------------------ the soft-grid rules
def _snap(v, off):
    return round((v - off) / CELL) * CELL + off


def orth(pts, wc):
    """A polyline squared onto the soft grid: runs along x or y on cell lines (a cell edge for an even width, a cell's middle
    for an odd one); a leg within two cells of straight is one run, a slanting leg a Z of three runs (an L when short);
    collinear runs merged."""
    off = 0 if wc % 2 == 0 else CELL // 2
    if len(pts) < 2:
        return []
    p = (_snap(pts[0][0], off), _snap(pts[0][1], off))
    out = [p]
    for (x, y) in pts[1:]:
        q = (_snap(x, off), _snap(y, off))
        dx, dy = q[0] - p[0], q[1] - p[1]
        if dx == 0 and dy == 0:
            continue
        if abs(dx) >= abs(dy) and abs(dy) <= 2 * CELL:
            nxt = [(q[0], p[1])]
        elif abs(dy) > abs(dx) and abs(dx) <= 2 * CELL:
            nxt = [(p[0], q[1])]
        elif abs(dx) >= abs(dy):
            if abs(dx) / 2 < 2 * CELL:
                nxt = [(q[0], p[1]), q]
            else:
                mx = _snap(p[0] + dx / 2, off); nxt = [(mx, p[1]), (mx, q[1]), q]
        else:
            if abs(dy) / 2 < 2 * CELL:
                nxt = [(p[0], q[1]), q]
            else:
                my = _snap(p[1] + dy / 2, off); nxt = [(p[0], my), (q[0], my), q]
        for n in nxt:
            if n != out[-1]:
                out.append(n)
        p = out[-1]
    # merge collinear points
    res = [out[0]]
    for i in range(1, len(out)):
        if len(res) >= 2:
            a, b, c = res[-2], res[-1], out[i]
            if (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
                res[-1] = c
                continue
        res.append(out[i])
    return [(float(a), float(b)) for a, b in res]


def band(line, wc, metric, box):
    """The cells (in box = (c0, r0, w, h)) a street covers: cell middles within half its width of its line, measured square
    (Chebyshev: square ends, square corners) for a soft-grid street and round (Euclidean) for a route's own line."""
    c0, r0, w, h = box
    cy, cx = np.mgrid[r0:r0 + h, c0:c0 + w]
    px = (cx + 0.5) * CELL; py = (cy + 0.5) * CELL
    hw = wc * CELL / 2 + 1e-6
    m = np.zeros((h, w), bool)
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        if metric == 'cheb':
            ddx = np.maximum(np.maximum(min(ax, bx) - px, 0), px - max(ax, bx))
            ddy = np.maximum(np.maximum(min(ay, by) - py, 0), py - max(ay, by))
            if ax != bx and ay != by:            # a slanting leg (never in an orth line): fall back to round
                metric = 'euclid'
            else:
                m |= np.maximum(ddx, ddy) <= hw
                continue
        vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy or 1e-9
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / L2, 0, 1)
        m |= np.hypot(px - (ax + t * vx), py - (ay + t * vy)) <= hw
    return m


def rle_decode(rows, w):
    out = []
    for row in rows:
        r = []; i = 0
        while i < len(row):
            j = i
            while j < len(row) and row[j].isdigit():
                j += 1
            n = int(row[i:j]) if j > i else 1
            r.append(row[j] * n); i = j + 1
        s = ''.join(r)
        assert len(s) == w, (len(s), w)
        out.append(s)
    return np.array([list(s) for s in out])


def rle_encode(arr):
    rows = []
    for row in arr:
        s = []; prev = None; n = 0
        for ch in row:
            if ch == prev:
                n += 1
            else:
                if prev is not None:
                    s.append((str(n) if n > 1 else '') + prev)
                prev, n = ch, 1
        s.append((str(n) if n > 1 else '') + prev)
        rows.append(''.join(s))
    return rows


# ------------------------------------------------------------------------------------------ the checker
def _dist_to_poly(x, y, pts):
    best = 1e18
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy or 1e-9
        t = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / L2))
        best = min(best, math.hypot(x - ax - t * vx, y - ay - t * vy))
    return best


def check_plan(P, blockout):
    from scipy import ndimage as ndi
    fails, notes = [], []
    tb = P['terrain']; c0, r0, w, h = tb['box_cells']
    ter = rle_decode(tb['rows'], w)
    box = (c0, r0, w, h)

    def local(m_cells):
        return m_cells

    def rect_mask(c, r, cw, ch):
        m = np.zeros((h, w), bool)
        m[max(0, r - r0):max(0, r - r0 + ch), max(0, c - c0):max(0, c - c0 + cw)] = True
        return m

    # the network
    net = np.zeros((h, w), bool); net_noclose = np.zeros((h, w), bool)
    bands = {}
    for s in P['streets']:
        line = [tuple(v) for v in s['vertices_px']]
        m = band(line, s['width_cells'], 'euclid' if s['class'] == 'arrival' or s.get('follows_route') else 'cheb', box)
        bands[s['id']] = m
        net |= m
        if s['class'] != 'close':
            net_noclose |= m
        # cells: soft-grid streets in x/y runs on the right cell lines
        if s['class'] != 'arrival' and not s.get('follows_route'):
            off = 0 if s['width_cells'] % 2 == 0 else CELL // 2
            for (ax, ay), (bx, by) in zip(line, line[1:]):
                if ax != bx and ay != by:
                    fails.append(f"cells: street {s['id']} has a slanting run {ax, ay}-{bx, by}")
                    break
            if any((v[0] - off) % CELL or (v[1] - off) % CELL for v in line):
                fails.append(f"cells: street {s['id']} has a vertex off its cell lines")
        # bridges: wherever a street and water overlap, the cells are a bridge (code b), never open water
        wet = m & np.isin(ter, list(WATER))
        if wet.sum() > 0 and s['class'] != 'arrival':
            fails.append(f"bridges: street {s['id']} overlaps water on {int(wet.sum())} cells with no bridge")
    for q in P['squares']:
        c, r, cw, ch = q['cells']
        m = rect_mask(c, r, cw, ch) & ~np.isin(ter, list(WATER | BARRIER))
        bands[q['id']] = m; net |= m; net_noclose |= m
    # buildings
    occ = np.zeros((h, w), bool)
    counted = 0
    zone = sum(1 for b in P['buildings'] if b.get('from_zone_plan'))
    if zone:
        notes.append(f'{zone} buildings from the built zone\'s own plan (checked there)')
    for b in P['buildings']:
        c, r, cw, ch = b['footprint_cells']
        if any(int(v) != v for v in (c, r, cw, ch)):
            fails.append(f"cells: building {b['id']} not on whole cells")
        m = rect_mask(c, r, cw, ch)
        if b.get('from_zone_plan'):                # the zone as built: its plan and rules (rules.route_clear) are the authority
            occ |= m; counted += 1 if b['counted'] else 0
            continue
        if (m & net).any():
            hit = [sid for sid, bm in bands.items() if (bm & m).any()]
            fails.append(f"off_streets: building {b['id']} ({b['type']}) stands on {', '.join(hit[:3])}")
        tt = ter[m]
        if np.isin(tt, list(WATER)).any():
            fails.append(f"off_water: building {b['id']} stands on water")
        if np.isin(tt, list(BARRIER)).any():
            fails.append(f"off_water: building {b['id']} stands on a barrier")
        if (occ & m).any():
            fails.append(f"cells: building {b['id']} overlaps another building")
        occ |= m
        counted += 1 if b['counted'] else 0
        # reach: the door within 3 cells of the faced street's band (a close's end: 1)
        dc, dr = b['door_cells']
        fm = bands.get(b['faces'])
        if fm is None:
            fails.append(f"reach: building {b['id']} faces no street ({b['faces']})"); continue
        rr, cc = np.nonzero(fm)
        if len(rr) == 0:
            fails.append(f"reach: building {b['id']} faces an empty street {b['faces']}"); continue
        dd = np.maximum(np.abs(rr + r0 - dr), np.abs(cc + c0 - dc)).min()
        if dd > 3:
            fails.append(f"reach: building {b['id']}'s door is {int(dd)} cells from {b['faces']}")
        # the door next to the building
        if not (c - 1 <= dc <= c + cw and r - 1 <= dr <= r + ch):
            fails.append(f"reach: building {b['id']}'s door is not at its wall")
    # sizes by type: each building within its form's footprint range (either way round), and a town of several forms
    st = P.get('size_table_px', {})
    forms = set()
    for b in P['buildings']:
        if b.get('from_zone_plan'):
            continue
        f = b.get('form', b['type']); forms.add(f)
        if f not in st:
            fails.append(f"sizes: building {b['id']}'s form {f} has no size range"); continue
        (w0, w1), (d0, d1) = st[f]; bw, bh = b['rect_px'][2], b['rect_px'][3]
        fit = lambda a, b_, lo_, hi_: lo_ - CELL <= a <= hi_ + CELL
        if not ((fit(bw, 0, w0, w1) and fit(bh, 0, d0, d1)) or (fit(bh, 0, w0, w1) and fit(bw, 0, d0, d1))):
            fails.append(f"sizes: building {b['id']} ({f}) is {bw} x {bh} px, outside {w0}-{w1} x {d0}-{d1}")
    if P['size'] in ('large', 'medium', 'city') and len(forms) < 4:
        fails.append(f'sizes: only {len(forms)} building forms ({sorted(forms)})')
    # outskirts and villages: houses on their streets, not floating in the fields
    if P['size'] in ('outskirts', 'hamlet', 'village'):
        for b in P['buildings']:
            fs = next((q for q in P['streets'] if q['id'] == b['faces']), None)
            if fs and fs['class'] == 'close':
                L = sum(abs(x1 - x0) + abs(y1 - y0) for (x0, y0), (x1, y1) in zip(fs['vertices_px'], fs['vertices_px'][1:])) / CELL
                if L > 8:
                    fails.append(f"outskirts: building {b['id']} stands {L:.0f} cells up a close, off its street")
    lo, hi = P['target']
    if not (lo <= counted <= hi):
        fails.append(f'count: {counted} counted buildings, outside {lo} to {hi}')
    if counted != P['buildings_counted']:
        fails.append(f"count: the plan says {P['buildings_counted']}, the list has {counted}")
    # arrivals
    routes = blockout.get('routes', {}); stations = blockout.get('stations', {})
    arr_ids = []
    for a in P['arrivals']:
        arr_ids.append(a['street'])
        if a['kind'] == 'ferry':
            if a['station'] not in stations:
                fails.append(f"arrivals: {a['id']}'s station {a['station']} is not in blockout-v55.json")
            continue
        rt = routes.get(a['route'])
        if rt is None:
            fails.append(f"arrivals: {a['id']}'s route {a['route']} is not in blockout-v55.json"); continue
        poly = rt.get('polyline') or rt.get('px') or rt.get('points')
        for e in a['entries_px']:
            d = _dist_to_poly(e[0], e[1], poly)
            if d > 24:
                fails.append(f"arrivals: {a['id']}'s entry {e} is {d:.0f} px off {a['route']}")
    # orphans: every street joined to an arrival
    lab, n = ndi.label(net)
    good = set()
    for sid in arr_ids:
        if sid in bands:
            good |= set(np.unique(lab[bands[sid]]).tolist()) - {0}
    for sid, m in bands.items():
        ls = set(np.unique(lab[m]).tolist()) - {0}
        if ls and not (ls & good):
            fails.append(f'orphans: {sid} is not joined to an arrival')
    # districts and gathering places
    if P['size'] == 'large' or P['size'] == 'city':
        fn = {d['function'] for d in P['districts'] if d.get('buildings')}
        if len([d for d in P['districts'] if d.get('buildings')]) < 3 or len(fn) < 2:
            fails.append(f"districts: {len(P['districts'])} districts, functions {sorted(fn)}")
        if len(P['gathering_places']) < 2:
            fails.append('districts: fewer than two gathering places')
    # layout: a landmark within two screens of every entry; a loop
    GL = P['game_layout']
    lms = GL['landmarks']
    for a in P['arrivals']:
        for e in a['entries_px']:
            ds = min(max(abs(e[0] - l['xy'][0]) / CELL / SCREEN[0], abs(e[1] - l['xy'][1]) / CELL / SCREEN[1]) for l in lms)
            if ds > 2.0:
                fails.append(f"layout: no landmark within two screens of the entry {e} ({a['id']}): {ds:.1f}")
    bg, nb = ndi.label(~net_noclose)
    edge = set(np.unique(np.concatenate([bg[0], bg[-1], bg[:, 0], bg[:, -1]])).tolist())
    blocks = len(set(range(1, nb + 1)) - edge)
    if P['size'] in ('large', 'medium', 'city') and blocks < 1:
        fails.append('layout: no loop (no street block)')
    # no empty blocks: each block between the streets at least half plots or a named open use
    cov = np.zeros((h, w), bool)
    for b in P['buildings']:
        cov |= rect_mask(*b['footprint_cells'])
        if b.get('plot_cells'):
            cov |= rect_mask(*b['plot_cells'])
    for q in P['squares'] + P.get('open_uses', []):
        cov |= rect_mask(*q['cells'])
    for o in P.get('outskirts', []):
        x0, y0, x1, y1 = o['box']
        cov |= rect_mask(x0 // CELL, y0 // CELL, (x1 - x0) // CELL, (y1 - y0) // CELL)
    for s in P['streets']:
        if s['class'] == 'close':
            cov |= bands[s['id']]
    sm = np.zeros((h, w), bool)
    for s in P['streets']:
        if s['class'] not in ('close', 'arrival'):
            sm |= bands[s['id']]
    for q in P['squares']:
        sm |= bands[q['id']]
    bad_t = np.isin(ter, list(WATER | BARRIER) + ['r', 'b'])
    lab_b, nb_ = ndi.label(~sm)
    edge_b = set(np.unique(np.concatenate([lab_b[0], lab_b[-1], lab_b[:, 0], lab_b[:, -1]])).tolist())
    thin = 0
    for i in range(1, nb_ + 1):
        if i in edge_b:
            continue
        mb = (lab_b == i) & ~bad_t
        area = int(mb.sum())
        if 12 <= area <= 1200 and (cov & mb).sum() < 0.5 * area:
            thin += 1
            rr_, cc_ = np.nonzero(mb)
            fails.append(f'blocks: the block at cells ({int(cc_.mean()) + c0}, {int(rr_.mean()) + r0}) is {100 * (cov & mb).sum() / area:.0f}% plots or open uses')
    # a city's roads are planned: its arrivals inside the city run in x and y, curving only at the water
    if P['size'] == 'city':
        tot = ax_ = 0.0
        citym = ndi.binary_dilation(occ, iterations=6)               # inside the city: within six cells of its buildings
        for a in P['arrivals']:
            if a.get('route_kind') == 'bridge':
                continue                                           # a bridge's line is the crossing's
            v = next((q['vertices_px'] for q in P['streets'] if q['id'] == a['street']), [])
            for (x0, y0), (x1, y1) in zip(v, v[1:]):
                mr, mc = int((y0 + y1) / 2 // CELL) - r0, int((x0 + x1) / 2 // CELL) - c0
                if 0 <= mr < h and 0 <= mc < w and ter[mr, mc] in ('~', 'b'):
                    continue                                       # a crossing of the water follows the water
                if 0 <= mr < h and 0 <= mc < w and citym[mr, mc]:
                    L = math.hypot(x1 - x0, y1 - y0); tot += L
                    ax_ += L if (abs(x1 - x0) < 0.5 or abs(y1 - y0) < 0.5) else 0
        if tot and ax_ / tot < 0.75:
            fails.append(f'planned: only {100 * ax_ / tot:.0f}% of the regional roads inside the city run in x and y runs')
        notes.append(f'{100 * ax_ / max(tot, 1):.0f}% of the city roads in x and y runs')
    # a desert town is green only along its water
    if P['site'].get('dry'):
        fx0, fy0, fx1, fy1 = P['footprint_px']
        win = rect_mask(fx0 // CELL, fy0 // CELL, (fx1 - fx0) // CELL, (fy1 - fy0) // CELL)
        named = np.zeros((h, w), bool)
        for o in P.get('outskirts', []):
            x0, y0, x1, y1 = o['box']; named |= rect_mask(x0 // CELL, y0 // CELL, (x1 - x0) // CELL, (y1 - y0) // CELL)
        dwet = ndi.distance_transform_edt(~np.isin(ter, list(WATER)))
        far_green = win & (ter == 'g') & (dwet > 8) & ~named
        landc = int((win & ~np.isin(ter, list(WATER))).sum()) or 1
        if far_green.sum() > 0.03 * landc:
            fails.append(f'dry: {100 * far_green.sum() / landc:.1f}% of the town is green more than 8 cells from water')
    # dead ends (reported)
    dead = 0
    for s in P['streets']:
        if s['class'] in ('close', 'arrival'):
            continue
        for v in (s['vertices_px'][0], s['vertices_px'][-1]):
            cc_, rr_ = int(v[0] // CELL) - c0, int(v[1] // CELL) - r0
            rad = s['width_cells'] // 2 + 2
            win = (slice(max(0, rr_ - rad), rr_ + rad + 1), slice(max(0, cc_ - rad), cc_ + rad + 1))
            others = np.zeros((h, w), bool)
            for sid, m in bands.items():
                if sid != s['id']:
                    others |= m
            if not others[win].any():
                dead += 1
    bx = P['footprint_px']
    screens = ((bx[2] - bx[0]) / CELL / SCREEN[0], (bx[3] - bx[1]) / CELL / SCREEN[1])
    notes.append(f'{blocks} blocks, {dead} dead ends, {screens[0]:.1f} x {screens[1]:.1f} screens')
    return fails, notes, counted


def main(argv):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    bo = os.path.join(root, 'docs', 'vision', 'research', 'blockout')
    d = argv[argv.index('--dir') + 1] if '--dir' in argv else os.path.join(bo, 'towns')
    only = argv[argv.index('--town') + 1] if '--town' in argv else None
    blockout = json.load(open(os.path.join(bo, 'blockout-v55.json')))
    files = sorted(f for f in os.listdir(d) if f.endswith('.json'))
    bad = 0
    for f in files:
        P = json.load(open(os.path.join(d, f)))
        if only and P['id'] != only:
            continue
        fails, notes, n = check_plan(P, blockout)
        lo, hi = P['target']
        print(f"{'PASS' if not fails else 'FAIL'} {P['id']:24s} {P['size']:10s} {n:3d} buildings ({lo} to {hi}), {len(P['streets'])} streets, "
              f"{len(P['arrivals'])} arrivals; {'; '.join(notes)}")
        for x in (fails if only else fails[:6]):
            print('     ', x)
        if fails and not only and len(fails) > 6:
            print(f'      and {len(fails) - 6} more')
        bad += bool(fails)
    print(f'{len(files) - bad if not only else ""} of {len(files)} plans pass' if not only else '')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
