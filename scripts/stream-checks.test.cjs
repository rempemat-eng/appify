const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {
  APP_ONLY,
  globToRegExp,
  workflowPaths,
  hostedRuns,
  gameOnly,
  gameSubset,
  touchedProtected,
  plan,
  readRecords,
  runChain,
  verifyGame,
} = require('./stream-checks.cjs');

const root = path.resolve(__dirname, '..');
const scripts = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')).scripts;
const ids = (steps) => steps.map((step) => step.id);
const sorted = (list) => [...list].sort((x, y) => x.localeCompare(y));
const trigger = (key, globs) =>
  `on:\n  pull_request:\n    ${key}:\n${globs.map((glob) => `      - '${glob}'\n`).join('')}jobs:\n`;

async function main() {
  // GitHub's path filters: * stays inside a folder, ** crosses folders, **/ may match none
  assert.ok(globToRegExp('game/**').test('game/tools/routes/main.txt'));
  assert.ok(!globToRegExp('game/**').test('scripts/game/x.py'));
  assert.ok(globToRegExp('**/*.md').test('README.md'));
  assert.ok(globToRegExp('**/*.md').test('docs/vision/a.md'));
  assert.ok(globToRegExp('lib/zone-*.ts').test('lib/zone-maps.ts'));
  assert.ok(!globToRegExp('lib/zone-*.ts').test('lib/zone-a/b.ts'));
  assert.ok(!globToRegExp('lib/a.ts').test('lib/axts'));

  const only = `on:\n  pull_request:\n    types: [opened]\n    paths:\n      - 'game/**'\n      - "x.yml"\n  push:\n    paths:\n      - 'never/**'\njobs:\n`;
  const ignore = `on:\n  pull_request:\n    paths-ignore:\n      - 'docs/**'\n      - '**/*.md'\n\npermissions:\n`;
  assert.deepEqual(workflowPaths(only), { paths: ['game/**', 'x.yml'], ignore: null });
  assert.deepEqual(workflowPaths(ignore), { paths: null, ignore: ['docs/**', '**/*.md'] });
  assert.equal(hostedRuns(only, ['game/a.gd']), true);
  assert.equal(hostedRuns(only, ['never/a', 'docs/a.md']), false, 'push filters are not read');
  assert.equal(hostedRuns(ignore, ['docs/a.md', 'AGENTS.md']), false);
  assert.equal(hostedRuns(ignore, ['docs/a.md', 'game/a.gd']), true);
  // anything unreadable or unusual keeps the check
  assert.equal(hostedRuns(undefined, ['docs/a.md']), true);
  assert.equal(hostedRuns('on:\n  pull_request:\n', ['docs/a.md']), true);
  assert.equal(hostedRuns(only.replace("'game/**'", "'!game/**'"), ['a']), true);

  assert.equal(gameOnly(['game/a.gd', 'docs/godot.md', 'AGENTS.md']), true);
  assert.equal(gameOnly(['game/a.gd', 'scripts/a.py']), false);
  assert.equal(gameOnly(['game/tools/a.ts']), false, 'the type check and lint would see it');
  assert.equal(gameOnly([]), false);

  // verify:game is `check` minus the listed app-only steps: a step nobody listed stays in
  const subset = gameSubset(scripts.check).map((step) => step.label);
  for (const kept of ['check:review', 'check:kit', 'check:quests'])
    assert.ok(subset.includes(kept));
  assert.equal(subset.length, scripts.check.split(' && ').length - APP_ONLY.length);
  assert.ok(
    gameSubset(`${scripts.check} && npm run check:new`).some((s) => s.label === 'check:new'),
  );
  assert.throws(() => gameSubset('tsc --noEmit && npm run lint'), /no longer has/);
  const ran = [];
  const refused = await verifyGame({
    root,
    changed: ['lib/game.ts'],
    log() {},
    run: () => ran.push(1),
  });
  assert.deepEqual([refused.ok, refused.refused, ran.length], [false, true, 0]);
  const run = async (command, args) => {
    ran.push(args[1]);
    return { status: args[1] === 'check:kit' ? 1 : 0, stdout: '', stderr: '' };
  };
  const partial = await verifyGame({ root, changed: ['game/a.gd'], log() {}, run });
  assert.equal(partial.ok, false, 'one failed step fails verify:game');
  assert.deepEqual(sorted(ran), sorted(subset), 'every remaining step still ran');

  assert.deepEqual(
    touchedProtected(['game/world/door.gd', '.github/workflows/a.yml', 'game/a.gd']),
    ['game/world/door.gd', '.github/workflows/a.yml'],
  );
  assert.deepEqual(touchedProtected(['game/actors/player.gd'], ['game/actors/player.gd']), []);

  // the plan follows the hosted path filters (fixtures shaped like .github/workflows on 13 Nov 2026)
  const workflows = {
    verify: trigger('paths-ignore', ['docs/**', '**/*.md']),
    godot: trigger('paths', ['game/**', 'scripts/godot-import-cache.py']),
    playtest: trigger('paths', ['game/**']),
    art: trigger('paths', ['scripts/**', 'assets/**', 'lib/zone-*.ts', 'package.json']),
  };
  const routes = [
    {
      name: 'first_night',
      files: ['game/tools/routes/first_night.txt', 'game/tools/routes/first_night.save.json'],
    },
    { name: 'main', files: ['game/tools/routes/main.txt'] },
  ];
  const game = [
    'game/world/raid_night.gd',
    'game/tools/routes/first_night.save.json',
    'docs/godot.md',
  ];
  assert.deepEqual(ids(plan({ changed: game, routes, workflows })), [
    'protected-paths',
    'check:godot',
    'verify:game',
    'route:first_night#1',
    'route:first_night#2',
    'route:first_night#3',
  ]);
  assert.deepEqual(ids(plan({ changed: game, routes, workflows, mode: 'final' })), [
    'protected-paths',
    'check:godot',
    'verify',
    'check:art-repro',
    'route:first_night#1',
    'route:first_night#2',
    'route:first_night#3',
    'route:main#1',
  ]);
  assert.deepEqual(ids(plan({ changed: ['docs/a.md'], routes, workflows })), ['protected-paths']);
  assert.deepEqual(ids(plan({ changed: ['scripts/a.cjs', 'package.json'], routes, workflows })), [
    'protected-paths',
    'verify',
    'check:art-repro',
  ]);
  assert.ok(
    ids(plan({ changed: ['game/data/sun.json'], routes, workflows })).includes('check:art-repro'),
  );
  assert.deepEqual(ids(plan({ changed: [], routes, mode: 'routes', extra: ['main'], repeat: 2 })), [
    'protected-paths',
    'route:main#1',
    'route:main#2',
  ]);
  assert.equal(
    plan({ changed: game, routes: [] }).length,
    4,
    'no readable filter keeps every check',
  );

  // a result counts only for the same tree and toolchain, and only when it finished with exit 0
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'stream-checks-test-'));
  try {
    const resultsFile = path.join(folder, 'deep', 'results.jsonl');
    const steps = plan({ changed: game, routes, workflows });
    const calls = [];
    let failing = 'route:first_night#2';
    const execute = async (step) => {
      calls.push(step.id);
      return { exit: step.id === failing ? 1 : 0, seconds: 1, waited: 0, log: 'x.log' };
    };
    const base = {
      steps,
      head: 'h',
      how: 'node 24',
      resultsFile,
      execute,
      changed: game,
      log() {},
    };
    let got = await runChain({ ...base, tree: 't1' });
    assert.equal(got.ok, false);
    assert.deepEqual(calls, [
      'check:godot',
      'verify:game',
      'route:first_night#1',
      'route:first_night#2',
    ]);
    assert.equal(got.rows.at(-1).state, 'NOT RUN', 'it stops at the first failure');
    calls.length = 0;
    failing = null;
    got = await runChain({ ...base, tree: 't1' });
    assert.deepEqual(
      calls,
      ['route:first_night#2', 'route:first_night#3'],
      'passes are not repeated',
    );
    assert.deepEqual([got.ok, got.complete], [true, true]);
    assert.equal(got.rows.filter((row) => row.note.startsWith('reused')).length, 3);
    calls.length = 0;
    await runChain({ ...base, tree: 't2' });
    assert.equal(calls.length, 5, 'another tree runs everything');
    calls.length = 0;
    await runChain({ ...base, tree: 't1', how: 'node 22' });
    assert.equal(calls.length, 5, 'another toolchain runs everything');
    calls.length = 0;
    await runChain({ ...base, tree: 't1', fresh: true });
    assert.equal(calls.length, 5, '--fresh trusts no record');
    // a restart mid-step leaves `started` and perhaps half a line: neither is a pass
    fs.appendFileSync(
      resultsFile,
      `${JSON.stringify({ id: 'check:godot', tree: 't3', how: 'node 24', state: 'started' })}\n{"id":"verify:game","tree":"t3","sta`,
    );
    assert.equal(readRecords(resultsFile).at(-1).state, 'started');
    calls.length = 0;
    got = await runChain({ ...base, tree: 't3', budget: -1 });
    assert.deepEqual(
      [calls.length, got.ok, got.complete],
      [0, false, false],
      'an empty budget starts nothing',
    );
    await runChain({ ...base, tree: 't3' });
    assert.equal(calls.length, 5);
    calls.length = 0;
    await runChain({ ...base, tree: 't3' });
    assert.equal(calls.length, 0, 'the record after a cut-off line is still read');
    // an edit while a step runs: no pass is recorded and the chain stops, even with --keep-going
    calls.length = 0;
    got = await runChain({ ...base, tree: 't5', treeNow: () => 't6', keepGoing: true });
    assert.deepEqual([calls, got.ok, got.rows[1].state], [['check:godot'], false, 'FAIL']);
    await runChain({ ...base, tree: 't5' });
    assert.equal(calls.length, 6, 'the step that ran across the edit runs again');
    // a protected path fails the chain before anything heavy starts, unless the brief allows it
    calls.length = 0;
    const edited = [...game, 'game/actors/player.gd'];
    got = await runChain({ ...base, tree: 't4', changed: edited });
    assert.deepEqual([got.ok, calls.length, got.rows[0].state], [false, 0, 'FAIL']);
    got = await runChain({
      ...base,
      tree: 't4',
      changed: edited,
      allow: ['game/actors/player.gd'],
    });
    assert.equal(got.ok, true);
  } finally {
    fs.rmSync(folder, { recursive: true, force: true });
  }
  console.log(
    'Stream check runner: plans, hosted path filters, verify:game and resumed results pass.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
