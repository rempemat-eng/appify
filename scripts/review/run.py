"""The scene gate runner.

    npm run review:scene -- woodland                         # a Godot zone: render, scene data, both detector sets
    npm run review:scene -- game/zones/woodland/woodland.tscn
    npm run review:scene -- shot.png [--scale 3.14] [--H 74]  # any picture (a screenshot, a crop, a mock-up)
    npm run review:scene -- crossroads --spawn square --stage homecoming
    npm run review:scene -- woodland --no-render              # scene data and the zone composite only

For a zone it renders the game at 1920 x 1080 on DISPLAY or its own Xvfb (docs/godot.md) at each
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

Exit status 1 when any blocker or fault is found; 2 when rendering is incomplete.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image

from .core import REPO, GAME_H, to_native, crop_nonblack, annotate, crop_sheet, write_json, Finding
from . import screen as SC, scene as SN

GRID = (6, 4)          # columns x rows of the audit grid on a 960 x 540 screen (160 x 135 art px a cell)
ENGINE_ERROR = re.compile(r'^\s*(?:SCRIPT ERROR|ERROR:|Parse Error|Failed loading resource|Cannot open file|godot errors at)', re.M)


class RenderError(RuntimeError):
    """A failed producer must never be mistaken for current capture evidence."""


def _log_text(value) -> str:
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')


def _godot_command(args: list[str], env: dict, log_path: str, timeout: int) -> None:
    try:
        result = subprocess.run(args, cwd=REPO, env=env, capture_output=True, text=True, timeout=timeout)
        log = _log_text(result.stdout) + '\n' + _log_text(result.stderr)
    except (OSError, subprocess.SubprocessError) as exc:
        log = _log_text(getattr(exc, 'stdout', '')) + '\n' + _log_text(getattr(exc, 'stderr', '')) + '\n' + str(exc)
        with open(log_path, 'w') as handle:
            handle.write(log)
        raise RenderError(f'Godot command failed: {exc}; see {log_path}') from exc
    with open(log_path, 'w') as handle:
        handle.write(log)
    if result.returncode or ENGINE_ERROR.search(log):
        raise RenderError(f'Godot command failed (exit {result.returncode}); see {log_path}')


def godot_bin() -> str:
    env = os.environ.get('GODOT')
    if env:
        if os.path.isfile(env) and os.access(env, os.X_OK):
            return env
        raise RenderError(f'Godot executable is unavailable: {env}')
    out = subprocess.run(['bash', os.path.join(REPO, 'game', 'tools', 'get_godot.sh')], capture_output=True,
                         text=True, cwd=REPO)
    lines = out.stdout.strip().splitlines()
    if out.returncode or ENGINE_ERROR.search(out.stdout + '\n' + out.stderr) or not lines:
        raise RenderError(f'Godot acquisition failed (exit {out.returncode}): {out.stdout}\n{out.stderr}')
    path = lines[-1]
    if not os.path.isfile(path) or not os.access(path, os.X_OK):
        raise RenderError(f'Godot acquisition returned no executable: {path}')
    return path


def start_xvfb(w=1920, h=1080):
    for n in range(91, 99):
        if os.path.exists(f'/tmp/.X11-unix/X{n}') or os.path.exists(f'/tmp/.X{n}-lock'):
            continue
        p = subprocess.Popen(['Xvfb', f':{n}', '-screen', '0', f'{w}x{h}x24'], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        if p.poll() is None:
            return p, f':{n}'
    raise RenderError('no free X display for Xvfb')


def render(zone: str, spawns: list[str], out: str, stage: str | None = None, at: str | None = None,
           wait: float = 4.0) -> list[str]:
    """Screenshots of a zone at 1920 x 1080, one per spawn, with a disposable user folder. The
    shot waits `wait` seconds so the damped camera has settled (a 2 s shot of a fresh start
    catches the camera still travelling in from the world's corner: render with --wait 1 to
    review the zone entry itself)."""
    xv = None
    shots = []
    try:
        if not spawns:
            raise RenderError('capture coverage is empty: no requested spawns')
        if any(not value or '/' in value or '\\' in value for value in [zone, *spawns]):
            raise RenderError('capture identifiers must be single path components')
        if 'zone' in spawns:
            raise RenderError("capture spawn 'zone' collides with the zone composite")
        g = godot_bin()
        with tempfile.TemporaryDirectory(prefix='review-godot-') as tmp:
            env = dict(os.environ, XDG_CONFIG_HOME=os.path.join(tmp, 'cfg'), XDG_DATA_HOME=os.path.join(tmp, 'data'))
            if not env.get('DISPLAY', '').strip():
                xv, env['DISPLAY'] = start_xvfb()
            try:
                # Remove prior outputs before import/render: an existing PNG is not proof of a new capture.
                for sp in spawns:
                    shot = os.path.join(out, f'{zone}_{sp}.png')
                    if os.path.lexists(shot):
                        os.unlink(shot)
                _godot_command([g, '--headless', '--path', 'game', '--import'], env,
                               os.path.join(out, 'render-import.log'), 600)
                for sp in spawns:
                    shot = os.path.join(out, f'{zone}_{sp}.png')
                    if os.path.lexists(shot):
                        os.unlink(shot)
                    args = [g, '--path', 'game', '--audio-driver', 'Dummy', '--resolution', '1920x1080', '--position', '0,0',
                            '--', '--fresh', f'--zone={zone}', f'--spawn={sp}', f'--wait={wait}', f'--shot={shot}']
                    if stage:
                        args.append(f'--stage={stage}')
                    if at:
                        args.append(f'--at={at}')
                    started = time.time()
                    _godot_command(args, env, os.path.join(out, f'{zone}_{sp}.log'), 180)
                    if os.path.islink(shot) or not os.path.isfile(shot) or os.stat(shot).st_mtime < started - 2:
                        raise RenderError(f'capture missing or stale: {shot}')
                    try:
                        with Image.open(shot) as image:
                            if image.format != 'PNG':
                                raise ValueError('not a PNG')
                            image.verify()
                    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
                        raise RenderError(f'capture is not a valid PNG: {shot}: {exc}') from exc
                    shots.append(shot)
            finally:
                if xv is not None:
                    xv.terminate()
                    try:
                        xv.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        xv.kill()
                        xv.wait(timeout=5)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RenderError(f'Godot render failed: {exc}') from exc
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
    # Invalidate an explicitly reused output even if registry loading fails before target resolution.
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        prior_report = os.path.join(a.out, 'report.json')
        if os.path.lexists(prior_report):
            os.unlink(prior_report)
    with open(os.path.join(REPO, 'game', 'data', 'zones.json')) as handle:
        zones = json.load(handle)
    zone = None
    if t in zones:
        zone = t
    elif t.endswith('.tscn'):
        zone = os.path.basename(t)[:-5].replace('_base', '')
    name = zone or os.path.splitext(os.path.basename(t))[0]
    out = a.out or os.path.join(REPO, 'artifacts', 'review', name)
    os.makedirs(out, exist_ok=True)
    report_path = os.path.join(out, 'report.json')
    if os.path.lexists(report_path):
        os.unlink(report_path)
    report = dict(target=t, generated=time.strftime('%Y-%m-%d %H:%M'), pictures=[], scene=None)

    if zone:
        z = SN.load_zone(zone)
        res = SN.review_zone(zone, a.H)
        comp = SN.composite(z)
        Image.fromarray(comp[..., :3]).save(os.path.join(out, f'{zone}_zone.png'))
        report['scene'] = dict(zone=zone, size=list(z.size), sprites=len(z.sprites), spawns=list(z.spawns),
                               doors=[{k: d[k] for k in ('name', 'zone', 'spawn')} for d in z.doors],
                               findings=[f.to_json() for f in res['findings']])
        report['pictures'].append(review_picture(comp, a.H, f'{zone}_zone', out, extra=res['findings'], biome=a.biome))
        if not a.no_render:
            spawns = a.spawn or list(z.spawns)
            try:
                for shot in render(zone, spawns, out, a.stage, a.at, a.wait):
                    with Image.open(shot) as img:
                        native, s, org = to_native(img, 2.0)
                    report['pictures'].append(review_picture(native, a.H, os.path.splitext(os.path.basename(shot))[0], out,
                                                             s, org, biome=a.biome))
            except RenderError as exc:
                report.update(incomplete=True, errors=[str(exc)])
                print(str(exc), file=sys.stderr)
    else:
        img = Image.open(t)
        img, off = crop_nonblack(img)
        native, s, org = to_native(img, a.scale)
        org = (org[0] + off[0], org[1] + off[1])
        report['pictures'].append(review_picture(native, a.H, name, out, s, org, biome=a.biome))

    allf = [f for p in report['pictures'] for f in p['findings']]
    if report['scene']:
        allf += report['scene']['findings']
    counts = {k: sum(1 for f in allf if f['severity'] == k) for k in ('blocker', 'fault', 'polish')}
    report['counts'] = counts
    write_json(report_path, report)
    print(f'{name}: {counts} -> {os.path.relpath(out, REPO)}/report.json')
    for p in report['pictures']:
        for i, f in enumerate(p['findings']):
            print(f'  [{p["picture"]} #{i + 1}] {f["severity"]:7s} {f["detector"]:24s} {f["box"]} {f["message"][:110]}')
    return 2 if report.get('incomplete') else (1 if counts['blocker'] or counts['fault'] else 0)


if __name__ == '__main__':
    sys.exit(main())
