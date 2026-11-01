#!/usr/bin/env python3
"""Exact content key for derived Godot imports; never a test-result cache."""
import argparse
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys

EXTRA = ('.github/workflows/godot.yml', 'scripts/godot-import-cache.py',
         'scripts/godot-import-cache.test.py')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)


def regular(root, name):
    path = root / name
    relative = path.relative_to(root)
    for parent in [relative, *relative.parents]:
        if (root / parent).is_symlink():
            raise ValueError(f'symlink input: {name}')
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f'not a regular input: {name}')
    return path.read_bytes()


def cache_key(root, engine, runner_os, runner_arch):
    root = Path(root).resolve()
    if Path(os.fsdecode(git(root, 'rev-parse', '--show-toplevel')).strip()).resolve() != root:
        raise ValueError('root must be the repository top level')
    if not runner_os or not runner_arch:
        raise ValueError('runner OS and architecture are required')
    if git(root, 'ls-files', '--others', '--exclude-standard', '-z', '--', 'game'):
        raise ValueError('untracked game input; use a clean checkout or stage new source')
    inputs = {}
    for record in git(root, 'ls-files', '--stage', '-z', '--', 'game').split(b'\0'):
        if not record:
            continue
        metadata, name = record.split(b'\t', 1)
        mode, _, stage = metadata.split()
        name = os.fsdecode(name)
        if stage != b'0' or mode not in (b'100644', b'100755'):
            raise ValueError(f'unsupported index entry: {name}')
        if name.startswith(('game/.godot/', 'game/reports/')):
            raise ValueError(f'generated output tracked as input: {name}')
        inputs[name] = mode
    if 'game/project.godot' not in inputs:
        raise ValueError('tracked game/project.godot is required')
    for name in EXTRA:
        inputs[name] = b'extra'
    digest = hashlib.sha256()

    def field(value):
        digest.update(len(value).to_bytes(8, 'big'))
        digest.update(value)

    field(b'mygame-godot-import-v1')
    field(runner_os.encode())
    field(runner_arch.encode())
    engine = Path(engine).absolute()
    field(hashlib.sha256(regular(engine.parent, engine.name)).digest())
    for name in sorted(inputs, key=os.fsencode):
        field(os.fsencode(name))
        field(inputs[name])
        field(regular(root, name))
    return 'godot-import-v1-' + digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--engine', required=True)
    parser.add_argument('--runner-os', required=True)
    parser.add_argument('--runner-arch', required=True)
    args = parser.parse_args()
    try:
        key = cache_key(args.root, args.engine, args.runner_os, args.runner_arch)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Godot import cache: {error}', file=sys.stderr)
        return 2
    print(key)
    return 0


if __name__ == '__main__':
    sys.exit(main())
