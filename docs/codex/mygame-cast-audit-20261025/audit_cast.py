#!/usr/bin/env python3
"""Audit pinned cast metadata; no image generation, downloads or gameplay changes.

Build snapshot: audit_cast.py --inputs INPUTS --out OUTPUT
Repeat audit:   audit_cast.py --snapshot source-snapshot.json --out OUTPUT
INPUTS contains pins.json, canonical.json and manifests/<id>.json, copied exactly
from the pinned Git objects. A clone can supply manifests via --cast-dir.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

FACINGS = ['S', 'N', 'E', 'W']
BASE = ['idle', 'walk', 'primary', 'secondary', 'special', 'guard', 'hit',
        'defeat', 'jump', 'stair_up', 'stair_down', 'dodge']
POWER = ['powered_' + c for c in BASE if c != 'special'] + ['powered_exit']
VARIANTS = {'brine': ['secondary_empty', 'powered_secondary_empty'],
            'rook': ['air_primary', 'powered_air_primary'],
            'pendle': ['reload'], 'velvet': ['powered_counter'],
            'ashe': ['powered_finisher']}


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def extract(inputs, cast_dir=None):
    pins = json.loads((inputs / 'pins.json').read_text())
    cb = (inputs / 'canonical.json').read_bytes()
    require(blob(cb) == pins['canonical_blob'], 'Canonical Git blob differs')
    canonical = json.loads(cb)
    kits = {x['id']: x for x in canonical['characters']}
    result = {'pins': pins, 'scope': 'metadata only; PNGs and Godot execution not tested',
              'characters': [], 'frame_records_checked': 0, 'anchor_points_checked': 0}
    for cid, expected in pins['manifests'].items():
        path = (cast_dir / cid / 'manifest.json') if cast_dir else inputs / 'manifests' / (cid + '.json')
        raw = path.read_bytes()
        require(blob(raw) == expected, cid + ': Git blob differs')
        m = json.loads(raw)
        require(m['id'] == cid, cid + ': wrong identity')
        require(set(m['directions']) == set(FACINGS), cid + ': directions')
        require(len(m['frame_size']) == 2 and all(finite(v) and v > 0 for v in m['frame_size']), cid + ': cell size')
        require(len(m['foot_pivot']) == 2 and all(finite(v) for v in m['foot_pivot']), cid + ': pivot')
        item = {'id': cid, 'manifest_blob': expected,
                'body_height_target': m['body_height_target'], 'frame_size': m['frame_size'],
                'foot_pivot': m['foot_pivot'], 'anchor_space': m['anchor_space'],
                'walk_speed_texels_per_second': m['walk_speed'],
                'canonical_planar_speed': kits[cid]['planar_speed'],
                'effects': m.get('effects', {}), 'clips': {},
                'canonical_actions': {'base': kits[cid]['base']['actions'],
                                      'powered': kits[cid]['powered']['actions']}}
        actual_count = 0
        for name, ce in m['clips'].items():
            prefix = cid + '/' + name
            n, ds = ce['frame_count'], ce['durations']
            require(isinstance(n, int) and n > 0 and len(ds) == n, prefix + ': duration count')
            require(all(finite(d) and d > 0 for d in ds), prefix + ': nonpositive/nonfinite duration')
            require(finite(ce['duration']) and abs(sum(ds) - ce['duration']) <= 0.001, prefix + ': duration sum')
            require(set(ce['facings']) == set(FACINGS), prefix + ': missing facing')
            rel, hold = ce.get('release_frame'), ce.get('hold_frame')
            require(rel is None or isinstance(rel, int) and 0 <= rel < n, prefix + ': release index')
            require(hold is None or isinstance(hold, int) and 0 <= hold < n, prefix + ': guard index')
            if rel is not None:
                require(finite(ce['release_time']) and abs(sum(ds[:rel]) - ce['release_time']) <= 0.001, prefix + ': release onset')
            roles = ce.get('roles')
            require(roles is None or len(roles) == n, prefix + ': role count')
            out = {k: ce.get(k) for k in ['frame_count', 'durations', 'duration', 'loop',
                   'release_frame', 'release_time', 'hold_frame', 'roles', 'release_anchor']}
            out['release_anchors_by_facing'] = {}
            out['pre_release_anchors_by_facing'] = {}
            out['anchor_keys_on_every_frame'] = {}
            for fc, fe in ce['facings'].items():
                frames = fe['frames']
                require(len(frames) == n, prefix + '/' + fc + ': frame count')
                common = None
                for i, fr in enumerate(frames):
                    require(fr['region'] == [i * m['frame_size'][0], 0, *m['frame_size']], prefix + ': atlas rectangle')
                    require(fr['sheet'] == 'sheets/' + name + '_' + fc + '.png', prefix + ': sheet name')
                    bounds = fr['packed_bounds']
                    require(len(bounds) == 4 and 0 <= bounds[0] < bounds[2] <= m['frame_size'][0]
                            and 0 <= bounds[1] < bounds[3] <= m['frame_size'][1], prefix + ': declared bounds')
                    require(len(fr['sha256']) == 64 and all(c in '0123456789abcdef' for c in fr['sha256']), prefix + ': frame hash syntax')
                    for pt in fr['anchors'].values():
                        require(len(pt) == 2 and all(finite(v) for v in pt), prefix + ': malformed anchor')
                        result['anchor_points_checked'] += 1
                    common = set(fr['anchors']) if common is None else common & set(fr['anchors'])
                    actual_count += 1
                out['anchor_keys_on_every_frame'][fc] = sorted(common)
                if rel is not None:
                    out['release_anchors_by_facing'][fc] = frames[rel]['anchors']
                    out['pre_release_anchors_by_facing'][fc] = frames[max(0, rel - 1)]['anchors']
            item['clips'][name] = out
        require(actual_count == m['pose_count'], cid + ': pose count')
        item['frame_records_checked'] = actual_count
        result['frame_records_checked'] += actual_count
        result['characters'].append(item)
    require(len(result['characters']) == 14, 'Expected exactly fourteen characters')
    return result


def audit(snapshot):
    report = {'source_main': snapshot['pins']['main'], 'metadata_status': 'valid',
              'visual_quality_status': 'not assessed', 'godot_runtime_status': 'not executed by metadata audit; see separate source-method log',
              'frame_records_checked': snapshot['frame_records_checked'],
              'anchor_points_checked': snapshot['anchor_points_checked'],
              'characters': [], 'timing_mismatch_count': 0, 'missing_action_clip_count': 0}
    retiming = {'status': 'owner review only; not an imported asset or balance change',
                'source_main': snapshot['pins']['main'],
                'method': 'Scale anticipation and recovery separately around the authored contact; review compressed poses before adoption.',
                'actions': []}
    for char in snapshot['characters']:
        cid, clips = char['id'], char['clips']
        missing = [n for n in BASE + POWER + VARIANTS.get(cid, []) if n not in clips]
        entry = {'id': cid, 'clip_count': len(clips), 'frame_records': char['frame_records_checked'],
                 'missing_requested_clips': missing, 'timing_differences': []}
        for form, action, clip in [('base','primary','primary'), ('base','secondary','secondary'),
                                  ('base','special','special'), ('powered','primary','powered_primary'),
                                  ('powered','secondary','powered_secondary')]:
            target = char['canonical_actions'][form][action]
            if clip not in clips:
                report['missing_action_clip_count'] += 1
                continue
            src = clips[clip]
            require(src['release_frame'] is not None, cid + '/' + clip + ': no release')
            original_release = sum(src['durations'][:src['release_frame']])
            original_end = sum(src['durations'])
            release, end = target['release_seconds'], target['duration_seconds']
            require(0 < original_release < original_end and 0 < release < end, cid + ': unschedulable action')
            prep_scale = release / original_release
            recover_scale = (end - release) / (original_end - original_release)
            ds = [d * (prep_scale if i < src['release_frame'] else recover_scale) for i, d in enumerate(src['durations'])]
            require(abs(sum(ds[:src['release_frame']]) - release) < 1e-9, 'retiming contact')
            require(abs(sum(ds) - end) < 1e-9 and all(d > 0 for d in ds), 'retiming duration')
            diff = {'clip': clip, 'canonical_duration': end, 'canonical_release': release,
                    'art_duration': original_end, 'art_release': original_release,
                    'release_frame': src['release_frame'], 'prep_time_factor': prep_scale,
                    'recovery_time_factor': recover_scale}
            if abs(original_release - release) > 0.001 or abs(original_end - end) > 0.001:
                entry['timing_differences'].append(diff)
                report['timing_mismatch_count'] += 1
            retiming['actions'].append({'id': cid, **diff, 'suggested_durations_seconds': ds})
        report['characters'].append(entry)
    report['character_count'] = len(snapshot['characters'])
    report['clip_count'] = sum(c['clip_count'] for c in report['characters'])
    return report, retiming


def write(path, value):
    options = {'separators': (',', ':')} if path.name == 'source-snapshot.json' else {'indent': 2}
    path.write_text(json.dumps(value, allow_nan=False, **options) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--inputs', type=Path)
    group.add_argument('--snapshot', type=Path)
    ap.add_argument('--cast-dir', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    snapshot = extract(args.inputs, args.cast_dir) if args.inputs else json.loads(args.snapshot.read_text())
    report, retiming = audit(snapshot)
    args.out.mkdir(parents=True, exist_ok=True)
    write(args.out / 'source-snapshot.json', snapshot)
    write(args.out / 'report.json', report)
    write(args.out / 'retiming.json', retiming)
    print(json.dumps({k:v for k,v in report.items() if k != 'characters'}, indent=2))


if __name__ == '__main__':
    main()
