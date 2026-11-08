"""Fences enclose something: closed loops, gates on paths, contents that fit (a kit plan's
version of rules.fences and rules.enclosures; docs/vision/placement-logic.md, rules 1 to 4).

Reads a kit plan (game/kit/zones/<zone>.json shape: cells, pieces at their feet in texels) and the
pieces' metadata, never pixels:

    rules.fences       every arm of a fence cell (placement.boundary.joins) meets the arm of the cell
                       next to it, so the runs close into loops; a run's end post stands against a
                       building; a gate lies in a loop
    rules.enclosures   each closed loop holds something (placement.enclosure "contents": hens,
                       sheep, crops, flowers) that the fence's style may keep (boundary.encloses),
                       with what it needs inside (a coop for hens, a trough for sheep, water and a
                       field shelter in a paddock, a sty, a wallow and a trough for pigs), at a
                       size that fits (a chicken run 4 to 7 cells a side (a hen house is shed-sized), a sheep fold 6 to 10, a
                       paddock 10 or more), and has a gate (a stile lets people over, not stock)
Where a gate meets its path is relations.py's `requires on route` on the gate pieces.

    python3 -m scripts.art.kit.enclosures [zone ...]       report (every kit zone by default)
"""
from __future__ import annotations

import json
import os
import sys

from scripts.art.kit.schema import ROOT

# numpy and scipy are imported where a plan has fences (check_zone, _walls): the world editor's
# validator (game/addons/world_editor/rules_adapter.gd) runs this module with the standard library
# only on CI's Godot job, and a plan without fences needs neither.

CELL = 24
HALF = 12
VEC = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}
# holds: what it needs inside, each a piece's placement.role (or one its enclosure.serves names);
# side in cells: min, max. As ground_rules.ENCLOSE.
ENCLOSE = {
    'chickens': ('coop',), 'sheep': ('trough',), 'horses': ('trough', 'shelter'), 'cattle': ('trough', 'shelter'),
    'goats': ('trough', 'shelter'), 'pigs': ('sty', 'wallow', 'trough'), 'crops': (), 'flowers': (),
}
SIDES = {'chickens': (4, 7), 'sheep': (6, 10), 'horses': (10, 99), 'cattle': (10, 99), 'goats': (4, 10), 'pigs': (3, 7),
         'crops': (2, 99), 'flowers': (1, 99)}
WALLS = ('house', 'forge', 'shelter', 'sty')


def library():
    out = {}
    for kind in ('prop', 'structure'):
        d = os.path.join(ROOT, 'game', 'kit', 'pieces', kind)
        for f in sorted(os.listdir(d)):
            if f.endswith('.json'):
                p = json.load(open(os.path.join(d, f)))
                out[p['id']] = p
    return out


def _f(check, msg, at=None):
    return {'check': check, 'message': msg, 'at': at, 'severity': 'fault'}


def segments(plan, lib):
    """Each fence piece's arms as ((x0, y0), (x1, y1), piece entry) in texels, a gate's whole span."""
    out = []
    for pc in plan.get('pieces', []):
        p = lib.get(pc['piece']) or {}
        b = (p.get('placement') or {}).get('boundary')
        if not b:
            continue
        x, y = pc['at']
        if b.get('gate'):
            half = b.get('span_cells', 3) * CELL / 2
            if set(b['joins']) == {'e', 'w'}:
                out.append(((x - half, y), (x + half, y), pc, 'gate'))
            else:
                out.append(((x, y - half), (x, y + half), pc, 'gate'))
            continue
        for s in b['joins']:
            dx, dy = VEC[s]
            out.append(((x, y), (x + dx * HALF, y + dy * HALF), pc, s))
    return out


def _walls(plan, lib, shape):
    """The buildings' solid boxes as walls (a front garden uses the house's front as its fourth side)."""
    import numpy as np
    m = np.zeros(shape, bool)
    for pc in plan.get('pieces', []):
        p = lib.get(pc['piece']) or {}
        if (p.get('placement') or {}).get('role') not in WALLS:
            continue
        col = (p.get('geometry') or {}).get('collision') or {}
        if col.get('shape') != 'rect':
            continue
        x, y = pc['at']
        r = [v * 3 for v in col['rect']]
        x0, y0 = int(x + r[0]), int(y + r[1])
        m[max(0, y0):max(0, y0 + int(r[3]) + 1), max(0, x0):max(0, x0 + int(r[2]) + 1)] = True
    return m


def check_zone(plan, lib=None) -> list:
    lib = lib or library()
    H, W = len(plan['rows']) * CELL, len(plan['rows'][0]) * CELL
    segs = segments(plan, lib)
    if not segs:
        return []
    import numpy as np
    from scipy import ndimage as ndi
    fs = []
    walls = _walls(plan, lib, (H + 1, W + 1))
    # 1. every arm's end meets another piece's arm end (or a gate's end, or a wall)
    ends = {}
    for a, b, pc, s in segs:
        if s == 'gate':
            for e in (a, b):
                ends.setdefault((round(e[0]), round(e[1])), []).append(pc.get('id'))
        else:
            ends.setdefault((round(b[0]), round(b[1])), []).append(pc.get('id'))
    for a, b, pc, s in segs:
        p = lib[pc['piece']]
        js = p['placement']['boundary']['joins']
        for e in ((a, b) if s == 'gate' else (b,)):
            key = (round(e[0]), round(e[1]))
            if len([i for i in ends[key] if i != pc.get('id')]) == 0:
                fs.append(_f('rules.fences', '%s: its %s end at %s meets no run: join it to the next fence cell or a gate, so the '
                             'fence encloses something' % (pc.get('id'), s if s != 'gate' else 'gate\'s', key), list(key)))
        if s != 'gate' and len(js) == 1:
            x, y = (int(v) for v in pc['at'])
            near = walls[max(0, y - CELL):y + CELL, max(0, x - CELL):x + CELL]
            if not near.any() and s == js[0]:
                fs.append(_f('rules.fences', '%s: an end post standing free: a run ends against a wall, or it closes its loop'
                             % pc.get('id'), pc['at']))
    # 2. the loops: draw the runs and the walls, fill from the zone's edge; what stays dry is inside
    m = walls.copy()
    for a, b, _pc, _s in segs:
        x0, x1 = sorted((int(round(a[0])), int(round(b[0]))))
        y0, y1 = sorted((int(round(a[1])), int(round(b[1]))))
        m[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True
    free = ~m
    lab, n = ndi.label(free)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    gates = [(a, b, pc) for a, b, pc, s in segs if s == 'gate']
    for g in gates:
        (a, b, pc) = g
        mx, my = int((a[0] + b[0]) / 2), int((a[1] + b[1]) / 2)
        around = lab[max(0, my - 3):my + 4, max(0, mx - 3):mx + 4]
        if not (set(np.unique(around)) - {0} - edge):
            fs.append(_f('rules.fences', '%s: the gate opens into no enclosure' % pc.get('id'), pc['at']))
    for k in range(1, n + 1):
        if k in edge:
            continue
        region = lab == k
        if region.sum() < CELL * CELL // 2:
            continue                                   # a sliver between a post and a wall
        ys, xs = np.nonzero(region)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        holds, needs = set(), set()
        for pc in plan.get('pieces', []):
            pl = lib.get(pc['piece'], {}).get('placement') or {}
            enc = pl.get('enclosure')
            if not enc:
                continue
            x, y = int(pc['at'][0]), int(pc['at'][1]) - 2
            inside = 0 <= y < region.shape[0] and 0 <= x < region.shape[1] and region[y, x]
            if not inside and pl.get('role') in WALLS:
                # a sty or a shelter is the pen's wall: it counts if its front faces into the pen
                inside = bool(region[max(0, y + 3):y + 3 + CELL, max(0, x - CELL):x + CELL].any())
            if inside:
                if enc['as'] == 'contents':
                    holds.update(enc['holds'])
                else:
                    for h in enc['holds']:
                        needs.update((h, r) for r in (enc.get('serves') or [pl.get('role')]))
        at = [box[0], box[1]]
        if not holds:
            fs.append(_f('rules.enclosures', 'the enclosure at %s holds nothing: put in what it is for (animals, crops, '
                         'flowers), or open it' % (at,), at))
            continue
        # every fence piece round it must keep what it holds: a fold of hurdles with a stretch of
        # picket in it lets the sheep out there (the Codex lead's review of #430: one permitting
        # style must not mask another that does not)
        bounding = {}
        bounds = ndi.binary_dilation(region, iterations=3) & ~region
        for a, b, pc, s in segs:
            x0, x1 = sorted((int(round(a[0])), int(round(b[0]))))
            y0, y1 = sorted((int(round(a[1])), int(round(b[1]))))
            if bounds[max(0, y0):y1 + 1, max(0, x0):x1 + 1].any():
                bounding[pc['id']] = (pc['piece'], lib[pc['piece']]['placement']['boundary'].get('encloses', []))
        for h in sorted(holds):
            weak = sorted(pid for pid, (_piece, keeps) in bounding.items() if h not in keeps)
            if weak:
                styles = sorted({lib[bounding[pid][0]]['placement']['boundary']['style'] for pid in weak})
                fs.append(_f('rules.enclosures', 'the enclosure at %s holds %s, but its %s fence (%s) does not keep them: '
                             'every stretch round a pen must' % (at, h, '/'.join(styles), ', '.join(weak[:4]) + (' ...' if len(weak) > 4 else '')), at))
            for need in ENCLOSE.get(h, ()):
                if (h, need) not in needs:
                    fs.append(_f('rules.enclosures', 'the enclosure at %s holds %s but has no %s inside' % (at, h, need), at))
            lo, hi = SIDES.get(h, (0, 99))
            for side in ((box[2] - box[0]) / CELL, (box[3] - box[1]) / CELL):
                if not lo - 0.25 <= side <= hi + 0.25:
                    fs.append(_f('rules.enclosures', 'the enclosure at %s is %.1f cells on a side; %s take %d to %d'
                                 % (at, side, h, lo, hi), at))
                    break
        touch = ndi.binary_dilation(region, iterations=3)
        if not any(touch[int(min(a[1], b[1])):int(max(a[1], b[1])) + 1, int(min(a[0], b[0])):int(max(a[0], b[0])) + 1].any()
                   for a, b, _pc in gates):
            fs.append(_f('rules.enclosures', 'the enclosure at %s has no gate: put one where its owner\'s path comes' % (at,), at))
    return fs


def main(argv=None) -> int:
    zones = argv if argv else sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, 'game', 'kit', 'zones')) if f.endswith('.json'))
    bad = 0
    lib = library()
    for z in zones:
        plan = json.load(open(os.path.join(ROOT, 'game', 'kit', 'zones', z + '.json')))
        fs = check_zone(plan, lib)
        bad += len(fs)
        print('[enclosures] %s: %s' % (z, 'ok' if not fs else '%d faults' % len(fs)))
        for f in fs:
            print('  FAULT %s: %s' % (f['check'], f['message']))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
