"""Produce source-guarded, unapproved PR302 review evidence. No subject source edits."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
HEAD = '04228475cbd9fb76e0a0a9af52240d7e40a5d858'
BASE = '71a402aff0bd64ee42a24b075317c31d1b7320a7'
GODOT = '/workspace/scratch/5f1a1f97c637/prism-verified-engine/Godot_v4.7.2-stable_linux.x86_64'
WRAPPER = ROOT.parent / 'lead-state/palette-pr-sheet-d572.py'


def git(*args: str) -> str:
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def guard() -> dict:
    head = git('rev-parse', 'HEAD')
    changed = git('status', '--porcelain', '--untracked-files=no')
    return {'head': head, 'tree': git('rev-parse', 'HEAD^{tree}'),
            'tracked_changes': changed, 'pass': head == HEAD and not changed}


def run(name: str, args: list[str], timeout: int = 600) -> dict:
    folder = OUT / 'commands' / name
    folder.mkdir(parents=True, exist_ok=False)
    before = guard()
    if not before['pass']:
        raise RuntimeError('Subject source changed; no producer started')
    started = time.time()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', GODOT=GODOT)
    with (folder / 'stdout.txt').open('wb') as stdout, (folder / 'stderr.txt').open('wb') as stderr:
        try:
            result = subprocess.run(args, cwd=ROOT, env=env, stdout=stdout,
                                    stderr=stderr, timeout=timeout, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    after = guard()
    record = {'command': args, 'started_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(started)),
              'duration_seconds': round(time.time() - started, 3), 'exit_code': code,
              'source_before': before, 'source_after': after}
    for name_ in ('stdout', 'stderr'):
        record[name_ + '_sha256'] = hashlib.sha256((folder / (name_ + '.txt')).read_bytes()).hexdigest()
    (folder / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(name, code, 'source_guard', after['pass'], flush=True)
    if not after['pass']:
        raise RuntimeError('Producer changed subject source; inspect without resetting')
    return record


def main() -> int:
    os.sched_setaffinity(0, {2})
    (OUT / 'materials').mkdir(exist_ok=True)
    (OUT / 'detail').mkdir(exist_ok=True)
    py = sys.executable
    tasks = [
        ('schema', [py, '-m', 'scripts.art.kit.schema']),
        ('kit-rules', [py, '-m', 'scripts.review.kit_rules', '--check']),
        ('ground-rules', [py, '-m', 'scripts.review.ground_rules', '--check']),
        ('plateau-swatch', [py, '-m', 'scripts.art.softgrid_swatches', str(OUT / 'swatches'), '--only', '0']),
        ('detail-bar', [py, '-m', 'scripts.art.kit.detail_bar', '--out', str(OUT / 'detail'),
                        '--swatch', str(OUT / 'swatches/swatch_0_plateau.png')]),
        ('material-sheets', [py, '-m', 'scripts.art.kit.approval', str(OUT / 'materials')]),
        ('woodland-python-preview', [py, '-m', 'scripts.art.kit.render_zone', 'woodland_kit',
                                     str(OUT / 'woodland-python-live-preview.png'), '--sprites']),
        ('y12', [py, str(WRAPPER), '--repo', str(ROOT), '--base', BASE, '--head', HEAD,
                 '--out', str(OUT / 'y12'), '--scene', 'woodland_kit', '--pr', 'PR302 frozen-head review'])
    ]
    records = []
    for name, args in tasks:
        records.append(run(name, args))
    (OUT / 'producer-summary.json').write_text(json.dumps(records, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
