"""Validate exported kit plans without renderer or scientific-Python dependencies.

The adapter preserves exact material cells as ``cell_regions`` in the painted
ground-rules model. It never invents a centreline or a river for a raster mask.
Authored paths/routes remain world-pixel polylines and keep their existing checks.
Piece/spawn coordinates are texels unless coordinate_space="cells"; door rects
are always cells. Full-library collision/deck metadata is world pixels, while
geometry.size_px is density-three art. Findings use world pixels for review.

    python3 -m scripts.review.kit_scene kitlab --check --json
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from collections import deque
from pathlib import Path

from scripts.art.kit import relations
from . import ground_rules

ROOT = Path(__file__).resolve().parents[2]
CELL = 8.0
DENSITY = 3.0
TEXEL_CELL = CELL * DENSITY
DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))
FLOW = {'^': (0, -1), '↑': (0, -1), '>': (1, 0), '→': (1, 0),
        'v': (0, 1), '↓': (0, 1), '<': (-1, 0), '←': (-1, 0),
        '↗': (1, -1), '↘': (1, 1), '↙': (-1, 1), '↖': (-1, -1)}


def _f(check, message, at=None, severity='fault'):
    return dict(check=check, message=message, at=list(at) if at is not None else None, severity=severity)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _xy(value):
    return isinstance(value, (list, tuple)) and len(value) == 2 and all(_number(v) for v in value)


def normalize(plan):
    """Deep-copy to texel positions; do not reinterpret explicit world-pixel paths."""
    if not isinstance(plan, dict):
        raise ValueError('a kit plan must be an object')
    out = copy.deepcopy(plan)
    space = plan.get('coordinate_space', 'texels')
    if space not in ('texels', 'cells'):
        raise ValueError('coordinate_space must be texels or cells')
    factor = TEXEL_CELL if space == 'cells' else 1.0
    for entry in out.get('pieces', []):
        if not isinstance(entry, dict) or not isinstance(entry.get('piece'), str) or ('id' in entry and not isinstance(entry['id'], str)) or not _xy(entry.get('at')):
            raise ValueError('every piece needs a finite [x,y] at position')
        entry['at'] = [v * factor for v in entry['at']]
    spawns = out.get('spawns', {})
    if not isinstance(spawns, dict) or any(not _xy(at) for at in spawns.values()):
        raise ValueError('spawns must map names to finite [x,y] positions')
    out['spawns'] = {key: [v * factor for v in at] for key, at in spawns.items()}
    for anchor in out.get('anchors', []):
        if not isinstance(anchor, dict) or not _xy(anchor.get('at')):
            raise ValueError('anchors need finite [x,y] positions')
        anchor['at'] = [v * factor for v in anchor['at']]
    for door in out.get('doors', []):
        rect = door.get('rect') if isinstance(door, dict) else None
        if not isinstance(rect, list) or len(rect) != 4 or not all(_number(v) for v in rect) or rect[2] <= 0 or rect[3] <= 0:
            raise ValueError('doors need finite positive cell rectangles')
    out['coordinate_space'] = 'texels'
    rows, legend = out.get('rows'), out.get('legend')
    if not isinstance(rows, list) or not rows or not all(isinstance(r, str) for r in rows) or not rows[0] or len({len(r) for r in rows}) != 1 or not isinstance(legend, dict):
        raise ValueError('rows must be a nonempty rectangular string grid with a legend')
    if any(not isinstance(key, str) or len(key) != 1 or not isinstance(value, str) for key, value in legend.items()):
        raise ValueError('legend must map single-character glyphs to material ids')
    for field in ('tiers', 'flow', 'variants'):
        values = out.get(field)
        if values is not None and (not isinstance(values, list) or len(values) != len(rows) or any(not isinstance(r, str) or len(r) != len(rows[0]) for r in values)):
            raise ValueError('%s must match rows dimensions' % field)
    if any(c not in '0123456789' for r in out.get('tiers', []) for c in r):
        raise ValueError('tiers must contain digits')
    if any(c not in FLOW and c not in '. ' for r in out.get('flow', []) for c in r):
        raise ValueError('flow must contain arrows, dots or spaces')
    return out


def _material(value):
    return value.get('terrain', value)


def _role(piece):
    return piece.get('placement', {}).get('role', piece.get('role', 'prop'))


def _approval(piece):
    value = piece.get('approval', 'candidate')
    return value.get('state', 'candidate') if isinstance(value, dict) else value


def _world_at(entry):
    return [v / DENSITY for v in entry['at']]


def _rect_cells(at, rect, width, height, share=0.0):
    """Cells with positive area in a world-pixel rect (optional legacy area share)."""
    x0, y0 = at[0] + rect[0], at[1] + rect[1]
    x1, y1 = x0 + rect[2], y0 + rect[3]
    if x1 <= x0 or y1 <= y0:
        return set()
    out = set()
    for y in range(max(0, math.floor(y0 / CELL)), min(height, math.ceil(y1 / CELL))):
        for x in range(max(0, math.floor(x0 / CELL)), min(width, math.ceil(x1 / CELL))):
            area = max(0.0, min(x1, (x + 1) * CELL) - max(x0, x * CELL)) * max(0.0, min(y1, (y + 1) * CELL) - max(y0, y * CELL))
            if area > 1e-9 and area + 1e-9 >= CELL * CELL * share:
                out.add((x, y))
    return out


def _geometry(entry, piece, width, height):
    at = _world_at(entry)
    geom = piece.get('geometry', {})
    game = piece.get('gameplay', {})
    blocks = game.get('blocks_move', piece.get('blocks_move', False))
    collision = geom.get('collision')
    occupied = set()
    if collision and collision.get('shape') == 'none':
        occupied = set()
    elif collision and collision.get('shape') == 'rect':
        occupied = _rect_cells(at, collision['rect'], width, height)
    elif collision and collision.get('shape') == 'circle':
        r = float(collision.get('radius', 0))
        for x, y in _rect_cells(at, [-r, -r, r * 2, r * 2], width, height):
            nx, ny = max(x * CELL, min(at[0], (x + 1) * CELL)), max(y * CELL, min(at[1], (y + 1) * CELL))
            if (nx - at[0]) ** 2 + (ny - at[1]) ** 2 < r * r:
                occupied.add((x, y))
    elif geom.get('footprint'):
        cx, cy = math.floor(at[0] / CELL), math.floor(at[1] / CELL)
        occupied = {(cx + int(dx), cy + int(dy)) for dx, dy in geom['footprint']}
    elif not collision or collision.get('shape') not in ('none',):
        occupied = {(math.floor(at[0] / CELL), math.floor((at[1] - 1e-7) / CELL))}
    deck = game.get('deck')
    return occupied if blocks else set(), _rect_cells(at, deck, width, height, 0.25) if deck else set()


def _solid_contains(entry, piece, point):
    if not piece.get('gameplay', {}).get('blocks_move', piece.get('blocks_move', False)):
        return False
    at, geom = _world_at(entry), piece.get('geometry', {})
    collision = geom.get('collision') or {}
    if collision.get('shape') == 'none':
        return False
    if collision.get('shape') == 'rect':
        x, y, w, h = collision['rect']
        return at[0] + x <= point[0] < at[0] + x + w and at[1] + y <= point[1] < at[1] + y + h
    if collision.get('shape') == 'circle':
        return (point[0] - at[0]) ** 2 + (point[1] - at[1]) ** 2 < collision.get('radius', 0) ** 2
    cell = math.floor(point[0] / CELL), math.floor(point[1] / CELL)
    return cell in relations._occupied(entry, piece, {'coordinate_space': 'texels'})


def _bodies(entry, piece, width, height):
    if not piece.get('gameplay', {}).get('blocks_move', piece.get('blocks_move', False)):
        return []
    at, collision = _world_at(entry), piece.get('geometry', {}).get('collision') or {}
    if collision.get('shape') == 'none':
        return []
    if collision.get('shape') == 'rect':
        x, y, w, h = collision['rect']
        return [('rect', at[0] + x, at[1] + y, at[0] + x + w, at[1] + y + h)]
    if collision.get('shape') == 'circle':
        return [('circle', *at, collision.get('radius', 0))]
    cells, _deck = _geometry(entry, piece, width, height)
    return [('rect', x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL) for x, y in cells]


def _bodies_overlap(a, b):
    for A in a:
        for B in b:
            if A[0] == B[0] == 'rect':
                if min(A[3], B[3]) - max(A[1], B[1]) > 1e-9 and min(A[4], B[4]) - max(A[2], B[2]) > 1e-9:
                    return True
            elif A[0] == B[0] == 'circle':
                if (A[1] - B[1]) ** 2 + (A[2] - B[2]) ** 2 < (A[3] + B[3]) ** 2:
                    return True
            else:
                rect, circle = (A, B) if A[0] == 'rect' else (B, A)
                x = max(rect[1], min(circle[1], rect[3]))
                y = max(rect[2], min(circle[2], rect[4]))
                if (x - circle[1]) ** 2 + (y - circle[2]) ** 2 < circle[3] ** 2:
                    return True
    return False


def _state(plan, library, materials):
    context = relations._context(plan, materials)
    grid, tiers, width, height = context
    raw = {(x, y): plan['legend'].get(c, '') for y, row in enumerate(plan['rows']) for x, c in enumerate(row)}
    route = {c for c, mid in grid.items() if _material(materials.get(mid, {})).get('route', False)}
    water = {c for c, mid in grid.items() if _material(materials.get(mid, {})).get('water') is not None or _material(materials.get(mid, {})).get('surface') == 'water'}
    raw_water = {c for c, mid in raw.items() if _material(materials.get(mid, {})).get('water') is not None or _material(materials.get(mid, {})).get('surface') == 'water'}
    occupied, decks = {}, set()
    for i, entry in enumerate(plan.get('pieces', [])):
        piece = library.get(entry.get('piece'), {})
        occupied[i], deck = _geometry(entry, piece, width, height)
        decks |= deck
    return dict(grid=grid, raw=raw, tiers=tiers, width=width, height=height, route=route,
                water=water, raw_water=raw_water, occupied=occupied, decks=decks)


def to_ground_plan(plan, library=None, materials=None):
    """Exact cell geometry plus world-pixel object geometry for shared ground rules."""
    plan = normalize(plan)
    library = relations.default_library() if library is None else library
    materials = relations.default_materials() if materials is None else materials
    state = _state(plan, library, materials)
    out = {key: copy.deepcopy(plan[key]) for key in ('paths', 'routes', 'water', 'places', 'buildings', 'stairs', 'rock', 'dressing', 'stages') if key in plan}
    out.update(screen={'w': state['width'] * CELL, 'h': state['height'] * CELL},
               cell_regions={'cell': CELL, 'route': [list(c) for c in sorted(state['route'])],
                             'water': [list(c) for c in sorted(state['water'] - state['decks'])]},
               stands={key: [v / DENSITY for v in at] for key, at in plan.get('spawns', {}).items()},
               doors=[dict(door, rect=[v * CELL for v in door['rect']]) for door in plan.get('doors', [])], objects=[])
    for i, entry in enumerate(plan.get('pieces', [])):
        piece = library.get(entry.get('piece'), {})
        role = _role(piece)
        if role == 'clutter':
            out.setdefault('dressing', {}).setdefault('ferns', []).append(_world_at(entry))
        cells = state['occupied'][i]
        if not cells:
            continue
        # Preserve the union as one exact cell box per occupied cell. No sprite
        # crown becomes solid; W5 handles seat-facing on its actual footprint.
        for x, y in sorted(cells):
            out['objects'].append([str(entry.get('id', entry.get('piece', i))), role,
                                   x * CELL, y * CELL, CELL, CELL])
    return out


def _components(cells):
    remaining = set(cells)
    while remaining:
        start = min(remaining)
        found, queue = {start}, deque([start])
        remaining.remove(start)
        while queue:
            x, y = queue.popleft()
            for dx, dy in DIRS:
                c = x + dx, y + dy
                if c in remaining:
                    remaining.remove(c)
                    found.add(c)
                    queue.append(c)
        yield found


def _extra_checks(plan, library, materials, state, guide):
    fs = []
    width, height = state['width'], state['height']
    grid, tiers, route, water = (state[k] for k in ('grid', 'tiers', 'route', 'water'))
    decks = state['decks']
    solid_bodies = []
    for i, entry in enumerate(plan.get('pieces', [])):
        piece = library.get(entry['piece'])
        if piece is None:
            continue
        at, name, role = _world_at(entry), str(entry.get('id', entry['piece'])), _role(piece)
        solid = state['occupied'][i]
        if role not in ('bridge', 'signpost') and solid & route:
            fs.append(_f('rules.route_clear', '%s: its solid footprint covers a route' % name, at))
        bodies = _bodies(entry, piece, width, height)
        for body in bodies:
            bounds = body[1:] if body[0] == 'rect' else (body[1] - body[3], body[2] - body[3], body[1] + body[3], body[2] + body[3])
            if bounds[0] < -1e-7 or bounds[1] < -1e-7 or bounds[2] > width * CELL + 1e-7 or bounds[3] > height * CELL + 1e-7:
                fs.append(_f('rules.bounds', '%s: solid geometry leaves the zone' % name, at))
                break
        for other_name, other_bodies in solid_bodies:
            if _bodies_overlap(bodies, other_bodies):
                fs.append(_f('rules.overlap', '%s and %s have overlapping solid geometry' % (name, other_name), at))
        solid_bodies.append((name, bodies))
        _solid, deck = _geometry(entry, piece, width, height)
        raw_deck = piece.get('gameplay', {}).get('deck')
        if raw_deck:
            x0, y0 = at[0] + raw_deck[0], at[1] + raw_deck[1]
            if x0 < -1e-7 or y0 < -1e-7 or x0 + raw_deck[2] > width * CELL + 1e-7 or y0 + raw_deck[3] > height * CELL + 1e-7:
                fs.append(_f('rules.stair' if role == 'stair' else 'rules.deck', '%s: walkable deck leaves the zone' % name, at))
        if deck:
            ys, xs = sorted({y for x, y in deck}), sorted({x for x, y in deck})
            if role == 'stair':
                head = [tiers.get((x, ys[0] - 1)) for x in xs]
                foot = [tiers.get((x, ys[-1] + 1)) for x in xs]
                faces = all(_material(materials.get(grid.get(c), {})).get('face') for c in deck)
                if not faces or None in head + foot or len(set(head)) != 1 or len(set(foot)) != 1 or head[0] <= foot[0]:
                    fs.append(_f('rules.stair', '%s: flight, upper rim and lower landing do not agree' % name, at))
            else:
                ends = ({(x, ys[0]) for x in xs}, {(x, ys[-1]) for x in xs}) if len(ys) >= len(xs) else ({(xs[0], y) for y in ys}, {(xs[-1], y) for y in ys})
                if not deck & water or any(end & water for end in ends):
                    fs.append(_f('rules.deck', '%s: deck does not span water between dry landings' % name, at))
        elif role == 'stair':
            fs.append(_f('rules.stair', '%s: stair has no walkable flight' % name, at))
        if role == 'clutter' and relations._occupied(entry, piece, plan) & (route | water):
            fs.append(_f('rules.clutter', '%s: clutter stands on a route or in water' % name, at))
        if role in ('fire', 'campfire') or piece.get('gameplay', {}).get('hazard') == 'fire':
            own = relations._occupied(entry, piece, plan)
            hearths = set()
            for j, other in enumerate(plan.get('pieces', [])):
                op = library.get(other.get('piece'), {})
                if i != j and _role(op) == 'hearth':
                    hearths |= relations._occupied(other, op, plan)
            for anchor in plan.get('anchors', []):
                if anchor.get('kind') == 'hearth':
                    hearths.add((math.floor(anchor['at'][0] / TEXEL_CELL), math.floor((anchor['at'][1] - 1e-7) / TEXEL_CELL)))
            if not own or not own <= hearths:
                fs.append(_f('rules.fire_hearth', '%s: fire must stand on a hearth' % name, at))
        debris = role in ('debris', 'storm_debris', 'puddle') or any(k in entry['piece'].lower() for k in ('debris', 'rubble', 'puddle'))
        if debris and plan.get('stages'):
            stage = entry.get('stage')
            allowed = piece.get('placement', {}).get('stages') or []
            condition = entry.get('if', entry.get('condition', entry.get('cond')))
            broken_only = stage == 'broken' or (stage is None and (set(allowed) == {'broken'} or isinstance(condition, dict) and condition.get('stage') == 'broken'))
            if not broken_only:
                fs.append(_f('rules.stage_debris', '%s: storm debris needs the broken stage' % name, at))
        geometry, audit = piece.get('geometry', {}), piece.get('audit', {})
        size, cells = geometry.get('size_px'), geometry.get('size_cells')
        category = audit.get('size_class')
        if _xy(size) and _xy(cells) and any(abs(size[k] / TEXEL_CELL - cells[k]) > 0.500001 for k in (0, 1)):
            fs.append(_f('rules.scale', '%s: size_cells disagrees with art size on the cell grid' % name, at,
                         'fault' if category else 'advice'))
        if not category:
            fs.append(_f('rules.scale', '%s: size class is unclassified; art scale is not audited' % name, at, 'advice'))
        elif category not in guide.get('kinds', {}):
            fs.append(_f('rules.scale', '%s: unknown size-guide class %s' % (name, category), at))
        elif not _xy(size) or any(v <= 0 for v in size):
            fs.append(_f('rules.scale', '%s: declared size class needs finite positive art dimensions' % name, at))
        else:
            bounds, tolerance = guide['kinds'][category], guide.get('tolerance', 2)
            if any(axis in bounds and not bounds[axis][0] - tolerance <= size[k] / DENSITY <= bounds[axis][1] + tolerance for k, axis in enumerate(('w', 'h'))):
                fs.append(_f('rules.scale', '%s: art size is outside its size-guide class' % name, at))
    for x, y in sorted(route):
        if any((x + dx, y + dy) in water - decks for dx, dy in DIRS):
            fs.append(_f('rules.route_water', 'route meets water without a deck', [(x + .5) * CELL, (y + .5) * CELL]))
        if any((x + dx, y + dy) in grid and tiers[x, y] != tiers[x + dx, y + dy] and ((x + dx, y + dy) in route or _material(materials.get(grid[x + dx, y + dy], {})).get('face')) and (x, y) not in decks and (x + dx, y + dy) not in decks for dx, dy in DIRS):
            fs.append(_f('rules.tier_route', 'route changes tier without a stair', [(x + .5) * CELL, (y + .5) * CELL]))
    falls = set()
    for entry in plan.get('pieces', []):
        piece = library.get(entry['piece'], {})
        if _role(piece) != 'waterfall':
            continue
        cells = relations._occupied(entry, piece, plan)
        falls |= cells
        top = min((y for x, y in cells), default=0)
        if not cells or any(not _material(materials.get(grid.get(c), {})).get('face') for c in cells) or any((x, top - 1) not in water for x, y in cells):
            fs.append(_f('rules.water_fall', '%s: fall must cover the face below its feeding channel' % entry.get('id', entry['piece']), _world_at(entry)))
    for x, y in sorted(water):
        below = x, y + 1
        if _material(materials.get(grid.get(below), {})).get('face') and below not in falls:
            fs.append(_f('rules.water_fall', 'water crosses a rim without a fall piece', [(x + .5) * CELL, (y + .5) * CELL]))
    for body in _components(water):
        edge = any(x in (0, width - 1) or y in (0, height - 1) for x, y in body)
        pool = any({(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)} <= body for x, y in body)
        if not edge and not pool:
            c = min(body)
            fs.append(_f('rules.water_end', 'channel reaches neither the zone edge nor a pool', [c[0] * CELL, c[1] * CELL]))
    for y, row in enumerate(plan.get('flow', [])):
        for x, glyph in enumerate(row):
            if glyph not in FLOW:
                continue
            at = [(x + .5) * CELL, (y + .5) * CELL]
            if (x, y) not in state['raw_water']:
                fs.append(_f('rules.water_flow', 'flow arrow is not on water', at))
                continue
            dx, dy = FLOW[glyph]
            target = x + dx, y + dy
            if target in tiers and tiers[target] > tiers[x, y]:
                fs.append(_f('rules.water_uphill', 'water flows to a higher tier', at))
            if target in tiers and target not in state['raw_water'] and target not in falls:
                fs.append(_f('rules.water_flow', 'water flow ends on dry ground', at))
    blocked = {c for c, mid in grid.items() if not mid or not _material(materials.get(mid, {})).get('walkable', True)} - decks
    for name, at in plan.get('spawns', {}).items():
        cell = math.floor(at[0] / TEXEL_CELL), math.floor(at[1] / TEXEL_CELL)
        point = [v / DENSITY for v in at]
        if cell not in grid or cell in blocked or any(_solid_contains(e, library.get(e['piece'], {}), point) for e in plan.get('pieces', [])):
            fs.append(_f('rules.walk', "spawn '%s' is outside open ground" % name, [v / DENSITY for v in at]))
    for door in plan.get('doors', []):
        x, y, w, h = door['rect']
        points = [(px, py) for py in range(math.floor(y * CELL) + 2, math.ceil((y + h) * CELL), 4)
                  for px in range(math.floor(x * CELL) + 2, math.ceil((x + w) * CELL), 4)]
        open_points = [p for p in points if (math.floor(p[0] / CELL), math.floor(p[1] / CELL)) in grid
                       and (math.floor(p[0] / CELL), math.floor(p[1] / CELL)) not in blocked
                       and not any(_solid_contains(e, library.get(e['piece'], {}), p) for e in plan.get('pieces', []))]
        if not open_points:
            fs.append(_f('rules.walk', "door '%s' has no open cell" % door.get('id', '?'), [(x + w / 2) * CELL, (y + h / 2) * CELL]))
    return fs


def check_zone(plan, library=None, materials=None, size_guide=None):
    """All placement, cell-native and shared physical checks, with stable findings."""
    try:
        plan = normalize(plan)
        library = relations.default_library() if library is None else library
        materials = relations.default_materials() if materials is None else materials
        if size_guide is None:
            with (ROOT / 'scripts/art/size_guide.json').open() as stream:
                size_guide = json.load(stream)
        findings = []
        for mid in sorted(set(plan['legend'].values())):
            if mid not in materials:
                findings.append(_f('rules.unknown_piece', "material '%s' is not in the kit" % mid))
        for entry in plan.get('pieces', []):
            if entry.get('piece') not in library:
                findings.append(_f('rules.unknown_piece', "piece '%s' is not in the library" % entry.get('piece'), _world_at(entry)))
        if findings:
            return findings
        used_materials = {plan['legend'].get(c) for row in plan['rows'] for c in row}
        if None in used_materials:
            return [_f('rules.unknown_piece', 'row contains a glyph missing from its legend')]
        gate_severity = 'fault' if plan.get('ship') else 'advice'
        for mid in sorted(used_materials):
            state = _approval(materials[mid])
            if state != 'approved':
                severity = gate_severity if state in ('candidate', 'gated') else 'fault'
                findings.append(_f('rules.unapproved', "material '%s' is %s" % (mid, state), severity=severity))
        for entry in plan.get('pieces', []):
            state = _approval(library[entry['piece']])
            if state != 'approved':
                severity = gate_severity if state in ('candidate', 'gated') else 'fault'
                findings.append(_f('rules.unapproved', "%s: piece is %s" % (entry.get('id', entry['piece']), state), _world_at(entry), severity))
        for finding in relations.check_zone(plan, library, materials):
            finding = dict(finding, at=[v / DENSITY for v in finding['at']] if finding.get('at') is not None else None,
                           severity='advice' if plan.get('lab') and finding['check'] == 'rules.off_grid' else 'fault')
            findings.append(finding)
        state = _state(plan, library, materials)
        findings += _extra_checks(plan, library, materials, state, size_guide)
        findings += [dict(f, severity='fault') for f in ground_rules.check_plan(to_ground_plan(plan, library, materials))]
        # Native footprint checks and shared ground checks may identify the same
        # rule at the same place. Keep the first precise finding only.
        seen, result = set(), []
        for finding in findings:
            key = finding['check'], tuple(finding.get('at') or []), finding['severity'], '' if finding['check'] == 'rules.route_clear' else finding['message']
            if key not in seen:
                seen.add(key)
                result.append(finding)
        return result
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError) as exc:
        return [_f('rules.plan', 'invalid kit plan: %s' % exc)]


def load_plan(target):
    path = Path(target)
    if not path.is_file():
        path = ROOT / 'game/kit/zones' / (str(target) if str(target).endswith('.json') else str(target) + '.json')
    with path.open() as stream:
        return json.load(stream)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('targets', nargs='*')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    reports = []
    for target in args.targets or [p.stem for p in sorted((ROOT / 'game/kit/zones').glob('*.json'))]:
        try:
            plan = load_plan(target)
            findings = check_zone(plan)
            zone = plan.get('zone', str(target)) if isinstance(plan, dict) else str(target)
        except (OSError, ValueError) as exc:
            zone, findings = str(target), [_f('rules.plan', 'cannot read kit plan: %s' % exc)]
        reports.append(dict(zone=zone, findings=findings))
    if args.json:
        print(json.dumps(reports[0] if len(reports) == 1 else {'zones': reports}, sort_keys=True))
    else:
        for report in reports:
            faults = sum(f['severity'] == 'fault' for f in report['findings'])
            print('[kit scene] %s: %d faults' % (report['zone'], faults))
            for f in report['findings']:
                print('  %s %s: %s' % (f['severity'], f['check'], f['message']))
    return 1 if args.check and any(f['severity'] == 'fault' for r in reports for f in r['findings']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
