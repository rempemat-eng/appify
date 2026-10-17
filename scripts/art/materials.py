"""Canonical ramps shared with the app's miniature art and interface.

Keep materials.json as the source; do not copy its colours into new generators.
"""
import json
from pathlib import Path

ART = json.loads((Path(__file__).resolve().parents[2] / 'art' / 'materials.json').read_text())
MATERIALS = ART['materials']
INK = ART['outline']
G, P, WTR = (MATERIALS[key] for key in ('grass', 'path', 'water'))
SAND, WOOD, STONE = (MATERIALS[key] for key in ('sand', 'wood', 'stone'))
LEAF, NAP, RED, CREAM = (MATERIALS[key] for key in ('leaf', 'nap', 'red', 'cream'))
GOLD = MATERIALS["gold"]
SLATE, ROOF, SNOW = (MATERIALS[key] for key in ("slate", "roof", "snow"))
