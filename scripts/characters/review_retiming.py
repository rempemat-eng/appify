"""Animator review of the cast's canonical retiming (Claude J, lane J, 25 Oct).

CAST-COMPAT's audit (draft #257, docs/codex/mygame-cast-audit-20261025/retiming.json) proposes,
for each of the 69 action clips, per-drawing durations that keep the authored contact drawing and
land release and completion on the canonical times. This turns those proposals into schedules a
60 Hz game can actually show, and gives each clip an animator's verdict:

- each drawing is held a whole number of 1/60 s ticks, and at least one;
- release falls on the tick nearest the canonical release, and completion on the tick nearest
  the canonical duration (each within half a tick), so the contact drawing is on screen at the
  moment the runner releases;
- ticks are shared out in proportion to #257's proposal (largest remainder), separately for
  preparation (drawings before the release drawing) and recovery (the release drawing onward).

Verdicts:
  ACCEPT    every drawing fits and the preparation keeps at least 35 % of its drawn time
  POSE      it fits, but preparation is squeezed below 35 %: the anticipation will read as a
            pop, so Claude A should check the key poses (and may drop an in-between) in castwork
  REDRAW    there are more preparation (or recovery) drawings than ticks: some drawings must go
  HOLD      the canonical action is longer than the drawing: the extra time is held on the
            anticipation key and on the settle, not spread evenly

    python3 scripts/characters/review_retiming.py --retiming <#257 retiming.json> \
        [--cast-dir game/assets/characters] [--out docs/characters]

Deterministic: same inputs, same bytes (run `npx oxfmt` on the output for the repo layout).
Reads JSON only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os

TICK = 1.0 / 60.0
SQUEEZE = 0.35


def _share(weights: list, ticks: int) -> list:
    """Integer ticks, each at least 1, summing to `ticks`, in proportion to weights."""
    n = len(weights)
    if n == 0:
        return []
    spare = ticks - n
    total = sum(weights) or 1.0
    raw = [w / total * spare for w in weights]
    base = [int(math.floor(r)) for r in raw]
    left = spare - sum(base)
    order = sorted(range(n), key=lambda i: (-(raw[i] - base[i]), i))
    for i in order[:left]:
        base[i] += 1
    return [b + 1 for b in base]


def review(action: dict, drawn: int | None) -> dict:
    sug = action['suggested_durations_seconds']
    rf = int(action['release_frame'])
    rel, dur = float(action['canonical_release']), float(action['canonical_duration'])
    p_ticks = int(round(rel / TICK))
    total_ticks = int(round(dur / TICK))
    r_ticks = total_ticks - p_ticks
    prep, rec = sug[:rf], sug[rf:]
    out = {
        'id': action['id'], 'clip': action['clip'],
        'drawings': len(sug), 'release_frame': rf,
        'canonical_release': rel, 'canonical_duration': dur,
        'art_release': action['art_release'], 'art_duration': action['art_duration'],
        'prep_factor': round(action['prep_time_factor'], 4),
        'recovery_factor': round(action['recovery_time_factor'], 4),
        'manifest_drawings': drawn,
    }
    problems = []
    if drawn is not None and drawn != len(sug):
        problems.append(f'manifest has {drawn} drawings, the proposal {len(sug)}')
    if len(prep) > p_ticks:
        problems.append(f'{len(prep)} preparation drawings for {p_ticks} ticks: drop {len(prep) - p_ticks}')
    if len(rec) > r_ticks:
        problems.append(f'{len(rec)} recovery drawings for {r_ticks} ticks: drop {len(rec) - r_ticks}')
    if problems and any('drop' in p for p in problems):
        verdict = 'REDRAW'
        ticks = None
    else:
        ticks = _share(prep, p_ticks) + _share(rec, r_ticks)
        if action['prep_time_factor'] < SQUEEZE:
            verdict = 'POSE'
        elif action['prep_time_factor'] > 1.0 or action['recovery_time_factor'] > 1.0:
            verdict = 'HOLD'
        else:
            verdict = 'ACCEPT'
    out.update(verdict=verdict, problems=problems, release_ticks=p_ticks, total_ticks=total_ticks)
    if ticks is not None:
        out['ticks'] = ticks
        out['release_at'] = round(sum(ticks[:rf]) * TICK, 4)
        out['ends_at'] = round(sum(ticks) * TICK, 4)
        out['shortest_drawing_ms'] = round(min(ticks) * TICK * 1000, 1)
    return out


def manifest_counts(cast_dir: str | None) -> dict:
    counts = {}
    if not cast_dir:
        return counts
    for cid in sorted(os.listdir(cast_dir)):
        p = os.path.join(cast_dir, cid, 'manifest.json')
        if not os.path.exists(p):
            continue
        with open(p) as fh:
            m = json.load(fh)
        for name, clip in m.get('clips', {}).items():
            counts[(cid, name)] = int(clip['frame_count'])
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--retiming', required=True)
    ap.add_argument('--cast-dir', default=None)
    ap.add_argument('--out', default='docs/characters')
    a = ap.parse_args()
    raw = open(a.retiming, 'rb').read()
    src = json.loads(raw)
    counts = manifest_counts(a.cast_dir)
    rows = [review(x, counts.get((x['id'], x['clip']))) for x in src['actions']]
    summary = {}
    for r in rows:
        summary[r['verdict']] = summary.get(r['verdict'], 0) + 1
    data = {
        'about': 'Claude J animator review of #257 retiming.json at 60 Hz (scripts/characters/review_retiming.py)',
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'source_main': src.get('source_main'),
        'tick_seconds': round(TICK, 6),
        'squeeze_threshold': SQUEEZE,
        'summary': dict(sorted(summary.items())),
        'clips': rows,
    }
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'cast-retiming-60hz.json'), 'w') as fh:
        json.dump(data, fh, indent=1)
        fh.write('\n')
    print(json.dumps(data['summary']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
