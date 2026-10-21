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
- inside the box: every outline, route, place, named thing, pocket and marker, unless it is
  marked outside_box (a marker the brief lists just past the line);
- paths: widths 24 to 64 (check 17); no straight run longer than 240 px and a bend at least
  every 300 px along routes (check 16); dead ends of 80 px or more end in a view, a resident, a
  bench or a story detail (check 20);
- tiers: a path that crosses from one tier to another does so on a stair at least 34 px wide
  within 24 px of the crossing (checks 19, 21; eastward 6.3: no ramps), and never walks along a
  face; a stair's tiers match the ground either side of it;
- things: named things, pockets and markers stand on walkable ground (a tier top, not a face),
  'beside the path' within 48 px of a path, 'a short way off' within 160; a pocket at the end
  of its trod; egg spots clear of every marker and named thing;
- things stand beside their path, not on it or on a stair;
- check 1: the markers give each screen of route 2 interactables and 3 story props;
- obstacles at least 800 px apart (brief 7); set pieces of this biome only, on the 8 px grid.

Run:
    python3 scripts/art/region_plan.py --check            (every plan; exits non-zero on a fault)
    python3 scripts/art/region_plan.py --fix [ids..]      (moves things that break a placement rule
                                                          to the nearest point that keeps them)
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
STRAIGHT_MAX = 240
BEND_EVERY = 300
BEND_DEG = 12
DEAD_MIN = 80
OBSTACLE_GAP = 800
DEAD_ENDS = {'view', 'resident', 'bench', 'story'}


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


def straight_runs(pts) -> list:
    """Lengths of the runs between bends of BEND_DEG or more."""
    runs, cur = [], 0.0
    for i in range(len(pts) - 1):
        cur += seg_len(pts[i], pts[i + 1])
        if i + 2 < len(pts):
            a = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
            b = math.atan2(pts[i + 2][1] - pts[i + 1][1], pts[i + 2][0] - pts[i + 1][0])
            d = abs((math.degrees(b - a) + 180) % 360 - 180)
            if d >= BEND_DEG:
                runs.append(cur)
                cur = 0.0
    runs.append(cur)
    return runs


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
        for p in t['outline']:
            if p[0] % GRID or p[1] % GRID:
                out.append(f'{pid}: tier {t["id"]} vertex {tuple(p)} off the {GRID} px grid')
            inside(p, f'tier {t["id"]} vertex')

    paths = {r['id']: r for r in plan.get('routes', []) + plan.get('trods', [])}
    stairs = plan.get('stairs', [])
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
        runs = straight_runs(pts)
        if max(runs) > STRAIGHT_MAX:
            out.append(f'{pid}: {pth["id"]} runs straight for {max(runs):.0f} px (at most {STRAIGHT_MAX})')
        if kind == 'route' and length(pts) > BEND_EVERY and max(runs) > BEND_EVERY:
            out.append(f'{pid}: {pth["id"]} has no bend for {max(runs):.0f} px')
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
        if p and dist_to_line(st['at'], p['points']) > 8:
            out.append(f'{pid}: stair {st["id"]} at {tuple(st["at"])} is not on {st["on"]}')
        if st['at'][0] % 4 or st['at'][1] % 4:
            out.append(f'{pid}: stair {st["id"]} at {tuple(st["at"])} off the 4 px cells')

    all_lines = [p['points'] for p in paths.values()]

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
        if sp['at'][0] % GRID or sp['at'][1] % GRID:
            out.append(f'{pid}: set piece {sp["piece"]} at {tuple(sp["at"])} off the grid')
        inside(sp['at'], f'set piece {sp["piece"]}')
    return out


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
    if '--fix' in argv:
        for pid in [a for a in argv if a in plan_ids()] or plan_ids():
            p = load(pid)
            for what, a, b in fix(p):
                print(f'{pid}: moved {what} from {a} to {b}')
            with open(os.path.join(PLANS, f'{pid}.json'), 'w') as fh:
                json.dump(p, fh, indent=1)
                fh.write('\n')
        return 0
    if '--check' in argv:
        faults = []
        for pid in plan_ids():
            p = load(pid)
            faults += check(p)
            print(summary(p))
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
