"""The ground rules on kit zones: the world editor's validator (docs/world-editor.md, "The validator").

A kit zone's plan (game/kit/zones/<zone>.json, the same data as its scene: game/tools/kit_zone.gd
turns one into the other) holds a material per cell and pieces at their feet. These checks read
that data and the pieces' metadata (game/kit/props/index.json, the kit manifest), never pixels, so
a fault is caught where it is placed (docs/vision/ground-rules.md, the same rules as
scripts/review/ground_rules.py on painted plans):

    rules.unknown_piece   a piece or material the library does not have
    rules.unapproved      a piece or material placed before it passed the library gate (advice
                          in a lab or a prototype zone, a fault where the plan says "ship": true)
    rules.route_clear     a piece that blocks movement stands on a route cell (bridges and
                          signposts by design)
    rules.route_water     a route cell meets water with no bridge deck over the crossing
    rules.water_end       a channel ends in a dead end (each body of water reaches the zone's
                          edge, or is a pool of at least 2 x 2 cells)
    rules.deck            a deck (a bridge) that does not span water from land to land
    rules.overlap         two solid pieces share a cell (rocks may touch, never overlap)
    rules.seating         a seat with no route edge within two cells in front of it (south)
    rules.off_grid        a piece whose snap is "cell" with its foot off the 4 world px grid
    rules.walk            a spawn or a door that stands on a blocked cell
    rules.stair           a stair whose flight is not all face, whose head is not flush with the
                          rim above it or whose foot does not land on the lower ground
    rules.water_fall      water crossing a south rim with no waterfall over the face under it, or a
                          waterfall with no water above it (ground-rules 2)
    rules.tier_route      a route that changes tier with no stair between (faces are derived
                          under every south rim: compose.derive, as the game draws them)

    python3 -m scripts.review.kit_rules              report every kit zone
    python3 -m scripts.review.kit_rules --check      exit 1 on any fault
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZONES = os.path.join(ROOT, 'game', 'kit', 'zones')
CELL = 24          # texels


def _f(check, msg, at=None, severity='fault'):
    return {'check': check, 'message': msg, 'at': at, 'severity': severity}


def load_kit():
    man = json.load(open(os.path.join(ROOT, 'game', 'kit', 'terrain', 'manifest.json')))
    idx = json.load(open(os.path.join(ROOT, 'game', 'kit', 'props', 'index.json')))
    return {m['id']: m for m in man['materials']}, idx


def grid(plan, mats):
    """The cells as material ids (strings), faces derived under every south rim; and the tiers."""
    legend = plan['legend']
    rows = plan['rows']
    g = np.array([[legend.get(c, '') for c in r] for r in rows], dtype=object)
    H, W = g.shape
    tiers = np.array([[int(c) for c in r] for r in plan['tiers']]) if plan.get('tiers') else np.zeros((H, W), int)
    faces = [m for m in mats.values() if m.get('face')]
    if faces and tiers.any():
        fm, fh = faces[0]['id'], faces[0]['face']['height_cells']
        t0 = tiers.copy()
        for x in range(W):
            for y in range(H - 1):
                if t0[y, x] > t0[y + 1, x]:
                    for kk in range(1, fh * int(t0[y, x] - t0[y + 1, x]) + 1):
                        if y + kk < H and t0[y + kk, x] < t0[y, x]:
                            g[y + kk, x] = fm
    grid.tiers = tiers
    return g


def blocked_cells(g, mats, plan, idx):
    """The walk mask in cells: a material that is not walkable, unless a deck covers the cell."""
    H, W = g.shape
    b = np.array([[bool(g[y, x]) and not mats[g[y, x]]['walkable'] for x in range(W)] for y in range(H)])
    for c in deck_cells(plan, idx, H, W):
        b[c[1], c[0]] = False
    return b


def rect_cells(foot, rect, H, W, share=0.5):
    """Cells a rect [x, y, w, h] (texels from the foot) covers by at least `share` of a cell."""
    x0, y0 = foot[0] + rect[0], foot[1] + rect[1]
    x1, y1 = x0 + rect[2], y0 + rect[3]
    out = []
    for cy in range(max(0, int(y0 // CELL)), min(H, int(np.ceil(y1 / CELL)))):
        for cx in range(max(0, int(x0 // CELL)), min(W, int(np.ceil(x1 / CELL)))):
            ox = max(0.0, min(x1, (cx + 1) * CELL) - max(x0, cx * CELL))
            oy = max(0.0, min(y1, (cy + 1) * CELL) - max(y0, cy * CELL))
            if ox * oy >= CELL * CELL * share:
                out.append((cx, cy))
    return out


def deck_cells(plan, idx, H, W):
    out = []
    for p in plan.get('pieces', []):
        e = idx.get(p['piece'])
        if e and e.get('deck'):
            out += rect_cells(p['at'], e['deck'], H, W, share=0.25)
    return out


def check_zone(plan) -> list:
    mats, idx = load_kit()
    fs = []
    ship = bool(plan.get('ship'))
    sev_gate = 'fault' if ship else 'advice'
    for c, m in plan['legend'].items():
        if m not in mats:
            fs.append(_f('rules.unknown_piece', "material '%s' is not in the kit" % m))
        elif mats[m]['approval'] != 'approved':
            fs.append(_f('rules.unapproved', "material '%s' is %s, not approved" % (m, mats[m]['approval']), severity=sev_gate))
    if any(f['check'] == 'rules.unknown_piece' for f in fs):
        return fs
    g = grid(plan, mats)
    H, W = g.shape
    route = np.array([[bool(g[y, x]) and mats[g[y, x]].get('route', False) for x in range(W)] for y in range(H)])
    water = np.array([[bool(g[y, x]) and bool(mats[g[y, x]].get('water')) for x in range(W)] for y in range(H)])
    decks = set(deck_cells(plan, idx, H, W))
    unapproved = set()
    solid = {}
    for p in plan.get('pieces', []):
        e = idx.get(p['piece'])
        at = p['at']
        if e is None:
            fs.append(_f('rules.unknown_piece', "piece '%s' is not in the library" % p['piece'], at))
            continue
        if e['approval'] != 'approved':
            unapproved.add(p['piece'])
        cx, cy = int(at[0] // CELL), int(at[1] // CELL)
        if e.get('snap', 'cell') == 'cell' and (at[0] % 12 or at[1] % CELL):
            fs.append(_f('rules.off_grid', "%s (%s): its foot %s is off the soft grid (x on 4, y on 8 world px)"
                         % (p.get('id'), p['piece'], at), at, severity='advice'))
        role = e.get('role')
        if e.get('blocks_move') and role not in ('bridge', 'signpost') and 0 <= cy - 1 < H and 0 <= cx < W:
            foot_cell = (cx, min(H - 1, int((at[1] - 1) // CELL)))
            if route[foot_cell[1], foot_cell[0]]:
                fs.append(_f('rules.route_clear', '%s (%s) stands on a route' % (p.get('id'), p['piece']), at))
        if e.get('collision') and e.get('blocks_move'):
            for c in rect_cells(at, e['collision'], H, W):
                if c in solid:
                    other = solid[c]
                    fs.append(_f('rules.overlap', '%s and %s share the cell %s' % (p.get('id'), other, c), at, severity='advice'))
                else:
                    solid[c] = p.get('id')
        if role == 'seat':
            front = route[min(H - 1, cy):min(H, cy + 2), max(0, cx - 1):cx + 2]
            if not front.any():
                fs.append(_f('rules.seating', '%s: no route edge within two cells in front of it (south)' % p.get('id'), at))
        if role == 'stair':
            cells = rect_cells(at, e['deck'], H, W, share=0.25) if e.get('deck') else []
            tiers = grid.tiers
            if not cells or not all(mats[g[c[1], c[0]]].get('face') for c in cells if g[c[1], c[0]]):
                fs.append(_f('rules.stair', '%s: its flight is not all on a face' % p.get('id'), at))
            else:
                ys = sorted({c[1] for c in cells})
                xs_ = sorted({c[0] for c in cells})
                head = [tiers[ys[0] - 1, x] for x in xs_] if ys[0] > 0 else []
                foot_ = [tiers[ys[-1] + 1, x] for x in xs_] if ys[-1] + 1 < H else []
                if not head or len(set(head)) != 1 or not foot_ or len(set(foot_)) != 1 or head[0] <= foot_[0]:
                    fs.append(_f('rules.stair', '%s: its head is not flush with one rim above, or its foot not on the lower ground' % p.get('id'), at))
        elif e.get('deck'):
            cells = rect_cells(at, e['deck'], H, W, share=0.25)
            ys = sorted({c[1] for c in cells})
            if not cells or not any(water[c[1], c[0]] for c in cells):
                fs.append(_f('rules.deck', '%s spans no water' % p.get('id'), at))
            elif water[ys[0], cells[0][0]] or water[ys[-1], cells[0][0]]:
                fs.append(_f('rules.deck', '%s does not reach land at both ends' % p.get('id'), at))
    if unapproved:
        fs.append(_f('rules.unapproved', '%d pieces placed before the library gate approved them: %s'
                     % (len(unapproved), ', '.join(sorted(unapproved)[:6]) + (' ...' if len(unapproved) > 6 else '')), severity=sev_gate))
    # routes meeting water: only under a deck
    for y in range(H):
        for x in range(W):
            if not route[y, x]:
                continue
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                Y, X = y + dy, x + dx
                if 0 <= Y < H and 0 <= X < W and water[Y, X] and (X, Y) not in decks:
                    fs.append(_f('rules.route_water', 'the route at cell %s runs into water with no bridge' % ((x, y),),
                                 [x * CELL + 12, y * CELL + 12]))
                    break
    # routes change tier only on a stair: a route cell next to a route or face cell of another tier
    # needs a deck (the stair's flight) between them
    tiers = grid.tiers
    for y in range(H):
        for x in range(W):
            if not route[y, x]:
                continue
            for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                Y, X = y + dy, x + dx
                if not (0 <= Y < H and 0 <= X < W) or tiers[Y, X] == tiers[y, x]:
                    continue
                if (route[Y, X] or (g[Y, X] and mats[g[Y, X]].get('face'))) and (X, Y) not in decks and (x, y) not in decks:
                    fs.append(_f('rules.tier_route', 'the route at cell %s changes tier with no stair' % ((x, y),), [x * CELL + 12, y * CELL + 12]))
                    break
    # water crossing a south rim falls over a waterfall piece, and a waterfall has water above it
    falls = set()
    for p in plan.get('pieces', []):
        e = idx.get(p['piece'])
        if e and e.get('role') == 'waterfall':
            cx, cy = int(p['at'][0] // CELL), int(p['at'][1] // CELL)
            cells_ = [(cx + c[0], cy + c[1]) for c in e.get('footprint') or []]
            falls |= set(cells_)
            top = min(c[1] for c in cells_) if cells_ else 0
            if not cells_ or not all(0 <= c[1] < H and 0 <= c[0] < W and g[c[1], c[0]] and mats[g[c[1], c[0]]].get('face') for c in cells_) \
                    or not all(top - 1 >= 0 and water[top - 1, c[0]] for c in cells_):
                fs.append(_f('rules.water_fall', '%s: not over a face with water above it, the width of the channel' % p.get('id'), p['at']))
    for y in range(H - 1):
        for x in range(W):
            if water[y, x] and g[y + 1, x] and mats[g[y + 1, x]].get('face') and (x, y + 1) not in falls:
                fs.append(_f('rules.water_fall', 'water at cell %s crosses a rim with no waterfall' % ((x, y),), [x * CELL + 12, y * CELL + 12]))
    # every body of water reaches the zone's edge or is a pool
    lab, n = ndi.label(water)
    for k in range(1, n + 1):
        m = lab == k
        edge = m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any()
        pool = ndi.binary_erosion(m, structure=np.ones((2, 2), bool)).any()
        if not edge and not pool:
            ys, xs = np.nonzero(m)
            fs.append(_f('rules.water_end', 'a channel of %d cells reaches neither the zone edge nor a pool' % m.sum(),
                         [int(xs.mean()) * CELL, int(ys.mean()) * CELL]))
    # the spawns stand on open ground
    blk = blocked_cells(g, mats, plan, idx)
    for name, at in plan.get('spawns', {}).items():
        cx, cy = int(at[0] // CELL), int(at[1] // CELL)
        if 0 <= cy < H and 0 <= cx < W and blk[cy, cx]:
            fs.append(_f('rules.walk', "spawn '%s' stands on a blocked cell" % name, at, severity='advice'))
    return fs


def zones():
    return sorted(f for f in os.listdir(ZONES) if f.endswith('.json'))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('zones', nargs='*')
    a = ap.parse_args(argv)
    bad = 0
    for z in a.zones or zones():
        plan = json.load(open(os.path.join(ZONES, z if z.endswith('.json') else z + '.json')))
        fs = check_zone(plan)
        faults = [f for f in fs if f['severity'] == 'fault']
        bad += len(faults)
        print('[kit rules] %s: %s' % (plan['zone'], 'ok' if not faults else '%d faults' % len(faults)))
        for f in fs:
            print('  %s %s: %s' % ('FAULT' if f['severity'] == 'fault' else 'advice', f['check'], f['message']))
    return 1 if (a.check and bad) else 0


if __name__ == '__main__':
    sys.exit(main())
