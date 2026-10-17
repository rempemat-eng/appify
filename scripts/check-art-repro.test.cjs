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
  write('scripts/art/garden.py', '# generator fixture\n');
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
    ['lib/garden-map.ts', fs.readFileSync(path.join(root, 'lib/garden-map.ts'))],
  ]);
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
        if (args[0] === 'scripts/art/garden.py') {
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
      mode + ': runs all six production entry points',
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
  for (const mode of [
    'changed',
    'deleted',
    'new',
    'failed-generator',
    'failed-format',
    'failed-sprites',
  ]) {
    const result = scenario(mode);
    check(!result.ok, mode + ': cannot silently pass');
    check(result.failures.length > 0, mode + ': emits actionable failure');
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
