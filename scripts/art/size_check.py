"""The size check (docs/vision/size-guide.md): report only, it never fails a build.

Every prop sprite in assets/zones/props is measured against its kind in
scripts/art/size_guide.json:

- the sprite's kind and module come from the guide's name map (`sprites`); animation
  frames (`_f1`, `_f2`) take their base sprite's entry;
- its drawn box is the trimmed box of pixels at least half opaque (contact shadows are
  softer and drop out), read from the PNG and divided by the PNG scale (4), so in zone
  px as the zones place it;
- it is OVER or UNDER when its height or width leaves the kind's range by more than the
  tolerance (2 px, the 1 px outline on each side).

What it cannot see: door heights, storey heights and counter heights inside a sprite
(they need declared DOOR_RECTS and STOREYS, verticality.md 5), and how a sprite is
placed. A sprite in `unmeasured` (a group, a part, an effect) and a sprite missing from
the name map are listed, never judged.

    python3 scripts/art/size_check.py              # summary per lane, then each finding
    python3 scripts/art/size_check.py --lane C     # one lane
    python3 scripts/art/size_check.py --all        # every sprite, in range or not
    python3 scripts/art/size_check.py --markdown   # the kinds table for the doc
    python3 scripts/art/size_check.py --json OUT   # findings as data
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
GUIDE = os.path.join(HERE, 'size_guide.json')
PROPS = os.path.join(ROOT, 'assets', 'zones', 'props')
FRAME = re.compile(r'_f\d+$')


def load_guide(path: str = GUIDE) -> dict:
    with open(path) as f:
        return json.load(f)


def measure(path: str, scale: int) -> tuple[float, float]:
    """(height, width) in zone px of the sprite's pixels that are at least half opaque."""
    alpha = Image.open(path).convert('RGBA').getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    box = alpha.getbbox()
    if box is None:
        return 0.0, 0.0
    return (box[3] - box[1]) / scale, (box[2] - box[0]) / scale


def judge(value: float, rng: list | None, tol: float) -> int:
    """-1 under, 0 in range, +1 over."""
    if not rng:
        return 0
    lo, hi = rng
    if value < lo - tol:
        return -1
    if value > hi + tol:
        return 1
    return 0


def check(guide: dict, props_dir: str = PROPS) -> list[dict]:
    scale = guide['unit']['png_scale']
    tol = guide['tolerance']
    kinds, sprites, lanes = guide['kinds'], guide['sprites'], guide['lanes']
    rows = []
    for fname in sorted(os.listdir(props_dir)):
        if not fname.endswith('.png'):
            continue
        name = fname[:-4]
        base = FRAME.sub('', name)
        entry = sprites.get(base)
        h, w = measure(os.path.join(props_dir, fname), scale)
        row = {'sprite': name, 'h': h, 'w': w}
        if entry is None:
            row.update(kind=None, module=None, lane='?', status='no kind')
            rows.append(row)
            continue
        kind, module = entry
        row.update(kind=kind, module=module, lane=lanes.get(module, '?'))
        if kind is None:
            row['status'] = 'unmeasured'
            row['why'] = guide.get('unmeasured', {}).get(base, '')
        else:
            k = kinds[kind]
            dh, dw = judge(h, k['h'], tol), judge(w, k['w'], tol)
            row['dh'], row['dw'] = dh, dw
            row['range'] = (k['h'], k['w'])
            if dh > 0 or dw > 0:
                row['status'] = 'over' if dh >= 0 and dw >= 0 else 'mixed'
            elif dh < 0 or dw < 0:
                row['status'] = 'under'
            else:
                row['status'] = 'ok'
        rows.append(row)
    return rows


def _fmt_range(r) -> str:
    return '-' if not r else (str(r[0]) if r[0] == r[1] else f'{r[0]} to {r[1]}')


def _finding(r: dict) -> str:
    (hr, wr) = r['range']
    parts = []
    if r['dh']:
        parts.append(f"h {r['h']:g} ({'over' if r['dh'] > 0 else 'under'} {_fmt_range(hr)})")
    if r['dw']:
        parts.append(f"w {r['w']:g} ({'over' if r['dw'] > 0 else 'under'} {_fmt_range(wr)})")
    return f"  {r['status']:5}  {r['sprite']:24} {r['kind']:16} {r['module']:16} " + '; '.join(parts)


def summary(rows: list[dict]) -> list[str]:
    lanes = sorted({r['lane'] for r in rows})
    out = ['lane  sprites  ok  over  under  mixed  unmeasured  no kind']
    for lane in lanes:
        rs = [r for r in rows if r['lane'] == lane]
        c = {s: sum(1 for r in rs if r['status'] == s) for s in ('ok', 'over', 'under', 'mixed', 'unmeasured', 'no kind')}
        out.append(f"{lane:4}  {len(rs):7}  {c['ok']:3}  {c['over']:4}  {c['under']:5}  {c['mixed']:5}  {c['unmeasured']:10}  {c['no kind']:7}")
    if 'E' not in lanes and len(lanes) > 1:
        out.append('E     owns no prop module (it places the valley\'s props; its residents are not props)')
    return out


def markdown(guide: dict) -> str:
    lines = ['| Kind | Group | Height | Width | Foot (cells) | Why |', '| --- | --- | --- | --- | --- | --- |']
    for name, k in guide['kinds'].items():
        lines.append(f"| `{name}` | {k['group']} | {_fmt_range(k['h'])} | {_fmt_range(k['w'])} | {k['foot']} | {k['reason']} |")
    return '\n'.join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--lane', help='only this lane (A to E)')
    ap.add_argument('--all', action='store_true', help='list every sprite, not only findings')
    ap.add_argument('--markdown', action='store_true', help='print the kinds table for the doc')
    ap.add_argument('--json', metavar='OUT', help='write the rows as JSON')
    args = ap.parse_args(argv)
    guide = load_guide()
    if args.markdown:
        print(markdown(guide))
        return 0
    rows = check(guide)
    if args.lane:
        rows = [r for r in rows if r['lane'] == args.lane.upper()]
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(rows, f, indent=1)
    print(f"size check: {len(rows)} sprites in assets/zones/props against scripts/art/size_guide.json "
          f"(tolerance {guide['tolerance']} px; report only)")
    print('\n'.join(summary(rows)))
    for lane in sorted({r['lane'] for r in rows}):
        rs = [r for r in rows if r['lane'] == lane]
        shown = rs if args.all else [r for r in rs if r['status'] in ('over', 'under', 'mixed')]
        if shown:
            print(f'\nlane {lane}')
            for r in sorted(shown, key=lambda r: (r['status'], r['module'] or '', r['sprite'])):
                if r['status'] in ('over', 'under', 'mixed'):
                    print(_finding(r))
                else:
                    print(f"  {r['status']:5}  {r['sprite']:24} {r['kind'] or '-':16} {r['module'] or '-':16} h {r['h']:g} w {r['w']:g}")
    missing = [r['sprite'] for r in rows if r['status'] == 'no kind']
    if missing:
        print('\nno kind in the name map (add them to size_guide.json "sprites"): ' + ', '.join(missing))
    return 0


if __name__ == '__main__':
    sys.exit(main())
