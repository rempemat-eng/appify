#!/usr/bin/env python3
"""Recover only the two hash-pinned pure combat modules from the archived ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'zipSha256': '0b0374b323d4525317b32deb57560a85c947e37fa1801a0835249f76cc05cd1c',
    'bundle': 'entry-6fdd0ef25567acc156c4a1e86a9a36fe.js',
    'bundleSha256': '94f8b4e105ea17d635f2fe7ae6a23d33b4f2fe1cc764761d64a4423b8d1ef82c',
    'catalogueModule': 3501,
    'catalogueSha256': '8b2dc37132bc29f9e9f184b42abc209933a2ba98f35ef46e9c1061838492ad6f',
    'engineModule': 3500,
    'engineSha256': '21aa782577f3d2fc51389efdd80c4c61a1a7ddd48d128e01eb318daa75d6bc10',
    'libraryFileId': 'libfile_a8686f8b8cfc8191b71d7f2712de1cd8',
}

def digest(value):
    return hashlib.sha256(value).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def extract(path):
    require(digest(path.read_bytes()) == EXPECTED['zipSha256'], 'Wrong archive SHA-256')
    with ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith('/' + EXPECTED['bundle'])]
        require(len(names) == 1, 'Expected exactly one pinned bundle')
        bundle = archive.read(names[0])
    require(digest(bundle) == EXPECTED['bundleSha256'], 'Wrong bundle SHA-256')
    result = {'provenance': EXPECTED}
    for label, ending in [('catalogue', b'},3501,[]);'), ('engine', b'},3500,[3501]);')]:
        lines = [line for line in bundle.splitlines(keepends=True) if line.rstrip(b'\r\n').endswith(ending)]
        require(len(lines) == 1, f'{label}: ambiguous module boundary')
        candidates = [lines[0], lines[0].rstrip(b'\r\n')]
        matches = [line for line in candidates if digest(line) == EXPECTED[label + 'Sha256']]
        require(bool(matches), f'{label}: byte identity failed')
        result[label] = matches[0].decode('utf-8')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    recovered = extract(args.archive)
    destination = ROOT / 'reference/original-modules.json'
    if args.check:
        require(json.loads(destination.read_text()) == recovered, 'Committed reference differs')
        print('PASS: archive, bundle and both original pure modules match exactly')
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(recovered, indent=2) + '\n')
        print(destination)
