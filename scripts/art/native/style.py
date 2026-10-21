"""The style numbers the native painters read (biome file, "style"): how crowns are clumped and
lit, how tufts stand, how dense the dressing is, how rock masses are shaded. `use(biome)` sets them
for a build; every painter reads `get(section, key, default)`, so a style verdict is a data change.
"""
from __future__ import annotations

_STYLE: dict = {}


def use(biome: dict):
    _STYLE.clear()
    _STYLE.update(biome.get('style', {}))


def get(section: str, key: str, default):
    return _STYLE.get(section, {}).get(key, default)
