"""Animator review of cast contract v2 manifests (Claude J, lane J, 26 Oct).

Reads a character's manifest.json (contract 2) and, optionally, the contract 1 manifest it
replaces, and reports what a 60 Hz game will actually show:

- ticks: how many 1/60 s ticks each drawing is on screen when the clip starts on a tick
  (the runner starts actions on a frame), and any drawing shorter than one tick, which a
  dropped or late frame can skip;
- timing: total duration and release time against contract 1 (Codex's canonical times must
  not move), and whether the release drawing starts at the release time;
- skate: for the walk, the planted foot's speed on screen in each facing against the body's
  walk_speed. player.gd moves the body at walk_speed on screen in every direction, so a
  planted foot must travel back at the same screen speed or it slides;
- fidgets: each fidget starts and ends on idle drawing 0 in every facing.

    python3 scripts/characters/review_cast_v2.py <v2 manifest> [--v1 <v1 manifest>] [--out f.json]

Reads JSON only; deterministic.
"""
from __future__ import annotations

import argparse
import json
import math

TICK = 1.0 / 60.0
SKATE_LIMIT = 0.15  # planted foot may differ from the body's speed by 15 %
_R = 0.7071
VECTORS = {'S': [0, 1], 'SE': [_R, _R], 'E': [1, 0], 'NE': [_R, -_R], 'N': [0, -1],
           'NW': [-_R, -_R], 'W': [-1, 0], 'SW': [-_R, _R]}


def ticks(durations: list) -> list:
    out, t, prev = [], 0.0, 0
    for d in durations:
        t += d
        k = math.floor(t / TICK + 1e-6)
        out.append(k - prev)
        prev = k
    return out


def clip_rows(m: dict, v1: dict | None) -> list:
    rows = []
    for name, cl in m['clips'].items():
        d = cl['durations']
        row = {'clip': name, 'drawings': cl['frame_count'], 'duration': cl['duration'],
               'ticks': ticks(d), 'sub_tick': [i for i, x in enumerate(d) if x < TICK - 1e-9]}
        rf = cl.get('release_frame')
        if rf is not None:
            row['release_frame'] = rf
            row['release_time'] = cl['release_time']
            row['release_offset_ms'] = round((sum(d[:rf]) - cl['release_time']) * 1000, 1)
            row['release_ticks'] = row['ticks'][rf]
        old = (v1 or {}).get('clips', {}).get(name)
        if old:
            row['v1_drawings'] = old['frame_count']
            row['duration_change_ms'] = round((cl['duration'] - old['duration']) * 1000, 1)
            if rf is not None and old.get('release_time') is not None:
                row['release_change_ms'] = round((cl['release_time'] - old['release_time']) * 1000, 1)
        rows.append(row)
    return rows


def skate(m: dict) -> dict:
    """Planted-foot screen speed per facing for the walk, against walk_speed."""
    walk = m['clips']['walk']
    d, sp = walk['durations'], float(m['walk_speed'])
    vec = m.get('facing_vectors') or VECTORS
    out = {}
    for f, facing in walk['facings'].items():
        frames = facing['frames']
        v = vec[f]
        speeds = []
        for i in range(len(frames)):
            j = (i + 1) % len(frames)
            for foot in ('foot_L', 'foot_R'):
                a, b = frames[i]['anchors'][foot], frames[j]['anchors'][foot]
                along = ((b[0] - a[0]) * v[0] + (b[1] - a[1]) * v[1]) / d[i]
                if along < 0:  # moving back against the travel: the stance foot
                    speeds.append(-along)
        speeds.sort()
        planted = speeds[len(speeds) // 2] if speeds else 0.0
        out[f] = {'planted_px_s': round(planted, 1), 'body_px_s': sp,
                  'slide_px_s': round(sp - planted, 1),
                  'ok': abs(sp - planted) <= SKATE_LIMIT * sp}
    return out


def fidgets(m: dict) -> dict:
    clips = m['clips']
    out = {}
    for name in (m.get('idle_fidgets') or {}).get('clips', []):
        bad = []
        for f in clips['idle']['facings']:
            idle0 = clips['idle']['facings'][f]['frames'][0]['sha256']
            fr = clips[name]['facings'][f]['frames']
            if fr[0]['sha256'] != idle0 or fr[-1]['sha256'] != idle0:
                bad.append(f)
        out[name] = {'seamless': not bad, 'facings_off_idle0': bad}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('--v1', default=None)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    with open(a.manifest) as fh:
        m = json.load(fh)
    v1 = None
    if a.v1:
        with open(a.v1) as fh:
            v1 = json.load(fh)
    data = {'id': m['id'], 'contract': m.get('contract'), 'walk_speed': m['walk_speed'],
            'v1_walk_speed': (v1 or {}).get('walk_speed'), 'clips': clip_rows(m, v1),
            'walk_skate': skate(m), 'fidgets': fidgets(m)}
    text = json.dumps(data, indent=1) + '\n'
    if a.out:
        with open(a.out, 'w') as fh:
            fh.write(text)
    sk = data['walk_skate']
    print(m['id'], 'sub-tick:', {r['clip']: r['sub_tick'] for r in data['clips'] if r['sub_tick']},
          'skating facings:', [f for f in sk if not sk[f]['ok']],
          'fidget seams:', all(v['seamless'] for v in data['fidgets'].values()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
