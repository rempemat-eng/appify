"""Doors, the paths that leave them, the gates paths go through and where fences meet buildings
(Matt's review of the farm study, 4 Nov: "the placement of the fence, doors and pathways does not
align"). A kit plan's version of docs/vision/placement-logic.md rules 5 to 8:

    rules.door_path          a path leaving a door starts centred on the door's opening (within a
                             texel at density 3) and runs straight out at least one cell before
                             it may bend (a door opening onto a lane or a square is not a door path)
    rules.door_clear         nothing (a fence, a bed, a barrel) stands in a door's threshold and
                             swing: the opening's width, as deep as the door is wide (a cell at least)
    rules.gate_path          a gate (or a stile) is centred on the path that crosses it
    rules.path_through_fence a path crosses a boundary only at a gate or a stile
    rules.fence_wall         a boundary that meets a building joins it at a corner or along its
                             wall foot, its end post beside the wall: never drawn in front of the
                             façade (over its base, door or windows) and never short of the wall

Doors are the pieces' geometry.doors: the opening's x span in texels from the foot ("x": [x0, x1),
the leaf between the frame posts) and the side it faces. A path is a run of route cells, so a door
whose centre is not on the half-cell grid (a cell's centre or edge) can never have one centred on
it: the finding says so, and the drawing's door must move.

Reads a kit plan (game/kit/zones/<zone>.json shape) and the pieces' metadata, never pixels; it runs
in placement_audit.check_plan, so the editor's live overlay and Validate, `npm run check:kit` and
test_kit all read it.
"""
from __future__ import annotations

import math

CELL = 24
DENSITY = 3
TOL = 1.0          # texels: how far a path's centre may sit from a door's or a gate's
CORNER = 6         # texels: an end post this close inside a wall's corner stands at the corner
REACH = 8          # texels: and this far outside it, beside the wall
WALLS = ('house', 'forge', 'shelter', 'sty')
VEC = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}


def _f(check, msg, at):
    return {'check': check, 'message': msg, 'at': [round(at[0], 1), round(at[1], 1)] if at else None, 'severity': 'fault'}


def _at(pc, plan):
    at = pc.get('at')
    if not isinstance(at, (list, tuple)) or len(at) != 2:
        return None
    k = CELL if plan.get('coordinate_space', 'texels') == 'cells' else 1
    return float(at[0]) * k, float(at[1]) * k


def _runs(values):
    """Contiguous runs of integers as (first, last)."""
    out = []
    for v in sorted(set(values)):
        if out and v == out[-1][1] + 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return [tuple(r) for r in out]


def wall_box(pc, piece, plan):
    """A building's walls in texels (L, T, R, B) from its collision rect (world px), or None."""
    col = (piece.get('geometry') or {}).get('collision') or {}
    at = _at(pc, plan)
    if col.get('shape') != 'rect' or at is None:
        return None
    r = [v * DENSITY for v in col['rect']]
    return at[0] + r[0], at[1] + r[1], at[0] + r[0] + r[2], at[1] + r[1] + r[3]


def doors(plan, lib):
    """Every placed door: {'pc', 'x0', 'x1', 'centre', 'y', 'faces', 'swing'} in texels."""
    out = []
    for pc in plan.get('pieces', []):
        piece = lib.get(pc.get('piece')) or {}
        at = _at(pc, plan)
        for d in (piece.get('geometry') or {}).get('doors') or []:
            if at is None:
                continue
            x0, x1 = at[0] + d['x'][0], at[0] + d['x'][1]
            out.append({'pc': pc, 'x0': x0, 'x1': x1, 'centre': (x0 + x1) / 2.0, 'y': at[1], 'faces': d.get('faces', 's'),
                        'swing': max(CELL, d.get('swing', d['x'][1] - d['x'][0]))})
    return out


def on_half_grid(v):
    """Whether a coordinate lies within TOL of a cell's centre or edge (where a run of cells can centre)."""
    m = v % (CELL / 2)
    return min(m, CELL / 2 - m) <= TOL


def _route_cells(plan, mats):
    from scripts.art.kit import relations as RL
    ctx = RL._context(plan, mats)
    if ctx is None:
        return None
    grid = ctx[0]
    return {c for c, m in grid.items() if RL._matches_material('route', m, mats)}


def _boxes(pc, piece, plan):
    """What a piece occupies on the ground, as texel boxes (x0, y0, x1, y1)."""
    from scripts.art.kit import enclosures as EN
    at = _at(pc, plan)
    if at is None:
        return []
    b = (piece.get('placement') or {}).get('boundary')
    if b:
        out = []
        for a, e, _pc, _s in EN.segments({'pieces': [dict(pc, at=list(at))]}, {pc['piece']: piece}):
            out.append((min(a[0], e[0]) - 1.5, min(a[1], e[1]) - 1.5, max(a[0], e[0]) + 1.5, max(a[1], e[1]) + 1.5))
        return out
    col = (piece.get('geometry') or {}).get('collision') or {}
    if col.get('shape') == 'rect':
        r = [v * DENSITY for v in col['rect']]
        return [(at[0] + r[0], at[1] + r[1], at[0] + r[0] + r[2], at[1] + r[1] + r[3])]
    if col.get('shape') == 'circle' and col.get('radius'):
        rr = col['radius'] * DENSITY
        return [(at[0] - rr, at[1] - rr, at[0] + rr, at[1] + rr)]
    # no solid body: the ground it stands on, a hand's breadth about its foot
    return [(at[0] - 6, at[1] - 6, at[0] + 6, at[1])]


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _crossing(route, line, along_x, lo, hi):
    """The run (first, last) of cells along a boundary line where a path crosses it, for cells
    lo..hi along the line. along_x: an east-west line at y=line (rows above and below); else a
    north-south line at x=line (columns west and east; a line through a cell's middle has that
    cell under it, so the path must reach both cells beyond)."""
    k = int(round(line / CELL))
    centred = abs(line - k * CELL) > TOL       # the line runs through cells' middles
    if centred:
        k = int(math.floor(line / CELL))
        sides = (k - 1, k, k + 1)
    else:
        sides = (k - 1, k)

    def crosses(i):
        return all(((i, s) if along_x else (s, i)) in route for s in sides)
    hits = [i for i in range(lo, hi + 1) if crosses(i)]
    if not hits:
        return None
    a = b = hits[0]
    while crosses(a - 1):
        a -= 1
    while crosses(b + 1):
        b += 1
    return a, b


def check_plan(plan, lib=None, mats=None) -> list:
    from scripts.art.kit import enclosures as EN
    from scripts.art.kit import relations as RL
    lib = lib if lib is not None else RL.default_library()
    mats = mats if mats is not None else RL.default_materials()
    route = _route_cells(plan, mats)
    if route is None:
        return []
    out = []
    pieces = [pc for pc in plan.get('pieces', []) if pc.get('piece') in lib and _at(pc, plan) is not None]

    def name(pc):
        return str(pc.get('id', pc.get('piece')))

    # 1. a door's path: centred on the opening, straight out a cell
    for d in doors(plan, lib):
        if d['faces'] != 's':
            continue
        row = int(math.ceil(d['y'] / CELL - 1e-6))
        c_lo, c_hi = int(math.floor(d['x0'] / CELL)), int(math.floor((d['x1'] - 1e-6) / CELL))
        for a, b in _runs(c for c, r in route if r == row):
            if b < c_lo or a > c_hi:
                continue
            if (b - a + 1) * CELL > (d['x1'] - d['x0']) + 2 * CELL:
                continue                                    # the door opens onto a lane or a square
            centre = (a + b + 1) * CELL / 2.0
            grid = '' if on_half_grid(d['centre']) else (
                ' Its door is off the half-cell grid (%.1f texels from a cell\'s centre or edge), so no path of whole cells can be '
                'centred on it: the drawing\'s door must move.' % min(d['centre'] % 12, 12 - d['centre'] % 12))
            if abs(centre - d['centre']) > TOL:
                out.append(_f('rules.door_path', '%s: the path from its door is centred at x=%g, the door\'s opening at x=%g: a path '
                              'leaves a door centred on it (move it %+g texels).%s' % (name(d['pc']), centre, d['centre'], d['centre'] - centre, grid),
                              (d['centre'], d['y'])))
            elif not all((c, row + 1) in route for c in range(a, b + 1)):
                out.append(_f('rules.door_path', '%s: the path from its door bends before it is a cell out: run it straight out a '
                              'cell first' % name(d['pc']), (d['centre'], d['y'])))
    # 2. a door's threshold and swing stay clear
    for d in doors(plan, lib):
        if d['faces'] != 's':
            continue
        zone = (d['x0'], d['y'], d['x1'], d['y'] + d['swing'])
        for pc in pieces:
            if pc is d['pc']:
                continue
            piece = lib[pc['piece']]
            pl = piece.get('placement') or {}
            if pl.get('role') == 'stock' or (piece.get('geometry') or {}).get('z_sort') in ('ground', 'under'):
                continue
            if any(_overlap(zone, box) for box in _boxes(pc, piece, plan)):
                out.append(_f('rules.door_clear', '%s stands in the doorway of %s (its threshold and swing, x %g to %g, y %g to %g): keep '
                              'a door clear' % (name(pc), name(d['pc']), zone[0], zone[2], zone[1], zone[3]), _at(pc, plan)))
    # 3. gates and stiles centred on their paths; paths cross only there
    segs = EN.segments({'pieces': pieces}, lib)
    for pc in pieces:
        b = (lib[pc['piece']].get('placement') or {}).get('boundary')
        if not b or not (b.get('gate') or b.get('stile')):
            continue
        x, y = _at(pc, plan)
        along_x = set(b['joins']) == {'e', 'w'}
        half = b.get('span_cells', 1) * CELL / 2.0
        pos, line = (x, y) if along_x else (y, x)
        run = _crossing(route, line, along_x, int(math.floor((pos - half) / CELL)), int(math.floor((pos + half - 1e-6) / CELL)))
        if run is None:
            continue
        centre = (run[0] + run[1] + 1) * CELL / 2.0
        if abs(centre - pos) > TOL:
            kind = 'stile' if b.get('stile') else 'gate'
            out.append(_f('rules.gate_path', '%s: the %s is centred at %s=%g, the path through it at %s=%g: a %s stands centred on '
                          'its path (move it %+g texels)%s' % (name(pc), kind, 'x' if along_x else 'y', pos, 'x' if along_x else 'y', centre, kind,
                                                              centre - pos, '' if along_x or (run[1] - run[0]) % 2 else
                                                              '; a north-south run\'s cells centre on the row lines, so the path through it is an even number of cells wide'),
                          (x, y)))
    seen = set()
    for a, e, pc, s in segs:
        b = lib[pc['piece']]['placement']['boundary']
        if s == 'gate' or b.get('stile') or id(pc) in seen:
            continue
        if a[1] == e[1]:                                    # east-west arm on the line y
            col = int(math.floor((a[0] + e[0]) / 2.0 / CELL))
            hit = _crossing(route, a[1], True, col, col)
        else:
            row = int(math.floor((a[1] + e[1]) / 2.0 / CELL))
            hit = _crossing(route, a[0], False, row, row)
        if hit is not None:
            seen.add(id(pc))
            out.append(_f('rules.path_through_fence', '%s: a path runs through the fence here: a path crosses a boundary only at a '
                          'gate (or a stile on a footpath), centred on it' % name(pc), _at(pc, plan)))
    # 4. where a boundary meets a building
    buildings = []
    for pc in pieces:
        piece = lib[pc['piece']]
        if (piece.get('placement') or {}).get('role') in WALLS:
            box = wall_box(pc, piece, plan)
            if box:
                buildings.append((pc, box))
    for pc in pieces:
        piece = lib[pc['piece']]
        b = (piece.get('placement') or {}).get('boundary')
        if not b:
            continue
        x, y = _at(pc, plan)
        geo = piece.get('geometry') or {}
        rise = geo.get('height_px', (geo.get('foot') or [0, 0])[1])     # how high it stands above its foot
        if b.get('gate') or b.get('stile'):
            half = b.get('span_cells', 1) * CELL / 2.0
            xs = (x - half, x + half) if set(b['joins']) == {'e', 'w'} else (x, x)
        else:
            xs = [x] + [x + VEC[j][0] * CELL / 2.0 for j in b['joins']]
        xmin, xmax = min(xs), max(xs)
        end = len(b['joins']) == 1 and not b.get('gate')
        for h, (L, T, R, B) in buildings:
            if y >= B - 2 and y - rise < B and xmax > L + CORNER and xmin < R - CORNER and y < B + rise:
                out.append(_f('rules.fence_wall', '%s: drawn in front of the façade of %s (over its base, door or windows): a fence meets '
                              'a building at a front corner (x=%g or %g) or along its wall foot, its end post beside the wall'
                              % (name(pc), name(h), L, R), (x, y)))
            elif T + 2 < y < B - 2 and L + CORNER < x < R - CORNER:
                out.append(_f('rules.fence_wall', '%s: stands inside %s' % (name(pc), name(h)), (x, y)))
            elif end and L - CELL <= x <= R + CELL and T - CELL <= y <= B + 2 and y > T + 2:
                beside = (L - REACH <= x <= L + CORNER) or (R - CORNER <= x <= R + REACH)
                if not beside and not (L + CORNER < x < R - CORNER):
                    gap = min(abs(x - L), abs(x - R))
                    out.append(_f('rules.fence_wall', '%s: its end post stands %g texels off the wall of %s: a run ends against the wall, '
                                  'its post beside it (within %d texels of the corner)' % (name(pc), gap, name(h), REACH), (x, y)))
    return out
