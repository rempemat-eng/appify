"""logic.composition: objects placed on a structure are composed with it.

Matt, 26 Oct 19:35, on the soft-grid swatches: "the square needs better centring with the objects
on top of it". A structure that carries props (a square, a plaza, a bed, a dock, a terrace) and the
props on it are one composition:

- the structure is whole cells (8 world px, 24 texels at density 3);
- its centrepiece (a well, a fountain, a statue: marked `centre`, else the prop with no twin
  nearest the axis) stands on the structure's centre axis;
- every other prop has a mirror twin of its kind across that axis (benches either side of the
  well), at the same height;
- the contents sit with even margins to the structure's edges, west and east;
- a path or a gate that meets the structure (`entries`) meets it on its axis.

Tolerance: 0.12 of a cell (3 texels at density 3), the margins twice that. A structure is
`{"id", "rect": [x0, y0, x1, y1], "props": [{"kind", "x", "y", "w", "centre"?}], "entries":
[{"x", "w"?}], "axis": "x"}` in texels (props by their foot point and base width). The scene gate
reads them from a picture's sidecar `<picture>.compose.json` (the swatch sheet writes one) or from a
plan's `structures`; `npm run check:review` holds a composed square that passes and three that
trip (an off-centre well, a lone bench, uneven margins).
"""
from __future__ import annotations

import json
import os

from .core import Finding

CELL = 24.0


def check(structures: list, cell: float = CELL) -> list[Finding]:
    tol = max(2.0, 0.12 * cell)
    out: list[Finding] = []
    for st in structures:
        sid = st.get('id', 'structure')
        x0, y0, x1, y1 = st['rect']
        box = (int(x0), int(y0), int(x1), int(y1))
        props = st.get('props', [])
        axis = (x0 + x1) / 2.0

        def bad(msg, fix, score=0.0, b=box):
            out.append(Finding('logic.composition', 'fault', b, f'{sid}: {msg}', fix, score=score, threshold=tol,
                               subject=sid))
        for v, name in ((x1 - x0, 'width'), (y1 - y0, 'depth')):
            if abs(v / cell - round(v / cell)) * cell > 0.5:
                bad(f'its {name} is {v / cell:.2f} cells, not whole cells',
                    'size the structure in whole cells, chosen round its contents (eastward-edges.md, placement)', v)
        if not props:
            continue
        # the centrepiece
        cen = [p for p in props if p.get('centre')]
        if not cen:
            kinds = [p['kind'] for p in props]
            lone = [p for p in props if kinds.count(p['kind']) == 1]
            if lone:
                cen = [min(lone, key=lambda p: abs(p['x'] - axis) - 0.01 * p.get('w', 0))]
        for p in cen:
            d = p['x'] - axis
            if abs(d) > tol:
                bad(f'its centrepiece ({p["kind"]}) stands {d:+.0f} texels off the centre axis',
                    'stand the centrepiece on the structure\'s centre axis (or resize the structure round it)', abs(d),
                    (int(p['x'] - p.get('w', 8) / 2), int(p['y'] - 8), int(p['x'] + p.get('w', 8) / 2), int(p['y'])))
        # mirror twins
        rest = [p for p in props if p not in cen]
        for p in rest:
            if abs(p['x'] - axis) <= tol:
                continue
            mx = 2 * axis - p['x']
            twin = [q for q in rest if q is not p and q['kind'] == p['kind'] and abs(q['x'] - mx) <= tol and
                    abs(q['y'] - p['y']) <= tol]
            if not twin:
                bad(f'the {p["kind"]} at x {p["x"]:.0f} has no twin across the axis (x {mx:.0f})',
                    'place props in mirrored pairs about the centre axis, or on the axis', abs(p['x'] - axis),
                    (int(p['x'] - p.get('w', 8) / 2), int(p['y'] - 8), int(p['x'] + p.get('w', 8) / 2), int(p['y'])))
        # even margins west and east
        lo = min(p['x'] - p.get('w', 0) / 2 for p in props)
        hi = max(p['x'] + p.get('w', 0) / 2 for p in props)
        mw, me = lo - x0, x1 - hi
        if abs(mw - me) > 2 * tol:
            bad(f'its contents sit with uneven margins: {mw:.0f} texels west, {me:.0f} east',
                'centre the contents, or size the structure so the margins match', abs(mw - me))
        # entries on the axis
        for e in st.get('entries', []):
            d = e['x'] - axis
            if abs(d) > tol:
                bad(f'a way in meets it {d:+.0f} texels off its axis',
                    'run the path to meet the structure on its centre axis', abs(d))
    return out


def sidecar_plan(picture: str) -> dict | None:
    p = os.path.splitext(picture)[0] + '.compose.json'
    return json.load(open(p)) if os.path.exists(p) else None


def sidecar(picture: str) -> list | None:
    p = os.path.splitext(picture)[0] + '.compose.json'
    if os.path.exists(p):
        return json.load(open(p)).get('structures', [])
    return None
