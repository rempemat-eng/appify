#!/usr/bin/env python3
"""Verify lossless kit extraction against #245's exact canonical input, without network access.

Usage: python3 game/combat/check_canonical_split.py /path/to/abilities-v1.json
The original file can be recovered with git show 1820a07:<path recorded in units.json>.
This is a data integrity check, not evidence that the runtime effects have been ported.
"""
import hashlib
import json
from pathlib import Path
import sys


def validate(source: Path, target: Path) -> None:
    raw = source.read_bytes()
    provenance = json.loads((target / 'units.json').read_text())['canonical_source']
    if hashlib.sha256(raw).hexdigest() != provenance['sha256']:
        raise ValueError('canonical input SHA-256 mismatch')
    original = json.loads(raw)
    shared = json.loads((target / 'canonical-shared.json').read_text())
    reconstructed = dict(shared)
    reconstructed['characters'] = [json.loads((target / (c['id'] + '.json')).read_text())
                                   for c in original['characters']]
    if reconstructed != original:
        raise ValueError('canonical split differs from original data')
    expected = {c['id'] + '.json' for c in original['characters']}
    actual = {p.name for p in target.glob('*.json')} - {'units.json', 'canonical-shared.json'}
    if actual != expected:
        raise ValueError('missing or extra character records')
    print(f'PASS: {len(expected)} kits and all shared rules exactly match pinned #245 input')


if __name__ == '__main__':
    validate(Path(sys.argv[1]), Path(__file__).resolve().parents[1] / 'data' / 'abilities')
