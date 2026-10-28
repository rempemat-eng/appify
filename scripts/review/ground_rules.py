"""The ground rules: the game's physical world model as checks (docs/vision/ground-rules.md).

Matt, 27 Oct 13:26: "really double down on the physics and establish correct ground rules for the
game (it will make placing stuff much easier later)". A zone is built in layers, each obeying the
ones before: terrain heights, water, ground materials, routes, structures, props by role, clutter.
These checks read a zone's plan (world px) and say where it breaks a rule:

    rules.water_source      every stream starts at a source (the zone's edge, a spring, a pool)
    rules.water_end         every channel ends in a pool, a lake, a fall or the zone's edge
    rules.water_fall        a fall's lip is flush with the rock's top, centred on the channel
                            that feeds it, as wide as that channel, and lands in a pool
    rules.ground_water      no route or worn ground under water except on a bridge's span
    rules.route_grid        route points on cells, runs along x or y, turns only as rounded
                            bends (radius 0.4 to 12 cells), turns at least two cells apart
    rules.route_ends        each route end meets a destination: a zone edge, a stand, a bridge,
                            a door, a place, or another route
    rules.route_clear       nothing stands on a route (only bridges and signposts by design)
    rules.seating           a bench stands beside a route (its edge within 2 cells), not on it,
                            facing it (the route in front of the bench's face)
    rules.rock_overlap      rocks rest on the ground side by side; two never overlap unless the
                            plan marks them stacked
    rules.clutter           clutter (ferns, flowers, leaves) never on a route's centre or water
    rules.stage_debris      storm debris and puddles only in the broken stage (a stage condition)

Existing checks enforce the rest: logic.tiers (one height per tier, faces and stairs agree),
roads_clear in check:kit (no road under a building), logic.composition (structures with props),
the crowns gate (trees' crowns not cut), grid_snap (feet and footprints on cells).

    python3 -m scripts.review.ground_rules            report every plan
    python3 -m scripts.review.ground_rules --check    exit 1 if a plan that declares
                                                      "ground_rules": true breaks one
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CELL = 8.0
SEATS = ('bench', 'forest_bench')
ON_ROUTE_OK = ('signpost', 'bridge')
ROCKY = ('boulder', 'rock', 'slab')


def _f(name, msg, at=None):
    return dict(check=name, message=msg, at=at)


# ------------------------------------------------------------------------------------------------
# geometry
# ------------------------------------------------------------------------------------------------
def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _line_dist(p, pts):
    return min(_seg_dist(p, a, b) for a, b in zip(pts, pts[1:]))


def _in_rects(p, rects, pad=0.0):
    return any(x - pad <= p[0] < x + w + pad and y - pad <= p[1] < y + h + pad for x, y, w, h in rects)


def _routes(plan):
    """(id, points, half width, spur) of every route: a scene's paths or a village's routes."""
    out = []
    for k, r in enumerate(plan.get('paths', [])):
        out.append((r.get('id', f'path-{k + 1}'), r['points'], float(r.get('radius', 8)), r.get('bend'), r.get('spur', False)))
    for r in plan.get('routes', []):
        out.append((r['id'], r['points'], float(r.get('width', 24)) / 2.0 - 4.0, r.get('bend'), r.get('kind') == 'spur'))
    return out


def _water(plan):
    """The water as rects (world px) and channels (polylines with half widths)."""
    w = plan.get('water', {})
    sw = w.get('soft')
    rects, chans = [], []
    if not sw:
        return rects, chans, w
    r = sw['river']
    hw = r['cells'] * CELL / 2.0
    chans.append(('river', r['points'], hw))
    rects += sw.get('pool', [])
    rects += r.get('add', [])
    rl = sw.get('rill')
    if rl:
        n = rl.get('cells_plan') or rl.get('cells', 1)
        chans.append(('rill', rl['points'], n * CELL / 2.0))
    return rects, chans, w


def _on_water(p, plan, pad=0.0):
    rects, chans, _ = _water(plan)
    if _in_rects(p, rects, pad):
        return True
    return any(_line_dist(p, pts) <= hw + pad for _n, pts, hw in chans)


def _places(plan):
    p = plan.get('places', {})
    return p if isinstance(p, dict) else {}


def _bridge_span(plan):
    b = _places(plan).get('bridge')
    if not b:
        return None
    return (b['x0'], b['x0'] + b['w'], b.get('y0', -1e9) - 8, b.get('y1', 1e9) + 8)


def _size(plan):
    if 'screen' in plan:
        return plan['screen']['w'], plan['screen']['h']
    return plan['box'][2], plan['box'][3]


def _objects(plan):
    for o in plan.get('objects', []):
        if isinstance(o, list):
            oid, kind, x, y, w, h = o
            yield oid, kind, (x + w / 2.0, y + h), (w, h)


# ------------------------------------------------------------------------------------------------
# 2. water
# ------------------------------------------------------------------------------------------------
def water_source(plan):
    out = []
    _rects, chans, w = _water(plan)
    W, H = _size(plan)
    for name, pts, _hw in chans:
        if name != 'rill':
            continue
        x, y = pts[0]
        if not (y <= 0 or x <= 0 or x >= W or y >= H or w.get('soft', {}).get('spring')):
            out.append(_f('rules.water_source', f'the {name} starts at {pts[0]} out of nowhere: give it a source '
                          '(the zone edge, a spring or a pool)', pts[0]))
    return out


def water_end(plan):
    out = []
    rects, chans, w = _water(plan)
    W, H = _size(plan)
    f = w.get('fall')
    for name, pts, _hw in chans:
        for end in (pts[0], pts[-1]):
            x, y = end
            at_edge = x <= 0 or y <= 0 or x >= W or y >= H
            in_pool = _in_rects(end, rects, pad=CELL)
            at_fall = f is not None and abs(y - f['y0']) <= CELL and abs(x - (f['x0'] + f['w'] / 2.0)) <= CELL
            if not (at_edge or in_pool or at_fall):
                out.append(_f('rules.water_end', f'the {name} ends at {end} in a dead end: run it to a pool, a lake, '
                              'a fall or the zone edge', end))
    return out


def water_fall(plan):
    out = []
    rects, chans, w = _water(plan)
    f = w.get('fall')
    if not f or not w.get('soft'):
        return out
    cx = f['x0'] + f['w'] / 2.0
    feeds = [(n, pts, hw) for n, pts, hw in chans if n == 'rill']
    for n, pts, hw in feeds:
        ex, ey = pts[-1]
        if abs(ex - cx) > 1.0:
            out.append(_f('rules.water_fall', f'the fall is not centred on the {n}: the channel arrives at x {ex}, '
                          f'the fall\'s middle is {cx}', pts[-1]))
        if abs(ey - f['y0']) > 1.0:
            out.append(_f('rules.water_fall', f'the {n} meets the lip at y {ey}, the lip is at {f["y0"]}: they must be flush',
                          pts[-1]))
        if abs(2 * hw - f['w']) > 1.0:
            out.append(_f('rules.water_fall', f'the fall is {f["w"]} px wide, the {n} that feeds it {2 * hw:g}: '
                          'the channel keeps its width over the lip', pts[-1]))
    face = f.get('face')
    if face and abs(face[1] - f['y0']) > 1.0:
        out.append(_f('rules.water_fall', f'the lip ({f["y0"]}) is not on the rock\'s top edge ({face[1]})', (cx, f['y0'])))
    if not _in_rects((cx, f['y1']), rects):
        out.append(_f('rules.water_fall', f'the fall lands at {(cx, f["y1"])} outside its pool', (cx, f['y1'])))
    return out


# ------------------------------------------------------------------------------------------------
# 3. ground materials and 4. routes
# ------------------------------------------------------------------------------------------------
def ground_water(plan):
    out = []
    span = _bridge_span(plan)
    for rid, pts, hw, _b, _s in _routes(plan):
        for a, b in zip(pts, pts[1:]):
            L = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2))
            for j in range(L + 1):
                p = (a[0] + (b[0] - a[0]) * j / L, a[1] + (b[1] - a[1]) * j / L)
                if _on_water(p, plan) and not (span and span[0] <= p[0] <= span[1] and span[2] <= p[1] <= span[3]):
                    out.append(_f('rules.ground_water', f'route {rid} runs under water at {tuple(round(v) for v in p)} '
                                  'off the bridge', p))
                    break
    return out


def route_grid(plan):
    out = []
    for rid, pts, hw, bend, spur in _routes(plan):
        for p in pts:
            if p[0] % CELL or p[1] % CELL:
                out.append(_f('rules.route_grid', f'route {rid}: point {p} is off the cells', p))
        segs = list(zip(pts, pts[1:]))
        for a, b in segs:
            if a[0] != b[0] and a[1] != b[1]:
                out.append(_f('rules.route_grid', f'route {rid}: a slanting run {a} to {b}; runs go along x or y and '
                              'turn in rounded bends', a))
        lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
        for k in range(1, len(segs) - 1):
            if lens[k] < 2 * CELL:
                out.append(_f('rules.route_grid', f'route {rid}: turns {lens[k]:g} px apart at {segs[k][0]}: a stair step '
                              '(turns at least two cells apart)', segs[k][0]))
        if bend is not None and not (0.4 * CELL <= bend <= 12 * CELL):
            out.append(_f('rules.route_grid', f'route {rid}: bend radius {bend} outside 0.4 to 12 cells', pts[0]))
    return out


def _destinations(plan):
    d = [tuple(v) for v in plan.get('stands', {}).values()]
    b = _places(plan).get('bridge')
    if b:
        d += [(b['x0'] + b['w'] / 2.0, b.get('y0', 0)), (b['x0'] + b['w'] / 2.0, b.get('y1', 0))]
    for dr in plan.get('doors', []):
        if 'rect' in dr:
            x, y, w, h = dr['rect']
            d.append((x + w / 2.0, y + h / 2.0))
    for bl in plan.get('buildings', []):
        if bl.get('door'):
            d.append(tuple(bl['door']))
    for st in plan.get('stairs', []):
        if 'at' in st:
            d.append(tuple(st['at']))
    return d


def _at_place(p, plan):
    """Inside a named place drawn as an ellipse (a glade, a stone circle), give or take a cell."""
    for pl in _places(plan).values():
        if isinstance(pl, dict) and 'at' in pl and 'r' in pl:
            (cx, cy), (rx, ry) = pl['at'], pl['r']
            if ((p[0] - cx) / (rx + CELL)) ** 2 + ((p[1] - cy) / (ry + CELL)) ** 2 <= 1.0:
                return True
    return False


def route_ends(plan):
    out = []
    W, H = _size(plan)
    rts = _routes(plan)
    dest = _destinations(plan)
    places = plan.get('places', [])
    prects = [p['rect'] for p in places] if isinstance(places, list) else []
    for rid, pts, hw, _b, _s in rts:
        for end in (pts[0], pts[-1]):
            x, y = end
            ok = x <= 0 or y <= 0 or x >= W or y >= H
            ok = ok or any(math.hypot(x - a, y - b) <= 3 * CELL for a, b in dest)
            ok = ok or _in_rects(end, prects, pad=CELL) or _at_place(end, plan)
            ok = ok or any(o != rid and _line_dist(end, p2) <= h2 + CELL for o, p2, h2, _b2, _s2 in rts)
            if not ok:
                out.append(_f('rules.route_ends', f'route {rid} ends at {end} going nowhere: end it at a door, a '
                              'bridge, a zone edge, a landmark or another route', end))
    return out


def _on_route(p, plan, shrink=0.0):
    return [rid for rid, pts, hw, _b, _s in _routes(plan) if _line_dist(p, pts) < hw - shrink]


def route_clear(plan):
    out = []
    for oid, kind, foot, (w, h) in _objects(plan):
        if kind in ON_ROUTE_OK:
            continue
        hit = []
        for dx in (-0.35 * w, 0.0, 0.35 * w):
            hit += _on_route((foot[0] + dx, foot[1] - 2), plan)
        if hit:
            out.append(_f('rules.route_clear', f'{oid} ({kind}) stands on route {hit[0]} at {foot}: move it beside the route',
                          foot))
    return out


def seating(plan):
    out = []
    for oid, kind, foot, (w, h) in _objects(plan):
        if kind not in SEATS:
            continue
        best = None
        for rid, pts, hw, _b, _s in _routes(plan):
            for dx in (-0.4 * w, 0.0, 0.4 * w):
                p = (foot[0] + dx, foot[1])
                d = _line_dist(p, pts) - hw
                if best is None or d < best[0]:
                    best = (d, rid, pts)
        if best is None or best[0] > 2 * CELL:
            out.append(_f('rules.seating', f'{oid}: a seat away from any route ({best[0] if best else "none"} px): stand it '
                          'beside one, facing it', foot))
            continue
        if best[0] < 0:
            out.append(_f('rules.seating', f'{oid}: the seat stands on route {best[1]}', foot))
            continue
        # the kit's bench faces south: the route must lie in front of it (south of its foot)
        ahead = _line_dist((foot[0], foot[1] + best[0] + 4 + 0.0), best[2])
        if ahead > _line_dist((foot[0], foot[1] - 12), best[2]):
            out.append(_f('rules.seating', f'{oid}: the seat turns its back on route {best[1]}: stand it so the route '
                          'lies in front of its face', foot))
    return out


# ------------------------------------------------------------------------------------------------
# 6. props by role and 7. clutter
# ------------------------------------------------------------------------------------------------
def _rock_box(b):
    x, y = b['at']
    w, h = b['size']
    return (x - w / 2.0, y - h, x + w / 2.0, y)


def rock_overlap(plan):
    out = []
    heap = plan.get('rock', {}).get('heap', [])
    for i, a in enumerate(heap):
        for b in heap[i + 1:]:
            if a.get('stacked') or b.get('stacked'):
                continue
            A, B = _rock_box(a), _rock_box(b)
            ox = min(A[2], B[2]) - max(A[0], B[0])
            oy = min(A[3], B[3]) - max(A[1], B[1])
            if ox > 1 and oy > 1:
                out.append(_f('rules.rock_overlap', f'rocks at {a["at"]} and {b["at"]} overlap ({ox:g} x {oy:g} px): lay them '
                              'side by side, or mark one stacked', a['at']))
    return out


def clutter(plan):
    out = []
    d = plan.get('dressing', {})
    pts = [(x, y, 'fern') for x, y, *_ in d.get('ferns', [])] + [(x, y, 'leaf') for x, y, *_ in d.get('leaves', [])]
    for x, y, kind in pts:
        if _on_route((x, y), plan, shrink=3.0):
            out.append(_f('rules.clutter', f'a {kind} at {(x, y)} lies on a route\'s centre', (x, y)))
        elif kind == 'fern' and _on_water((x, y), plan):
            out.append(_f('rules.clutter', f'a {kind} at {(x, y)} grows in the water', (x, y)))
    return out


def stage_debris(kit, plan=None):
    out = []
    if plan is not None and not plan.get('stages'):
        return out            # a zone without stages (the vault's rubble is its own, not the storm's)
    for o in kit.get('objects', []):
        name = ((o.get('id') or '') + ' ' + (o.get('png') or '')).lower()
        if any(k in name for k in ('puddle', 'debris', 'rubble')) and not o.get('cond'):
            out.append(_f('rules.stage_debris', f'{o.get("id")}: storm debris or puddles in every stage: give it the '
                          'broken stage\'s condition', None))
    return out


CHECKS = (water_source, water_end, water_fall, ground_water, route_grid, route_ends, route_clear, seating,
          rock_overlap, clutter)


def check_plan(plan) -> list[dict]:
    out = []
    for c in CHECKS:
        try:
            out += c(plan)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue          # a plan without that layer
    return out


def plans():
    yield 'woodland', os.path.join(ROOT, 'art', 'scenes', 'woodland.json'), None
    zdir = os.path.join(ROOT, 'game', 'data', 'plans')
    for f in sorted(os.listdir(zdir)):
        if f.endswith('.json'):
            kit = os.path.join(ROOT, 'game', 'zones', f[:-5], 'kit.json')
            yield f[:-5], os.path.join(zdir, f), kit if os.path.exists(kit) else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    bad = 0
    for name, path, kit in plans():
        plan = json.load(open(path))
        fs = check_plan(plan)
        if kit:
            fs += stage_debris(json.load(open(kit)), plan)
        strict = bool(plan.get('ground_rules'))
        tag = 'ok' if not fs else f'{len(fs)} finding(s)' + ('' if strict else ' (advisory)')
        print(f'[ground rules] {name}: {tag}')
        for f in fs:
            print(f'  {f["check"]}: {f["message"]}')
        if strict and fs:
            bad += 1
    return 1 if (a.check and bad) else 0


if __name__ == '__main__':
    sys.exit(main())
