"""Trees drawn over a house or over each other in a kit zone (Matt, 12 Nov, the Frostline at
bf525d25; Claude A's fault (a): "trees overlapping the hut and each other").

A kit plan (game/kit/zones/<zone>.json) places pieces from the props index by their foot. This
lays every piece's still picture where the game draws it and measures, from the pictures' own
opaque pixels (not their cell footprints, which rules.overlap in kit_scene.py checks):

  logic.tree_overlap  fault: a tree's opaque pixels cover a house's (role 'house') by more than
                      HOUSE_SHARE of the smaller picture.
                      polish: a tree covers another tree by more than TREE_SHARE. Only advice: a wood's
                      crowns overlap by design (main's woodland_kit lab, up to 0.93, and Eastward's
                      forests); a reviewer judges whether a stand by a house reads as separate trees.

    python3 -m scripts.review.kit_overlap [zone ...] [--commit <sha>] [--json]

With --commit the plan, the index and the pictures are read from that commit (the calibration
pins F3 to the Frostline as Matt saw it, bf525d25).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

from .core import REPO, Finding

HOUSE_SHARE = 0.05      # a tree over a house: the bf525d25 Frostline's trees cover the Col hut by
#                         0.09 and 0.38 of the smaller; 0ef53b94 (re-spaced) 0; main's kit zones 0
TREE_SHARE = 0.25       # a tree over a tree (polish): bf525d25 0.28 to 0.38 by the hut; 0ef53b94 at
#                         most 0.08; main's woodland_kit lab up to 0.93 (a wood)
TREE_ROLES = ('tree',)
HOUSE_ROLES = ('house', 'building')


def reader(commit: str | None):
    def read(rel: str) -> bytes:
        if commit:
            return subprocess.run(['git', 'show', f'{commit}:{rel}'], cwd=REPO, capture_output=True, check=True).stdout
        with open(os.path.join(REPO, rel), 'rb') as f:
            return f.read()
    return read


def _variant(piece: dict, name: str | None) -> dict:
    vs = piece.get('variants') or {}
    v = vs.get(name or 'still') or vs.get('still') or (next(iter(vs.values())) if vs else {})
    return v


def layout(zone: str, commit: str | None = None):
    """Every tree and house of a kit zone as (id, role, x0, y0, alpha mask) in texels."""
    read = reader(commit)
    plan = json.loads(read(f'game/kit/zones/{zone}.json'))
    index = json.loads(read('game/kit/props/index.json'))
    cache, out = {}, []
    for e in plan.get('pieces', []):
        piece = index.get(e.get('piece'))
        if not piece or piece.get('role') not in TREE_ROLES + HOUSE_ROLES:
            continue
        v = _variant(piece, e.get('variant'))
        png = v.get('png') or ''
        if not png.startswith('res://'):
            continue
        rel = 'game/' + png[len('res://'):]
        if rel not in cache:
            try:
                cache[rel] = np.asarray(Image.open(io.BytesIO(read(rel))).convert('RGBA'))[..., 3] > 128
            except (subprocess.CalledProcessError, OSError):
                cache[rel] = None
        a = cache[rel]
        if a is None:
            continue
        foot = v.get('foot') or piece.get('foot') or [a.shape[1] // 2, a.shape[0]]
        x0, y0 = int(round(e['at'][0] - foot[0])), int(round(e['at'][1] - foot[1]))
        out.append((str(e.get('id', e['piece'])), piece['role'], x0, y0, a))
    return out


def _overlap(p, q) -> tuple[int, int, int]:
    _, _, ax, ay, a = p
    _, _, bx, by, b = q
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + a.shape[1], bx + b.shape[1]), min(ay + a.shape[0], by + b.shape[0])
    if x1 <= x0 or y1 <= y0:
        return 0, int(a.sum()), int(b.sum())
    sa = a[y0 - ay:y1 - ay, x0 - ax:x1 - ax]
    sb = b[y0 - by:y1 - by, x0 - bx:x1 - bx]
    return int((sa & sb).sum()), int(a.sum()), int(b.sum())


def check(zone: str, commit: str | None = None) -> list[Finding]:
    items = layout(zone, commit)
    fs = []
    for i, p in enumerate(items):
        for q in items[i + 1:]:
            roles = {p[1], q[1]}
            if not roles & set(TREE_ROLES):
                continue
            house = bool(roles & set(HOUSE_ROLES))
            limit = HOUSE_SHARE if house else TREE_SHARE
            n, na, nb = _overlap(p, q)
            share = n / max(1, min(na, nb))
            if share <= limit:
                continue
            box = (min(p[2], q[2]), min(p[3], q[3]), max(p[2] + p[4].shape[1], q[2] + q[4].shape[1]),
                   max(p[3] + p[4].shape[0], q[3] + q[4].shape[0]))
            what = 'the house' if house else 'another tree'
            fs.append(Finding('logic.tree_overlap', 'fault' if house else 'polish', box,
                              f'{zone}: {p[0]} and {q[0]} overlap by {share:.0%} of the smaller picture: a tree drawn over '
                              f'{what} (Matt, 12 Nov: the trees by the Col hut)',
                              'move the tree clear of the house\'s walls and roof (a crown may not hide a wall, a door or a '
                              'window), and space trees so each crown reads on its own, touching at the tips at most; '
                              'thin the stand rather than stack it', score=share, threshold=limit,
                              subject=f'{p[0]}+{q[0]}'))
    return fs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('zones', nargs='*')
    ap.add_argument('--commit')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    zones = a.zones or sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(REPO, 'game', 'kit', 'zones'))
                              if f.endswith('.json'))
    rep = {z: [f.to_json() for f in check(z, a.commit)] for z in zones}
    if a.json:
        print(json.dumps(rep, indent=1))
    else:
        for z, fs in rep.items():
            print(f'[kit overlap] {z}: {sum(f["severity"] == "fault" for f in fs)} faults, '
                  f'{sum(f["severity"] == "polish" for f in fs)} polish')
            for f in fs:
                print(f'  {f["severity"]} {f["detector"]} {f["box"]}: {f["message"]}')
    return 1 if any(f['severity'] == 'fault' for fs in rep.values() for f in fs) else 0


if __name__ == '__main__':
    sys.exit(main())
