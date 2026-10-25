"""Read-only integrity and contract audit of the assembled text-only handoff."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package', type=Path, required=True,
                    help='Final handoff directory containing README.md, canonical/ and animation/')
parser.add_argument('--report', type=Path,
                    default=Path(__file__).with_name('final-package-qc.json'))
args = parser.parse_args()
root = args.package.resolve(strict=True)
report_path = args.report.resolve()
if not root.is_dir():
    parser.error('--package must identify a directory')
if report_path.is_relative_to(root):
    parser.error('--report must be outside the inspected package so the audit does not mutate it')

checks = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


def load(path):
    return json.loads((root / path).read_text())


def finite(value):
    if isinstance(value, dict):
        return all(finite(x) for x in value.values())
    if isinstance(value, list):
        return all(finite(x) for x in value)
    return not isinstance(value, float) or math.isfinite(value)


inventory = []
for path in sorted(root.rglob('*')):
    check('no symlink payload: ' + str(path.relative_to(root)), not path.is_symlink())
    if not path.is_file():
        continue
    relative = path.relative_to(root)
    check('file stays within package: ' + str(relative), path.resolve().is_relative_to(root))
    check('no game/ path: ' + str(relative), 'game' not in relative.parts)
    check('no engine project or raster: ' + str(relative),
          path.name != 'project.godot' and path.suffix.lower() not in
          {'.png', '.gif', '.jpg', '.jpeg', '.webp', '.pck', '.tscn', '.tres', '.zip', '.mp4'})
    raw = path.read_bytes()
    raw.decode('utf-8')
    check('UTF-8 text: ' + str(relative), b'\x00' not in raw)
    inventory.append({'path': str(relative), 'bytes': len(raw),
                      'sha256': hashlib.sha256(raw).hexdigest()})

data = load('canonical/abilities-v1.json')
legacy = load('animation/legacy-east-animation-reference.json')
original = load('canonical/reference/original-modules.json')
catalogue = load('canonical/reference/catalogue.json')
stateful = load('canonical/stateful-audit.json')
for kind in ['catalogue', 'engine']:
    expected = original['provenance'][kind + 'Sha256']
    check(kind + ' original module SHA256',
          hashlib.sha256(original[kind].encode()).hexdigest() == expected)
    check(kind + ' data source SHA256', data['source'][kind + 'Sha256'] == expected)
check('stateful audit names the same engine',
      stateful['source_engine_sha256'] == original['provenance']['engineSha256'])
check('canonical JSON finite', finite(data))
check('canonical14 IDs exact order',
      [c['id'] for c in data['characters']] == catalogue['CHARACTER_IDS'])
check('legacy14 IDs match', set(legacy['characters']) == set(catalogue['CHARACTER_IDS']))
check('legacy239 clips', sum(len(c['clips']) for c in legacy['characters'].values()) == 239)
check('legacy2135 reference drawings', sum(c['pose_count'] for c in legacy['characters'].values()) == 2135)
check('render density does not rescale balance', data['units']['rendering_density_changes_balance'] is False)

for character in data['characters']:
    for form in ['base', 'powered']:
        for action in ['primary', 'secondary', 'special']:
            timing = character[form]['actions'][action]
            check(character['id'] + '/' + form + '/' + action + ' time order',
                  0 <= timing['release_seconds'] <= timing['duration_seconds'] and
                  timing['duration_seconds'] > 0 and timing['cooldown_seconds'] >= 0)
        for projectile in character[form]['primary_projectiles']:
            check(character['id'] + '/' + form + '/' + projectile['kind'] + ' projectile limits',
                  projectile['speed'] > 0 and projectile['radius'] > 0 and
                  projectile['damage'] >= 0 and projectile['pierce_budget'] >= 0 and
                  projectile['planar_spawn_forward'] == 9)
    check(character['id'] + ' art-unit warning',
          'new74px' in character['art_contract']['per_facing_screen_anchors'])

for identifier, character in legacy['characters'].items():
    check(identifier + ' foot pivot within virtual frame',
          all(0 <= p < dimension for p, dimension in zip(character['foot_pivot'], character['frame_size'])))
    for name, clip in character['clips'].items():
        count, durations, release = clip['frame_count'], clip['durations'], clip['release_frame']
        check(identifier + '/' + name + ' reference count/timing',
              len(durations) == count and all(math.isfinite(t) and t > 0 for t in durations) and
              math.isclose(sum(durations), clip['duration'], abs_tol=1e-12))
        if release is not None:
            check(identifier + '/' + name + ' release index/time',
                  0 <= release < count and
                  math.isclose(clip['release_time'], sum(durations[:release]), abs_tol=1e-12))
        if clip['hold_frame'] is not None:
            check(identifier + '/' + name + ' guard hold index', 0 <= clip['hold_frame'] < count)
        if 'hand_anchors' in clip:
            check(identifier + '/' + name + ' attachment count', len(clip['hand_anchors']) == count)

provenance = load('animation/source-provenance.json')
for record in provenance['records']:
    raw = (root / 'animation/source' / record['path']).read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    check('exact source Git blob ' + record['path'], actual == record['git_blob_sha'])

schema = load('animation/manifest-proposal.schema.json')
check('proposal schema has four explicit views',
      set(schema['properties']['view']['enum']) == {'S', 'N', 'E', 'W'})
check('no fixed frame quota',
      schema['properties']['clips']['additionalProperties']['properties']['frame_count'] ==
      {'type': 'integer', 'minimum': 1})
checker_source = (root / 'animation/validate_reference.py').read_text()
check('legacy archive is an explicit optional argument',
      "add_argument('--archive'" in checker_source and 'if args.archive is not None:' in checker_source)
check('legacy checker contains no hardcoded scratch path', '/workspace/scratch/' not in checker_source)
readme = (root / 'README.md').read_text()
check('README distinguishes projectile launch directions',
      "each projectile's launch direction" in readme)

# The materialised catalogue must agree with the verified original module,
# not merely have the same character IDs.
catalogue_probe = r"""
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {join} from 'node:path';
import assert from 'node:assert/strict';
const root=process.argv[1];
const {loadCanonicalCombat}=await import(pathToFileURL(join(root,'canonical/reference/adapter.mjs')));
const engine=loadCanonicalCombat();
const catalogue=JSON.parse(readFileSync(join(root,'canonical/reference/catalogue.json')));
const data=JSON.parse(readFileSync(join(root,'canonical/abilities-v1.json')));
const checks=[];
assert.deepEqual(JSON.parse(JSON.stringify(engine.ROSTER)),catalogue.ROSTER);
checks.push('original exported catalogue equals materialised reference');
for(const character of data.characters){
 const original=engine.ROSTER.find(item=>item.id===character.id);
 for(const key of ['role','primary','secondary','block','special']){
  assert.equal(character.catalogue_prose[key],original[key]);
  checks.push(character.id+'/'+key+' description equals original export');
 }
}
process.stdout.write(JSON.stringify({checks}));
"""
probe = subprocess.run(['node', '--input-type=module', '-e', catalogue_probe, str(root)],
                       text=True, capture_output=True, check=True)
checks.extend(json.loads(probe.stdout)['checks'])

current_files = {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()}
check('package bytes remain unchanged during the audit',
      current_files == {item['path'] for item in inventory} and
      all(hashlib.sha256((root / item['path']).read_bytes()).hexdigest() == item['sha256']
          for item in inventory))

contents = '\n'.join(item['path'] + '\0' + item['sha256'] for item in inventory).encode()
report = {
    'status': 'passed',
    'checks': len(checks),
    'package_files': len(inventory),
    'package_bytes': sum(item['bytes'] for item in inventory),
    'inventory_sha256': hashlib.sha256(contents).hexdigest(),
    'scope': 'Independent final-package text inventory, exact source/module hashes, exported catalogue descriptions, '
             'IDs, time ordering, legacy attachment structure and contract shape. Canonical combat behaviour probes, formal JSON '
             'schema validation and new Godot/art validation are separate.',
    'inventory': inventory,
    'notes': ['No inspected package file was modified.',
              'The report is deliberately written outside the inspected package.'],
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key != 'inventory'}))
