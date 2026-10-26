"""logic.tiers: raised ground reads as one landform with one height per tier.

Matt, 26 Oct 19:42, on the plateau and cliff swatches: "make sure the logic is correct" (two parts
of one plateau read as different heights; the steps' top flush with neither; three face blocks
that do not join into one landform). From the plan, in texels:

- every tier has one level; its face is (level - level below) tall everywhere (a face of another
  height means another tier, or a mistake);
- a stair cut into a tier's face stands where the rim runs straight across its whole width (not
  across a corner), its head flush with that rim and its foot on the lower ground (rim + face);
- tiers nest: a tier's top lies inside the tier it stands on.

`{"tiers": [{"id", "level", "below", "face_px", "rects": [[x, y, w, h], ...], "on"?}], "stairs":
[{"tier", "x0", "x1", "y_top", "y_foot"}], "density": 3, "cell": 8}` (levels, rects and cell in
world px, the rest in texels). The scene gate reads it from a picture's sidecar
`<picture>.compose.json`; `npm run check:review` holds a plan that passes and three that trip.
"""
from __future__ import annotations

import numpy as np

from .core import Finding


def _mask(rects, cell, shape):
    gh, gw = shape
    cy, cx = (np.mgrid[0:gh, 0:gw] + 0.5) * cell
    m = np.zeros((gh, gw), bool)
    for x, y, w, h in rects:
        m |= (cx >= x) & (cx < x + w) & (cy >= y) & (cy < y + h)
    return m


def check(plan: dict) -> list[Finding]:
    D = float(plan.get('density', 3))
    cell = float(plan.get('cell', 8))
    tiers = {t['id']: t for t in plan.get('tiers', [])}
    out: list[Finding] = []
    tol = max(2.0, 0.12 * cell * D)
    for t in tiers.values():
        want = (t['level'] - t['below']) * D
        if abs(t['face_px'] - want) > 0.5:
            out.append(Finding('logic.tiers', 'fault', (0, 0, 1, 1),
                               f'{t["id"]}: its face is {t["face_px"]} texels but its level stands {want:.0f} over '
                               'the ground below', 'draw every face of a tier at the height between its level and the '
                               'level below it', score=abs(t['face_px'] - want), subject=t['id']))
        if t.get('on'):
            base = tiers.get(t['on'])
            if base and base['level'] != t['below']:
                out.append(Finding('logic.tiers', 'fault', (0, 0, 1, 1),
                                   f'{t["id"]} stands on {base["id"]} but its foot is at {t["below"]}, not '
                                   f'{base["level"]}', 'make a tier\'s foot the level of the tier it stands on',
                                   subject=t['id']))
    for st in plan.get('stairs', []):
        t = tiers.get(st['tier'])
        if not t:
            continue
        span = max(1, int(max(r[1] + r[3] for r in t['rects']) / cell) + 2), \
            max(1, int(max(r[0] + r[2] for r in t['rects']) / cell) + 2)
        m = _mask(t['rects'], cell, span)
        c0, c1 = int(st['x0'] / (cell * D)), int(np.ceil(st['x1'] / (cell * D)))
        rims = []
        for c in range(c0, c1):
            ys = np.nonzero(m[:, c])[0] if 0 <= c < m.shape[1] else []
            rims.append((ys.max() + 1) * cell * D if len(ys) else -1)
        box = (int(st['x0']), int(st['y_top']), int(st['x1']), int(st['y_foot']))
        if len(set(rims)) != 1 or rims[0] < 0:
            out.append(Finding('logic.tiers', 'fault', box, f'a stair into {t["id"]} straddles a turn of its rim',
                               'cut a stair where the rim runs straight across its whole width', subject=t['id']))
            continue
        rim = rims[0]
        if abs(st['y_top'] - rim) > tol:
            out.append(Finding('logic.tiers', 'fault', box, f'a stair\'s head is {st["y_top"] - rim:+.0f} texels off '
                               f'the rim of {t["id"]}', 'set the stair\'s head flush with the upper tier\'s rim',
                               score=abs(st['y_top'] - rim), subject=t['id']))
        if abs(st['y_foot'] - (rim + t['face_px'])) > tol:
            out.append(Finding('logic.tiers', 'fault', box, f'a stair\'s foot is {st["y_foot"] - rim - t["face_px"]:+.0f}'
                               f' texels off the ground below {t["id"]}', 'land the stair\'s foot on the lower ground',
                               subject=t['id']))
    return out
