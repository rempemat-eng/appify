/** Real Git/copy/diff boundaries; generator processes are substituted. No Python needed. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const {
  checkArtReproducibility,
  generators,
  generatedTypescript,
} = require('./check-art-repro.cjs');

const owned = fs.mkdtempSync(path.join(os.tmpdir(), 'napattack-art-repro-test-'));
const root = path.join(owned, 'repo');
let checks = 0;
let exceptionalSnapshot;
function check(value, message) {
  assert.ok(value, message);
  checks++;
}
function write(file, data) {
  const target = path.join(root, file);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, data);
}
try {
  fs.mkdirSync(root);
  write('.gitignore', 'node_modules/\n');
  write('assets/example.png', Buffer.from([0, 1, 2, 255]));
  write('node_modules/.bin/oxfmt', '# installed formatter fixture\n');
  const atlasModules = [
    'lib/zone-maps.ts',
    'lib/zone-assets.ts',
    'lib/journey-assets.ts',
    'lib/resident-sprites.ts',
    'lib/resident-assets.ts',
    'lib/decor-assets.ts',
    'lib/decor-sizes.ts',
  ];
  for (const file of atlasModules) write(file, 'atlas fixture\n');
  write('assets/journeys/example.png', Buffer.from([6, 7, 8, 255]));
  for (const name of generators) write(`scripts/art/${name}.py`, '# generator fixture\n');
  write('lib/mission-map.ts', 'mission map fixture\n');
  write('assets/zones/town/ground.png', Buffer.from([3, 4, 5, 255]));
  assert.deepEqual(generators, [
    'garden',
    'pets',
    'battle',
    'worlds',
    'vignettes',
    'icons',
    'mission_map',
    'zones',
    'journey',
    'rocket',
    'residents',
    'decor',
    'world_routes',
    'world_land',
    'cliff_core',
    'kit_golden',
  ]);
  checks++;
  for (const file of atlasModules) check(generatedTypescript.includes(file), 'formats ' + file);
  check(generatedTypescript.includes('lib/mission-map.ts'), 'formats the destination map module');
  write('lib/garden-map.ts', 'tracked, then deliberately unstaged\n');
  for (const args of [
    ['init', '-q'],
    ['add', '--all'],
  ]) {
    const result = spawnSync('git', args, { cwd: root, encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
  }
  write('lib/garden-map.ts', 'current uncommitted work must survive\n');
  write('untracked-note.txt', 'not part of the snapshot\n');
  const originals = new Map([
    ['assets/example.png', fs.readFileSync(path.join(root, 'assets/example.png'))],
    ['lib/mission-map.ts', fs.readFileSync(path.join(root, 'lib/mission-map.ts'))],
    [
      'assets/zones/town/ground.png',
      fs.readFileSync(path.join(root, 'assets/zones/town/ground.png')),
    ],
    ['lib/garden-map.ts', fs.readFileSync(path.join(root, 'lib/garden-map.ts'))],
  ]);
  for (const file of [...atlasModules, 'assets/journeys/example.png'])
    originals.set(file, fs.readFileSync(path.join(root, file)));
  const originalIndex = spawnSync('git', ['write-tree'], { cwd: root, encoding: 'utf8' }).stdout;
  function scenario(mode) {
    const calls = [];
    let snapshot;
    const result = checkArtReproducibility({
      root,
      log() {},
      run(command, args, options) {
        snapshot = options.cwd;
        if (mode === 'exception') exceptionalSnapshot = snapshot;
        calls.push({ command, args });
        check(snapshot !== root, mode + ': generators never execute in the caller checkout');
        check(
          !fs.existsSync(path.join(snapshot, 'untracked-note.txt')),
          mode + ': excludes untracked source',
        );
        check(
          fs.readFileSync(path.join(snapshot, 'lib/garden-map.ts'), 'utf8') ===
            'current uncommitted work must survive\n',
          mode + ': uses current tracked bytes, not HEAD',
        );
        const previewRoot = path.join(path.dirname(snapshot), 'previews');
        check(
          options.env.npm_config_offline === 'true',
          mode + ': generator npm subprocesses stay offline',
        );
        const dependencyLink = path.join(snapshot, 'node_modules');
        if (mode !== 'replaced-dependencies' || args[0] !== 'scripts/check-sprites.cjs')
          check(
            fs.lstatSync(dependencyLink).isSymbolicLink() &&
              fs.readlinkSync(dependencyLink) === path.join(root, 'node_modules'),
            mode + ': installed toolchain is available before generators',
          );
        check(options.env.JOURNEY_PREVIEW === previewRoot, mode + ': journey preview stays owned');
        check(
          options.env.MAP_PREVIEW === path.join(previewRoot, 'mission-map.png'),
          mode + ': map preview stays owned',
        );
        check(options.env.ZONE_PREVIEW === previewRoot, mode + ': zone previews stay owned');
        if (args[0] === 'scripts/art/mission_map.py') {
          fs.writeFileSync(options.env.MAP_PREVIEW, 'map preview fixture');
          if (mode === 'changed-mission-map')
            fs.writeFileSync(path.join(snapshot, 'lib/mission-map.ts'), 'drift');
          if (mode === 'failed-mission-map')
            return { status: 1, stdout: '', stderr: 'synthetic map failure' };
        }
        if (args[0] === 'scripts/art/zones.py') {
          fs.writeFileSync(
            path.join(options.env.ZONE_PREVIEW, 'zone-town.png'),
            'zone preview fixture',
          );
          if (mode === 'changed-zone-map')
            fs.writeFileSync(path.join(snapshot, 'lib/zone-maps.ts'), 'drift');
          if (mode === 'changed-zone-assets')
            fs.writeFileSync(path.join(snapshot, 'lib/zone-assets.ts'), 'drift');
          if (mode === 'changed-zone')
            fs.writeFileSync(path.join(snapshot, 'assets/zones/town/ground.png'), 'drift');
          if (mode === 'new-zone')
            fs.writeFileSync(path.join(snapshot, 'assets/zones/uncommitted.png'), 'new');
          if (mode === 'failed-zone')
            return { status: 1, stdout: '', stderr: 'synthetic zone failure' };
        }
        if (args[0] === 'scripts/art/journey.py') {
          fs.writeFileSync(
            path.join(options.env.JOURNEY_PREVIEW, 'journeys.png'),
            'journey preview fixture',
          );
          if (mode === 'changed-journey')
            fs.writeFileSync(path.join(snapshot, 'lib/journey-assets.ts'), 'drift');
          if (mode === 'changed-journey-png')
            fs.writeFileSync(path.join(snapshot, 'assets/journeys/example.png'), 'drift');
          if (mode === 'new-journey')
            fs.writeFileSync(path.join(snapshot, 'assets/journeys/uncommitted.png'), 'new');
          if (mode === 'failed-journey')
            return { status: 1, stdout: '', stderr: 'synthetic journey failure' };
        }
        if (mode === 'replaced-dependencies' && args[0] === '--write') {
          fs.unlinkSync(dependencyLink);
          fs.writeFileSync(dependencyLink, 'unexpected replacement');
        }
        if (args[0] === 'scripts/art/garden.py') {
          if (mode === 'dependency-prefix-file')
            fs.writeFileSync(path.join(snapshot, 'node_modules-unexpected'), 'new');
          if (mode === 'changed')
            fs.writeFileSync(path.join(snapshot, 'assets/example.png'), Buffer.from([9, 8, 7]));
          if (mode === 'deleted') fs.unlinkSync(path.join(snapshot, 'assets/example.png'));
          if (mode === 'new')
            fs.writeFileSync(path.join(snapshot, 'assets/new.png'), Buffer.from([1]));
          if (mode === 'exception') throw new Error('synthetic unexpected exception');
        }
        if (mode === 'failed-generator' && args[0] === 'scripts/art/vignettes.py')
          return { status: 1, stdout: '', stderr: 'synthetic generator failure' };
        if (mode === 'failed-format' && args[0] === '--write')
          return { status: 1, stdout: '', stderr: 'synthetic formatter failure' };
        if (mode === 'failed-sprites' && args[0] === 'scripts/check-sprites.cjs')
          return { status: 1, stdout: '', stderr: 'synthetic sprite failure' };
        return { status: 0, stdout: '', stderr: '' };
      },
    });
    check(!fs.existsSync(snapshot), mode + ': disposable copy is cleaned up');
    check(
      calls
        .filter((c) => c.args[0].startsWith('scripts/art/'))
        .map((c) => c.args[0])
        .join('|') === generators.map((name) => `scripts/art/${name}.py`).join('|'),
      mode + ': runs every production entry point',
    );
    const format = calls.find((c) => c.args[0] === '--write');
    assert.deepEqual(format.args.slice(1), generatedTypescript);
    checks++;
    check(
      calls.at(-1).args[0] === 'scripts/check-sprites.cjs',
      mode + ': sprite check runs last even after failure',
    );
    for (const [file, bytes] of originals) {
      assert.deepEqual(fs.readFileSync(path.join(root, file)), bytes);
      checks++;
    }
    check(
      spawnSync('git', ['write-tree'], { cwd: root, encoding: 'utf8' }).stdout === originalIndex,
      mode + ': caller index is untouched',
    );
    return result;
  }
  check(scenario('clean').ok, 'matching bytes pass');
  const priorIndex = process.env.GIT_INDEX_FILE;
  try {
    process.env.GIT_INDEX_FILE = path.join(root, '.git', 'index');
    check(scenario('clean').ok, 'an inherited Git index cannot redirect snapshot writes');
  } finally {
    if (priorIndex === undefined) delete process.env.GIT_INDEX_FILE;
    else process.env.GIT_INDEX_FILE = priorIndex;
  }
  const priorPreviews = {
    MAP_PREVIEW: process.env.MAP_PREVIEW,
    ZONE_PREVIEW: process.env.ZONE_PREVIEW,
    JOURNEY_PREVIEW: process.env.JOURNEY_PREVIEW,
  };
  try {
    process.env.MAP_PREVIEW = path.join(root, 'caller-map.png');
    process.env.ZONE_PREVIEW = path.join(root, 'caller-zones');
    process.env.JOURNEY_PREVIEW = path.join(root, 'caller-journeys');
    check(scenario('inherited-previews').ok, 'foreign preview overrides cannot cause drift');
    check(!fs.existsSync(process.env.MAP_PREVIEW), 'never writes caller map preview');
    check(!fs.existsSync(process.env.ZONE_PREVIEW), 'never creates caller zone preview directory');
    check(
      !fs.existsSync(process.env.JOURNEY_PREVIEW),
      'never creates caller journey preview directory',
    );
  } finally {
    for (const [key, value] of Object.entries(priorPreviews)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
  for (const mode of [
    'changed',
    'deleted',
    'new',
    'failed-generator',
    'failed-format',
    'failed-sprites',
    'changed-mission-map',
    'changed-zone',
    'new-zone',
    'failed-mission-map',
    'failed-zone',
    'changed-zone-map',
    'changed-zone-assets',
    'changed-journey',
    'changed-journey-png',
    'new-journey',
    'failed-journey',
    'replaced-dependencies',
    'dependency-prefix-file',
  ]) {
    const result = scenario(mode);
    check(!result.ok, mode + ': cannot silently pass');
    check(result.failures.length > 0, mode + ': emits actionable failure');
    const expected = {
      'changed-mission-map': 'Tracked output drift: lib/mission-map.ts',
      'changed-zone': 'Tracked output drift: assets/zones/town/ground.png',
      'new-zone': 'Uncommitted generated files: assets/zones/uncommitted.png',
      'failed-mission-map': 'mission_map.py: exit 1',
      'failed-zone': 'zones.py: exit 1',
      'changed-zone-map': 'Tracked output drift: lib/zone-maps.ts',
      'changed-zone-assets': 'Tracked output drift: lib/zone-assets.ts',
      'changed-journey': 'Tracked output drift: lib/journey-assets.ts',
      'changed-journey-png': 'Tracked output drift: assets/journeys/example.png',
      'new-journey': 'Uncommitted generated files: assets/journeys/uncommitted.png',
      'failed-journey': 'journey.py: exit 1',
      'replaced-dependencies': 'Installed toolchain link was replaced or removed',
      'dependency-prefix-file': 'Uncommitted generated files: node_modules-unexpected',
    }[mode];
    if (expected) check(result.failures.includes(expected), mode + ': identifies exact failure');
  }
  assert.throws(() => scenario('exception'), /synthetic unexpected exception/);
  checks++;
  check(
    !fs.existsSync(exceptionalSnapshot),
    'unexpected exceptions also clean the disposable copy',
  );
  console.log(
    `PASS: ${checks} art-repro isolation, byte drift, failure propagation and cleanup assertions.`,
  );
} finally {
  fs.rmSync(owned, { recursive: true, force: true });
}
