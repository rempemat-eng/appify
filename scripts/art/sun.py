"""The one sun (game/data/sun.json): the projection every cast shadow is thrown by.

    from scripts.art.sun import CAST      # (kx, ky): a texel h above the ground lands kx h east, ky h south

Read by the painted zones' bake (scripts/art/native/compose.SHADOW, so the kit bake too) and by the
kit's prop masks (scripts/art/kit/props.footprint_shadow); the live ground reads the same file
(TerrainGround.sun()), so the number lives in one place. A day-night cycle would vary this vector;
see docs/world-editor.md, "The sun".
"""
from __future__ import annotations

import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PATH = os.path.join(ROOT, 'game', 'data', 'sun.json')


def load(path: str = PATH) -> tuple:
    kx, ky = json.load(open(path))['cast']
    return float(kx), float(ky)


CAST = load()
