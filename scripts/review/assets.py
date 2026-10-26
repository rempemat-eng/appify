"""The asset gate: review one drawn asset (a prop, building, plant, rock, water piece, ground
or background tile) before it may be placed in any zone.

Matt, 25 Oct 19:19: "this might be easiest to do after the props or background is first
drawn. it could be checked after and the level of detail could be compared with other props
and such before it gets placed and left in the world."

    npm run review:asset -- crossroads/barrel_29          # an asset in game/zones/<zone>/art
    npm run review:asset -- path/to/new_prop.png --kind barrel --biome valley
    npm run review:asset -- --all [--record]              # every placed asset (seeds the catalogue)

For each asset: a sheet (alone at 1x and 4x, on neutral and on its biome's ground, beside
Bramble for scale and beside its approved siblings), the detail and construction detectors,
the per-object detail bar against Eastward, and a JSON report. `--record` writes its
catalogue entry, art/catalogue/<zone>/<name>.json, which the placement gate (gate.py, run by
`npm run check:kit`) requires before the asset may stand in a zone.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from .core import REPO, GAME_H, Finding, write_json, merge_findings, COLOURS
from . import detail as D, construct as C, bands as B, screen as SC

ZONES = os.path.join(REPO, 'game', 'zones')
CATALOGUE = os.path.join(REPO, 'art', 'catalogue')
BRAMBLE = os.path.join(REPO, 'game', 'assets', 'characters', 'bramble', 'sheets', 'idle_S.png')
ZONE_BIOME = {'woodland': 'woodland', 'crossroads': 'valley', 'undercroft': 'cellar', 'kit': 'woodland'}
BIOME_GROUND = {'woodland': (150, 166, 92), 'valley': (150, 166, 92), 'meadow': (150, 166, 92),
                'desert': (214, 178, 120), 'cellar': (96, 88, 84)}
NEUTRAL = (128, 128, 128)
GROUND_ASSETS = {'ground', 'flow'}
FAIL_SEVERITIES = {'blocker', 'fault'}


def sha256(path: str) -> str:
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


# the 2x kit's ground props (scripts/art/native/props.py), drawn into ground pictures rather than
# placed as sprites: reviewed as assets in their own right at the game's density
KIT = {
    'mushroom_ring': ('mushroom_ring4', {}), 'fern': ('fern4', {}), 'boulder': ('boulder4', {}),
    'bench': ('bench4', {}), 'stump': ('stump4', {}), 'log': ('log4', {}), 'lantern': ('lantern4', {}),
    'signpost': ('signpost4', {}), 'fence': ('fence4', {}), 'post': ('post4', {}),
}
KIT_DIR = os.path.join(REPO, 'artifacts', 'review', 'kit')


def render_kit(name: str, density: float = 3.0) -> str:
    from scripts.art.native import ctx, load_biome
    if not ctx._configured:
        ctx.configure(density, load_biome('meadow'), {})
    from scripts.art.native import props as P
    fn, kw = KIT[name]
    img, _, _ = getattr(P, fn)(density, **kw)
    os.makedirs(KIT_DIR, exist_ok=True)
    p = os.path.join(KIT_DIR, name + '.png')
    img.save(p)
    return p


def asset_path(ref: str) -> tuple[str, str, str]:
    """(path, zone, name) for 'zone/name', 'zone/art/name.png', 'kit/name' or a png path."""
    if ref.startswith('kit/'):
        name = ref.split('/', 1)[1]
        return render_kit(name), 'kit', name
    if os.path.exists(ref):
        p = os.path.abspath(ref)
        parts = p.split(os.sep)
        zone = parts[parts.index('zones') + 1] if 'zones' in parts else (parts[-2] if len(parts) > 1 else 'new')
        return p, zone, os.path.splitext(os.path.basename(p))[0]
    zone, name = ref.split('/', 1)
    name = name.replace('art/', '').replace('.png', '')
    p = os.path.join(ZONES, zone, 'art', name + '.png')
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    return p, zone, name


def all_assets() -> list[tuple[str, str, str]]:
    out = []
    for p in sorted(glob.glob(os.path.join(ZONES, '*', 'art', '**', '*.png'), recursive=True)):
        rel = os.path.relpath(p, ZONES).split(os.sep)
        zone = rel[0]
        name = '/'.join(rel[2:])[:-4]
        out.append((p, zone, name))
    return out


def bramble() -> Image.Image:
    im = Image.open(BRAMBLE).convert('RGBA')
    return im.crop((0, 0, 160, 144)).crop(im.crop((0, 0, 160, 144)).getbbox())


def on_ground(rgba: np.ndarray, colour) -> np.ndarray:
    a = rgba[..., 3:4] / 255.0
    bg = np.zeros_like(rgba[..., :3], dtype=float)
    bg[:] = colour
    return (rgba[..., :3] * a + bg * (1 - a)).astype(np.uint8)


def group_of(kind: str, rgb, alpha) -> str:
    fam = D.family_map(rgb)
    if (alpha & (fam == 1)).sum() > 0.5 * alpha.sum():
        return 'foliage'
    if kind in ('boulder', 'standing_stone', 'rock', 'crag', 'cairn'):
        return 'stone'
    return 'prop'


def review(path: str, zone: str, name: str, kind: str | None = None, biome: str | None = None,
           H: float = GAME_H, density: float = 3.0) -> dict:
    img = Image.open(path).convert('RGBA')
    rgba = np.asarray(img)
    base = os.path.basename(name)
    kind = kind or C.kind_of(base)
    biome = biome or ZONE_BIOME.get(zone, 'valley')
    findings, score = review_rgba(rgba, f'{zone}/{name}', kind, biome, H, density, ground=base in GROUND_ASSETS)
    sev = [f.severity for f in findings]
    status = 'fail' if any(s in FAIL_SEVERITIES for s in sev) else 'pass'
    return dict(id=f'{zone}/{name}', file=os.path.relpath(path, REPO), sha256=sha256(path), kind=kind, biome=biome,
                H=H, density=density, size=list(img.size), status=status,
                counts={s: sev.count(s) for s in ('blocker', 'fault', 'polish')},
                detail_bar=score, findings=[f.to_json() for f in findings])


def review_rgba(rgba: np.ndarray, subject: str, kind: str, biome: str, H: float = GAME_H, density: float = 3.0,
                ground: bool = False):
    """Every asset check on one RGBA picture (alpha marks the object). Returns (findings, detail bar)."""
    alpha = rgba[..., 3] > 128
    findings: list[Finding] = []
    score = None
    if subject.endswith('_shadow'):
        # a ground-coded cast and contact shadow picture (town.py): no form or material to judge;
        # the scene gate checks where shadows fall
        return [], None
    if ground or alpha.mean() > 0.97:
        # a ground or background picture: judged like a screen (water, repetition, flats, artefacts)
        ignore = SC.hud_mask(rgba) | ~alpha       # transparent parts of an overlay are not art
        rep = SC.review_screen(rgba, H, biome=biome, subject=subject, ignore=ignore)
        findings = list(rep['_objs'])
        # organic edges on the soft grid (edges.py): judged on the ground picture itself, where no
        # sprite stands on them (on a composed screen trunks, logs and props join the dirt)
        from . import edges as E
        findings += E.ragged_ground(rgba[..., :3], H, subject, ignore)
    else:
        rgb_n = on_ground(rgba, NEUTRAL)
        f1, parts = D.judge_object(rgb_n, alpha, H, subject, kind=kind)
        findings += f1
        findings += C.floating_parts(alpha, H, subject)
        findings += C.stilts(rgb_n, alpha, H, subject)
        findings += C.dotted(rgb_n, alpha, H, subject)
        findings += C.scale(alpha, H, kind, subject, density)
        findings += C.mushrooms(rgb_n, alpha, H, subject, density)
        findings += C.biome_form(rgb_n, alpha, H, subject, biome)
        findings += C.crown_holes(rgb_n, alpha, H, subject)
        findings += C.water_shape(rgb_n, alpha, H, subject)
        findings += C.object_light(rgb_n, alpha, H, subject)
        findings += C.repeated_parts(rgb_n, alpha, H, subject)
        findings += C.glyphs(rgb_n, alpha, H, subject)
        findings += C.construction(rgb_n, alpha, H, subject, kind)
        findings += C.cylinder(rgb_n, alpha, H, subject)
        from . import edges as E
        if any(k in subject.split('/')[-1] for k in E.ORGANIC_SPRITES):
            # a laid-out piece of ground drawn as a sprite (beds, a pond): its outline on the soft grid
            findings += E.ragged(alpha, H, subject, min_area=0.02, sprite=True)
        ol = D.outline_share(rgb_n, alpha)
        if ol < 0.4 and alpha.sum() > 0.05 * H * H:
            x0, y0, x1, y1 = C.bbox(alpha)
            findings.append(Finding('detail.outline', 'polish', (x0, y0, x1, y1),
                                    f'{subject}: only {ol:.0%} of the silhouette is drawn in an edge tone',
                                    'close the silhouette in the material\'s own dark edge tone (the house outline), '
                                    'broken only where the light hits (art-style.md 1)', score=ol, threshold=0.4,
                                    subject=subject))
        grp = group_of(kind, rgb_n, alpha)
        score = B.score(rgb_n, alpha, H, grp)
        score['group'] = grp
        if score.get('ratio') is not None:
            r = score['ratio']
            low = 0.3 if grp == 'foliage' else 0.45
            if r < 0.9:
                x0, y0, x1, y1 = C.bbox(alpha)
                findings.append(Finding('detail.bar', 'fault' if r < low else 'polish', (x0, y0, x1, y1),
                                        f'{subject}: detail bar {r:.2f} of Eastward\'s {grp} band '
                                        f'({score["ours"]["tones"]:.1f} tones, {score["ours"]["shapes"]:.1f} shapes a patch '
                                        f'against {score["band"]["tones"]}, {score["band"]["shapes"]})',
                                        'add drawn structure in clusters of two or more pixels: parts, joints, wear, '
                                        'texture of the material, small story details (art-style.md, Eastward\'s level of '
                                        'detail is required)', score=r, threshold=0.9, subject=subject))
    return merge_findings(findings, iou=0.5), score


# ------------------------------------------------------------------------------------------
def anchors() -> list[dict]:
    """The style anchors (catalogue records with `style_anchor`): the props Matt named as the style
    he is going for (26 Oct: the bench and the green-capped lamp). Every asset sheet shows them."""
    out = []
    for rec in sorted(glob.glob(os.path.join(CATALOGUE, '*', '*.json'))):
        try:
            r = json.load(open(rec))
        except Exception:
            continue
        if r.get('style_anchor'):
            out.append(r)
    return out


def siblings(zone: str, name: str, kind: str, n: int = 3) -> list[str]:
    """The same category in the catalogue, approved first; then the style anchors."""
    out = []
    for rec in sorted(glob.glob(os.path.join(CATALOGUE, '*', '*.json'))):
        try:
            r = json.load(open(rec))
        except Exception:
            continue
        if r.get('kind') == kind and r.get('id') != f'{zone}/{name}':
            out.append((0 if r.get('status') == 'pass' else 1, r['file']))
    sib = [f for _, f in sorted(out)[:n]]
    for r in anchors():
        f = r['file']
        if r.get('id') != f'{zone}/{name}' and f not in sib:
            if not os.path.exists(os.path.join(REPO, f)) and r['id'].startswith('kit/'):
                render_kit(r['id'].split('/', 1)[1])
            sib.append(f)
    return sib


def sheet(path: str, report: dict, out: str) -> None:
    """The asset alone at 1x and 4x, on neutral grey and its biome's ground, beside Bramble for
    scale and beside up to three siblings, every finding boxed on the 4x copy."""
    im = Image.open(path).convert('RGBA')
    br = bramble()
    zone, name = report['id'].split('/', 1)
    sibs = [Image.open(os.path.join(REPO, f)).convert('RGBA') for f in siblings(zone, name, report['kind'])]
    ground = BIOME_GROUND.get(report['biome'], (150, 166, 92))
    z = 4
    big = im.resize((im.width * z, im.height * z), Image.NEAREST)
    W = max(im.width * z + 20, 4 * (im.width + br.width + 20) + sum(s.width + 10 for s in sibs) + 40, 520)
    Hs = 30 + im.height * z + 30 + max([im.height, br.height] + [s.height for s in sibs]) * 2 + 60
    canvas = Image.new('RGBA', (W, Hs), (24, 24, 24, 255))
    d = ImageDraw.Draw(canvas)
    d.text((6, 6), f'{report["id"]}  kind {report["kind"]}  biome {report["biome"]}  status {report["status"].upper()}  '
                   f'{report["counts"]}', fill=(240, 240, 240, 255))
    # 4x on neutral with boxes
    bg = Image.new('RGBA', big.size, NEUTRAL + (255,))
    bg.alpha_composite(big)
    bd = ImageDraw.Draw(bg)
    for i, f in enumerate(report['findings']):
        x0, y0, x1, y1 = [v * z for v in f['box']]
        c = COLOURS.get(f['severity'], (255, 255, 0)) + (255,)
        bd.rectangle([x0, y0, x1 - 1, y1 - 1], outline=c, width=2)
        bd.text((x0 + 2, y0 + 1), str(i + 1), fill=c)
    canvas.alpha_composite(bg, (10, 26))
    y = 26 + big.height + 10
    # 1x and 2x rows: neutral and biome ground, with Bramble and siblings
    for row, colour in enumerate((NEUTRAL, ground)):
        for k, zz in enumerate((1, 2)):
            strip = [im] + [br] + sibs
            x = 10 + k * (W // 2)
            hmax = max(s.height for s in strip) * zz
            panel = Image.new('RGBA', (W // 2 - 20, hmax + 8), colour + (255,))
            px = 4
            for s in strip:
                ss = s.resize((s.width * zz, s.height * zz), Image.NEAREST)
                if px + ss.width > panel.width:
                    break
                panel.alpha_composite(ss, (px, hmax + 4 - ss.height))
                px += ss.width + 6
            canvas.alpha_composite(panel, (x, y))
        y += max(s.height for s in [im, br] + sibs) * 2 + 14
    canvas.convert('RGB').save(out)


def record(report: dict, reviewer: dict | None = None) -> str:
    zone, name = report['id'].split('/', 1)
    p = os.path.join(CATALOGUE, zone, name.replace('/', '__') + '.json')
    rec = dict(report)
    rec['reviewed'] = datetime.date.today().isoformat()
    rec['reviewer'] = reviewer or {'agent': 'detail-auditor', 'verdict': 'pending',
                                   'note': 'detectors only; the agent checklist has not been run on this asset'}
    rec['findings'] = [{k: f[k] for k in ('detector', 'severity', 'box', 'message', 'fix')} for f in report['findings']]
    write_json(p, rec)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('asset', nargs='*', help="zone/name, or a png path")
    ap.add_argument('--all', action='store_true', help='every asset under game/zones/*/art')
    ap.add_argument('--kit', action='store_true', help='also the 2x kit ground props (kit/<name>)')
    ap.add_argument('--kind')
    ap.add_argument('--biome')
    ap.add_argument('--out', default=os.path.join(REPO, 'artifacts', 'review', 'assets'))
    ap.add_argument('--record', action='store_true', help='write the catalogue entry (art/catalogue)')
    ap.add_argument('--no-sheet', action='store_true')
    a = ap.parse_args(argv)
    items = all_assets() if a.all else [asset_path(r) for r in a.asset]
    if a.kit:
        items += [asset_path('kit/' + k) for k in KIT]
    if not items:
        ap.error('name an asset or pass --all')
    os.makedirs(a.out, exist_ok=True)
    summary = []
    for path, zone, name in items:
        rep = review(path, zone, name, a.kind, a.biome)
        stem = f'{zone}__{name.replace("/", "__")}'
        write_json(os.path.join(a.out, stem + '.json'), rep)
        if not a.no_sheet:
            sheet(path, rep, os.path.join(a.out, stem + '.png'))
        if a.record:
            record(rep)
        summary.append((rep['id'], rep['status'], rep['counts'], sorted({f['detector'] for f in rep['findings']
                                                                        if f['severity'] in FAIL_SEVERITIES})))
        print(f'{rep["status"].upper():4s} {rep["id"]:40s} {rep["counts"]}  '
              f'{", ".join(summary[-1][3])}')
    fails = sum(1 for s in summary if s[1] == 'fail')
    print(f'\n{len(summary)} assets, {fails} fail, {len(summary) - fails} pass. Reports and sheets in {a.out}')
    return 0 if fails == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
