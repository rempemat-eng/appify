"""Regenerate the kit's golden scenes (art/golden/<scene>/) from their plans, biomes and the kit.

    python3 scripts/art/kit_golden.py

Registered in scripts/check-art-repro.cjs, so the committed golden pictures and manifests must be
exactly what the kit draws. Each scene renders in its own process (the painters size themselves
for one density at import).
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN = os.path.join(ROOT, 'art', 'golden')

for scene in sorted(os.listdir(GOLDEN)):
    man = os.path.join(GOLDEN, scene, 'manifest.json')
    if not os.path.exists(man):
        continue
    for tag in sorted(json.load(open(man)).get('renders', {})):
        d = tag.rstrip('x').replace('_', '.')
        subprocess.run([sys.executable, '-m', 'scripts.art.native.build', '--scene', scene, '--density', d, '--golden'],
                       cwd=ROOT, check=True)
