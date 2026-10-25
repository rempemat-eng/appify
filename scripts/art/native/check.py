"""npm run check:kit: the kit's three gates (rules-system.md 2 and 5).

1. Palette codes only. Kit code holds no literal colour (no '#rrggbb', no RGB triple) and draws
   no PIL shapes; colours come from palette.py. Every biome palette entry is a house colour.
2. The golden rebuild. Every scene in art/golden/ is rebuilt from its plan, its biome and the kit
   and must match the frozen picture pixel for pixel. The rebuild is skipped when the same inputs
   (build.inputs: the kit, the biome, the plan, the house palette) and the same golden were
   already verified on this machine (.cache/kit/verified/, keyed by their hash), so it costs a
   render only when something it reads has changed.
3. The lawn band. The golden's lawn measure (measure.py, MEASURE.md) sits in its biome's band.
4. The drawn villages (village.py, town.py) and the Undercroft (undercroft.py): house colours only, few lone pixels, and a note when a
   zone's pictures are older than the kit or its plan.

    python3 -m scripts.art.native.check            all gates
    python3 -m scripts.art.native.check --no-cache rebuild even if verified
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

HEX = re.compile(r"""['"]#[0-9a-fA-F]{6}['"]""")
TRIPLE = re.compile(r'\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)')
DRAW = re.compile(r'\bImageDraw\b|\bImageFont\b')
# files that may name colours: the palette itself reads them from the house palette and accents
PALETTE_FILES = {'palette.py', 'check.py'}


def lint_codes() -> list:
    bad = []
    for base, _dirs, names in os.walk(HERE):
        for n in names:
            if not n.endswith('.py') or n in PALETTE_FILES:
                continue
            p = os.path.join(base, n)
            for i, line in enumerate(open(p), 1):
                code = re.sub(r'(^|\s)#(\s|$).*', '', line)      # the comment off (a '#rrggbb' string stays)
                if HEX.search(code):
                    bad.append(f'{os.path.relpath(p, ROOT)}:{i}: a literal colour (use palette codes)')
                for m in TRIPLE.finditer(code):
                    v = [int(g) for g in m.groups()]
                    if max(v) > 7 and max(v) <= 255 and min(v) >= 0 and sum(x > 7 for x in v) >= 2:
                        bad.append(f'{os.path.relpath(p, ROOT)}:{i}: an RGB triple {tuple(v)} (use palette codes)')
                if DRAW.search(code):
                    bad.append(f'{os.path.relpath(p, ROOT)}:{i}: PIL drawing (draw with the raster kit)')
    return bad


def lint_biomes() -> list:
    from scripts.art.native import palette as PAL
    bad = []
    bdir = os.path.join(ROOT, 'scripts', 'art', 'biomes')
    for n in sorted(os.listdir(bdir)):
        if not n.endswith('.json'):
            continue
        b = json.load(open(os.path.join(bdir, n)))
        for e in b.get('palette', []):
            if e == 'ink':
                continue
            if not (isinstance(e, list) and len(e) == 2 and e[0] in PAL.RAMPS and 0 <= int(e[1]) <= 6):
                bad.append(f'biomes/{n}: palette entry {e!r} is not [house family, tone 0..6]')
        txt = open(os.path.join(bdir, n)).read()
        if n == 'meadow.json' and HEX.search(txt):
            bad.append(f'biomes/{n}: a literal colour (palette entries are codes)')
    return bad


def _sha(path: str) -> str:
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def goldens() -> list:
    gd = os.path.join(ROOT, 'art', 'golden')
    out = []
    for scene in sorted(os.listdir(gd)) if os.path.isdir(gd) else []:
        man = os.path.join(gd, scene, 'manifest.json')
        if os.path.exists(man):
            m = json.load(open(man))
            for tag, r in sorted(m.get('renders', {}).items()):
                out.append((scene, m['biome'], float(tag.rstrip('x').replace('_', '.')), os.path.join(gd, scene, r['file'])))
    return out


def rebuild(scene: str, biome: str, d: float, golden: str, use_cache: bool) -> tuple:
    from scripts.art.native import build
    key = hashlib.sha256((build.input_hash(scene, biome, d) + _sha(golden)).encode()).hexdigest()
    stamp = os.path.join(ROOT, '.cache', 'kit', 'verified', key)
    if use_cache and os.path.exists(stamp):
        return True, 'verified before (inputs unchanged)', json.load(open(stamp))
    out = os.path.join(ROOT, '.cache', 'kit', scene)
    # a fresh process: the painters size themselves for one density at import
    r = subprocess.run([sys.executable, '-m', 'scripts.art.native.build', '--scene', scene, '--density', '%g' % d,
                        '--out', out, '--compare', golden], cwd=ROOT, capture_output=True, text=True)
    lines = (r.stdout + r.stderr).strip().split('\n')
    if r.returncode != 0:
        return False, '\n'.join(lines[-12:]), None
    from PIL import Image
    import numpy as np
    from scripts.art.native import measure
    mask = np.asarray(Image.open(os.path.join(out, 'lawn_mask_%sx.png' % ('%g' % d).replace('.', '_')))) > 127
    meas = measure.lawn(Image.open(golden), mask)
    os.makedirs(os.path.dirname(stamp), exist_ok=True)
    json.dump(meas, open(stamp, 'w'))
    return True, lines[0], meas


def villages() -> list:
    """4. The drawn villages (town.py, village.py): every picture of a zone plan with "art" is in
    house colours only, the village's own drawings have at most LONE_MAX lone pixels, the ground at
    most LONE_GROUND, and kit.json was written from today's kit and plan (else: regenerate)."""
    import glob
    import numpy as np
    from PIL import Image
    from scripts.art.native import palette as PAL
    from scripts.art.native import raster
    from scripts.art.native import town
    LONE_MAX, LONE_GROUND = 0.01, 0.02
    house = {PAL.rgb(f, t) for f in PAL.RAMPS for t in range(7)} | {PAL.ink()}
    bad, notes = [], []
    for plan_path in sorted(glob.glob(os.path.join(ROOT, 'game', 'data', 'plans', '*.json'))):
        plan = json.load(open(plan_path))
        if 'art' not in plan:
            continue
        zdir = os.path.join(ROOT, 'game', 'zones', plan['id'])
        kp = os.path.join(zdir, 'kit.json')
        if not os.path.exists(kp):
            bad.append(f'{plan["id"]}: no kit.json (python3 game/tools/gen_village.py {plan["id"]})')
            continue
        kit = json.load(open(kp))
        if plan['art'].get('kit') == 'undercroft':     # the vault kit (undercroft.py) has its own inputs and tool
            from scripts.art.native import undercroft
            stale, tool = kit.get('inputs') != undercroft.input_hash(plan_path, kit['density']), 'gen_undercroft.py'
        else:
            stale, tool = kit.get('inputs') != town.input_hash(plan_path, kit['density']), 'gen_village.py ' + plan['id']
        if stale:
            notes.append(f'{plan["id"]}: the kit or the plan changed since it was drawn: python3 game/tools/{tool}')
        drawn = set(kit.get('kit_drawn', []))
        for f in sorted(glob.glob(os.path.join(zdir, 'art', '*.png'))):
            img = Image.open(f).convert('RGBA')
            a = np.asarray(img)
            cols = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] > 0][:, :3], axis=0)}
            off = [c for c in cols if c not in house]
            name = os.path.basename(f)
            if off:
                bad.append(f'{plan["id"]}/{name}: {len(off)} colour(s) off the house palette')
            lim = LONE_GROUND if name == 'ground.png' else (LONE_MAX if name in drawn else None)
            if lim is not None:
                ls = raster.lone_share(img)
                if ls > lim:
                    bad.append(f'{plan["id"]}/{name}: {100 * ls:.2f} % lone pixels (at most {100 * lim:.0f} %)')
    return bad, notes


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    use_cache = '--no-cache' not in argv
    fails = []
    bad = lint_codes() + lint_biomes()
    print(f'[kit] palette codes only: {"ok" if not bad else str(len(bad)) + " finding(s)"}')
    fails += bad
    gs = goldens()
    if not gs:
        fails.append('no golden scene under art/golden/')
    for scene, biome_name, d, golden in gs:
        ok, msg, meas = rebuild(scene, biome_name, d, golden, use_cache)
        print(f'[kit] rebuild {scene} at {d:g}x: {"ok" if ok else "FAILED"}: {msg}')
        if not ok:
            fails.append(f'{scene} at {d:g}x does not rebuild to its golden (python3 -m scripts.art.native.build '
                         f'--scene {scene} --density {d:g} --compare {os.path.relpath(golden, ROOT)})')
            continue
        from scripts.art.native import load_biome
        band = load_biome(biome_name).get('lawn', {}).get('measure')
        if band and meas:
            lo, hi = band['edge_share']
            es, lp = meas['edge_share'], meas['lone_px']
            inside = lo <= es <= hi and lp <= band.get('lone_px_max', 1.0)
            print(f'[kit] lawn {scene}: edge share {es:.3f} (band {lo:.2f} to {hi:.2f}), lone px {100 * lp:.1f} % '
                  f'(at most {100 * band.get("lone_px_max", 1.0):.0f} %): {"ok" if inside else "OUT OF BAND"}')
            if not inside:
                fails.append(f'{scene}: lawn measure out of the {biome_name} band')
    vbad, vnotes = villages()
    print(f'[kit] drawn villages (house colours, lone pixels): {"ok" if not vbad else str(len(vbad)) + " finding(s)"}')
    for n in vnotes:
        print('[kit] note:', n)
    fails += vbad
    for f in fails:
        print('FAIL:', f)
    if not fails:
        print('PASS: kit gates (palette codes, golden rebuild, lawn band, drawn villages)')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
