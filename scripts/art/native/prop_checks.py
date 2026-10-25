"""Checks on a biome's object pictures at the density the game uses (Claude B; lane R 25 Oct
17:08, findings 3, 4 and 8 and comparison item 3).

    python3 -m scripts.art.native.prop_checks --zone woodland --density 3

For each recipe of the zone's biome, rendered by screen.sprite at that density:
- every tree and foliage crown is solid: its drawn share of the row hull is at least
  CROWN_FLOOR (a lace crown at 3x measured 0.60 to 0.77; the solid crowns at 2x 0.90 to 0.99);
- every tree stands on one unbroken trunk, joined into its crown, in one piece
  (props_trees.trunk_connected);
- the stones are not smooth blobs: at most STONE_FLAT of their 2 x 2 blocks are flat and they
  use at least STONE_COLOURS colours (the old ones: 76 to 79 % and 11 to 12).

One density per process (ctx), so run it once for each density the game ships.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CROWN_FLOOR = 0.88
STONE_FLAT = 0.64
STONE_COLOURS = 14


def flat_share(A: np.ndarray) -> float:
    flat = tot = 0
    for y in range(0, A.shape[0] - 1, 2):
        for x in range(0, A.shape[1] - 1, 2):
            b = A[y:y + 2, x:x + 2]
            if (b[..., 3] > 0).all():
                tot += 1
                flat += bool((b.reshape(-1, 4) == b[0, 0]).all())
    return flat / max(1, tot)


def check(zone: str, density: float, seeds=(7, 19)) -> tuple:
    from scripts.art.native import ctx, load_biome, load_plan
    plan = load_plan(zone)
    biome = load_biome(plan['biome'])
    ctx.configure(density, biome, plan)
    from scripts.art.native import props_trees as PT
    from scripts.art.native import screen
    faults, rows = [], []
    for kind, rec in biome['recipes'].items():
        if kind.startswith('_'):
            continue
        paint = rec['paint']
        if paint not in ('tree', 'foliage', 'standing_stone'):
            continue
        for seed in seeds:
            img, anc, a, ex = screen.sprite(kind, rec, seed)
            A = np.asarray(img.convert('RGBA'))
            al = A[..., 3] > 0
            row = dict(kind=kind, seed=seed)
            if paint in ('tree', 'foliage'):
                op = PT.crown_opacity(al)
                row['opacity'] = round(op, 3)
                if op < CROWN_FLOOR:
                    faults.append(f'{kind} (seed {seed}): crown {op:.2f} drawn, under {CROWN_FLOOR}')
            if paint == 'tree':
                for f in PT.trunk_connected(al, d=density):
                    faults.append(f'{kind} (seed {seed}): {f}')
            if paint == 'standing_stone':
                fl = flat_share(A)
                cols = len({tuple(c) for c in A[al][:, :3]})
                row.update(flat=round(fl, 2), colours=cols)
                if fl > STONE_FLAT:
                    faults.append(f'{kind} (seed {seed}): {fl:.0%} flat 2 x 2 blocks, over {STONE_FLAT:.0%}')
                if cols < STONE_COLOURS:
                    faults.append(f'{kind} (seed {seed}): {cols} colours, under {STONE_COLOURS}')
            rows.append(row)
    return faults, rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--zone', default='woodland')
    ap.add_argument('--density', type=float, default=3.0)
    a = ap.parse_args(argv)
    faults, rows = check(a.zone, a.density)
    for r in rows:
        print(' ', r)
    for f in faults:
        print('FAULT', f)
    print(f'prop_checks {a.zone} at {a.density:g}: {len(rows)} pictures, {len(faults)} faults')
    return 1 if faults else 0


if __name__ == '__main__':
    sys.exit(main())
