"""Calibration: recall on Matt's flagged faults, false positives on approved and reference art.

    python3 -m scripts.review.calibrate --flagged <folder of Matt's screenshots> \\
        --eastward <folder of Eastward shots 08.jpg ...> [--out artifacts/review/calibration]

Recall: every fault in calibration_set.json must be caught by at least one of its routes
(screen: the image detectors on Matt's picture, boxed inside the fault; zone: the scene data
checks on the Godot zone, boxed inside the fault's zone box; asset: the asset gate on the
asset that draws it, with one of the listed detectors).

False positives: every fault-level finding on art that is approved or is the reference counts
as one: the image detectors on the pilot golden and on five clean daylight Eastward shots
(screens), and the asset checks on prop crops cut from them (objects). The pictures are local
only; the numbers are written to calibration_results.json beside this file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

from .core import REPO, to_native, crop_nonblack, box_overlap, write_json, annotate
from . import screen as SC, scene as SN, assets as A, objects as O

HERE = os.path.dirname(os.path.abspath(__file__))
FAULTS = ('blocker', 'fault')


def hit(findings, detectors, box, size=None):
    whole = box is not None and size is not None and (box[2] - box[0]) * (box[3] - box[1]) >= 0.5 * size[0] * size[1]
    for f in findings:
        if (f.get('extra') or {}).get('summary') and not whole:
            continue
        if f['detector'] in detectors and f['severity'] in FAULTS:
            if box is None or box_overlap(f['box'], box) > 0.2:
                return f
    return None


def pinned(ref: str, folder: str):
    """An asset as it was at a commit: 'zone/name@commit' or 'file:<repo path>@commit|x0,y0,x1,y1'."""
    import subprocess
    crop = None
    if '|' in ref:
        ref, c = ref.split('|')
        crop = tuple(int(v) for v in c.split(','))
    what, commit = ref.split('@')
    if what.startswith('file:'):
        rp = what[5:]
        zone = rp.split('/')[1] if rp.startswith('game/') else 'file'
        name = os.path.splitext(os.path.basename(rp))[0]
        if rp.startswith('game/bosses/'):
            zone = rp.split('/')[2]
    else:
        zone, name = what.split('/', 1)
        rp = f'game/zones/{zone}/art/{name}.png'
    data = subprocess.run(['git', 'show', f'{commit}:{rp}'], cwd=REPO, capture_output=True, check=True).stdout
    d = os.path.join(folder, commit, zone)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, name + '.png')
    open(out, 'wb').write(data)
    if crop:
        Image.open(out).crop(crop).save(out)
    return out, zone, name


def pinned_game(zone: str, commit: str, folder: str) -> str:
    """The zone's scene data as it was at a commit, in a folder laid out like game/: its data, its
    zone folder and every res:// file the scenes reach (followed through instanced scenes). A
    zone fault stays a test of the detectors after the zone itself is fixed (W7, W8, W12)."""
    import re
    import subprocess
    root = os.path.join(folder, commit, 'game')
    if os.path.isdir(os.path.join(root, 'zones', zone)):
        return root
    os.makedirs(os.path.join(folder, commit), exist_ok=True)
    tar = subprocess.run(['git', 'archive', commit, 'game/data', f'game/zones/{zone}'], cwd=REPO,
                         capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', os.path.join(folder, commit)], input=tar, check=True)
    todo = [os.path.join(root, 'zones', zone, f) for f in os.listdir(os.path.join(root, 'zones', zone))
            if f.endswith('.tscn')]
    seen = set()
    while todo:
        t = todo.pop()
        for rp in re.findall(r'res://([^"]+)', open(t, errors='ignore').read()):
            out = os.path.join(root, rp)
            if rp in seen or os.path.exists(out):
                continue
            seen.add(rp)
            r = subprocess.run(['git', 'show', f'{commit}:game/{rp}'], cwd=REPO, capture_output=True)
            if r.returncode:
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'wb').write(r.stdout)
            if rp.endswith('.tscn'):
                todo.append(out)
    return root


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--flagged', required=True)
    ap.add_argument('--eastward', required=True)
    ap.add_argument('--out', default=os.path.join(REPO, 'artifacts', 'review', 'calibration'))
    a = ap.parse_args(argv)
    cal = json.load(open(os.path.join(HERE, 'calibration_set.json')))
    H = cal['H']
    os.makedirs(a.out, exist_ok=True)

    screens, zones, assets, sizes = {}, {}, {}, {}

    def screen(img):
        if img not in screens:
            im, off = crop_nonblack(Image.open(os.path.join(a.flagged, img)))
            nat, s, org = to_native(im)
            biome = cal.get('images', {}).get(img, {}).get('biome', '')
            rep = SC.review_screen(nat, H, biome=biome)
            screens[img] = rep['findings']
            sizes[img] = (nat.shape[1], nat.shape[0])
            annotate(nat, rep['_objs'], os.path.join(a.out, 'flagged_' + img), zoom=2, title=img)
        return screens[img]

    def zone(z):
        """'woodland' is the zone now; 'woodland@<commit>' the zone as Matt saw it (pinned_game)."""
        if z not in zones:
            name, _, commit = z.partition('@')
            keep = SN.GAME
            if commit:
                SN.GAME = pinned_game(name, commit, os.path.join(a.out, 'pinned'))
            try:
                zones[z] = [f.to_json() for f in SN.review_zone(name, H, wiring=False)['findings']]
            finally:
                SN.GAME = keep
        return zones[z]

    def asset(ref):
        if ref not in assets:
            if '@' in ref:
                p, zn, nm = pinned(ref, os.path.join(a.out, 'pinned'))
            else:
                # a frozen picture in the repo (scripts/review/calibration/...) or a live asset
                p, zn, nm = A.asset_path(os.path.join(REPO, ref) if ref.endswith('.png') else ref)
            assets[ref] = A.review(p, zn, nm)['findings']
        return assets[ref]

    rows = []
    for f in cal['faults']:
        caught = []
        if 'screen' in f:
            h = hit(screen(f['image']), f['screen'], f['box'], sizes.get(f['image']))
            if h:
                caught.append(('screen', h['detector'], h['box']))
        for z, spec in f.get('zone', {}).items():
            h = hit(zone(z), spec['detectors'], spec['box'])
            if h:
                caught.append(('zone ' + z, h['detector'], h['box']))
        for ref, dets in f.get('asset', {}).items():
            h = hit(asset(ref), dets, None)
            if h:
                caught.append(('asset ' + ref, h['detector'], h['box']))
        rows.append(dict(id=f['id'], what=f['what'], caught=bool(caught), by=caught))
        mark = 'CAUGHT' if caught else 'MISSED'
        print(f'{f["id"]:4s} {mark:6s} {f["what"]:60s} ' + '; '.join(f'{r} {d}' for r, d, _ in caught))
    recall = sum(r['caught'] for r in rows) / len(rows)
    print(f'\nrecall {sum(r["caught"] for r in rows)}/{len(rows)} = {recall:.0%}')

    # false positives on clean art
    fp = {}
    g = cal['clean']['golden']
    gimg = np.asarray(Image.open(os.path.join(REPO, g['path'])).convert('RGBA'))
    rep = SC.review_screen(gimg, g['H'])
    fp['golden screen'] = [f for f in rep['findings'] if f['severity'] in FAULTS]
    annotate(gimg, rep['_objs'], os.path.join(a.out, 'clean_golden.png'), zoom=1, title='golden')
    k, ground = O.ground_palette(gimg)
    for x0, y0, x1, y1, name in g['props']:
        sub = gimg[y0:y1, x0:x1].copy()
        sub[..., 3] = np.where(np.isin(k[y0:y1, x0:x1], ground), 0, 255)
        f2, _ = A.review_rgba(sub, f'golden:{name}', '', 'meadow', g['H'], 2.0)
        fp[f'golden prop {name}'] = [x.to_json() for x in f2 if x.severity in FAULTS and x.detector != 'detail.bar' and not x.extra.get('needs_alpha')]
    e = cal['clean']['eastward']
    from .calibrate_boxes import EW
    for shot in e['shots']:
        nat, s, org = to_native(Image.open(os.path.join(a.eastward, shot + '.jpg')), e['scale'])
        rep = SC.review_screen(nat, e['H'])
        fp[f'eastward {shot} screen'] = [f for f in rep['findings'] if f['severity'] in FAULTS]
        annotate(nat, rep['_objs'], os.path.join(a.out, f'clean_eastward_{shot}.png'), zoom=2, title=shot)
        if shot in EW:
            k, ground = O.ground_palette(nat)
            for x0, y0, x1, y1, name, grp in EW[shot]:
                sub = np.dstack([nat[y0:y1, x0:x1, :3], np.where(np.isin(k[y0:y1, x0:x1], ground), 0, 255).astype(np.uint8)])
                f2, _ = A.review_rgba(sub, f'eastward{shot}:{name}', '', 'valley', e['H'], 3.0)
                fp[f'eastward {shot} prop {name}'] = [x.to_json() for x in f2 if x.severity in FAULTS and x.detector != 'detail.bar' and not x.extra.get('needs_alpha')]
    print()
    nscreens = sum(1 for k in fp if 'screen' in k)
    nprops = sum(1 for k in fp if 'prop' in k)
    sfp = sum(len(v) for k, v in fp.items() if 'screen' in k)
    pfp = sum(len(v) for k, v in fp.items() if 'prop' in k)
    for k, v in fp.items():
        if v:
            print(f'FP {k}: ' + '; '.join(f'{x["detector"]} {x["box"]}' for x in v))
    print(f'\nfalse positives: {sfp} on {nscreens} clean screens ({sfp / nscreens:.1f} a screen), '
          f'{pfp} on {nprops} clean props ({pfp / nprops:.2f} a prop; the detail bar is excluded: it measures, '
          'the reference sets it; checks that need a real alpha channel are not counted on cut crops)')
    write_json(os.path.join(HERE, 'calibration_results.json'),
               dict(recall=dict(caught=sum(r['caught'] for r in rows), total=len(rows), rows=rows),
                    false_positives=dict(screens=nscreens, screen_findings=sfp, props=nprops, prop_findings=pfp,
                                         detail={k: [f'{x["detector"]} {x["box"]}' for x in v] for k, v in fp.items()})))
    return 0 if recall == 1.0 else 1


if __name__ == '__main__':
    sys.exit(main())
