"""Cell-native placement predicates, mirrored by game/world/terrain/relations.gd.

The shared cases are engineering fixtures, pending Claude's authored design cases.
Positions default to texels (24 per cell); coordinate_space="cells" is explicit.
Feet on a horizontal cell line belong to the cell immediately above it. Geometry
footprints are authored offsets from floor(anchor); absent footprints use that
single foot cell, never a guessed sprite-sized box. Logical facing does not rotate
geometry: current KitPiece rendering does not rotate it either.

Negative relations (not_on/not_near/not_overlap) are prohibitions in either list.
This preserves existing rocks' forbids:not_overlap intent instead of accidentally
allowing overlap through double negation. This interpretation requires design review.
Unknown relations or targets always fail, including in negative constraints.
Approval gates are deliberately separate from these placement predicates.
"Under" a terrain material/surface means below its north rim: the entire north
boundary of the footprint must meet that terrain. "Under" a piece/role instead
tests its authored overhang. This follows the live waterfall placement metadata;
it does not replace the validator's tier, face and water-supply physics checks.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CELL = 24.0
EPS = 1e-7
RELATIONS = {'adjacent', 'within', 'on', 'facing', 'near', 'under', 'at_edge',
             'at_corner', 'on_anchor', 'not_on', 'not_near', 'not_overlap'}
NEGATIVE = {'not_on', 'not_near', 'not_overlap'}
VOCABULARY = {'route', 'route_edge', 'water', 'face', 'tier_edge', 'zone_edge'}
DIRECTIONS = {'s': (0, 1), 'n': (0, -1), 'e': (1, 0), 'w': (-1, 0)}


def default_library():
    out = {}
    for path in sorted((ROOT / 'game/kit/pieces').rglob('*.json')):
        with path.open() as stream:
            piece = json.load(stream)
        if isinstance(piece, dict) and isinstance(piece.get('id'), str):
            out[piece['id']] = piece
    return out


def default_materials():
    with (ROOT / 'game/kit/terrain/manifest.json').open() as stream:
        return {m['id']: m for m in json.load(stream)['materials']}


def _material(value):
    return value.get('terrain', value)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _position(entry, plan):
    at = entry.get('at')
    if not isinstance(at, (list, tuple)) or len(at) != 2 or not all(_number(v) for v in at):
        return None
    scale = 1.0 if plan.get('coordinate_space', 'texels') == 'cells' else CELL
    return at[0] / scale, at[1] / scale


def _foot(position):
    return math.floor(position[0]), math.floor(position[1] - EPS)


def _occupied(entry, piece, plan, overhang=False):
    position = _position(entry, plan)
    if position is None:
        return set()
    geometry = piece.get('geometry') or {}
    offsets = geometry.get('overhang' if overhang else 'footprint')
    if not offsets and overhang:
        offsets = geometry.get('footprint')
    if not offsets:
        return {_foot(position)}
    origin = math.floor(position[0]), math.floor(position[1])
    return {(origin[0] + int(c[0]), origin[1] + int(c[1])) for c in offsets}


def _context(plan, materials):
    rows = plan.get('rows')
    legend = plan.get('legend')
    if not isinstance(rows, list) or not rows or not all(isinstance(r, str) for r in rows):
        return None
    width = len(rows[0])
    if (width == 0 or any(len(r) != width for r in rows) or not isinstance(legend, dict)
            or any(not isinstance(k, str) or len(k) != 1 or not isinstance(v, str) for k, v in legend.items())
            or any(c not in legend and c != ' ' for row in rows for c in row)):
        return None
    tier_rows = plan.get('tiers', ['0' * width] * len(rows))
    if (not isinstance(tier_rows, list) or len(tier_rows) != len(rows)
            or any(not isinstance(r, str) or len(r) != width or any(c not in '0123456789' for c in r)
                   for r in tier_rows)):
        return None
    anchors = plan.get('anchors', [])
    if not isinstance(anchors, list) or any(not isinstance(a, dict) or _position(a, plan) is None
            or any(k in a and not isinstance(a[k], str) for k in ('id', 'kind')) for a in anchors):
        return None
    grid = {(x, y): legend.get(c, '') for y, row in enumerate(rows) for x, c in enumerate(row)}
    tiers = {(x, y): int(c) for y, row in enumerate(tier_rows) for x, c in enumerate(row)}
    faces = [(key, _material(m)['face']) for key, m in materials.items() if _material(m).get('face')]
    if faces:
        face_id, spec = sorted(faces)[0]
        height = int(spec.get('height_cells', 2))
        for y in range(len(rows) - 1):
            for x in range(width):
                delta = tiers[x, y] - tiers[x, y + 1]
                for step in range(1, max(0, height * delta) + 1):
                    if y + step < len(rows) and tiers[x, y + step] < tiers[x, y]:
                        grid[x, y + step] = face_id
    return grid, tiers, width, len(rows)


def _known(what, library, materials, plan):
    prefix, sep, name = what.partition(':')
    if not sep:
        name = what
        prefix = ''
    anchors = plan.get('anchors', [])
    roles = {p.get('placement', {}).get('role') for p in library.values()}
    surfaces = {_material(m).get('surface') for m in materials.values()}
    anchor_names = {name for a in anchors if isinstance(a, dict) for name in (a.get('kind'), a.get('id')) if name is not None}
    if prefix == 'piece':
        return name in library
    if prefix == 'role':
        return name in roles
    if prefix == 'material':
        return name in materials
    if prefix == 'surface':
        return name in surfaces
    if prefix == 'anchor':
        return name in anchor_names
    if prefix:
        return False
    return name in VOCABULARY or name in library or name in roles or name in materials or name in surfaces or name in anchor_names


def _matches_material(what, mid, materials):
    material = _material(materials.get(mid, {}))
    if what.startswith('material:'):
        return mid == what[9:]
    if what.startswith('surface:'):
        return material.get('surface') == what[8:]
    if ':' in what:
        return False
    if what == 'route':
        return bool(material.get('route'))
    if what == 'water':
        return material.get('water') is not None or material.get('surface') == 'water'
    if what == 'face':
        return bool(material.get('face'))
    return mid == what or material.get('surface') == what


def _known_ground(what, materials):
    if not isinstance(what, str):
        return False
    if what in ('route', 'water', 'face'):
        return True
    if what.startswith('material:'):
        return what[9:] in materials
    if what.startswith('surface:'):
        return any(_material(m).get('surface') == what[8:] for m in materials.values())
    return ':' not in what and (what in materials or any(_material(m).get('surface') == what for m in materials.values()))


def _matches_piece(what, piece_id, piece):
    role = piece.get('placement', {}).get('role')
    if what.startswith('piece:'):
        return piece_id == what[6:]
    if what.startswith('role:'):
        return role == what[5:]
    return ':' not in what and (piece_id == what or role == what)


def _targets(what, plan, library, materials, context, index, under=False):
    grid, tiers, width, height = context
    if what == 'route_edge':
        route = {c for c, mid in grid.items() if _matches_material('route', mid, materials)}
        cells = {c for c in route if any((c[0] + dx, c[1] + dy) not in route for dx, dy in DIRECTIONS.values())}
    elif what == 'tier_edge':
        cells = {c for c, tier in tiers.items() if any(tiers.get((c[0] + dx, c[1] + dy), tier) != tier for dx, dy in DIRECTIONS.values())}
    elif what == 'zone_edge':
        cells = {c for c in grid if c[0] in (0, width - 1) or c[1] in (0, height - 1)}
    else:
        cells = {c for c, mid in grid.items() if _matches_material(what, mid, materials)}
    if under and _known_ground(what, materials):
        return cells
    for other_index, entry in enumerate(plan.get('pieces', [])):
        if other_index == index or not isinstance(entry, dict):
            continue
        if not isinstance(entry.get('piece'), str):
            continue
        piece = library.get(entry.get('piece'), {})
        if _matches_piece(what, entry.get('piece'), piece):
            cells |= _occupied(entry, piece, plan, overhang=under)
    for anchor in plan.get('anchors', []):
        if not isinstance(anchor, dict):
            continue
        name = what[7:] if what.startswith('anchor:') else what
        if name in (anchor.get('kind'), anchor.get('id')):
            p = _position(anchor, plan)
            if p is not None:
                cells.add(_foot(p))
    return cells


def _distance(a, b):
    return min((max(abs(x - X), abs(y - Y)) for x, y in a for X, Y in b), default=math.inf)


def _in_front(position, targets, facing):
    dx, dy = DIRECTIONS.get(facing, (0, 0))
    for x, y in targets:
        rx, ry = x + 0.5 - position[0], y + 0.5 - position[1]
        dot, cross = rx * dx + ry * dy, rx * dy - ry * dx
        if dot > EPS and abs(cross) <= dot + EPS:
            return True
    return False


def _predicate(relation, entry, occupied, targets, plan, terrain_under=False):
    rel = relation['rel']
    if rel == 'facing' or relation.get('facing', False):
        targets = {c for c in targets if _in_front(_position(entry, plan), {c}, str(entry.get('facing', 's')).lower())}
    distance = _distance(occupied, targets)
    radius = float(relation.get('cells', 1))
    if rel == 'under' and terrain_under:
        top = min((y for _x, y in occupied), default=0) - 1
        north = {(x, top) for x, _y in occupied}
        result = bool(north) and north <= targets
    elif rel in ('on', 'under', 'on_anchor'):
        result = bool(occupied & targets)
    elif rel in ('not_on', 'not_overlap'):
        result = not bool(occupied & targets)
    elif rel in ('within', 'near'):
        result = distance <= radius + EPS
    elif rel == 'not_near':
        result = distance > radius + EPS
    elif rel == 'adjacent':
        result = EPS < distance <= radius + EPS
    elif rel in ('at_edge', 'at_corner'):
        directions = set()
        for x, y in occupied:
            for dx, dy in DIRECTIONS.values():
                for step in range(1, math.floor(radius + EPS) + 1):
                    if (x + dx * step, y + dy * step) in targets:
                        directions.add((dx, dy))
        result = not bool(occupied & targets) and bool(directions)
        if rel == 'at_corner':
            result = result and any(a[0] * b[0] + a[1] * b[1] == 0 for a in directions for b in directions)
    elif rel == 'facing':
        result = bool(targets) and (distance <= radius + EPS if 'cells' in relation else True)
    else:
        return False
    return result


def _finding(check, message, at):
    return {'check': check, 'message': message, 'at': copy.deepcopy(at)}


def check_zone(plan, library=None, materials=None):
    """Validate all instances. Empty injected registries stay empty; inputs are not mutated."""
    library = default_library() if library is None else library
    materials = default_materials() if materials is None else materials
    if not isinstance(plan, dict):
        return [_finding('rules.plan', 'zone: invalid plan', [])]
    if plan.get('coordinate_space', 'texels') not in ('texels', 'cells'):
        return [_finding('rules.plan', 'zone: unknown coordinate space', [])]
    context = _context(plan, materials)
    if context is None or not isinstance(plan.get('pieces', []), list):
        return [_finding('rules.plan', 'zone: invalid cells or tiers', [])]
    grid, tiers, width, height = context
    unknown = sorted({mid for mid in grid.values() if mid and mid not in materials})
    if unknown:
        return [_finding('rules.unknown_piece', mid + ': material is not in the library', []) for mid in unknown]
    out = []
    entries = plan.get('pieces', [])
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            out.append(_finding('rules.plan', 'zone: invalid piece instance', []))
            continue
        pid = entry.get('piece')
        at = entry.get('at', [])
        if not isinstance(pid, str) or ('id' in entry and not isinstance(entry['id'], str)):
            out.append(_finding('rules.plan', 'zone: invalid piece id', at))
            continue
        eid = str(entry.get('id', pid))
        piece = library.get(pid)
        if piece is None:
            out.append(_finding('rules.unknown_piece', eid + ': piece is not in the library', at))
            continue
        position = _position(entry, plan)
        if position is None:
            out.append(_finding('rules.position', eid + ': invalid foot position', at))
            continue
        occupied = _occupied(entry, piece, plan)
        placement = piece.get('placement') or {}
        if any(x < 0 or y < 0 or x >= width or y >= height for x, y in occupied):
            out.append(_finding('rules.bounds', eid + ': footprint is outside the zone', at))
        snap = placement.get('snap', 'free')
        step = (0.5, 1.0) if snap == 'cell' else (0.5, 0.5)
        if snap not in ('cell', 'half', 'free') or (snap != 'free' and any(abs(v / s - round(v / s)) > EPS for v, s in zip(position, step))):
            out.append(_finding('rules.off_grid', eid + ': foot is off the soft grid', at))
        facing = str(entry.get('facing', 's')).lower()
        orientations = placement.get('orientations', [])
        if facing not in DIRECTIONS or (orientations and 'any' not in orientations and facing not in orientations):
            out.append(_finding('rules.orientation', eid + ': orientation is not allowed', at))
        stage = entry.get('stage', plan.get('stage', ''))
        if placement.get('stages') and stage not in placement['stages']:
            out.append(_finding('rules.stage', eid + ': stage is not allowed', at))
        here = {grid.get(c, '') for c in occupied}
        allowed = placement.get('ground', {}).get('allow', [])
        denied = placement.get('ground', {}).get('deny', [])
        unknown_ground = list(dict.fromkeys(t for t in allowed + denied if not _known_ground(t, materials)))
        for target in unknown_ground:
            out.append(_finding('rules.ground', eid + ': unknown ground target ' + str(target), at))
        if not unknown_ground and allowed and any(not any(_matches_material(t, mid, materials) for t in allowed) for mid in here):
            out.append(_finding('rules.ground', eid + ': ground is not allowed', at))
        if not unknown_ground and denied and any(any(_matches_material(t, mid, materials) for t in denied) for mid in here):
            out.append(_finding('rules.ground', eid + ': ground is denied', at))
        if placement.get('tiers') and any(tiers.get(c, -1) not in placement['tiers'] for c in occupied):
            out.append(_finding('rules.tiers', eid + ': tier is not allowed', at))
        for field in ('requires', 'forbids'):
            for relation in placement.get(field, []):
                rel, what = relation.get('rel', ''), relation.get('what', '')
                if (rel not in RELATIONS or not isinstance(what, str) or not _known(what, library, materials, plan)
                        or not _number(relation.get('cells', 1)) or relation.get('cells', 1) < 0):
                    out.append(_finding('rules.relation', f'{eid}: unknown relation or target {rel} {what}', at))
                    continue
                targets = _targets(what, plan, library, materials, context, index, under=rel == 'under')
                verdict = _predicate(relation, entry, occupied, targets, plan, terrain_under=rel == 'under' and _known_ground(what, materials))
                violation = not verdict if field == 'requires' or rel in NEGATIVE else verdict
                if violation:
                    check = 'rules.seating' if placement.get('role') == 'seat' and what in ('route', 'route_edge') else 'rules.' + field
                    verb = 'violates' if field == 'forbids' and rel in NEGATIVE else field
                    message = f'{eid}: {verb} {rel} {what}'
                    if relation.get('note'):
                        message += ': ' + relation['note']
                    out.append(_finding(check, message, at))
        clearance = placement.get('clearance', 0)
        if _number(clearance) and clearance > 0:
            for other_index, other in enumerate(entries):
                if other_index == index or not isinstance(other, dict):
                    continue
                other_piece = library.get(other.get('piece')) if isinstance(other.get('piece'), str) else None
                if other_piece is not None and _distance(occupied, _occupied(other, other_piece, plan)) <= clearance + EPS:
                    other_id = str(other.get('id', other.get('piece')))
                    out.append(_finding('rules.clearance', eid + ': clearance overlaps ' + other_id, at))
    for pid in sorted(library):
        limits = library[pid].get('placement', {}).get('per_zone', {})
        count = sum(isinstance(e, dict) and e.get('piece') == pid for e in entries)
        if 'min' in limits and count < limits['min']:
            out.append(_finding('rules.count', pid + ': fewer than per-zone minimum', []))
        if 'max' in limits and count > limits['max']:
            out.append(_finding('rules.count', pid + ': exceeds per-zone maximum', []))
    return out


def check_placement(plan, candidate, library=None, materials=None):
    """Preview a candidate without blocking incremental work on unrelated zone faults.

    Candidate-local failures and new effects on other pieces still refuse placement.
    Zone minima belong to Validate Zone, never to incremental construction.
    """
    previous = check_zone(plan, library, materials)
    trial = copy.deepcopy(plan)
    entries = trial.setdefault('pieces', [])
    if 'id' in candidate:
        entries[:] = [entry for entry in entries if not isinstance(entry, dict) or entry.get('id') != candidate['id']]
    entries.append(copy.deepcopy(candidate))
    after = check_zone(trial, library, materials)
    eid = str(candidate.get('id', candidate.get('piece')))
    pid = candidate.get('piece')
    old_count = sum(isinstance(entry, dict) and entry.get('piece') == pid for entry in plan.get('pieces', []))
    new_count = sum(isinstance(entry, dict) and entry.get('piece') == pid for entry in entries)
    out = []
    for finding in after:
        if finding['check'] == 'rules.count' and finding['message'].endswith(': fewer than per-zone minimum'):
            continue
        local = finding['message'].startswith(eid + ': ') and finding['at'] == candidate.get('at', [])
        structural = finding['check'] == 'rules.plan' or (finding['check'] == 'rules.unknown_piece' and not finding['at'])
        increases_max = finding['check'] == 'rules.count' and finding['message'] == str(pid) + ': exceeds per-zone maximum' and new_count > old_count
        if local or structural or increases_max or finding not in previous:
            out.append(finding)
    return out


evaluate = check_placement
