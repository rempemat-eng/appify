"""npm run check:kit: the kit's three gates (rules-system.md 2 and 5).

1. Palette codes only. Kit code holds no literal colour (no '#rrggbb', no RGB triple) and draws
   no PIL shapes; colours come from palette.py. Every biome palette entry is a house colour.
2. The golden rebuild. Every scene in art/golden/ is rebuilt from its plan, its biome and the kit
   and must match the frozen picture pixel for pixel. The rebuild is skipped when the same inputs
   (build.inputs: the kit, the biome, the plan, the house palette) and the same golden were
   already verified on this machine (.cache/kit/verified/, keyed by their hash), so it costs a
   render only when something it reads has changed.
3. The lawn band. The golden's lawn measure (measure.py, MEASURE.md) sits in its biome's band.
4. The drawn villages (village.py, town.py): house colours only, few lone pixels, and a note when a
   zone's pictures are older than the kit or its plan.
5. Every trunk shows its crown in the zones gen_zone writes (crowns()).

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
        if kit.get('inputs') != town.input_hash(plan_path, kit['density']):
            notes.append(f'{plan["id"]}: the kit or the plan changed since it was drawn: python3 game/tools/gen_village.py {plan["id"]}')
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


def crowns() -> list:
    """5. Every trunk shows its crown (25 Oct): in each zone drawn by gen_zone (game/zones/<zone>/kit.json
    with [id, kind, x, y, w, h] objects), the objects are stacked by their feet as the game sorts
    them, and a tree (a picture with a crown of greens over a trunk) fails when its trunk shows
    but less than CROWN_MIN of its crown does (hidden by what stands in front or cut by the zone's
    edge), or when its crown lies mostly over a bigger crown of another kind in nearly the same colour, so it reads
    as part of that one (a small tree's pole under a bigger tree's crown)."""
    import glob
    import numpy as np
    from PIL import Image
    from scipy import ndimage as ndi
    CROWN_MIN, OVER_MAX, COLOUR_MIN = 0.4, 0.3, 12.0
    bad = []
    for kp in sorted(glob.glob(os.path.join(ROOT, 'game', 'zones', '*', 'kit.json'))):
        kit = json.load(open(kp))
        objs = kit.get('objects', [])
        if not objs or not isinstance(objs[0], list):
            continue
        zdir = os.path.dirname(kp)
        D = float(kit['density'])
        gw, gh = Image.open(os.path.join(zdir, 'art', 'ground.png')).size
        pics = {}
        for k in sorted({o[1] for o in objs}):
            a = np.asarray(Image.open(os.path.join(zdir, 'art', k + '.png')).convert('RGBA')).astype(int)
            al = a[..., 3] > 0
            green = al & (a[..., 1] > a[..., 0] + 4)
            H = a.shape[0]
            low = np.zeros_like(al)
            low[int(H * 0.45):] = True
            trunk = al & ~green & low
            lab, n = ndi.label(trunk)
            yb = int(np.nonzero(al.any(1))[0].max()) + 1 if al.any() else H
            base = np.unique(lab[yb - 3:yb][lab[yb - 3:yb] > 0])   # a trunk stands on the ground (no berries)
            trunk = np.isin(lab, base) & (lab > 0)
            L = a[..., :3].astype(float)
            tree = green.sum() > 0.3 * al.sum() and trunk.sum() > 20
            pics[k] = (al, green, trunk, L, tree)
        order = sorted(range(len(objs)), key=lambda i: (objs[i][3] + objs[i][5], i))
        owner = np.full((gh, gw), -1)
        crown_owner = np.full((gh, gw), -1)
        placed = {}
        for i in order:
            oid, kind, x, y, w, h = objs[i]
            al, green, trunk, L, tree = pics[kind]
            ph, pw = al.shape
            X0 = int(round((x + w / 2) * D)) - pw // 2
            Y0 = int(round((y + h) * D)) - ph
            placed[i] = (X0, Y0)
            ys, xs = np.nonzero(al)
            gy, gx = ys + Y0, xs + X0
            ok = (gy >= 0) & (gy < gh) & (gx >= 0) & (gx < gw)
            if tree:
                cys, cxs = np.nonzero(green)
                cy_, cx_ = cys + Y0, cxs + X0
                cok = (cy_ >= 0) & (cy_ < gh) & (cx_ >= 0) & (cx_ < gw)
                under = crown_owner[cy_[cok], cx_[cok]]
                if len(under) and (under >= 0).mean() > OVER_MAX:
                    j = int(np.bincount(under[under >= 0]).argmax())
                    oj = objs[j]
                    alj, gj, _tj, Lj, _ = pics[oj[1]]
                    Xj, Yj = placed[j]
                    m = under == j
                    lj = Lj[cy_[cok][m] - Yj, cx_[cok][m] - Xj].mean(0)
                    li = L[cys[cok][m], cxs[cok][m]].mean(0)
                    dist = float(np.sqrt(((li - lj) ** 2).sum()))
                    if dist < COLOUR_MIN and green.sum() < 0.6 * gj.sum() and kind != oj[1] \
                            and 'pine' not in (kind, oj[1]):        # a conifer's tiers read against any crown
                        bad.append(f'{os.path.basename(zdir)}/{oid} ({kind}): its crown lies over {oj[0]}\'s crown in the same '
                                   f'colour (mean RGB {dist:.0f} apart); move it or give it a lighter or darker green')
            owner[gy[ok], gx[ok]] = i
            crown_owner[gy[ok], gx[ok]] = np.where(pics[kind][1][ys[ok], xs[ok]], i, -1) if tree else -1
        for i in order:
            oid, kind, x, y, w, h = objs[i]
            al, green, trunk, L, tree = pics[kind]
            if not tree:
                continue
            X0, Y0 = placed[i]

            def shown(mask):
                ys, xs = np.nonzero(mask)
                gy, gx = ys + Y0, xs + X0
                ok = (gy >= 0) & (gy < gh) & (gx >= 0) & (gx < gw)
                return (owner[gy[ok], gx[ok]] == i).sum() / max(1, mask.sum())
            t_, c_ = shown(trunk), shown(green)
            if t_ > 0.3 and c_ < CROWN_MIN:
                bad.append(f'{os.path.basename(zdir)}/{oid} ({kind}): its trunk shows ({100 * t_:.0f} %) but only '
                           f'{100 * c_:.0f} % of its crown does')
    return bad


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
    cbad = crowns()
    print(f'[kit] every trunk shows its crown (gen_zone zones): {"ok" if not cbad else str(len(cbad)) + " finding(s)"}')
    fails += cbad
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
