"""Prop sets for the regions after the Crossroads/woodland slice (docs/vision/props-backlog.md).

Each set is one module that paints its pieces and writes them the way the farmyard does
(scripts/art/kit/farm.py): pictures under game/kit/props/art/<set>/, one piece file per design in
game/kit/pieces/prop/, an idle strip for anything that moves (world/loop_fx.gd plays it only on
screen and holds frame 0 under reduced motion). `_common` holds the shared drawing tools: a small
oblique ray renderer for stacked stones, boxes and posts, and the tone measure the reviews use.

    python3 -m scripts.art.kit.sets.brackens           # the Brackens' drove-road set
    python3 -m scripts.art.kit.sets.brackens --check   # exit 1 if a picture is stale

SETS lists the set modules; `audit_rows()` gives scripts/art/kit/placement_audit.py each piece's
purpose, role and verdict without painting anything.
"""
from __future__ import annotations

SETS = ('brackens', 'act1')


def audit_rows() -> dict:
    """{piece id: (purpose, role, requires, forbids, verdict, note)} for every set's pieces (None for
    requires/forbids keeps what the piece file says, as the farm rows do)."""
    import importlib
    rows = {}
    for name in SETS:
        rows.update(importlib.import_module('scripts.art.kit.sets.' + name).AUDIT)
    return rows
