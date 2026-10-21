"""The asset ledger (docs/vision/asset-ledger.md): which old art may go into the new world.

Matt, 20 Oct 20:16: "can u make sure no old assets are reused that dont fit the soft grid,
level of detail etc. established for the newest version". Every picture the game ships
(everything under assets/) is listed in scripts/art/asset_ledger.json with a grade:

- KEEP     fits the newest standard on every check below; a kit or region build may use it.
- REWORK   the subject stays in the new world, the art must be redone first (the entry says
           which checks fail and whether the fix is a redraw or a mechanical pass).
- RETIRE   the picture has no place in the new world (old zone ground and scenery, which the
           regions are rebuilt over on the soft grid; sprites the prop audit dropped; art a
           merged or open PR removes).

The checks, per sprite, measured at 1x (each PNG brought back to its native pixel grid):

- grid    a built thing's foot line (its lowest 4 rows) spans whole 8 px cells: 8n px, or 8n + 1
          or 8n + 2 with its outline, or 8n - 1 (soft-grid rule 4: big props span whole cells);
          vegetation, people, animals and parts are free. No module declares FOOT yet, so this
          reads the pixels; once FOOT is declared the declaration is checked instead.
- size    size_check.py: the drawn box inside its kind's height and width ranges.
- bar     detail_bar.py on the largest solid square inside the sprite (at most 96 px, the
          outline ring left out), against the reference kind for what it is, with the house
          rulings (house-style.md 7): tones at 85 % when the art is ramp-built, shapes and
          dressing at 90 %, and both cleanliness tests. A sprite with no solid 18 px square is
          too small for a 16 px patch: its detail counts only if the prop audit passed it by eye.
- style   style_lint.py: palette (on the house palette, or on today's ramps that the one
          decided recolour maps onto it), colour budget, outline (dark, the material's edge tone
          not one flat ink, not doubled), light from the west, speckle and dither.
- logic   the prop audit (prop-logic.md 10, PR #97): KEEP passes; ADJUST and REDRAW are faults
          (re-checked by eye when the sprite changed since); DROP retires; a sprite missing
          from the audit is a doubt, so it fails until someone checks it by eye and writes the
          verdict into its `eye` field.

Grounds and scenery of the old zones are RETIRE by rule (the regions are rebuilt on the
soft grid from docs/vision/regions/); their lint numbers are stored to show why.

    python3 scripts/art/asset_ledger.py --build [--audit docs/vision/prop-logic.md] [--date D]
    python3 scripts/art/asset_ledger.py --report OUT.png      # contact sheets per lane
    python3 scripts/art/asset_ledger.py --summary             # tables for the doc and the PR
    python3 scripts/art/asset_ledger.py --lanes               # what each lane must redo
    python3 scripts/art/asset_ledger.py --redo PATH ...       # re-measure some assets in place

A by-eye verdict (`eye`) written into an entry survives a rebuild: use it to mark a logic
fault fixed or a cloth or open structure checked by eye (house-style 7 rulings).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
LEDGER = os.path.join(HERE, 'asset_ledger.json')
IMAGE_EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
BAR_DATE = '2026-10-20T01:24:00+01:00'      # Matt: "it has to be reached" (art-style.md)
AUDIT_DATE = '2026-10-20T00:09:34+01:00'    # the prop audit's main, 9175f1e
SQUARE_MIN, SQUARE_MAX = 18, 96
TONES_RAMP, TONES, SHAPES, DRESSING = 0.85, 0.9, 0.9, 0.9
FOOT_RESIDUES = (7, 0, 1, 2)                # a foot of n cells: 8n px, plus the 1 px outline each side, or 1 short

# Who owns what (coherence-plan.md, "Who does what"). Generators the table does not name
# (battle, worlds, vignettes, mission_map, scenery) fall to Claude A, the world lane.
MODULE_OWNER = {
    'frost_props': 'A', 'zones': 'A', 'frost_zones': 'A', 'scenery': 'A', 'journey': 'A', 'battle': 'A',
    'worlds': 'A', 'vignettes': 'A', 'mission_map': 'A', 'map_tiles': 'A',
    'world_props': 'B', 'valley_props': 'B', 'harbour_props': 'B', 'home_props': 'B', 'garden_props': 'B',
    'garden': 'B', 'garden_meadow': 'B', 'decor': 'B', 'home_zones': 'B',
    'steampunk_props': 'C', 'cyber_props': 'C', 'isle_props': 'C', 'isle_zones': 'C', 'city_zones': 'C',
    'western_props': 'D', 'caldera_props': 'D', 'castle_props': 'D', 'space_props': 'D',
    'sunstone_zones': 'D', 'space_zones': 'D',
    'valley_zones': 'E',
}
UNASSIGNED = {'battle', 'worlds', 'vignettes', 'mission_map', 'scenery'}

# Which module draws which zone, and what the region briefs (docs/vision/regions/, PR #96)
# do with the place. The ground picture retires either way; a kept place is rebuilt there.
ZONES = {
    'hollow': ('frost_zones', 'kept, placed'), 'snowmelt': ('frost_zones', 'kept, placed'),
    'saddle': ('frost_zones', 'kept, placed'), 'summit': ('frost_zones', 'kept, placed'),
    'ridge': ('valley_zones', 'kept, placed'), 'woodland': ('valley_zones', 'kept, redrawn'),
    'riverside': ('valley_zones', 'kept, redrawn'), 'park': ('valley_zones', 'kept, redrawn'),
    'town': ('valley_zones', 'replaced by Crossroads'), 'halt': ('valley_zones', 'replaced by the halt farm'),
    'harbour': ('valley_zones', 'replaced by Driftwood'), 'headland': ('valley_zones', 'kept, walled'),
    'junction': ('city_zones', 'replaced by the station square'), 'canal': ('city_zones', 'kept, sunk'),
    'market': ('city_zones', 'kept, placed'), 'docks': ('city_zones', 'kept, placed'),
    'waterfront': ('city_zones', 'replaced'), 'heights': ('city_zones', 'replaced by terrace blocks'),
    'skyport': ('city_zones', 'kept, placed'), 'neon': ('city_zones', 'kept, placed'),
    'downtown': ('city_zones', 'replaced'), 'plaza': ('city_zones', 'replaced by Neon Square'),
    'point': ('city_zones', 'replaced by the Gull Strand'),
    'landing': ('isle_zones', 'kept'), 'rainforest': ('isle_zones', 'kept'),
    'headwaters': ('isle_zones', 'kept'), 'cove': ('isle_zones', 'kept'),
    'gulch': ('sunstone_zones', 'kept, placed'), 'oasis': ('sunstone_zones', 'kept, placed'),
    'hearthold': ('sunstone_zones', 'kept, placed'), 'springs': ('sunstone_zones', 'kept, placed'),
    'scorch': ('sunstone_zones', 'replaced by the ash fields'), 'caldera': ('sunstone_zones', 'replaced by the Ember forge'),
    'station': ('space_zones', 'later (P7), no brief yet'), 'lumen': ('space_zones', 'later (P7), no brief yet'),
    'home': ('home_zones', 'the hut inside, kept'), 'garden': ('garden', 'kept: the home hub'),
}
ZONE_FN = {'hearthold': 'castle', 'landing': 'isle_landing', 'rainforest': 'isle_rainforest',
           'headwaters': 'isle_headwaters', 'cove': 'isle_cove', 'heights': 'city_heights', 'plaza': 'city_plaza',
           'waterfront': 'city_waterfront', 'market': 'city_market', 'downtown': 'city_downtown', 'docks': 'city_docks',
           'point': 'city_point', 'neon': 'city_neon'}


def soft_grid_zone(zone: str, module: str) -> bool:
    """Whether the zone's function builds its ground with the terrace toolkit (tiers with south
    faces and side bands on the 8 px grid: terrace.build), read from its source."""
    try:
        src = open(os.path.join(HERE, f'{module}.py')).read()
    except OSError:
        return False
    if not re.search(r'^import terrace\b|^from terrace import', src, re.M):
        return False
    fn = ZONE_FN.get(zone, zone)
    m = re.search(rf'^def {fn}\(.*?(?=^def |\Z)', src, re.M | re.S)
    return bool(m and re.search(r'\b(T|terrace)\.build\(', m.group(0)))


BEYOND = {'beyond': 'zones', 'beyond-sea': 'zones', 'beyond-peaks': 'zones', 'beyond-dunes': 'sunstone_zones',
          'beyond-ash': 'sunstone_zones', 'beyond-regolith': 'space_zones'}

# Sprites outside assets/zones/props that are the same subject as a zone sprite.
RESIDENT_OWNER = {**{n: 'A' for n in ('warden', 'skater')},
                  **{n: 'C' for n in ('tinkerer', 'boatwoman', 'vendor', 'courier', 'porter', 'seller', 'docker',
                                      'stroller', 'ferryman', 'naturalist', 'beachcomber')},
                  **{n: 'D' for n in ('steward', 'cowhand', 'saloon', 'trader', 'prospector', 'smith', 'attendant',
                                      'botanist', 'stargazer')},
                  **{n: 'E' for n in ('gardener', 'baker', 'fisher', 'keeper', 'farmer', 'hiker', 'forager',
                                      'picnicker', 'miller', 'angler')}}

# What the detail bar compares a sprite with (detail_bar.py kinds), from the size guide's kind.
BAR_BY_KIND = {
    **{k: 'tree' for k in ('broadleaf', 'young_tree', 'sapling', 'veteran_tree', 'birch', 'willow', 'conifer', 'palm',
                           'small_palm', 'acacia', 'bush', 'fern', 'tall_plant', 'flowers', 'cactus', 'small_cactus')},
    **{k: 'stone-wall' for k in ('rock', 'boulder', 'crag', 'standing_stone', 'cairn', 'well', 'fountain', 'low_wall',
                                 'fireplace', 'keep', 'gatehouse', 'castle_tower', 'postern', 'curtain_wall', 'shrine',
                                 'planter')},
    **{k: 'wood-front' for k in ('stump', 'log', 'woodpile', 'bench', 'bench_side', 'crate', 'crate_stack', 'barrel', 'keg',
                                 'chest', 'stall', 'food_stall', 'cart_stall', 'furniture_low', 'furniture_table', 'cupboard',
                                 'tall_furniture', 'bed', 'armchair', 'seat', 'cafe_set', 'trough', 'rail', 'barrier', 'fence',
                                 'gate', 'rowing_boat', 'canoe', 'sailboat', 'narrowboat', 'net_rack', 'false_front',
                                 'smithy', 'barn', 'shed', 'boathouse', 'hut', 'wagon', 'handcart', 'sign', 'tall_sign',
                                 'beehive', 'training')},
    **{k: 'machinery' for k in ('lamp', 'lantern_post', 'post', 'bollard', 'pole', 'vending', 'appliance', 'small_machine',
                                'car', 'van', 'truck', 'tram', 'locomotive', 'railcar', 'tub', 'launch', 'ferry',
                                'container_stack', 'anchor', 'buoy', 'telescope', 'grow_pod', 'bin', 'module', 'lander',
                                'shuttle', 'dome', 'lunar_habitat', 'crane', 'mast', 'gantry_crane', 'windpump',
                                'water_tower', 'industrial', 'vent', 'jar')},
    **{k: 'facade' for k in ('cottage', 'house', 'farmhouse', 'water_mill', 'windmill', 'tower', 'landmark_tower', 'civic',
                             'shop', 'town_house', 'workshop', 'warehouse', 'station_building', 'signal_box', 'adobe',
                             'city_building', 'kiosk', 'pavilion', 'shelter')},
}
BY_EYE_KINDS = {'tent', 'sack', 'pile', 'bale', 'haystack', 'scarecrow', 'snowman', 'washing_line', 'campfire', 'hammock',
                'resident', 'figure', 'horse', 'cow', 'camel', 'camel_lying', 'sheep', 'lamb', 'ibex', 'small_animal',
                'heron', 'turtle', 'snag'}
OPEN_KINDS = {'crane', 'mast', 'gantry_crane', 'windpump', 'pole', 'fence', 'rail', 'barrier', 'gate', 'net_rack'}
GRID_FREE_GROUPS = {'nature', 'people and animals'}

# Pictures generated from other pictures, graded by where they come from rather than one by one.
RULES = [
    {'glob': 'assets/world/**', 'grade': 'RETIRE', 'owner': 'A', 'fix': 'none',
     'why': ('the world canvas (PR #123, #126): tiles cut by world_canvas.py from the old zones\' grounds, which retire; '
             'a plane is re-graded when its region is rebuilt on the soft grid and its tiles are cut from the new ground')},
]

# Pictures removed by an open PR, with why (RETIRE).
REMOVED = {'assets/journeys/capsule.png': 'the space elevator\'s capsule: the rocket replaces the space elevator (PR #131)'}


# ---------------------------------------------------------------------------------------- helpers

def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, '/')


def native(img: Image.Image) -> tuple[Image.Image, int]:
    """The picture on its own pixel grid: the largest s for which it is made of s x s blocks."""
    a = np.asarray(img.convert('RGBA'))
    for s in (8, 4, 3, 2):
        if a.shape[0] % s or a.shape[1] % s:
            continue
        sub = a[::s, ::s]
        if np.array_equal(np.repeat(np.repeat(sub, s, 0), s, 1), a):
            return Image.fromarray(sub, 'RGBA'), s
    return img.convert('RGBA'), 1


def git_last_changes(paths: list[str]) -> dict:
    """Each asset's last commit on this checkout: (short sha, ISO date, subject)."""
    out = {}
    try:
        log = subprocess.run(['git', 'log', '--format=@%h\t%cI\t%s', '--name-only', '--', 'assets'],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return out
    want, cur = set(paths), None
    for line in log.splitlines():
        if line.startswith('@'):
            cur = tuple(line[1:].split('\t', 2))
        elif line and line in want and line not in out:
            out[line] = cur
    return out


def _after(iso: str | None, ref: str) -> bool:
    if not iso:
        return False
    return datetime.datetime.fromisoformat(iso) > datetime.datetime.fromisoformat(ref)


# ---------------------------------------------------------------------------------------- the audit

def _expand(names_cell: str, module_names: list[str]) -> list[str]:
    """`a`, `_b`, `x` to `y` (n), `stall` a to d  ->  the sprite names the audit row means."""
    have = set(module_names)
    toks = re.findall(r'`([^`]+)`|(\ba to d\b)|(\bto\b)', names_cell)
    out, last_full, pending_to = [], None, False
    for tick, atod, to in toks:
        if atod:
            out += [f'{last_full}_{s}' for s in 'bcd' if f'{last_full}_{s}' in have]
            continue
        if to:
            pending_to = True
            continue
        name = tick
        if name.startswith('_') and last_full:
            parts = last_full.split('_')
            for k in range(len(parts), 0, -1):
                cand = '_'.join(parts[:k]) + name
                if cand in have:
                    name = cand
                    break
            else:
                name = last_full + name
        else:
            last_full = name
        if pending_to and out:
            def key(n):
                return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', n)]
            ordered = sorted(have, key=key)
            a, b = out[-1], name
            if a in ordered and b in ordered:
                i, j = ordered.index(a), ordered.index(b)
                out += ordered[i + 1:j + 1]
            else:
                out.append(name)
            pending_to = False
            continue
        out.append(name)
    return out


def read_audit(path: str, names_by_module: dict) -> dict:
    """prop-logic.md 10c as {(module, sprite): {grade, why, fix, owner}}."""
    rows, owner = {}, None
    with open(path) as f:
        text = f.read()
    sec = text.split('### c. The audit table', 1)[1].split('### d.', 1)[0]
    for line in sec.splitlines():
        m = re.match(r'#### Claude ([A-E])', line)
        if m:
            owner = m.group(1)
            continue
        if not line.startswith('| `'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 5:
            continue
        names, module, grade, why, fix = cells[:5]
        for n in _expand(names, names_by_module.get(module, [])):
            rows[(module, n)] = {'grade': grade, 'why': why, 'fix': fix, 'owner': owner}
    return rows


# ---------------------------------------------------------------------------------------- measures

def _style():
    import style_lint
    return style_lint


def sprite_style(img1: Image.Image) -> dict:
    sl = _style()
    m = sl.measure(img1)
    if not m:
        return {}
    misses = sl.misses(m)
    palette = 'house' if m['on_house'] >= sl.ON_HOUSE_MIN else 'recolour' if m['on_today'] >= sl.ON_HOUSE_MIN else 'off'
    if palette == 'recolour' and 'palette' in misses:
        misses.remove('palette')
    out = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}
    out['palette'] = palette
    out['misses'] = misses
    return out


def box_of(img1: Image.Image) -> tuple[int, int]:
    a = np.asarray(img1)[..., 3] >= 128
    ys, xs = np.nonzero(a)
    if not len(ys):
        return 0, 0
    return int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1)


def foot_width(img1: Image.Image) -> int:
    a = np.asarray(img1)[..., 3] >= 128
    ys = np.nonzero(a.any(1))[0]
    if not len(ys):
        return 0
    y1 = ys.max()
    rows = a[max(0, y1 - 3):y1 + 1]
    xs = np.nonzero(rows.any(0))[0]
    return int(xs.max() - xs.min() + 1)


def largest_square(img1: Image.Image):
    """(x, y, side) of the largest square of fully opaque pixels, the outline ring left out."""
    from scipy.ndimage import binary_erosion
    a = np.asarray(img1)[..., 3] == 255
    a = binary_erosion(a, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    h, w = a.shape
    dp = np.zeros((h + 1, w + 1), np.int32)
    best = (0, 0, 0)
    for y in range(h):
        row, prev, cur = a[y], dp[y], dp[y + 1]
        for x in range(w):
            if row[x]:
                v = 1 + min(prev[x], prev[x + 1], cur[x])
                cur[x + 1] = v
                if v > best[2]:
                    best = (int(x - v + 1), int(y - v + 1), int(v))
    return best


def sprite_bar(img1: Image.Image, bar_kind: str | None, ramp_built: bool) -> dict:
    if not bar_kind:
        return {'status': 'by eye', 'why': 'no reference kind for this subject (house-style 7: by eye)'}
    x, y, s = largest_square(img1)
    if s < SQUARE_MIN:
        return {'status': 'n/a', 'kind': bar_kind, 'square': s,
                'why': f'no solid {SQUARE_MIN} px square (largest {s}): too small for a 16 px patch'}
    s2 = min(s, SQUARE_MAX)
    x0, y0 = x + (s - s2) // 2, y + (s - s2) // 2
    box = (x0, y0, x0 + s2, y0 + s2)
    import detail_bar as db
    ref = db.bar(bar_kind)
    try:
        _ok, ours, _lines = db.check_image(img1.convert('RGB'), box, bar_kind)
    except ValueError as e:
        return {'status': 'n/a', 'kind': bar_kind, 'square': s, 'why': str(e)}
    tf = TONES_RAMP if ramp_built else TONES
    low = [m for m, f in (('tones', tf), ('shapes', SHAPES), ('dressing', DRESSING)) if ours[m] < f * ref[m]]
    noisy = []
    if ours['isolated'] > ref['isolated'] + db.ISOLATED_MARGIN:
        noisy.append('isolated')
    if ours['cluster'] < db.CLUSTER_SHARE * ref['cluster']:
        noisy.append('cluster')
    r = {'status': 'pass' if not (low or noisy) else 'fail', 'kind': bar_kind, 'box': list(box),
         'patches': ours['patches'], 'tones_at': tf,
         **{m: [ours[m], round(ref[m], 2)] for m in ('tones', 'shapes', 'dressing', 'isolated', 'cluster')}}
    if low:
        r['low'] = low
    if noisy:
        r['noisy'] = noisy
    return r


def ground_numbers(img1: Image.Image) -> dict:
    """Cleanliness and palette of an opaque picture (a ground, a scenery cell), with numpy."""
    a = np.asarray(img1.convert('RGBA')).astype(np.int32)
    solid = a[..., 3] == 255
    key = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    key = np.where(solid, key, -1)
    p = np.pad(key, 1, constant_values=-2)
    c = p[1:-1, 1:-1]
    n4 = [p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]
    d4 = [p[:-2, :-2], p[2:, 2:], p[:-2, 2:], p[2:, :-2]]
    inner = solid & np.all([k >= 0 for k in n4], axis=0)
    lone = inner & np.all([k != c for k in n4], axis=0)
    chk = lone & np.all([k == c for k in d4], axis=0)
    with open(os.path.join(ROOT, 'art', 'materials.json')) as f:
        mats = json.load(f)
    today = {int(h.lstrip('#')[:6], 16) for r in mats['materials'].values() for h in r}
    vals, counts = np.unique(key[solid], return_counts=True)
    on_today = sum(int(n) for v, n in zip(vals, counts) if int(v) in today) / max(1, int(solid.sum()))
    return {'px': int(solid.sum()), 'colours': int(len(vals)), 'on_today': round(on_today, 3),
            'isolated': round(float(lone.sum() / max(1, inner.sum())), 3),
            'checker': round(float(chk.sum() / max(1, inner.sum())), 4)}


# Which region brief takes over each of today's zones (docs/vision/regions/, PR #96).
REGION_LANE = {**{z: 'E' for z in ('garden', 'ridge', 'hollow', 'saddle', 'snowmelt', 'summit', 'woodland', 'riverside',
                                   'town', 'park', 'halt', 'harbour', 'headland')},
               **{z: 'C' for z in ('junction', 'canal', 'market', 'docks', 'waterfront', 'heights', 'skyport', 'neon',
                                   'downtown', 'plaza', 'point', 'landing', 'rainforest', 'headwaters', 'cove')},
               **{z: 'D' for z in ('gulch', 'oasis', 'scorch', 'hearthold', 'caldera', 'springs', 'station', 'lumen')},
               'home': 'B'}


def placements() -> dict:
    """{sprite: {zone: count}} from lib/zone-maps.ts (zoneMaps' objects)."""
    try:
        src = open(os.path.join(ROOT, 'lib', 'zone-maps.ts')).read()
    except OSError:
        return {}
    i = src.find('export const zoneMaps')
    if i < 0:
        return {}
    j = src.find('\nexport const', i + 10)
    out: dict = {}
    cur = None
    for line in src[i:j if j > 0 else None].splitlines():
        m = re.match(r'^  ([a-z]+): \{', line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"^\s+\['[^']*', '([a-z_0-9]+)', -?\d+", line)
        if m and cur:
            z = out.setdefault(m.group(1), {})
            z[cur] = z.get(cur, 0) + 1
    return out


# ---------------------------------------------------------------------------------------- inventory

def inventory() -> list[dict]:
    """Every picture under assets/, gathered into ledger entries (a sprite with its frames, a
    resident with its eight frames, a zone with its ground and data pictures)."""
    files = []
    for dp, _dn, fn in os.walk(os.path.join(ROOT, 'assets')):
        for f in fn:
            if f.lower().endswith(IMAGE_EXT):
                files.append(rel(os.path.join(dp, f)))
    files.sort()
    guide = json.load(open(os.path.join(HERE, 'size_guide.json')))
    gsprites = guide['sprites']
    entries: dict[str, dict] = {}

    def add(eid, path, **kw):
        e = entries.setdefault(eid, {'id': eid, 'files': [], **kw})
        e['files'].append(path)

    for p in files:
        parts = p.split('/')
        top = parts[1]
        name = os.path.splitext(parts[-1])[0]
        if top == 'zones' and parts[2] == 'props':
            base = re.sub(r'_f\d+$', '', name)
            kind, module = gsprites.get(base, (None, None))
            add(f'prop/{base}', p, cls='sprite', name=base, kind=kind, module=module or '?',
                generator=f'scripts/art/{module}.py' if module else '?')
        elif top == 'zones' and parts[2] == 'scenery':
            add(f'scenery/{name}', p, cls='scenery', name=name, module='scenery', generator='scripts/art/scenery.py',
                region=name.split('_')[0])
        elif top == 'zones' and len(parts) == 3:
            mod = BEYOND.get(name, 'zones')
            add(f'scenery/{name}', p, cls='scenery', name=name, module=mod, generator=f'scripts/art/{mod}.py',
                region='beyond the zones')
        elif top == 'zones':
            z = parts[2]
            mod, place = ZONES.get(z, ('zones', '?'))
            if z == 'garden':
                add('garden/ground', p, cls='ground', name='garden', module='garden', generator='scripts/art/garden.py',
                    place=place)
            else:
                add(f'zone/{z}', p, cls='zone', name=z, module=mod, generator=f'scripts/art/{mod}.py', place=place)
        elif top == 'residents':
            who = name.split('-')[0]
            add(f'resident/{who}', p, cls='resident', name=who, kind='resident', module='residents',
                generator='scripts/art/residents.py', owner=RESIDENT_OWNER.get(who, '?'))
        elif top == 'garden':
            if len(parts) == 4 and parts[2] == 'hut':
                add('garden/hut-colourways', p, cls='sprite', name='hut', kind='hut', module='garden',
                    generator='scripts/art/garden.py')
            elif len(parts) == 4 and parts[2] == 'growth':
                crop = re.sub(r'_\d+$', '', name)
                add(f'growth/{crop}', p, cls='sprite', name=crop, kind='flowers' if crop.startswith('plot') else 'young_tree',
                    module='garden', generator='scripts/art/garden.py', grid='free')
            elif name.startswith(('ground', 'path-')):
                add('garden/ground', p, cls='ground', name='garden', module='garden', generator='scripts/art/garden.py',
                    place=ZONES['garden'][1])
            elif name.startswith('water-'):
                add(f'garden/{name.rsplit("-", 1)[0]}', p, cls='overlay', name=name.rsplit('-', 1)[0], module='garden',
                    generator='scripts/art/garden.py')
            elif name.startswith('light-'):
                add(f'garden/{name}', p, cls='overlay', name=name, module='garden', generator='scripts/art/garden.py')
            else:
                kind, module = gsprites.get(name, (None, None))
                add(f'garden/{name}', p, cls='sprite', name=name, kind=kind, module='garden',
                    generator='scripts/art/garden.py', same_as=f'prop/{name}' if module else None)
        elif top == 'decor':
            add(f'decor/{name}', p, cls='sprite', name=name, kind=None, module='decor', generator='scripts/art/decor.py',
                grid='indoor')
        elif top == 'journeys':
            vehicle = '-' not in name
            add(f'journey/{name}', p, cls='sprite' if vehicle else 'picture', name=name, module='journey',
                generator='scripts/art/journey.py', grid='side view')
        elif top == 'worlds':
            if parts[2] == 'props':
                kind, _m = gsprites.get(name, (None, None))
                add(f'mission-world/props/{name}', p, cls='sprite', name=name, kind=kind, module='worlds',
                    generator='scripts/art/worlds.py')
            else:
                add(f'mission-world/{parts[2]}', p, cls='picture', name=parts[2], module='worlds',
                    generator='scripts/art/worlds.py')
        elif top == 'battle':
            add(f'battle/{name}', p, cls='picture', name=name, module='battle', generator='scripts/art/battle.py')
        elif top == 'scenes':
            add(f'scene/{name}', p, cls='picture', name=name, module='vignettes', generator='scripts/art/vignettes.py')
        elif top == 'missions':
            add(f'mission-map/{name}', p, cls='picture', name=name, module='mission_map',
                generator='scripts/art/mission_map.py')
        elif top == 'world':   # the world canvas (PR #123): tiles cut from the zones' grounds
            add(f'world-canvas/{parts[2]}', p, cls='zone', name=parts[2], module='world_canvas',
                generator='scripts/art/world_canvas.py', place='tiles of the old grounds')
        else:
            add(f'other/{"/".join(parts[1:-1])}', p, cls='picture', name=name, module='?', generator='?')
    for e in entries.values():
        if 'owner' not in e:
            e['owner'] = MODULE_OWNER.get(e['module'], 'A' if e['module'] == 'world_canvas' else '?')
    return sorted(entries.values(), key=lambda e: e['id'])


# ---------------------------------------------------------------------------------------- grading

FIX_OF = {'grid': 'redraw', 'size': 'redraw', 'bar': 'redraw', 'speckle': 'redraw', 'dither': 'redraw',
          'light-west': 'redraw', 'logic': 'redraw', 'colours': 'repaint', 'palette': 'repaint',
          'outline-flat-ink': 'outline', 'outline-double': 'outline', 'outline-light': 'outline',
          'detail unverified': 'redraw'}


def grade_sprite(e: dict, guide: dict, audit: dict, changes: dict) -> None:
    kinds = guide['kinds']
    kind = e.get('kind')
    k = kinds.get(kind) if kind else None
    fails, notes = [], []
    # every frame is measured; the entry keeps the first frame's numbers and the union of misses
    style_all, size_all = [], []
    img_main = None
    for p in e['files']:
        img = Image.open(os.path.join(ROOT, p))
        img1, s = native(img)
        if img_main is None or p.endswith(('-0.png', f'/{e["name"]}.png')):
            img_main = (img1, s, p)
        st = sprite_style(img1)
        style_all.append(st)
        size_all.append(box_of(img1))
    img1, scale, mainp = img_main
    st = next((x for x in style_all if x), {})
    misses = sorted({m for x in style_all for m in x.get('misses', [])})
    h, w = box_of(img1)
    m = {'scale': scale, 'h': h, 'w': w}
    m['style'] = {kk: st[kk] for kk in ('colours', 'on_house', 'on_today', 'palette', 'outline_dark', 'flat_ink', 'double',
                                         'west_east', 'isolated', 'checker') if kk in st}
    # grid
    g = e.get('grid')
    if g:
        m['grid'] = g
    elif not k:
        m['grid'] = 'n/a (no kind)'
    elif k['group'] in GRID_FREE_GROUPS or 'trunk' in k['foot'] or k['foot'] in ('free', '') or kind in guide['unmeasured']:
        m['grid'] = 'free'
    else:
        fw = foot_width(img1)
        r = fw % 8
        ok = r in FOOT_RESIDUES
        m['grid'] = {'foot_px': fw, 'cells': round(fw / 8, 2), 'kind_foot': k['foot'], 'ok': ok}
        if not ok:
            fails.append('grid')
            notes.append(f'foot line {fw} px: not whole 8 px cells (kind foot {k["foot"]})')
    # size
    if k and not (e['name'] in guide.get('unmeasured', {})):
        tol = guide['tolerance']
        hs = [x[0] for x in size_all]
        ws = [x[1] for x in size_all]
        def judge(lo_hi, vals):
            if not lo_hi:
                return 0
            return 1 if max(vals) > lo_hi[1] + tol else -1 if min(vals) < lo_hi[0] - tol else 0
        dh, dw = judge(k['h'], hs), judge(k['w'], ws)
        m['size'] = {'kind': kind, 'h_range': k['h'], 'w_range': k['w'],
                     'status': 'ok' if not (dh or dw) else ('over' if dh >= 0 and dw >= 0 else 'under' if dh <= 0 and dw <= 0 else 'mixed')}
        if dh or dw:
            fails.append('size')
            rng = ' x '.join('-' if not r else f'{r[0]}-{r[1]}' for r in (k['h'], k['w']))
            notes.append(f'{h} x {w} px ({m["size"]["status"]}) against {kind} {rng}')
    elif e['name'] in guide.get('unmeasured', {}):
        m['size'] = {'status': 'unmeasured', 'why': guide['unmeasured'][e['name']]}
    else:
        m['size'] = {'status': 'no kind'}
    # style
    for x in misses:
        fails.append(x)
    # logic (the prop audit)
    au = None
    mod_keys = [(e['module'], e['name'])]
    if e['id'].startswith('garden/'):
        mod_keys = [('garden', e['name']), ('garden_props', e['name'])]
    elif e['cls'] == 'resident':
        mod_keys = [('residents', e['name'])]
    elif e['id'].startswith('decor/'):
        mod_keys = [('decor', e['name'])]
    for mk in mod_keys:
        if mk in audit:
            au = audit[mk]
            break
    if au is None and e.get('same_as'):
        same = e['same_as'].split('/', 1)[1]
        for mk, v in audit.items():
            if mk[1] == same:
                au = v
                break
    last = max((changes.get(p) for p in e['files'] if changes.get(p)), key=lambda c: c[1], default=None)
    if last:
        m['last_change'] = {'sha': last[0], 'date': last[1][:16], 'subject': last[2][:120]}
    eye = e.get('eye', {})
    if au:
        m['audit'] = {'grade': au['grade'], 'why': au['why'], 'fix': au['fix']}
        if au['grade'] == 'DROP':
            e['grade'] = 'RETIRE'
            e['why'] = f'the prop audit dropped it: {au["why"]}'
            e['fails'] = ['logic']
            e['measured'] = m
            return
        if au['grade'] in ('ADJUST', 'REDRAW'):
            changed = last and _after(last[1], AUDIT_DATE)
            if eye.get('logic', '').startswith('fixed'):
                m['logic'] = f'fixed by eye: {eye["logic"]}'
            else:
                fails.append('logic')
                m['logic'] = ('re-check: changed since the audit' if changed else 'fault') + f' ({au["grade"]}: {au["why"]})'
        else:
            m['logic'] = 'ok (KEEP in the audit)'
    else:
        if eye.get('logic', '').startswith('ok'):
            m['logic'] = f'by eye: {eye["logic"]}'
        else:
            fails.append('logic')
            m['logic'] = 'not audited'
    # the detail bar
    bar_kind = BAR_BY_KIND.get(kind) if kind and kind not in BY_EYE_KINDS else None
    if e['id'].startswith('decor/') or e['id'].startswith('growth/'):
        bar_kind = 'tree' if e['id'].startswith('growth/orchard') else None
    if e['cls'] == 'resident':
        bar_kind = None
    if e['module'] == 'western_props' and kind in ('false_front', 'smithy', 'shop', 'civic', 'town_house'):
        bar_kind = 'wood-front'
    if e['module'] == 'castle_props' and bar_kind == 'facade':
        bar_kind = 'stone-wall'
    if e['module'] == 'space_props' and bar_kind in ('facade', 'wood-front', 'stone-wall'):
        bar_kind = 'machinery'
    ramp = st.get('palette') in ('house', 'recolour')
    b = sprite_bar(img1, bar_kind, ramp)
    m['bar'] = b
    if b['status'] == 'fail':
        if kind in OPEN_KINDS:
            b['ruling'] = 'open structure: measured on its largest solid part (house-style 7)'
        fails.append('bar')
        notes.append('bar ' + ', '.join([f'{x} LOW' for x in b.get('low', [])] + [f'{x} NOISY' for x in b.get('noisy', [])])
                     + f' as {b["kind"]}')
    elif b['status'] in ('n/a', 'by eye'):
        if eye.get('bar', '').startswith('ok'):
            b['eye'] = eye['bar']
        elif au and au['grade'] == 'KEEP' and not (last and _after(last[1], AUDIT_DATE)):
            b['eye'] = 'KEEP by eye in the prop audit, unchanged since'
        else:
            fails.append('detail unverified')
            notes.append('detail not measurable and not checked by eye since the bar')
    # verdict
    order = ['logic', 'size', 'grid', 'bar', 'detail unverified', 'speckle', 'dither', 'light-west', 'colours', 'palette',
             'outline-double', 'outline-flat-ink', 'outline-light']
    fails = sorted(set(fails), key=lambda f: order.index(f) if f in order else 99)
    e['fails'] = fails
    e['measured'] = m
    if not fails:
        e['grade'] = 'KEEP'
        e['why'] = 'passes every check' + (' (palette through the one recolour)' if st.get('palette') == 'recolour' else '')
        e['fix'] = 'none'
        return
    e['grade'] = 'REWORK'
    kinds_of_fix = {FIX_OF.get(f, 'redraw') for f in fails}
    e['fix'] = 'redraw' if 'redraw' in kinds_of_fix else 'repaint' if 'repaint' in kinds_of_fix else 'outline'
    bits = []
    if 'logic' in fails:
        bits.append(m['logic'])
    bits += notes
    sty = [f for f in fails if f in ('speckle', 'dither', 'light-west', 'colours', 'palette', 'outline-double',
                                      'outline-flat-ink', 'outline-light')]
    if sty:
        bits.append('style: ' + ', '.join(sty))
    e['why'] = '; '.join(bits)


def grade_picture(e: dict, ramp_note: bool = True) -> None:
    """Grounds, scenery, journey and battle pictures: numbers, then the rule for the class."""
    main = next((p for p in e['files'] if os.path.basename(p) in ('ground.png',)), e['files'][0])
    img1, s = native(Image.open(os.path.join(ROOT, main)))
    m = {'scale': s, 'h': img1.height, 'w': img1.width, 'measured_file': main, **ground_numbers(img1)}
    e['measured'] = m
    fails = []
    if m['isolated'] > 0.06:
        fails.append('speckle')
    if m['checker'] > 0.005:
        fails.append('dither')
    if m['on_today'] < 0.9:
        fails.append('palette')
    e['fails'] = fails


def grade_entry(e: dict, guide: dict, audit: dict, changes: dict) -> None:
    eid = e['id']
    for p in e['files']:
        if p in REMOVED:
            grade_picture(e)
            e['grade'], e['why'], e['fix'] = 'RETIRE', REMOVED[p], 'none'
            return
    if e['cls'] in ('sprite', 'resident'):
        grade_sprite(e, guide, audit, changes)
        if e['cls'] == 'resident' and e['grade'] == 'REWORK':
            e['why'] += '; (a resident is not placed on the grid: it walks)'
        return
    grade_picture(e)
    if e['cls'] == 'zone' and eid != 'zone/home' and soft_grid_zone(e['name'], e['module']):
        eye = e.get('eye', {})
        e['measured']['soft_grid'] = 'terrace.build: tiers with south faces and side bands'
        if not e['fails'] and eye.get('bar', '').startswith('ok'):
            e['grade'], e['fix'], e['why'] = 'KEEP', 'none', 'built on the soft grid with the terrace toolkit; bar checked by eye'
        else:
            e['grade'], e['fix'] = 'REWORK', 'redraw'
            e['fails'] = e['fails'] + ([] if eye.get('bar', '').startswith('ok') else ['bar by eye'])
            e['why'] = ('built on the soft grid with the terrace toolkit; not KEEP until its ground passes the cleanliness '
                        'checks and its faces, banks and ground are compared with the bar (write the verdict into `eye`)')
        if e.get('place'):
            e['why'] += f'. The place: {e["place"]}'
        return
    if e['cls'] in ('zone', 'scenery') and eid != 'zone/home':
        e['grade'] = 'RETIRE'
        e['fix'] = 'none'
        what = 'scenery past the walked zones' if e['cls'] == 'scenery' else 'an old zone\'s ground and its data pictures'
        e['why'] = (f'by rule: {what}, painted before the soft grid (no tiers, south faces or side bands); '
                    f'the regions are rebuilt on the soft grid from docs/vision/regions/ with the kits')
        if e.get('place'):
            e['why'] += f'. The place: {e["place"]}'
        e['fails'] = ['soft grid'] + e['fails']
        return
    if eid == 'zone/home':
        e['grade'], e['fix'] = 'REWORK', 'redraw'
        e['fails'] = ['bar unmeasurable', 'logic'] + e['fails']
        e['why'] = ('the hut inside stays; its furniture is being redrawn to the size guide (PR #136) and the rooms '
                    'have no indoor baseline for the bar, so they are judged by eye: not KEEP until that lands')
        return
    if eid.startswith('garden/'):
        e['grade'], e['fix'] = 'REWORK', 'redraw'
        e['fails'] = ['soft grid'] + e['fails']
        e['why'] = ('the home hub stays (its size, place, geometry and harness: home-valley brief 10), but its ground is '
                    'not on the soft grid: no tiers with south faces and side bands, the raised yard (verticality 4d) '
                    'not built; redraw the ground with the terrace toolkit, keeping the geometry and the harness')
        if e['cls'] == 'overlay':
            e['why'] = 'drawn to fit today\'s garden ground: redrawn with it'
        return
    if eid.startswith('journey/'):
        e['grade'], e['fix'] = 'REWORK', 'redraw'
        e['fails'] = ['house style'] + e['fails']
        e['why'] = ('a journey picture: the journeys stay as shortcuts beside the routes (routes brief 9), but this '
                    'layer was painted in the older style before the house style and the bar; redraw it in the '
                    'house style at the bar (judged by eye: side views have no baseline)')
        return
    if eid.startswith(('battle/', 'scene/', 'mission-world/', 'mission-map/')):
        e['grade'], e['fix'] = 'REWORK', 'redraw'
        e['fails'] = ['house style'] + e['fails']
        e['why'] = ('a picture for another screen (battle, scene or mission) in the older style (art-style.md: '
                    '"still use the older style and need the same pass"); not for the world, redraw before reuse')
        return
    e['grade'], e['fix'] = 'REWORK', 'redraw'
    e['why'] = 'unclassified picture: graded by hand before it is used'


# ---------------------------------------------------------------------------------------- build

def build(audit_path: str | None, date: str, only: set | None = None) -> dict:
    guide = json.load(open(os.path.join(HERE, 'size_guide.json')))
    old = {}
    if os.path.exists(LEDGER):
        old = json.load(open(LEDGER)).get('assets', {})
    entries = inventory()
    names_by_module: dict = {}
    for e in entries:
        mod = e['module']
        if e['id'].startswith('garden/'):
            for mm in ('garden', 'garden_props'):
                names_by_module.setdefault(mm, []).append(e['name'])
        if e['cls'] == 'resident':
            mod = 'residents'
        names_by_module.setdefault(mod, []).append(e['name'])
    for k in ('garden_props', 'home_props', 'world_props', 'harbour_props', 'valley_props'):
        names_by_module.setdefault(k, [])
    audit = {}
    if audit_path and os.path.exists(audit_path):
        audit = read_audit(audit_path, names_by_module)
    else:   # keep the audit verdicts the ledger already holds
        for eid, o in old.items():
            a = o.get('measured', {}).get('audit')
            if a:
                audit[(o.get('module'), o.get('name'))] = {**a, 'owner': o.get('owner')}
    changes = git_last_changes([p for e in entries for p in e['files']])
    placed = placements()
    for e in entries:
        if e['id'].startswith('prop/') and e['name'] in placed:
            e['placed'] = dict(sorted(placed[e['name']].items()))
    out = {}
    for e in entries:
        if only is not None and e['id'] not in only and not any(p in only for p in e['files']):
            if e['id'] in old:
                out[e['id']] = old[e['id']]
                continue
        if e['id'] in old and 'eye' in old[e['id']]:
            e['eye'] = old[e['id']]['eye']
        grade_entry(e, guide, audit, changes)
        prev = old.get(e['id'])
        canon = lambda x: json.dumps(x, sort_keys=True)  # noqa: E731  (tuples and lists alike)
        same = prev and prev.get('grade') == e['grade'] and canon(prev.get('measured')) == canon(e.get('measured'))
        e['checked'] = prev['checked'] if same and prev.get('checked') else date
        if e['module'] in UNASSIGNED:
            e['owner_note'] = 'generator not in the lane table: Claude A by default'
        keep = ('files', 'cls', 'name', 'kind', 'module', 'generator', 'owner', 'owner_note', 'place', 'grade', 'fix',
                'why', 'fails', 'measured', 'placed', 'eye', 'checked', 'same_as', 'spin_off')
        out[e['id']] = {k: e[k] for k in keep if k in e and e[k] is not None}
    # a garden or mission copy that is the same drawing as a zone sprite takes its verdict
    for eid, e in out.items():
        twin = 'prop/' + e['name'] if eid.startswith(('garden/', 'mission-world/props/')) else None
        if not twin or twin not in out or e['cls'] != 'sprite' or len(e['files']) != 1:
            continue
        a = np.asarray(native(Image.open(os.path.join(ROOT, e['files'][0])))[0])
        b = np.asarray(native(Image.open(os.path.join(ROOT, out[twin]['files'][0])))[0])
        if a.shape == b.shape and np.array_equal(a, b):
            t = out[twin]
            for k in ('grade', 'fix', 'fails', 'measured'):
                if k in t:
                    e[k] = t[k]
                else:
                    e.pop(k, None)
            e['why'] = f'the same drawing as {twin}: ' + t.get('why', '')
            e['same_as'] = twin
            e['checked'] = t['checked']
    # pictures kept for the desktop spin-off: the grade still says what the phone game may use,
    # the tag says the picture is not deleted when it retires (Matt, 21 Oct)
    tags = spin_off_files()
    for e in out.values():
        why = next((tags[f] for f in e['files'] if f in tags), None)
        if why:
            e['spin_off'] = why
        else:
            e.pop('spin_off', None)
    return out


def spin_off_files() -> dict:
    """Files kept for the desktop spin-off (Matt, 21 Oct: "i do want to make a spin off game for
    the computer using some of the assets, so keep some of the stuff that doesnt conform
    perfectly to mobile"), with why. Today: the woodland zone the real-time fight prototype is
    built on (prototypes/realtime-combat, build/build_assets.py packs its ground and the props
    it places), read from lib/zone-maps.ts the same way."""
    why = ('kept for the desktop spin-off: the real-time fight prototype (prototypes/realtime-combat) is built on '
           'the woodland zone; retire it from the phone game, but do not delete it')
    out = {'assets/zones/woodland/ground.png': why}
    src = open(os.path.join(ROOT, 'lib', 'zone-maps.ts')).read()
    i = src.find('\n  woodland: {\n    objects: [')
    if i < 0:
        return out
    end = src.index('\n    ],', i)
    for kind in re.findall(r"\['[^']+', '([^']+)', -?\d+, -?\d+, \d+, \d+", src[i:end]):
        out[f'assets/zones/props/{kind}.png'] = why
    return out


def write(assets: dict, main_sha: str) -> None:
    doc = {
        '_about': ('The asset ledger (docs/vision/asset-ledger.md). Every picture under assets/ with its grade: KEEP may go '
                   'into a kit or region build, REWORK must be redone first, RETIRE has no place in the new world. '
                   'Written by scripts/art/asset_ledger.py --build; `eye` verdicts are written by hand and survive a '
                   'rebuild. Checked by scripts/check-assets.cjs (npm run check:assets).'),
        'main': main_sha,
        'grades': {'KEEP': 'fits the newest standard on every check', 'REWORK': 'the subject stays; redo the art first',
                   'RETIRE': 'no place in the new world'},
        'fix': {'redraw': 'a new drawing (detail, size, footprint, logic, light, speckle)',
                'repaint': 'the same drawing on the house ramps (colours off the ramps or over budget)',
                'outline': 'only the outline step: the material\'s edge tone instead of one ink, no doubling'},
        'thresholds': {'bar_tones_ramp_built': TONES_RAMP, 'bar_tones': TONES, 'bar_shapes': SHAPES,
                       'bar_dressing': DRESSING, 'bar_square_px': [SQUARE_MIN, SQUARE_MAX], 'foot_residues_mod_8': list(FOOT_RESIDUES)},
        'region_builds': {'globs': ['lib/world-canvas*.ts', 'scripts/art/world_canvas.py', 'scripts/art/*_kit.py',
                                    'scripts/art/*_kits.py', 'scripts/art/terrace.py', '**/regions/**', '**/kits/**'],
                          'exempt_marker': 'ledger: compare'},
        'rules': RULES,
        'assets': assets,
    }
    text = json.dumps(doc, indent=1, ensure_ascii=False) + '\n'   # all or nothing
    with open(LEDGER, 'w') as f:
        f.write(text)


# ---------------------------------------------------------------------------------------- summary and report

LANES = 'ABCDE'


def load() -> dict:
    return json.load(open(LEDGER))


def summary(doc: dict) -> str:
    a = doc['assets']
    lines = ['| Lane | KEEP | REWORK (redraw) | REWORK (repaint) | REWORK (outline only) | RETIRE | Entries | Files |',
             '| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |']
    tot = [0] * 7
    for lane in LANES:
        es = [e for e in a.values() if e['owner'] == lane]
        c = [sum(1 for e in es if e['grade'] == 'KEEP'),
             sum(1 for e in es if e['grade'] == 'REWORK' and e.get('fix') == 'redraw'),
             sum(1 for e in es if e['grade'] == 'REWORK' and e.get('fix') == 'repaint'),
             sum(1 for e in es if e['grade'] == 'REWORK' and e.get('fix') == 'outline'),
             sum(1 for e in es if e['grade'] == 'RETIRE'), len(es), sum(len(e['files']) for e in es)]
        tot = [x + y for x, y in zip(tot, c)]
        lines.append(f'| {lane} | ' + ' | '.join(str(x) for x in c) + ' |')
    lines.append('| **All** | ' + ' | '.join(f'**{x}**' for x in tot) + ' |')
    return '\n'.join(lines)


def fail_counts(doc: dict, lane: str | None = None) -> dict:
    c: dict = {}
    for e in doc['assets'].values():
        if lane and e['owner'] != lane:
            continue
        if e['grade'] != 'REWORK':
            continue
        for f in e.get('fails', []):
            c[f] = c.get(f, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


def severity(e: dict) -> float:
    """How far an entry is from KEEP, for 'worst offenders': redraw fails weigh most."""
    s = 0.0
    w = {'logic': 3, 'size': 3, 'grid': 2, 'bar': 3, 'detail unverified': 1, 'speckle': 2, 'dither': 2, 'light-west': 2,
         'colours': 1.5, 'palette': 1.5, 'outline-double': 0.5, 'outline-flat-ink': 0.3, 'outline-light': 0.3}
    for f in e.get('fails', []):
        s += w.get(f, 1)
    m = e.get('measured', {})
    b = m.get('bar', {})
    if isinstance(b, dict) and b.get('status') == 'fail':
        for k in b.get('low', []):
            ours, ref = b[k]
            s += max(0.0, 1 - ours / ref) * 4
    st = m.get('style', {})
    if st.get('colours', 0) > 64:
        s += min(3, st['colours'] / 256)
    if st.get('isolated', 0) > 0.06:
        s += st['isolated'] * 10
    return round(s, 2)


def _thumb(e: dict) -> Image.Image:
    p = os.path.join(ROOT, e['files'][-1 if e['id'].startswith('growth/') else 0])
    for f in e['files']:
        if f.endswith(('-0.png', f'/{e["name"]}.png', '/ground.png')):
            p = os.path.join(ROOT, f)
            break
    img1, _s = native(Image.open(p))
    if e['cls'] in ('sprite', 'resident'):
        f = 2 if max(img1.size) <= 80 else 1
        t = img1.resize((img1.width * f, img1.height * f), Image.NEAREST)
        lim = 170
    else:
        t, lim = img1, 150
    if max(t.size) > lim:
        r = lim / max(t.size)
        t = t.resize((max(1, int(t.width * r)), max(1, int(t.height * r))), Image.NEAREST if t is not img1 else Image.BOX)
    return t.convert('RGBA')


def report(doc: dict, out: str) -> None:
    """Contact sheets per lane, readable at a glance: green KEEP, amber REWORK (worst first,
    with the fix and the failing checks), red RETIRE; sprites at 2x on grey, pictures as
    thumbnails. Writes OUT and one OUT-<lane>.png per lane."""
    from PIL import ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 12)
        mid = ImageFont.truetype('DejaVuSans-Bold.ttf', 16)
        big = ImageFont.truetype('DejaVuSans-Bold.ttf', 24)
    except OSError:
        font = mid = big = ImageFont.load_default()
    col = {'KEEP': (52, 168, 72), 'REWORK': (232, 152, 24), 'RETIRE': (212, 52, 52)}
    W, CW = 2400, 198
    cols = (W - 16) // CW
    bg, fg, card, dim = (40, 38, 44), (236, 233, 227), (78, 76, 84), (170, 166, 160)
    sheets = []
    lanes_present = []
    for lane in LANES:
        es = [{**e, 'id': k} for k, e in doc['assets'].items() if e['owner'] == lane]
        if not es:
            continue
        lanes_present.append(lane)
        groups = []
        for g in ('KEEP', 'REWORK', 'RETIRE'):
            gs = [e for e in es if e['grade'] == g]
            if g == 'REWORK':
                gs.sort(key=lambda e: (-severity(e), e['id']))
            else:
                gs.sort(key=lambda e: e['id'])
            groups.append((g, gs))
        blocks = []   # (kind, payload, height)
        for g, gs in groups:
            note = {'KEEP': 'may go into a kit or region build',
                    'REWORK': 'the subject stays; redo the art first (worst first: fix, then failing checks)',
                    'RETIRE': 'no place in the new world'}[g]
            blocks.append(('head', (g, len(gs), note), 34))
            row = []
            for e in gs:
                row.append((e, _thumb(e)))
                if len(row) == cols:
                    blocks.append(('row', row, max(t.height for _e, t in row) + 52))
                    row = []
            if row:
                blocks.append(('row', row, max(t.height for _e, t in row) + 52))
        c = {g: len(gs) for g, gs in groups}
        H = 60 + sum(h for _k, _p, h in blocks) + 16
        sh = Image.new('RGB', (W, H), bg)
        d = ImageDraw.Draw(sh)
        d.text((16, 16), f'Lane {lane}', fill=fg, font=big)
        x = 130
        for g in ('KEEP', 'REWORK', 'RETIRE'):
            d.rectangle([x, 20, x + 16, 36], fill=col[g])
            d.text((x + 22, 18), f'{g} {c[g]}', fill=fg, font=mid)
            x += 150
        d.text((x + 10, 20), f'{len(es)} entries, {sum(len(e["files"]) for e in es)} files', fill=dim, font=mid)
        y = 60
        for kind, payload, h in blocks:
            if kind == 'head':
                g, n, note = payload
                d.rectangle([8, y + 6, W - 8, y + 30], fill=(56, 54, 60))
                d.rectangle([8, y + 6, 20, y + 30], fill=col[g])
                d.text((28, y + 9), f'{g} ({n}): {note}', fill=fg, font=mid)
            else:
                for i, (e, t) in enumerate(payload):
                    x0 = 8 + i * CW
                    d.rectangle([x0, y, x0 + CW - 8, y + h - 6], fill=card)
                    d.rectangle([x0, y, x0 + CW - 8, y + 6], fill=col[e['grade']])
                    d.rectangle([x0, y, x0 + 6, y + h - 6], fill=col[e['grade']])
                    sh.paste(t, (x0 + 6 + (CW - 14 - t.width) // 2, y + 10), t)
                    label = e['id'].split('/', 1)[1] if e['id'].startswith('prop/') else e['id']
                    d.text((x0 + 10, y + h - 40), label[-25:], fill=fg, font=font)
                    if e['grade'] == 'REWORK':
                        fl = ' '.join(f.replace('outline-', 'ol-').replace('detail unverified', 'unverified')
                                      for f in e.get('fails', [])[:3])
                        d.text((x0 + 10, y + h - 24), f'{e.get("fix", "")}: {fl}'[:29], fill=col['REWORK'], font=font)
                    else:
                        d.text((x0 + 10, y + h - 24), e['grade'], fill=col[e['grade']], font=font)
            y += h
        sheets.append(sh)
        sh.save(os.path.splitext(out)[0] + f'-{lane}.png', optimize=True)
    H = sum(s.height for s in sheets) + 64
    page = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(page)
    d.text((16, 18), f'Asset ledger, main at {doc["main"]}: green KEEP, amber REWORK (redraw / repaint / outline), red RETIRE',
           fill=fg, font=big)
    y = 64
    for s2 in sheets:
        page.paste(s2, (0, y))
        y += s2.height
    page.save(out, optimize=True)


def lane_lists(doc: dict) -> dict:
    """Per lane: its own entries by verdict and fix, and the non-KEEP sprites placed today in
    the zones its region brief takes over (whichever lane owns them)."""
    a = doc['assets']
    out = {}
    for lane in LANES:
        own = {k: e for k, e in a.items() if e['owner'] == lane}
        r = {'redraw': [], 'repaint': [], 'outline': [], 'retire': [], 'keep': []}
        for k, e in sorted(own.items(), key=lambda kv: (-severity(kv[1]), kv[0])):
            if e['grade'] == 'KEEP':
                r['keep'].append(k)
            elif e['grade'] == 'RETIRE':
                r['retire'].append(k)
            else:
                r[e.get('fix', 'redraw')].append(k)
        region = {}
        for k, e in a.items():
            if not k.startswith('prop/') or e['grade'] == 'KEEP':
                continue
            zs = [z for z in e.get('placed', {}) if REGION_LANE.get(z) == lane]
            if zs:
                region[k] = {'owner': e['owner'], 'grade': e['grade'], 'fix': e.get('fix'), 'zones': zs}
        r['region_uses'] = region
        out[lane] = r
    return out


def lanes_markdown(doc: dict) -> str:
    """What each lane must redo, as markdown: its own entries by fix (worst first), then the
    non-KEEP sprites placed today in its region's zones."""
    ll = lane_lists(doc)
    out = []
    short = lambda k: k.split('/', 1)[1] if k.startswith('prop/') else k  # noqa: E731
    for lane in LANES:
        r = ll[lane]
        out.append(f'### Lane {lane}')
        for fix, label in (('redraw', 'Redraw'), ('repaint', 'Repaint on the house ramps'), ('outline', 'Outline pass only'),
                           ('retire', 'Retire'), ('keep', 'KEEP')):
            if r[fix]:
                out.append(f'- **{label} ({len(r[fix])}):** ' + ', '.join(f'`{short(k)}`' for k in r[fix]))
        if r['region_uses']:
            by = {}
            for k, v in r['region_uses'].items():
                by.setdefault(v['owner'], []).append(k)
            out.append(f'- **Placed today in its region\'s zones, not KEEP ({len(r["region_uses"])}):** ' + '; '.join(
                f'lane {o}: ' + ', '.join(f'`{short(k)}`' for k in sorted(ks)) for o, ks in sorted(by.items())))
        out.append('')
    return '\n'.join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--audit', default=os.path.join(ROOT, 'docs', 'vision', 'prop-logic.md'))
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    ap.add_argument('--redo', nargs='*', help='re-measure only these entry ids or files')
    ap.add_argument('--report', metavar='OUT.png')
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--lanes', action='store_true', help='what each lane must redo, as markdown')
    args = ap.parse_args(argv)
    if args.build or args.redo:
        sha = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        assets = build(args.audit, args.date, set(args.redo) if args.redo else None)
        write(assets, sha)
        print(f'wrote {rel(LEDGER)}: {len(assets)} entries, {sum(len(e["files"]) for e in assets.values())} files')
    if args.summary or args.build:
        doc = load()
        print(summary(doc))
        for lane in LANES:
            print(f'lane {lane} fails:', fail_counts(doc, lane))
    if args.lanes:
        print(lanes_markdown(load()))
    if args.report:
        report(load(), args.report)
        print('wrote', args.report)
    return 0


if __name__ == '__main__':
    sys.exit(main())
