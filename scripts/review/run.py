"""The scene gate runner.

    npm run review:scene -- woodland                         # a Godot zone: render, scene data, both detector sets
    npm run review:scene -- game/zones/woodland/woodland.tscn
    npm run review:scene -- shot.png [--scale 3.14] [--H 74]  # any picture (a screenshot, a crop, a mock-up)
    npm run review:scene -- crossroads --spawn square --stage homecoming
    npm run review:scene -- woodland --no-render              # scene data and the zone composite only

For a zone it renders the game headless at 1920 x 1080 under Xvfb (docs/godot.md) at each
spawn (or the one asked for), brings every shot to its 960 x 540 art grid, composes the whole
zone from its scene, and runs the screen detectors (water, artefacts, repetition, flats) on
each picture and the scene detectors (occlusion, intersections, crowns at the edge, reach and
paths, painted shadows, rows, wiring) on the zone. It writes, under --out (default
artifacts/review/<name>/):

    report.json            every finding: detector, severity, box (art px), message, fix
    <picture>_boxed.png    the picture with every finding boxed and numbered
    <picture>_crops.png    one enlarged crop per finding
    grid/<picture>/r<row>c<col>.png
                           the fixed grid of 3x crops the auditors must visit, every one

Exit status 1 when any blocker or fault is found.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image

from .core import REPO, GAME_H, to_native, crop_nonblack, annotate, crop_sheet, write_json, Finding
from . import screen as SC, scene as SN

GRID = (6, 4)          # columns x rows of the audit grid on a 960 x 540 screen (160 x 135 art px a cell)


def _kit_plan(target, zone, override=None):
    """Read an explicit exported plan, or the authoritative kit plan for a zone."""
    path = override or (target if target.endswith('.json') else None)
    if path is None and zone:
        path = os.path.join(REPO, 'game', 'kit', 'zones', zone + '.json')
    if not path:
        return None
    if not os.path.isfile(path):
        if override or target.endswith('.json'):
            raise ValueError('cannot read exported kit plan: ' + str(path))
        return None
    with open(path) as stream:
        plan = json.load(stream)
    if override or target.endswith('.json'):
        if not isinstance(plan, dict):
            raise ValueError('an exported kit plan must be an object')
        return plan
    return plan if isinstance(plan, dict) and 'rows' in plan and 'legend' in plan else None


def _kit_findings(plan, error=None):
    from .kit_scene import check_zone
    raw = ([dict(check='rules.plan', message=error, at=None, severity='fault')]
           if error is not None else check_zone(plan))
    findings = []
    for f in raw:
        at = f.get('at')
        x, y = (float(at[0]) * 3, float(at[1]) * 3) if isinstance(at, (list, tuple)) and len(at) == 2 else (0, 0)
        findings.append(Finding(f['check'], 'polish' if f.get('severity') == 'advice' else 'fault',
                                (x - 6, y - 6, x + 6, y + 6), f['message'],
                                'Correct the exported cell/piece data and validate again.'))
    return raw, findings


def godot_bin() -> str:
    env = os.environ.get('GODOT')
    if env and os.path.exists(env):
        return env
    out = subprocess.run(['bash', os.path.join(REPO, 'game', 'tools', 'get_godot.sh')], capture_output=True,
                         text=True, cwd=REPO)
    return out.stdout.strip().splitlines()[-1]


def start_xvfb(w=1920, h=1080):
    for n in range(91, 99):
        if os.path.exists(f'/tmp/.X11-unix/X{n}') or os.path.exists(f'/tmp/.X{n}-lock'):
            continue
        p = subprocess.Popen(['Xvfb', f':{n}', '-screen', '0', f'{w}x{h}x24'], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        if p.poll() is None:
            return p, f':{n}'
    raise RuntimeError('no free X display for Xvfb')


def render(zone: str, spawns: list[str], out: str, stage: str | None = None, at: str | None = None,
           wait: float = 4.0) -> list[str]:
    """Screenshots of a zone at 1920 x 1080, one per spawn, with a disposable user folder. The
    shot waits `wait` seconds so the damped camera has settled (a 2 s shot of a fresh start
    catches the camera still travelling in from the world's corner: render with --wait 1 to
    review the zone entry itself)."""
    g = godot_bin()
    xv, disp = start_xvfb()
    shots = []
    tmp = tempfile.mkdtemp(prefix='review-godot-')
    env = dict(os.environ, DISPLAY=disp, XDG_CONFIG_HOME=os.path.join(tmp, 'cfg'), XDG_DATA_HOME=os.path.join(tmp, 'data'))
    try:
        subprocess.run([g, '--headless', '--path', 'game', '--import'], cwd=REPO, env=env, capture_output=True,
                       timeout=600)
        for sp in spawns:
            shot = os.path.join(out, f'{zone}_{sp}.png')
            args = [g, '--path', 'game', '--audio-driver', 'Dummy', '--resolution', '1920x1080', '--position', '0,0',
                    '--', '--fresh', f'--zone={zone}', f'--spawn={sp}', f'--wait={wait}', f'--shot={shot}']
            if stage:
                args.append(f'--stage={stage}')
            if at:
                args.append(f'--at={at}')
            r = subprocess.run(args, cwd=REPO, env=env, capture_output=True, text=True, timeout=180)
            log = r.stdout + r.stderr
            errs = [l for l in log.splitlines() if 'SCRIPT ERROR' in l or l.startswith('ERROR:')]
            if errs:
                print(f'  godot errors at {sp}: {errs[:3]}', file=sys.stderr)
            if os.path.exists(shot):
                shots.append(shot)
    finally:
        xv.terminate()
        shutil.rmtree(tmp, ignore_errors=True)
    return shots


def grid(native: np.ndarray, out_dir: str, zoom: int = 3) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    H, W = native.shape[:2]
    cols, rows = GRID
    cw, ch = int(np.ceil(W / cols)), int(np.ceil(H / rows))
    paths = []
    for r in range(int(np.ceil(H / ch))):
        for c in range(int(np.ceil(W / cw))):
            crop = native[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw, :3]
            p = os.path.join(out_dir, f'r{r}c{c}.png')
            Image.fromarray(crop).resize((crop.shape[1] * zoom, crop.shape[0] * zoom), Image.NEAREST).save(p)
            paths.append(p)
    return paths


def review_picture(native: np.ndarray, H: float, name: str, out: str, scale: float = 1.0, origin=(0, 0),
                   extra: list[Finding] | None = None, biome='') -> dict:
    rep = SC.review_screen(native, H, biome=biome, subject=name)
    fs = rep['_objs'] + (extra or [])
    annotate(native, fs, os.path.join(out, f'{name}_boxed.png'), zoom=2 if native.shape[1] <= 1000 else 1, title=name)
    crop_sheet(native, fs, os.path.join(out, f'{name}_crops.png'))
    cells = grid(native, os.path.join(out, 'grid', name))
    return dict(picture=name, size=[native.shape[1], native.shape[0]], scale=scale, H=H,
                findings=[f.to_json(scale, origin) for f in fs], grid=[os.path.relpath(c, out) for c in cells])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('target', help='a zone id, a .tscn under game/zones, or a picture')
    ap.add_argument('--plan', help='a plan JSON (default: game/data/plans/<zone>.json when it exists)')
    ap.add_argument('--out')
    ap.add_argument('--spawn', action='append', help='spawn(s) to render (default: every spawn)')
    ap.add_argument('--stage')
    ap.add_argument('--at')
    ap.add_argument('--no-render', action='store_true')
    ap.add_argument('--wait', type=float, default=4.0, help='seconds before each shot (the camera settles)')
    ap.add_argument('--scale', type=float, help='source px per art px (default: measured)')
    ap.add_argument('--H', type=float, default=GAME_H, help='character height in art px (game 74, pilot 50, Eastward 54)')
    ap.add_argument('--biome', default='')
    a = ap.parse_args(argv)

    t = a.target
    zones = json.load(open(os.path.join(REPO, 'game', 'data', 'zones.json')))
    zone = None
    if t in zones:
        zone = t
    elif t.endswith('.tscn'):
        zone = os.path.basename(t)[:-5].replace('_base', '')
    name = zone or os.path.splitext(os.path.basename(t))[0]
    out = a.out or os.path.join(REPO, 'artifacts', 'review', name)
    os.makedirs(out, exist_ok=True)
    report = dict(target=t, generated=time.strftime('%Y-%m-%d %H:%M'), pictures=[], scene=None)

    kit_error = None
    try:
        kit_plan = _kit_plan(t, zone, a.plan)
    except (OSError, ValueError) as exc:
        kit_plan, kit_error = {}, str(exc)
    kit_findings = []
    if kit_plan is not None:
        raw, kit_findings = _kit_findings(kit_plan, kit_error)
        report['kit'] = dict(zone=kit_plan.get('zone'), findings=raw)

    # An exported JSON plan is a data review; a zone id still gets the normal
    # composite/screenshot review, augmented by the same kit-plan checks.
    if kit_plan is not None and t.endswith('.json'):
        pass
    elif zone:
        z = SN.load_zone(zone)
        res = SN.review_zone(zone, a.H)
        comp = SN.composite(z)
        Image.fromarray(comp[..., :3]).save(os.path.join(out, f'{zone}_zone.png'))
        report['scene'] = dict(zone=zone, size=list(z.size), sprites=len(z.sprites), spawns=list(z.spawns),
                               doors=[{k: d[k] for k in ('name', 'zone', 'spawn')} for d in z.doors],
                               findings=[f.to_json() for f in res['findings']])
        report['pictures'].append(review_picture(comp, a.H, f'{zone}_zone', out,
                                                 extra=res['findings'] + kit_findings, biome=a.biome))
        if not a.no_render:
            spawns = a.spawn or list(z.spawns)
            for shot in render(zone, spawns, out, a.stage, a.at, a.wait):
                img = Image.open(shot)
                native, s, org = to_native(img, 2.0)
                report['pictures'].append(review_picture(native, a.H, os.path.splitext(os.path.basename(shot))[0], out,
                                                         s, org, biome=a.biome))
    else:
        img = Image.open(t)
        img, off = crop_nonblack(img)
        native, s, org = to_native(img, a.scale)
        org = (org[0] + off[0], org[1] + off[1])
        # structures that carry props, declared beside the picture (logic.composition)
        from . import composition as CP
        sts = CP.sidecar(t)
        extra = CP.check(sts) if sts else []
        from . import tiers as TI
        tp = CP.sidecar_plan(t)
        if tp and tp.get('tiers'):
            extra += TI.check(tp)
        report['pictures'].append(review_picture(native, a.H, name, out, s, org, extra=extra, biome=a.biome))

    allf = [f for p in report['pictures'] for f in p['findings']]
    if kit_plan is not None and t.endswith('.json'):
        allf += [f.to_json() for f in kit_findings]
    if report['scene']:
        allf += report['scene']['findings']
    counts = {k: sum(1 for f in allf if f['severity'] == k) for k in ('blocker', 'fault', 'polish')}
    report['counts'] = counts
    write_json(os.path.join(out, 'report.json'), report)
    print(f'{name}: {counts} -> {os.path.relpath(out, REPO)}/report.json')
    for p in report['pictures']:
        for i, f in enumerate(p['findings']):
            print(f'  [{p["picture"]} #{i + 1}] {f["severity"]:7s} {f["detector"]:24s} {f["box"]} {f["message"][:110]}')
    return 1 if counts['blocker'] or counts['fault'] else 0


if __name__ == '__main__':
    sys.exit(main())
