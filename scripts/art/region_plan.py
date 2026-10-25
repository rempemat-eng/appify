"""Region plans as data: read, check and draw a region's plan (art/regions/<id>.json).

Claude F, 21 Oct (lane F: the Frostline, the massif and the Brackens). A region is laid out as
data before it is painted, so the painter, Claude G's routes and the checks all read one source:
tier outlines in screen space, routes and trods as polylines, stairs where a path changes tier,
the brief's named things, secret pockets, markers, obstacles, edges, thresholds and, where the
region is built from the cliff core's set pieces, their placements ({piece, biome, at, seed}, the
shape Codex's C36 placement library takes). Coordinates are world px (world plan v5.3, 11264 x
6912); tiers are local to the plan, with a provisional base until the geography chunk (P1).

What `check()` holds a plan to (the brief's rules that can be checked before any art exists;
docs/vision/regions/*.md section 8, research/world-benchmark.md, eastward-edges.md):
- structure on the 8 px grid: every outline vertex, stair and route width (eastward 1.1, 1.2);
  tier outlines run along x or y only, turning at cell corners (Matt, 21 Oct 11:44: the grid
  shape, to-all-grid-2x), with no tab or notch of 1 to 2 cells; corners are rounded by the kit
  unless a tier is marked "corners": "square" (a built edge); a note (not a fault) where an
  east-west edge runs a screen width without stepping in or out (a-to-f-grid, to-all-volume);
- inside the box: every outline, route, place, named thing, pocket and marker, unless it is
  marked outside_box (a marker the brief lists just past the line);
- paths: widths 24 to 64 (check 17); every segment along x or y, turning at cell corners (the
  grid shape, Matt 21 Oct 11:44, which replaces benchmark 16's bend every 240 to 300 px);
  bridges and causeways are on their own deck tier, so the tier rule does not read them; dead ends of 80 px or more end in a view, a resident, a
  bench or a story detail (check 20);
- tiers: a path that crosses from one tier to another does so on a stair at least 34 px wide
  within 24 px of the crossing (checks 19, 21; eastward 6.3: no ramps), and never walks along a
  face; a stair's tiers match the ground either side of it;
- things: named things, pockets and markers stand on walkable ground (a tier top, not a face),
  'beside the path' within 48 px of a path, 'a short way off' within 160; a pocket at the end
  of its trod; egg spots clear of every marker and named thing;
- things stand beside their path, not on it or on a stair;
- check 1: the markers give each screen of route, and each screen area, 2 interactables and 3
  story props;
- set pieces from the cliff core's library, or marked proposed;
- obstacles at least 800 px apart (brief 7); set pieces of this biome only, on the 8 px grid.
- placement, reach and water ends (from Claude I's lull_delta.py, #177): nothing placed in
  water, the sea or a building; every placed thing and egg spot reachable from the routes on
  stairs, bridges and fords; every water body with a source and an outlet, or declared closed.
- crossings, water height, rails and meets (lane R, 22 and 23 Oct): every crossing of open water
  carried by a bridge, ford or declared crossing; water never runs uphill and every drop has a
  fall; rails end at a stop, declare their crossings and change tier on an incline, and a rail
  two plans share has one line; a path ending on the box edge meets a neighbour's path or a
  lane G route.

Run:
    python3 scripts/art/region_plan.py --check            (every plan; exits non-zero on a fault)
    python3 scripts/art/region_plan.py --fix [ids..]      (moves things that break a placement rule
                                                          to the nearest point that keeps them)
    python3 scripts/art/region_plan.py --dress [ids..]    (adds dressing slots so every screen area
                                                          has 2 interactables and 3 story props, then
                                                          fixes)
    python3 scripts/art/region_plan.py [OUT_DIR] [ids..]  (draws each plan, 1 px a world px / 4,
                                                          to OUT_DIR, default napattack-region-plans
                                                          in the system's temp folder)
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
PLANS = os.path.join(ROOT, 'art', 'regions')
GRID = 8
FACE = 32
STAIR_MIN = 34
NEAR_STAIR = 24
BESIDE = 48
OFF = 160
DEAD_MIN = 80
OBSTACLE_GAP = 800
DEAD_ENDS = {'view', 'resident', 'bench', 'story'}
SPANS = {'bridge', 'causeway'}
# the cliff core's set pieces (claude-a/cliff-core, PR #165: Plan's pieces); a plan may name one
# not in it only as 'proposed'
LIBRARY = {'stair', 'ledge', 'path', 'spring', 'pond', 'snow_corner', 'boulders', 'scree', 'ivy'}
# what counts on a screen (world_audit's density, benchmark check 1): interactables, and story
# props (the markers' S slots); named things that are places to use count as interactables
NAMED_INTERACT = {'well', 'npc', 'landmark', 'camp', 'view', 'shrine'}


def load(pid: str) -> dict:
    with open(os.path.join(PLANS, f'{pid}.json')) as fh:
        return json.load(fh)


def plan_ids() -> list:
    return sorted(f[:-5] for f in os.listdir(PLANS) if f.endswith('.json'))


# --- geometry ------------------------------------------------------------------------------

def seg_len(a, b) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def length(pts) -> float:
    return sum(seg_len(a, b) for a, b in zip(pts, pts[1:]))


def sample(pts, step: float = 4.0):
    """Points every `step` px along a polyline, with the distance along it."""
    out, done = [], 0.0
    for a, b in zip(pts, pts[1:]):
        L = seg_len(a, b)
        n = max(1, int(L // step))
        for i in range(n):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, done + L * t))
        done += L
    out.append((pts[-1][0], pts[-1][1], done))
    return out


def dist_to_line(p, pts) -> float:
    best = 1e9
    for a, b in zip(pts, pts[1:]):
        ax, ay, bx, by = *a, *b
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


class Ground:
    """The plan's screen tier map at 4 px, with each tier's south face (FACE px under its
    south rim, carved from the ground below) marked as face."""

    def __init__(self, plan: dict):
        self.x0, self.y0, self.w, self.h = plan['box']
        self.s = 4
        W, H = self.w // self.s, self.h // self.s
        self.tier = np.zeros((H, W), np.int16)
        for t in sorted(plan.get('tiers', []), key=lambda t: t['tier']):
            img = Image.new('L', (W, H), 0)
            ImageDraw.Draw(img).polygon([((x - self.x0) / self.s, (y - self.y0) / self.s) for x, y in t['outline']],
                                        fill=1)
            m = np.asarray(img).astype(bool)
            self.tier[m] = np.maximum(self.tier[m], t['tier'])
        # a face: a cell d px under a rim whose tier stands n tiers higher, d < n * FACE (a drop
        # of two tiers at once hangs a 64 px face). A face cell's tier is its lower ground.
        self.face = np.zeros_like(self.tier, bool)
        top = int(self.tier.max()) - int(self.tier.min())
        for d in range(1, top * FACE // self.s + 1):
            up = np.vstack([self.tier[:1].repeat(d, 0), self.tier[:-d]])
            self.face |= (up - self.tier) * FACE > (d - 1) * self.s

    def at(self, x, y):
        c, r = int((x - self.x0) // self.s), int((y - self.y0) // self.s)
        if not (0 <= r < self.tier.shape[0] and 0 <= c < self.tier.shape[1]):
            return None, False
        return int(self.tier[r, c]), bool(self.face[r, c])


# --- the checks ----------------------------------------------------------------------------

TAB_MAX = 16                      # a tab or notch: an end edge of 1 to 2 cells between two like turns
CORNERS = ('rounded', 'square')   # outline corners: rounded by the kit (cliff_core.grid_mask), or
#                                   square for a built edge (a quay, a wall); rounded when unmarked
VARIETY_RUN = 320                 # a face that runs a screen width without stepping (advisory)


def tabs(outline) -> list:
    """The tabs and notches of an outline along x or y: an edge of at most TAB_MAX px whose two
    ends turn the same way, so it caps a 1 to 2 cell finger poking out or a slot cut in. (A
    step, whose ends turn opposite ways, is a jog of the mass and is fine.)"""
    o = [tuple(v) for v in outline]
    n = len(o)
    if n <= 4:
        return []                                        # a rectangle has no finger to cut
    area = sum(o[i][0] * o[(i + 1) % n][1] - o[(i + 1) % n][0] * o[i][1] for i in range(n))

    def turn(a, b, c):
        return (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
    out = []
    for i in range(n):
        a, b, c, d = o[i - 1], o[i], o[(i + 1) % n], o[(i + 2) % n]
        if a[0] != b[0] and a[1] != b[1]:
            continue                                     # not yet on the grid: the edge rule speaks
        ln = abs(c[0] - b[0]) + abs(c[1] - b[1])
        t1, t2 = turn(a, b, c), turn(b, c, d)
        if 0 < ln <= TAB_MAX and t1 and t2 and (t1 > 0) == (t2 > 0):
            out.append((b, 'tab' if (t1 > 0) == (area > 0) else 'notch'))
    return out


def tidy(o) -> list:
    """An outline without repeated vertices or vertices in the middle of a straight run."""
    o = [list(v) for v in o]
    changed = True
    while changed and len(o) > 4:
        changed = False
        for i in range(len(o)):
            a, b, c = o[i - 1], o[i], o[(i + 1) % len(o)]
            if b == a or (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
                del o[i]
                changed = True
                break
    return o


def _area(o) -> float:
    n = len(o)
    return abs(sum(o[i][0] * o[(i + 1) % n][1] - o[(i + 1) % n][0] * o[i][1] for i in range(n))) / 2


def detab(outline) -> list:
    """The outline with its tabs and notches (see tabs) closed: the finger's two sides are cut
    back to the shorter one, so the tip lands on the line it stood out from. A tab whose closing
    would take more than a tenth of the shape (a tier only a cell or two wide) is left for a
    person: the check still reports it."""
    o = tidy(outline)
    skip = set()
    for _ in range(4 * len(o) + 8):
        found = [f for f in tabs(o) if f[0] not in skip]
        if not found:
            break
        n = len(o)
        i = next(k for k in range(n) if tuple(o[k]) == found[0][0])
        a, b, c, d = o[i - 1], o[i], o[(i + 1) % n], o[(i + 2) % n]
        ab, cd = abs(b[0] - a[0]) + abs(b[1] - a[1]), abs(d[0] - c[0]) + abs(d[1] - c[1])
        v = (a[0] - b[0], a[1] - b[1]) if ab <= cd else (d[0] - c[0], d[1] - c[1])
        new = [list(q) for q in o]
        new[i] = [b[0] + v[0], b[1] + v[1]]
        new[(i + 1) % n] = [c[0] + v[0], c[1] + v[1]]
        new = tidy(new)
        if len(new) < 4 or abs(_area(new) - _area(o)) > 0.1 * _area(o):
            skip.add(found[0][0])
            continue
        o = new
    return o


# --- placement, reach and water ends (from Claude I's lull_delta.py, #177) -----------------

def _in_poly(p, poly) -> bool:
    x, y, inside = p[0], p[1], False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def coast_polys(P: dict) -> list:
    """The plan's land outlines: `coast` as one polygon, or as {name: polygon} for several
    islands (Claude C; string values there are notes). Outside every one of them is sea."""
    c = P.get('coast')
    if not c:
        return []
    polys = list(c.values()) if isinstance(c, dict) else [c]
    return [q for q in polys if isinstance(q, list) and len(q) >= 3 and isinstance(q[0], list)]


def placed(P: dict) -> list:
    """Everything a plan places, as (label, at, the entry)."""
    return [(n['thing'], n['at'], n) for n in P.get('named', [])] + \
        [(k['holds'], k['at'], k) for k in P.get('pockets', [])] + \
        [(f"marker {m['what']}", m['at'], m) for m in P.get('markers', []) if not m.get('outside_box')] + \
        [(r['who'], r['at'], r) for r in P.get('residents', [])] + \
        [(f"camp {c['id']} enemy", e, c) for c in P.get('camps', []) for e in c.get('enemies', [])]


def camps_check(P: dict) -> list:
    """Camps (the Godot game's fights, docs/godot.md 'Camps'; game/data/plans/undercroft.json):
    each has an id unique in the plan, at least one enemy, and an `arena` rect [x, y, w, h] on
    the plan's ground, inside the box, holding all its enemies, at least 96 x 64 world px (room
    to dodge on a 320 x 180 screen) and touched by a path, so the player walks into it. Its
    enemies are reached by the flood fill like any placed thing (reach)."""
    out = []
    pid = P['id']
    x0, y0, w, h = P['box']
    seen = set()
    paths = [p['points'] for p in P.get('routes', []) + P.get('trods', [])]
    for c in P.get('camps', []):
        cid = c.get('id')
        if cid in seen:
            out.append(f'{pid}: camp {cid} twice')
        seen.add(cid)
        if not c.get('enemies'):
            out.append(f'{pid}: camp {cid} has no enemies')
        a = c.get('arena')
        if not a:
            out.append(f'{pid}: camp {cid} has no arena rect')
            continue
        ax, ay, aw, ah = a
        if aw < 96 or ah < 64:
            out.append(f'{pid}: camp {cid} arena {a} is smaller than 96 x 64 world px')
        if ax < x0 or ay < y0 or ax + aw > x0 + w or ay + ah > y0 + h:
            out.append(f'{pid}: camp {cid} arena {a} leaves the box')
        for e in c.get('enemies', []):
            if not (ax <= e[0] <= ax + aw and ay <= e[1] <= ay + ah):
                out.append(f'{pid}: camp {cid} enemy at {tuple(e)} is outside its arena')
        if not any(ax - 8 <= x <= ax + aw + 8 and ay - 8 <= y <= ay + ah + 8 for pts in paths for x, y, _s in sample(pts, 8)):
            out.append(f'{pid}: camp {cid} arena {a} is touched by no path')
    return out


def _decked(P: dict, at) -> bool:
    """On a bridge, a deck span or an island the plan declares."""
    for b in P.get('places', []):
        if b.get('span') and b['span'][0] <= at[0] <= b['span'][1] and abs(at[1] - b['at'][1]) <= 16:
            return True
        ix, iy, iw, ih = b.get('island', (0, 0, 0, 0))
        if ix <= at[0] <= ix + iw and iy <= at[1] <= iy + ih:
            return True
    for w in P.get('water', []):
        if any(abs(at[0] - b['at'][0]) <= b['span'] / 2 and abs(at[1] - b['at'][1]) <= 16 for b in w.get('bridges', [])):
            return True
    return False


def placement(P: dict) -> list:
    """Nothing placed stands in water (inside a closed water body and off its islands, within
    half a channel's width and 6 px of its line, or in the sea outside the plan's `coast`), or
    inside a building's footprint (`buildings`: {id, foot: [x, y] its south-west corner, w}; a
    door marker stands at its building). A thing that stands in the shallows or on stilts by
    design says so with "in_water": true."""
    pid, out = P['id'], []
    coast = coast_polys(P)
    for what, at, e in placed(P):
        if e.get('in_water') or _decked(P, at):
            continue
        if coast and not any(_in_poly(at, c) for c in coast):
            out.append(f'{pid}: {what} at {tuple(at)} stands in the sea (outside the coast)')
        for w in P.get('water', []):
            if w.get('closed'):
                if _in_poly(at, w['points']) and not any(_in_poly(at, i['outline']) for i in w.get('islands', [])):
                    out.append(f'{pid}: {what} at {tuple(at)} stands in the {w["id"]}')
            elif dist_to_line(at, w['points']) < w.get('width', 8) / 2 + 6:
                out.append(f'{pid}: {what} at {tuple(at)} stands in the {w["id"]}')
        for b in P.get('buildings', []):
            if what.startswith('marker door'):
                break
            x, y = b['foot']
            if x - 4 <= at[0] <= x + b['w'] + 4 and y - 80 <= at[1] <= y + 4:
                out.append(f'{pid}: {what} at {tuple(at)} stands in the building {b["id"]}')
    return out


def reach(P: dict) -> list:
    """Reachability on the plan alone (rules-system.md G0): a flood fill at 4 px over walkable
    ground (tier tops, not faces, not water, not the sea outside the coast, not land marked
    walkable: false) from every route's ends, changing tier only on a stair and crossing water
    only on a bridge, causeway, jetty, boardwalk, slipway or declared island. Faults every
    named thing, pocket, marker, resident and egg spot it cannot reach."""
    from collections import deque
    G = Ground(P)
    x0, y0 = P['box'][0], P['box'][1]
    c = G.s
    H, W = G.tier.shape

    def px(q):
        return ((q[0] - x0) / c, (q[1] - y0) / c)
    wet = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(wet)
    if coast_polys(P):
        dr.rectangle([0, 0, W, H], fill=1)
        for poly in coast_polys(P):
            dr.polygon([px(q) for q in poly], fill=0)
    for wt in P.get('water', []):
        if wt.get('closed'):
            dr.polygon([px(q) for q in wt['points']], fill=1)
            for i in wt.get('islands', []):
                dr.polygon([px(q) for q in i['outline']], fill=0)
        else:
            dr.line([px(q) for q in wt['points']], fill=1, width=max(1, int(wt.get('width', 8) / c)))
    for a in P.get('areas', []):
        if a.get('walkable') is False:
            ax, ay, aw, ah = a['rect']
            dr.rectangle([px((ax, ay)), px((ax + aw, ay + ah))], fill=1)
    wet = np.asarray(wet).astype(bool)
    deck = Image.new('L', (W, H), 0)
    dd = ImageDraw.Draw(deck)
    for pth in P.get('routes', []) + P.get('trods', []):
        if pth.get('kind') in SPANS or pth['id'] in ('jetty', 'boardwalk', 'slipway'):
            dd.line([px(q) for q in pth['points']], fill=1, width=max(1, int(pth['width'] / c)))
        for f in ([pth['ford']] if pth.get('ford') else []) + pth.get('fords', []):
            dd.rectangle([px((f[0] - 16, f[1] - 16)), px((f[0] + 16, f[1] + 16))], fill=1)
    for pl in P.get('places', []):
        if pl.get('span'):
            a, b = pl['span']
            dd.rectangle([px((a, pl['at'][1] - 16)), px((b, pl['at'][1] + 16))], fill=1)
        if pl.get('island'):
            ix, iy, iw, ih = pl['island']
            dd.rectangle([px((ix, iy)), px((ix + iw, iy + ih))], fill=1)
    for wt in P.get('water', []):
        for b in wt.get('bridges', []):
            dd.rectangle([px((b['at'][0] - b['span'] / 2, b['at'][1] - 16)),
                          px((b['at'][0] + b['span'] / 2, b['at'][1] + 16))], fill=1)
        for f in wt.get('fords', []):
            dd.rectangle([px((f[0] - 16, f[1] - 16)), px((f[0] + 16, f[1] + 16))], fill=1)
    deck = np.asarray(deck).astype(bool)
    stair = np.zeros((H, W), bool)
    yy, xx = np.mgrid[0:H, 0:W]
    for st in P.get('stairs', []):
        sx, sy = px(st['at'])
        stair |= (np.abs(xx - sx) <= (st['width'] / 2 + 8) / c) & (np.abs(yy - sy) <= (FACE + 16) / c)
    walk = (~wet & ~G.face) | deck | stair
    tier = G.tier
    seen = np.zeros((H, W), bool)
    q = deque()
    for pth in P.get('routes', []):
        for p in (pth['points'][0], pth['points'][-1]):
            cx = min(max(int((p[0] - x0) // c), 0), W - 1)
            cy = min(max(int((p[1] - y0) // c), 0), H - 1)
            if walk[cy, cx] and not seen[cy, cx]:
                seen[cy, cx] = True
                q.append((cy, cx))
    while q:
        r, k = q.popleft()
        for d1, d2 in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r2, k2 = r + d1, k + d2
            if not (0 <= r2 < H and 0 <= k2 < W) or seen[r2, k2] or not walk[r2, k2]:
                continue
            if tier[r2, k2] != tier[r, k] and not (stair[r2, k2] or stair[r, k] or deck[r2, k2] or deck[r, k]):
                continue
            seen[r2, k2] = True
            q.append((r2, k2))
    out = []
    things = [(w, a) for w, a, _e in placed(P)] + [(e['what'], e['at']) for e in P.get('egg_spots', [])]
    for what, at in things:
        cx, cy = int((at[0] - x0) // c), int((at[1] - y0) // c)
        if not seen[max(0, cy - 3):cy + 4, max(0, cx - 3):cx + 4].any():
            out.append(f'{P["id"]}: {what} at {tuple(at)} cannot be reached from the routes')
    return out


def water_ends(P: dict) -> list:
    """Every water body says where it comes from and where it goes (`source` and `outlet`, a
    name or a point; a stream that leaves the box names where), or is `declared_closed` (a
    sealed tarn, a dew pond). Water does not appear from nowhere (Claude I, #177)."""
    out = []
    for w in P.get('water', []):
        if w.get('declared_closed'):
            continue
        for k in ('source', 'outlet'):
            if not w.get(k):
                out.append(f'{P["id"]}: water {w["id"]} has no {k} (or mark it declared_closed)')
    return out


# --- crossings, water height, rails and meets at the box edge (lane R, 22 and 23 Oct) -------

def _seg_x(a, b, c, d):
    """Where segment ab crosses segment cd, or None (touching ends count)."""
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a, b, c, d
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def _cross_points(pa, pb) -> list:
    """Every point where polyline pa crosses polyline pb."""
    out = []
    for a, b in zip(pa, pa[1:]):
        for c, d in zip(pb, pb[1:]):
            q = _seg_x(tuple(a[:2]), tuple(b[:2]), tuple(c[:2]), tuple(d[:2]))
            if q and not any(math.hypot(q[0] - o[0], q[1] - o[1]) < 4 for o in out):
                out.append(q)
    return out


def _near(pt, pts, r) -> bool:
    return any(math.hypot(pt[0] - q[0], pt[1] - q[1]) <= r for q in pts)


def _walked(P: dict) -> list:
    """The plan's walked paths, without the ones that are a deck themselves."""
    return [p for p in P.get('routes', []) + P.get('trods', [])
            if p.get('kind') not in SPANS and p['id'] not in ('jetty', 'boardwalk', 'slipway')]


def crossings_declared(P: dict) -> list:
    """Every place a route or trod crosses open water carries it over: a bridge on the water, a
    ford on the path, a crossing the plan declares, or a deck span or island, within half the
    water's width plus 16 px of the crossing (lane R, 22 Oct)."""
    out = []
    for w in P.get('water', []):
        if w.get('closed') or w.get('declared_closed') and not w.get('width'):
            continue
        r = w.get('width', 8) / 2 + 16
        carried = [b['at'] for b in w.get('bridges', [])] + list(w.get('fords', [])) + \
            [c['at'] for c in P.get('crossings', []) if c.get('over', w['id']) == w['id']]
        for pth in _walked(P):
            mine = carried + ([pth['ford']] if pth.get('ford') else []) + list(pth.get('fords', []))
            for q in _cross_points(pth['points'], w['points']):
                if not _near(q, mine, r) and not _decked(P, q):
                    out.append(f'{P["id"]}: {pth["id"]} crosses {w["id"]} at ({q[0]:.0f}, {q[1]:.0f}) with no bridge, '
                               f'ford or crossing within {r:.0f} px')
    return out


def _falls(w) -> list:
    out = []
    for f in w.get('falls', []):
        out.append(tuple(f['at']) if isinstance(f, dict) else tuple(f[:2]))
    return out


def _tier_runs(G, pts, step=4.0, settle=32.0):
    """The ground's tier along a polyline as (tier, x, y) where it settles: a change counts
    only once the new tier holds for `settle` px, so a line along a rim (flicking between the
    tier above and the face's foot) reads as one tier."""
    seq = [(G.at(x, y)[0], x, y) for x, y, _s in sample(pts, step)]
    seq = [q for q in seq if q[0] is not None]
    k = max(1, int(settle / step))
    out = []
    i = 0
    while i < len(seq):
        t = seq[i][0]
        j = i
        while j < len(seq) and seq[j][0] == t:
            j += 1
        if j - i >= k or not out or j >= len(seq):
            if not out or out[-1][0] != t:
                out.append(seq[i])
        i = j
    return out


def water_height(P: dict) -> list:
    """A stream never runs uphill: along its points (source to outlet) its ground's tier never
    rises, and every drop has a fall within 48 px (lane R, 23 Oct)."""
    out = []
    G = Ground(P)
    for w in P.get('water', []):
        if w.get('closed') or len(w.get('points', [])) < 2:
            continue
        falls = _falls(w)
        last = None
        rose = dropped = False
        for t, x, y in _tier_runs(G, w['points']):
            if last is not None and t > last[0] and not rose:
                out.append(f'{P["id"]}: water {w["id"]} rises from tier {last[0]} to {t} at ({x:.0f}, {y:.0f}) '
                           f'(points run source to outlet; water never runs uphill)')
                rose = True
            if last is not None and t < last[0] and not _near((x, y), falls, 48) and not dropped:
                out.append(f'{P["id"]}: water {w["id"]} drops from tier {last[0]} to {t} at ({x:.0f}, {y:.0f}) '
                           f'with no fall within 48 px')
                dropped = True
            last = (t, x, y)
    return out


INCLINES = ('cutting', 'embankment', 'rope incline')
VIADUCT = 128                     # px either side of a rail's viaduct point the ground's tier does not touch it


def rails_check(P: dict) -> list:
    """Rails (lane R, 23 Oct): each end at a stop or buffer of the plan (within 64 px: a
    platform is long), at another rail, or
    leaving across the box edge; every crossing of a path, another rail or open water declared
    in the rail's `crossings` (or a water bridge, or its viaduct) within 24 px; every change of
    tier on an incline (`inclines`: {at, kind} with kind a cutting, an embankment or a rope
    incline) within 48 px, except on its viaduct (within VIADUCT px of `viaduct`). A rail in a
    tunnel is under the ground: only its ends count; two rails joined end to end meet, not cross."""
    out = []
    pid = P['id']
    x0, y0, w, h = P['box']
    stops = [s['at'] for s in P.get('stops', [])]
    rails = P.get('rails', [])
    G = Ground(P)
    for r in rails:
        pts = r['points']
        for end in (pts[0], pts[-1]):
            on_edge = abs(end[0] - x0) <= 8 or abs(end[0] - x0 - w) <= 8 or abs(end[1] - y0) <= 8 or abs(end[1] - y0 - h) <= 8
            others = [q for o in rails if o is not r for q in o['points']]
            if not (on_edge or _near(end, stops + list(r.get('buffers', [])), 64) or _near(end, others, 24)):
                out.append(f'{pid}: rail {r["id"]} ends at {tuple(end)} with no stop or buffer')
        if r.get('tunnel'):
            continue
        declared = [c['at'] for c in r.get('crossings', [])] + ([r['viaduct']] if r.get('viaduct') else [])
        against = [(p['id'], p['points']) for p in _walked(P)] + [(o['id'], o['points']) for o in rails if o is not r]
        for wtr in P.get('water', []):
            if not wtr.get('closed'):
                against.append((wtr['id'], wtr['points']))
                declared += [b['at'] for b in wtr.get('bridges', [])]
        for oid, opts in against:
            for q in _cross_points(pts, opts):
                if _near(q, [pts[0], pts[-1]], 4) and _near(q, [opts[0], opts[-1]], 4):
                    continue                  # one line runs on from the other's end: a junction
                if not _near(q, declared, 24):
                    out.append(f'{pid}: rail {r["id"]} crosses {oid} at ({q[0]:.0f}, {q[1]:.0f}), not declared in its crossings')
        inc = [i['at'] for i in r.get('inclines', []) if i.get('kind') in INCLINES]
        for i in r.get('inclines', []):
            if i.get('kind') not in INCLINES:
                out.append(f'{pid}: rail {r["id"]} incline at {tuple(i["at"])} is a {i.get("kind")!r} (one of {", ".join(INCLINES)})')
        last = None
        deck = [r['viaduct']] if r.get('viaduct') else []
        for t, x, y in _tier_runs(G, pts):
            if _near((x, y), deck, VIADUCT):
                continue                      # carried over the ground on its viaduct
            if last is not None and t != last and not _near((x, y), inc, 48):
                out.append(f'{pid}: rail {r["id"]} changes tier {last} to {t} at ({x:.0f}, {y:.0f}) with no incline within 48 px')
            last = t
    return out


def shared_rails(plans: list) -> list:
    """A rail two plans both draw has the same line where their boxes overlap (lane R, 23 Oct)."""
    out = []
    for i, A in enumerate(plans):
        for B in plans[i + 1:]:
            ax, ay, aw, ah = A['box']
            bx, by, bw, bh = B['box']
            ox0, oy0, ox1, oy1 = max(ax, bx), max(ay, by), min(ax + aw, bx + bw), min(ay + ah, by + bh)
            ra = {r['id']: r for r in A.get('rails', [])}
            for rb in B.get('rails', []):
                if rb['id'] not in ra:
                    continue
                pa, pb = ra[rb['id']]['points'], rb['points']
                for (src, dst, sp, dp) in ((A, B, pa, pb), (B, A, pb, pa)):
                    for x, y, _s in sample(sp, 8.0):
                        if ox0 <= x <= ox1 and oy0 <= y <= oy1 and dist_to_line((x, y), dp) > 8:
                            out.append(f'{src["id"]}: rail {rb["id"]} at ({x:.0f}, {y:.0f}) is off {dst["id"]}\'s line '
                                       f'for the same rail where the boxes overlap')
                            break
    return out


_G_ROUTES = None


def g_routes() -> list:
    """Lane G's routes as polylines [(x, y), ...] (lib/world-routes.ts, read with node + tsx), or
    [] if they cannot be read here (then the meet check uses the other plans only)."""
    global _G_ROUTES
    if _G_ROUTES is None:
        import subprocess
        root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        code = ("const m = await import('file://' + process.argv[1]);"
                "process.stdout.write(JSON.stringify(m.worldRoutes.map(r => r.points.map(p => [p[0], p[1]]))));")
        try:
            r = subprocess.run([os.environ.get('NODE', 'node'), '--import', 'tsx', '--input-type=module', '-e', code,
                                os.path.join(root, 'lib', 'world-routes.ts')], cwd=root, capture_output=True,
                               text=True, timeout=120)
            _G_ROUTES = json.loads(r.stdout) if r.returncode == 0 else []
        except Exception:
            _G_ROUTES = []
    return _G_ROUTES


def edge_meets(P: dict, others: list, routes: list) -> list:
    """A path that ends on the box edge meets something on the other side: a path of the
    neighbour's plan or one of lane G's routes, within 16 px (lane R, 23 Oct)."""
    out = []
    x0, y0, w, h = P['box']
    lines = [p['points'] for o in others for p in o.get('routes', []) + o.get('trods', [])] + routes
    for pth in P.get('routes', []) + P.get('trods', []):
        for end in (pth['points'][0], pth['points'][-1]):
            if not (end[0] in (x0, x0 + w) or end[1] in (y0, y0 + h)):
                continue
            if not any(dist_to_line(tuple(end[:2]), [q[:2] for q in ln]) <= 16 for ln in lines if len(ln) > 1):
                out.append(f'{P["id"]}: {pth["id"]} ends on the box edge at {tuple(end[:2])} and meets no path of a '
                           f'neighbour or lane G route there')
    return out


def variety(plan: dict) -> list:
    """Advisory (a-to-f-grid): a tier's east-west edge that runs more than a screen width without
    stepping in or out. Volume comes from masses that step (to-all-volume)."""
    out = []
    y0, y1 = plan['box'][1], plan['box'][1] + plan['box'][3]
    for t in plan.get('tiers', []):
        o = t['outline']
        for a, b in zip(o, o[1:] + o[:1]):
            if a[1] == b[1] and a[1] not in (y0, y1) and abs(b[0] - a[0]) > VARIETY_RUN:
                out.append(f'{plan["id"]}: tier {t["id"]} runs {abs(b[0] - a[0])} px flat at y {a[1]} '
                           f'from x {min(a[0], b[0])} (a step in or out every screen width)')
    return out


def check(plan: dict) -> list:
    out = []
    pid = plan['id']
    x0, y0, w, h = plan['box']
    G = Ground(plan)

    def inside(p, what, slack=0):
        if not (x0 - slack <= p[0] <= x0 + w + slack and y0 - slack <= p[1] <= y0 + h + slack):
            out.append(f'{pid}: {what} at {tuple(p)} lies outside the box')

    for v in (x0, y0):
        if v % GRID:
            out.append(f'{pid}: box {plan["box"]} off the {GRID} px grid')
    for v in (w, h):
        if v % 32:
            out.append(f'{pid}: box {plan["box"]} is not whole 32 px audit cells')
    for a in plan.get('areas', []):
        ax, ay, aw, ah = a['rect']
        if (ax - x0) % 32 or (ay - y0) % 32 or aw % 32 or ah % 32:
            out.append(f'{pid}: area {a["id"]} {a["rect"]} is not whole 32 px audit cells of the box')
    for t in plan.get('tiers', []):
        o = t['outline']
        for a, b in zip(o, o[1:] + o[:1]):
            if a[0] != b[0] and a[1] != b[1]:
                out.append(f'{pid}: tier {t["id"]} edge {tuple(a)} to {tuple(b)} is not along x or y '
                           f'(the grid shape, to-all-grid-2x)')
                break
        for i, (u, why) in enumerate(tabs(o)):
            out.append(f'{pid}: tier {t["id"]} has a {why} {tuple(u)} (a 1 to 2 cell {why}; masses step in '
                       f'and out by more, to-all-grid-2x)')
            if i == 2:
                break
        if t.get('corners', 'rounded') not in CORNERS:
            out.append(f'{pid}: tier {t["id"]} corners {t["corners"]!r} (one of {", ".join(CORNERS)})')
        for p in t['outline']:
            if p[0] % GRID or p[1] % GRID:
                out.append(f'{pid}: tier {t["id"]} vertex {tuple(p)} off the {GRID} px grid')
            inside(p, f'tier {t["id"]} vertex')

    paths = {r['id']: r for r in plan.get('routes', []) + plan.get('trods', [])}
    stairs = plan.get('stairs', [])
    for wtr in plan.get('water', []):
        pts = wtr['points'] + (wtr['points'][:1] if wtr.get('closed') else [])
        if any(a[0] != b[0] and a[1] != b[1] for a, b in zip(pts, pts[1:])):
            out.append(f'{pid}: water {wtr["id"]} has an edge not along x or y (the grid shape)')
    for st in stairs:
        if st['width'] < STAIR_MIN:
            out.append(f'{pid}: stair {st["id"]} is {st["width"]} px wide (at least {STAIR_MIN})')
        if st['on'] not in paths:
            out.append(f'{pid}: stair {st["id"]} is on an unknown path {st["on"]}')
    for pth in paths.values():
        pts = pth['points']
        kind = 'route' if pth in plan.get('routes', []) else 'trod'
        ws = [pth['width']] + [wd for *_, wd in pth.get('widths', [])]
        for wd in ws:
            if not 24 <= wd <= 64 or wd % GRID:
                out.append(f'{pid}: {pth["id"]} width {wd} (24 to 64, whole cells)')
        for p in pts:
            inside(p, f'{pth["id"]} point')
        # the grid shape (Matt, 21 Oct 11:44, to-all-grid-2x): a path runs straight along x or y
        # and turns only at cell corners; this replaces benchmark 16's bend every 240 to 300 px
        for a, b in zip(pts, pts[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                out.append(f'{pid}: {pth["id"]} segment {tuple(a)} to {tuple(b)} is not along x or y')
                break
        if pth.get('kind') in SPANS:      # a bridge or causeway: on its own deck tier
            continue
        if pth.get('dead_end'):
            if pth['dead_end'] not in DEAD_ENDS:
                out.append(f'{pid}: {pth["id"]} ends in {pth["dead_end"]} (not a view, resident, bench or story)')
            if length(pts) < DEAD_MIN:
                out.append(f'{pid}: dead end {pth["id"]} is {length(pts):.0f} px (pockets need {DEAD_MIN} or more)')
        # tier changes along it: each on a stair, never along a face
        prev, face_run, last_xy = None, 0.0, None
        for x, y, d in sample(pts):
            t, f = G.at(x, y)
            if t is None:
                continue
            if f:
                face_run += 4
            else:
                if face_run > 0:
                    near = [st for st in stairs if st['on'] == pth['id'] and math.hypot(st['at'][0] - x, st['at'][1] - y) <= NEAR_STAIR + FACE]
                    if not near:
                        out.append(f'{pid}: {pth["id"]} crosses a face near ({x:.0f}, {y:.0f}) with no stair')
                    face_run = 0.0
                if prev is not None and t != prev:
                    near = [st for st in stairs if st['on'] == pth['id']
                            and math.hypot(st['at'][0] - x, st['at'][1] - y) <= NEAR_STAIR + FACE
                            and {st['from_tier'], st['to_tier']} == {t, prev}]
                    if not near:
                        out.append(f'{pid}: {pth["id"]} changes tier {prev} -> {t} near ({x:.0f}, {y:.0f}) '
                                   f'with no stair between them')
                prev = t
            last_xy = (x, y)
    for st in stairs:
        p = paths.get(st['on'])
        if p:
            # a stair cuts a south face, so it sits on a leg that runs north and south (eastward 6.1)
            legs = [(a, b) for a, b in zip(p['points'], p['points'][1:]) if dist_to_line(st['at'], [a, b]) <= 8]
            if legs and not any(a[0] == b[0] for a, b in legs):
                out.append(f'{pid}: stair {st["id"]} at {tuple(st["at"])} is on an east-west leg of {st["on"]}')
        if p and dist_to_line(st['at'], p['points']) > 8:
            out.append(f'{pid}: stair {st["id"]} at {tuple(st["at"])} is not on {st["on"]}')
        if st['at'][0] % 4 or st['at'][1] % 4:
            out.append(f'{pid}: stair {st["id"]} at {tuple(st["at"])} off the 4 px cells')

    all_lines = [p['points'] for p in paths.values()]
    # every trod joins the ways: it touches another path somewhere (an end on it, or a crossing),
    # or one of its ends lies on the box's edge
    for t in plan.get('trods', []):
        others = [q['points'] for q in paths.values() if q is not t]
        ends = (t['points'][0], t['points'][-1])
        on_edge = any(e[0] in (x0, x0 + w) or e[1] in (y0, y0 + h) for e in ends)
        touches = any(dist_to_line((x, y), ln) <= 8 for x, y, _ in sample(t['points'], 8) for ln in others)
        if not (on_edge or touches):
            out.append(f'{pid}: trod {t["id"]} touches no other path')

    def near_path(p):
        return min((dist_to_line(p, ln) for ln in all_lines), default=1e9)

    def on_ground(p, what):
        t, f = G.at(*p)
        if t is not None and f:
            out.append(f'{pid}: {what} at {tuple(p)} stands on a face')

    def clear_of_ways(p, what):
        for pth in paths.values():
            d = dist_to_line(p, pth['points'])
            if d < pth['width'] / 2 + 4:
                out.append(f'{pid}: {what} at {tuple(p)} stands on {pth["id"]} ({d:.0f} px from its line)')
        for st in stairs:
            if seg_len(p, st['at']) < st['width'] / 2 + 8:
                out.append(f'{pid}: {what} at {tuple(p)} stands on the stair {st["id"]}')

    for n in plan.get('named', []):
        inside(n['at'], n['thing'])
        on_ground(n['at'], n['thing'])
        clear_of_ways(n['at'], n['thing'])
        lim = BESIDE if n['where'] == 'beside the path' else OFF
        d = near_path(n['at'])
        if d > lim:
            out.append(f'{pid}: {n["thing"]} is {d:.0f} px from a path ({n["where"]}: at most {lim})')
    for pk in plan.get('pockets', []):
        inside(pk['at'], pk['holds'])
        on_ground(pk['at'], pk['holds'])
        tr = paths.get(pk['trod'])
        if not tr:
            out.append(f'{pid}: pocket {pk["holds"]} has no trod {pk["trod"]}')
        elif seg_len(tr['points'][-1], pk['at']) > 24:
            out.append(f'{pid}: pocket {pk["holds"]} is {seg_len(tr["points"][-1], pk["at"]):.0f} px from the end of its trod')
    for m in plan.get('markers', []):
        if not m.get('outside_box'):
            inside(m['at'], f'marker {m["what"]}')
            on_ground(m['at'], f'marker {m["what"]}')
            clear_of_ways(m['at'], f'marker {m["what"]}')
        if near_path(m['at']) > BESIDE:
            out.append(f'{pid}: marker {m["what"]} at {tuple(m["at"])} is {near_path(m["at"]):.0f} px from a path')
    for e in plan.get('egg_spots', []):
        for thing in plan.get('markers', []) + plan.get('named', []):
            if seg_len(thing['at'], e['at']) < e['keep_clear_r']:
                out.append(f'{pid}: {thing.get("what") or thing.get("thing")} stands on the egg spot {e["what"]}')
    # check 1: per screen of route, 2 interactables and 3 story props (the brief's markers)
    screens = sum(length(r['points']) for r in plan.get('routes', [])) / 576
    marks = [m for m in plan.get('markers', []) if not m.get('outside_box')]
    for t, per in (('I', 2), ('S', 3)):
        have = sum(1 for m in marks if m['t'] == t)
        if have < math.floor(per * screens):
            out.append(f'{pid}: {have} {"interactables" if t == "I" else "story props"} for {screens:.1f} screens '
                       f'of route (at least {per} a screen)')
    # per screen (an area of the plan): 2 interactables and 3 story props (check 1)
    for a in plan.get('areas', []):
        if a.get('walkable') is False:
            continue
        i_, s_ = area_counts(plan, a['rect'])
        if i_ < 2 or s_ < 3:
            out.append(f'{pid}: area {a["id"]} has {i_} interactables and {s_} story props (2 and 3 a screen)')
    obs = plan.get('obstacles', [])
    for i, a in enumerate(obs):
        if a.get('passed_by') and a['passed_by'] not in paths:
            out.append(f'{pid}: obstacle {a["kind"]} passed by an unknown path')
        for b in obs[i + 1:]:
            if seg_len(a['at'], b['at']) < OBSTACLE_GAP:
                out.append(f'{pid}: obstacles {a["kind"]} and {b["kind"]} are {seg_len(a["at"], b["at"]):.0f} px apart')
    for sp in plan.get('set_pieces', []):
        if sp['biome'] != plan['biome'] and sp['biome'] not in plan.get('biomes', []):
            out.append(f'{pid}: set piece {sp["piece"]} of biome {sp["biome"]} (this plan: {plan["biome"]})')
        if sp['piece'] not in LIBRARY and not sp.get('proposed'):
            out.append(f'{pid}: set piece {sp["piece"]} is not in the cliff core library (mark it proposed)')
        if sp['at'][0] % GRID or sp['at'][1] % GRID:
            out.append(f'{pid}: set piece {sp["piece"]} at {tuple(sp["at"])} off the grid')
        inside(sp['at'], f'set piece {sp["piece"]}')
    out += placement(plan) + reach(plan) + water_ends(plan) + crossings_declared(plan) + water_height(plan) + \
        rails_check(plan) + camps_check(plan)
    return out


def area_counts(plan: dict, rect) -> tuple:
    x, y, w, h = rect

    def inside(p):
        return x <= p[0] < x + w and y <= p[1] < y + h
    i_ = sum(1 for m in plan.get('markers', []) if m['t'] == 'I' and not m.get('outside_box') and inside(m['at']))
    i_ += sum(1 for n in plan.get('named', []) if n['kind'] in NAMED_INTERACT and inside(n['at']))
    s_ = sum(1 for m in plan.get('markers', []) if m['t'] == 'S' and not m.get('outside_box') and inside(m['at']))
    return i_, s_


DRESS_I = ('bench', 'signpost', 'water trough')
DRESS_S = ('cairn', 'standing stone', 'cairn', 'offering stone')


def dress(plan: dict) -> list:
    """Add dressing markers (`dress: true`) so each walkable area has 2 interactables and 3 story
    props, spread along the paths inside it and set off to their side; `fix` then settles them.
    Returns what was added."""
    paths = plan.get('routes', []) + plan.get('trods', [])
    added = []
    k = len(plan.get('markers', []))
    for a in plan.get('areas', []):
        if a.get('walkable') is False:
            continue
        x, y, w, h = a['rect']
        i_, s_ = area_counts(plan, a['rect'])
        pts = [(px, py, q) for q in paths for px, py, _ in sample(q['points'], 8)
               if x + 16 <= px < x + w - 16 and y + 16 <= py < y + h - 16]
        need = [('I', DRESS_I)] * max(0, 2 - i_) + [('S', DRESS_S)] * max(0, 3 - s_)
        if not pts or not need:
            continue
        for j, (t, kinds) in enumerate(need):
            px, py, q = pts[int((j + 0.5) * len(pts) / len(need))]
            side = 1 if (j + k) % 2 else -1
            at = [int(px + side * (q['width'] / 2 + 16)) // 4 * 4, int(py) // 4 * 4]
            m = {'t': t, 'what': kinds[(k + j) % len(kinds)], 'at': at, 'dress': True}
            plan['markers'].append(m)
            added.append((a['id'], m['what'], tuple(at)))
            k += 1
    return added


def grid_shape(outline, seed=0) -> list:
    """An outline turned into runs along x or y (each slanted edge becomes a step: along x then
    y, or y then x, whichever keeps the corner outside the shape more often), without repeats
    or points in the middle of a run."""
    out = []
    n = len(outline)
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        out.append(list(a))
        if a[0] != b[0] and a[1] != b[1]:
            out.append([b[0], a[1]] if (i + seed) % 2 == 0 else [a[0], b[1]])
    keep = []
    for i, q in enumerate(out):
        a, c = out[i - 1], out[(i + 1) % len(out)]
        if q == a or (a[0] == q[0] == c[0]) or (a[1] == q[1] == c[1]):
            continue
        keep.append(q)
    return keep


def simplify(pts, tol):
    """Douglas-Peucker: the fewest points within tol px of the line."""
    if len(pts) < 3:
        return list(pts)
    a, b = pts[0], pts[-1]
    best, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = dist_to_line(pts[i], [a, b])
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [a, b]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def grid_path(pts, tol=20) -> list:
    """A path turned into long runs along x or y: simplified to within tol px, each slanted
    segment then becomes a step (along its longer axis first), points snapped to the 8 px
    grid, repeats and mid-run points dropped."""
    pts = simplify([list(p) for p in pts], tol) if any(a[0] != b[0] and a[1] != b[1] for a, b in zip(pts, pts[1:])) else pts
    q = [[int(round(x / GRID)) * GRID, int(round(y / GRID)) * GRID] for x, y in pts]
    out = [q[0]]
    for a, b in zip(q, q[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            out.append([b[0], a[1]] if abs(b[0] - a[0]) >= abs(b[1] - a[1]) else [a[0], b[1]])
        out.append(b)
    keep = [out[0]]
    for i in range(1, len(out) - 1):
        a, b, c = keep[-1], out[i], out[i + 1]
        if b == a or (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
            continue
        keep.append(b)
    if out[-1] != keep[-1]:
        keep.append(out[-1])
    return keep


def crossings(plan: dict, G: 'Ground', pth: dict) -> list:
    """Where a path crosses a face: (x, y, tier before, tier after) at the middle of each run of
    face samples along it."""
    out, prev, run = [], None, []
    for x, y, _ in sample(pth['points']):
        t, f = G.at(x, y)
        if t is None:
            continue
        if f:
            run.append((x, y))
            continue
        if run and prev is not None and t != prev:
            mx, my = run[len(run) // 2]
            out.append((int(mx) // 4 * 4, int(my) // 4 * 4, prev, t))
        run = []
        prev = t
    return out


def seat_stairs(plan: dict) -> list:
    """Move each stair to the nearest crossing of its path between its two tiers. Returns what
    moved."""
    G = Ground(plan)
    paths = {r['id']: r for r in plan.get('routes', []) + plan.get('trods', [])}
    moved, used = [], set()
    for st in plan.get('stairs', []):
        pth = paths.get(st['on'])
        if not pth:
            continue
        want = {st['from_tier'], st['to_tier']}
        cands = [c for c in crossings(plan, G, pth) if {c[2], c[3]} == want and (pth['id'], c[0], c[1]) not in used]
        if not cands:
            continue
        c = min(cands, key=lambda c: seg_len(c[:2], st['at']))
        used.add((pth['id'], c[0], c[1]))
        if [c[0], c[1]] != list(st['at']):
            moved.append((st['id'], tuple(st['at']), (c[0], c[1])))
            st['at'] = [c[0], c[1]]
    return moved


def fix(plan: dict) -> list:
    """Move each marker, named thing and pocket that breaks a placement rule to the nearest
    point that keeps them all (walkable ground, beside its path but off it, off stairs, 16 px
    from the next thing), searching 4 px steps up to 96 px away. The brief's point is kept as
    moved_from. Returns what moved."""
    G = Ground(plan)
    paths = plan.get('routes', []) + plan.get('trods', [])
    stairs = plan.get('stairs', [])
    things = [('named', n) for n in plan.get('named', [])] + \
        [('marker', m) for m in plan.get('markers', []) if not m.get('outside_box')]
    moved = []

    def ok(x, y, lim, me):
        t, f = G.at(x, y)
        if t is None or f:
            return False
        ds = [(dist_to_line((x, y), q['points']), q['width']) for q in paths]
        if any(d < w / 2 + 6 for d, w in ds) or min(d for d, _ in ds) > lim:
            return False
        if any(seg_len((x, y), st['at']) < st['width'] / 2 + 10 for st in stairs):
            return False
        return all(o is me or seg_len((x, y), o['at']) >= 16 for _, o in things)
    for kind, th in things:
        lim = BESIDE if kind == 'marker' or th.get('where') == 'beside the path' else OFF
        x0, y0 = th['at']
        if ok(x0, y0, lim, th):
            continue
        best = None
        for dx in range(-96, 97, 4):
            for dy in range(-96, 97, 4):
                d = math.hypot(dx, dy)
                if (best is None or d < best[0]) and ok(x0 + dx - x0 % 4, y0 + dy - y0 % 4, lim, th):
                    best = (d, [x0 + dx - x0 % 4, y0 + dy - y0 % 4])
        if best:
            th.setdefault('moved_from', [x0, y0])
            th['at'] = best[1]
            moved.append((th.get('what') or th.get('thing'), (x0, y0), tuple(best[1])))
    return moved


def summary(plan: dict) -> str:
    paths = plan.get('routes', []) + plan.get('trods', [])
    L = sum(length(p['points']) for p in plan.get('routes', []))
    i = sum(1 for m in plan.get('markers', []) if m['t'] == 'I')
    s = sum(1 for m in plan.get('markers', []) if m['t'] == 'S')
    return (f'{plan["id"]}: {len(plan.get("tiers", []))} tiers, {len(paths)} paths ({L:.0f} px of route, '
            f'{L / 576:.1f} screens), {len(plan.get("stairs", []))} stairs, {len(plan.get("named", []))} named, '
            f'{len(plan.get("pockets", []))} pockets, markers I {i} S {s}, {len(plan.get("set_pieces", []))} set pieces')


# --- the picture ---------------------------------------------------------------------------

TIER_COL = [(176, 196, 120), (150, 132, 150), (126, 104, 126), (104, 84, 108), (88, 70, 96), (190, 200, 214),
            (210, 218, 228), (226, 232, 238), (240, 244, 248)]


def draw(plan: dict, scale: int = 4) -> Image.Image:
    G = Ground(plan)
    x0, y0, w, h = plan['box']
    k = G.s / scale
    H, W = G.tier.shape
    rgb = np.zeros((H, W, 3), np.uint8)
    for t in range(int(G.tier.max()) + 1):
        rgb[G.tier == t] = TIER_COL[min(t, len(TIER_COL) - 1)]
    rgb[G.face] = (70, 52, 60)
    img = Image.fromarray(rgb).resize((int(W * k), int(H * k)), Image.NEAREST)
    d = ImageDraw.Draw(img)

    def P(p):
        return ((p[0] - x0) / scale, (p[1] - y0) / scale)
    for wtr in plan.get('water', []):
        if len(wtr['points']) > 2 and wtr.get('closed'):
            d.polygon([P(p) for p in wtr['points']], fill=(80, 130, 190))
        else:
            d.line([P(p) for p in wtr['points']], fill=(80, 130, 190), width=max(1, int(wtr.get('width', 16) / scale)))
    for r in plan.get('routes', []):
        d.line([P(p) for p in r['points']], fill=(214, 178, 120), width=max(1, int(r['width'] / scale)))
    for r in plan.get('trods', []):
        d.line([P(p) for p in r['points']], fill=(230, 210, 170), width=max(1, int(r['width'] / scale)))
    for st in plan.get('stairs', []):
        x, y = P(st['at'])
        d.rectangle([x - 5, y - 3, x + 5, y + 3], fill=(250, 250, 250), outline=(20, 20, 20))
    for sp in plan.get('set_pieces', []):
        x, y = P(sp['at'])
        d.rectangle([x - 3, y - 3, x + 3, y + 3], outline=(255, 120, 40))
    for n in plan.get('named', []):
        x, y = P(n['at'])
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(240, 60, 60))
    for pk in plan.get('pockets', []):
        x, y = P(pk['at'])
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(60, 200, 240))
    for m in plan.get('markers', []):
        x, y = P(m['at'])
        c = {'I': (255, 255, 255), 'S': (30, 30, 30), 'A': (250, 220, 60)}[m['t']]
        d.point([(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)], fill=c)
    for e in plan.get('egg_spots', []):
        x, y = P(e['at'])
        r = e['keep_clear_r'] / scale
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 0, 255))
    return img


def main(argv) -> int:
    if '--fix' in argv or '--dress' in argv or '--grid' in argv:
        for pid in [a for a in argv if a in plan_ids()] or plan_ids():
            p = load(pid)
            if '--grid' in argv:
                for t in p.get('tiers', []):
                    t['outline'] = detab(grid_shape(t['outline']))
                for r in p.get('routes', []) + p.get('trods', []):
                    r['points'] = grid_path(r['points'])
                for wtr in p.get('water', []):
                    wtr['points'] = grid_shape(wtr['points']) if wtr.get('closed') else grid_path(wtr['points'])
            if '--dress' in argv:
                for area, what, at in dress(p):
                    print(f'{pid}: dressed {area} with a {what} at {at}')
            for sid, a, b in seat_stairs(p):
                print(f'{pid}: seated stair {sid} from {a} at {b}')
            for what, a, b in fix(p):
                print(f'{pid}: moved {what} from {a} to {b}')
            with open(os.path.join(PLANS, f'{pid}.json'), 'w') as fh:
                json.dump(p, fh, indent=1)
                fh.write('\n')
        return 0
    if '--check' in argv:
        faults = []
        plans = [load(pid) for pid in plan_ids()]
        routes = g_routes()
        if not routes:
            print('note: lane G routes could not be read (node + tsx); edge meets use the other plans only')
        for p in plans:
            faults += check(p)
            faults += edge_meets(p, [o for o in plans if o is not p], routes)
            print(summary(p))
            for nt in variety(p):
                print('note', nt)
        faults += shared_rails(plans)
        for f in faults:
            print('FAULT', f)
        print(f'{"ok" if not faults else "FAIL"} region plans: {len(plan_ids())} plans, {len(faults)} faults')
        return 1 if faults else 0
    args = [a for a in argv if not a.startswith('--')]
    out = args[0] if args and not args[0] in plan_ids() else os.path.join(tempfile.gettempdir(), 'napattack-region-plans')
    ids = [a for a in args if a in plan_ids()] or plan_ids()
    os.makedirs(out, exist_ok=True)
    for pid in ids:
        p = load(pid)
        draw(p).save(os.path.join(out, f'{pid}.png'))
        print(summary(p))
        for f in check(p):
            print('  FAULT', f)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
