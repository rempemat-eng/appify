"""Capture the frozen subject with a private TCP X server; preserve all engine errors."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('e1_produce', HERE / 'produce.py')
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)
PRIVATE = producer.ROOT.parent / 'lead-state/palette-xvfb'
XKB = Path('/usr/bin/xkbcomp')
TARGET = PRIVATE / 'root/usr/bin/xkbcomp'


def main() -> int:
    os.sched_setaffinity(0, {2})
    out = HERE / 'captures'
    out.mkdir(exist_ok=False)
    provenance = {'subject_before': producer.guard(), 'private_packages': {}}
    for p in PRIVATE.glob('*.deb'):
        provenance['private_packages'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    if not provenance['subject_before']['pass']:
        raise RuntimeError('Subject changed')
    if not TARGET.is_file():
        raise RuntimeError('Private xkbcomp missing')
    linked = False
    xv = None
    results = []
    try:
        # Atomic and never replacing a path. Lead explicitly authorised this temporary repair.
        os.symlink(str(TARGET), XKB)
        linked = True
        provenance['temporary_symlink'] = {'path': str(XKB), 'target': str(TARGET)}
        env = dict(os.environ, LD_LIBRARY_PATH=str(PRIVATE / 'root/usr/lib/x86_64-linux-gnu'),
                   LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe', LP_NUM_THREADS='1')
        with (out / 'xvfb.log').open('wb') as log:
            args = [str(PRIVATE / 'root/usr/bin/Xvfb'), ':97', '-screen', '0', '1920x1080x24',
                    '-listen', 'tcp', '-nolisten', 'unix', '-nolisten', 'local', '-ac']
            provenance['xvfb_command'] = args
            xv = subprocess.Popen(args, env=env, stdout=log, stderr=log)
            time.sleep(2)
            if xv.poll() is not None:
                raise RuntimeError('Private X server exited: inspect xvfb.log')
            with socket.create_connection(('127.0.0.1', 6097), timeout=3):
                pass
            env['DISPLAY'] = '127.0.0.1:97'
            with tempfile.TemporaryDirectory(prefix='palette-review-profile-') as profile:
                env.update(XDG_DATA_HOME=profile + '/data', XDG_CONFIG_HOME=profile + '/config',
                           XDG_CACHE_HOME=profile + '/cache')
                for zone, spawn in [('woodland_kit', 'start'), ('woodland_kit', 'undercroft'),
                                    ('kitlab_tiers', 'start')]:
                    name = zone + '-' + spawn
                    image = out / (name + '.png')
                    command = [producer.GODOT, '--path', str(producer.ROOT / 'game'),
                               '--rendering-method', 'gl_compatibility', '--audio-driver', 'Dummy',
                               '--resolution', '1920x1080', '--position', '0,0', '--', '--fresh',
                               '--zone=' + zone, '--spawn=' + spawn, '--wait=4', '--shot=' + str(image)]
                    before = producer.guard()
                    started = time.time()
                    with (out / (name + '.log')).open('wb') as log_:
                        result = subprocess.run(command, cwd=producer.ROOT, env=env,
                                                stdout=log_, stderr=log_, timeout=180, check=False)
                    after = producer.guard()
                    text = (out / (name + '.log')).read_text(errors='replace')
                    errors = [s for s in text.splitlines() if s.startswith('ERROR:') or 'SCRIPT ERROR' in s]
                    row = {'zone': zone, 'spawn': spawn, 'command': command,
                           'exit_code': result.returncode, 'duration_seconds': round(time.time() - started, 3),
                           'source_before': before, 'source_after': after, 'engine_errors': errors,
                           'png_present': image.is_file()}
                    if image.is_file():
                        row['png_sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
                    results.append(row)
                    print(name, result.returncode, 'errors', len(errors), 'png', image.is_file(), flush=True)
                    if not after['pass']:
                        raise RuntimeError('Capture changed tracked subject source; inspect without resetting')
    finally:
        if xv is not None and xv.poll() is None:
            xv.terminate()
            xv.wait(timeout=10)
        if linked and XKB.is_symlink() and os.readlink(XKB) == str(TARGET):
            XKB.unlink()
        provenance['symlink_cleanup'] = not XKB.exists() and not XKB.is_symlink()
        provenance['subject_after'] = producer.guard()
        provenance['captures'] = results
        (out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
