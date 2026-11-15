const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const {
  APP_ONLY,
  FAST_ARGS,
  ART_BYTE_STEPS,
  leftToFinal,
  reusableRecord,
  changedPaths,
  toolchainKey,
  artBytesProblem,
  artBytesProblems,
  probePythons,
  routeEnv,
  FAST_TIMEOUT,
  hostedPins,
  main: cli,
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

const stub = (failing) => {
  const calls = [];
  const execute = async (step) => {
    calls.push(step.id);
    return { exit: failing.has(step.id) ? 1 : 0, seconds: 1, waited: 0, log: `${step.id}.log` };
  };
  return { calls, execute, failing };
};
const chain = (folder, name, more) => {
  const lines = [];
  return {
    lines,
    options: {
      tree: 't',
      head: 'h',
      how: 'tools',
      resultsFile: path.join(folder, `${name}.jsonl`),
      log: (line) => lines.push(line),
      ...more,
    },
  };
};

const made = (id, exit, state = 'done') => ({ id, tree: 't', how: 'tools', state, exit });

/** Audit B1: an older pass must not outlive a later failure on the same tree. */
async function testNewestRecordDecides(folder) {
  const steps = [{ id: 'verify', command: 'npm', args: ['run', 'verify'] }];
  const { calls, execute, failing } = stub(new Set());
  const { options } = chain(folder, 'newest', { steps, execute });
  assert.equal((await runChain(options)).rows[0].note, 'ran');
  failing.add('verify');
  assert.equal((await runChain({ ...options, fresh: true })).ok, false, 'the --fresh run fails');
  calls.length = 0;
  const after = await runChain(options);
  assert.deepEqual(calls, ['verify'], 'the pass before the failure is not reused');
  assert.equal(after.ok, false);
  assert.deepEqual(
    after.earlier.map((record) => [record.id, record.exit]),
    [['verify', 1]],
  );
  failing.clear();
  calls.length = 0;
  assert.equal((await runChain(options)).ok, true);
  assert.deepEqual(calls, ['verify'], 'it runs again until its newest record is a pass');
  calls.length = 0;
  assert.equal((await runChain(options)).rows[0].note.startsWith('reused'), true);
  assert.equal(calls.length, 0);
  // the rule itself, on plain records
  const verify = { id: 'verify' };
  assert.equal(reusableRecord([made('verify', 0), made('verify', 1)], verify, 't', 'tools'), null);
  assert.ok(reusableRecord([made('verify', 1), made('verify', 0)], verify, 't', 'tools'));
  assert.equal(
    reusableRecord([made('verify', 0), made('verify', 0, 'moved')], verify, 't', 'tools'),
    null,
    'a run the tree moved under is a failure too',
  );
  assert.ok(
    reusableRecord([made('verify', 0), made('verify', undefined, 'started')], verify, 't', 'tools'),
    'an unfinished start is no result either way',
  );
}

/** Audit B2: three of three cannot be collected over retries. */
async function testRouteFailureVoidsEveryRun(folder) {
  const routes = [{ name: 'main', files: ['game/tools/routes/main.txt'] }];
  const steps = plan({ changed: [], routes, mode: 'routes', extra: ['main'] });
  const { calls, execute, failing } = stub(new Set(['route:main#2']));
  const { options, lines } = chain(folder, 'routes', { steps, execute, mode: 'routes' });
  assert.equal((await runChain(options)).ok, false);
  assert.deepEqual(calls, ['route:main#1', 'route:main#2']);
  failing.clear();
  calls.length = 0;
  lines.length = 0;
  const retry = await runChain(options);
  assert.deepEqual(
    calls,
    ['route:main#1', 'route:main#2', 'route:main#3'],
    'run 1 passed before the failure, so it does not count',
  );
  assert.equal(retry.ok, true);
  assert.deepEqual(
    retry.earlier.map((record) => record.id),
    ['route:main#2'],
  );
  assert.ok(
    lines.some((line) => /^EARLIER route:main#2 .*exit 1/.test(line)),
    lines.join('\n'),
  );
  assert.match(
    lines.at(-2),
    /3 passed \(0 reused\), 0 failed, 0 not run, 1 earlier failure on this tree/,
  );
  calls.length = 0;
  const again = await runChain(options);
  assert.equal(calls.length, 0, 'three passes in a row after the last failure are reused');
  assert.equal(again.earlier.length, 1, 'and the failure is still named');
  // with --keep-going a later run can pass after the failure: it counts, the earlier one does not
  const { options: kept } = chain(folder, 'routes-kept', { steps, execute, mode: 'routes' });
  failing.add('route:main#2');
  await runChain({ ...kept, keepGoing: true });
  failing.clear();
  calls.length = 0;
  await runChain(kept);
  assert.deepEqual(calls, ['route:main#1', 'route:main#2']);
  // another route's failure voids nothing here
  const other = { id: 'route:other#1', tree: 't', how: 'tools', state: 'done', exit: 1 };
  const pass = { id: 'route:main#1', tree: 't', how: 'tools', state: 'done', exit: 0 };
  assert.ok(reusableRecord([pass, other], steps[1], 't', 'tools'));
  assert.equal(
    reusableRecord([pass, { ...other, id: 'route:main#3' }], steps[1], 't', 'tools'),
    null,
  );
}

/** Audit B3: a rename must show the path it left as well as the one it made. */
function testRenamesShowBothPaths() {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'stream-checks-git-'));
  try {
    const env = { ...process.env };
    for (const key of Object.keys(env)) if (key.startsWith('GIT_')) delete env[key];
    const git = (...args) => {
      const got = spawnSync(
        'git',
        [
          '-c',
          'user.name=t',
          '-c',
          'user.email=t@example.invalid',
          '-c',
          'commit.gpgsign=false',
          ...args,
        ],
        { cwd: repo, env, encoding: 'utf8' },
      );
      assert.equal(got.status, 0, got.stderr);
    };
    const body = 'extends Node\n'.repeat(40);
    for (const file of ['game/actors/player.gd', 'scripts/art/gen.py', 'lib/a.ts']) {
      fs.mkdirSync(path.join(repo, path.dirname(file)), { recursive: true });
      fs.writeFileSync(path.join(repo, file), `# ${file}\n${body}`);
    }
    fs.mkdirSync(path.join(repo, 'docs'));
    git('init', '-q', '-b', 'main');
    git('add', '--all');
    git('commit', '-q', '-m', 'base');
    git('checkout', '-q', '-b', 'work');
    git('mv', 'game/actors/player.gd', 'game/actors/hero.gd');
    git('mv', 'scripts/art/gen.py', 'docs/gen.md');
    git('mv', 'lib/a.ts', 'game/a.txt');
    git('commit', '-q', '-m', 'moves');
    const saved = { ...process.env };
    for (const key of Object.keys(process.env)) if (key.startsWith('GIT_')) delete process.env[key];
    let changed;
    try {
      changed = changedPaths(repo, 'main');
    } finally {
      Object.assign(process.env, saved);
    }
    assert.deepEqual(changed, [
      'docs/gen.md',
      'game/a.txt',
      'game/actors/hero.gd',
      'game/actors/player.gd',
      'lib/a.ts',
      'scripts/art/gen.py',
    ]);
    assert.deepEqual(
      touchedProtected(changed),
      ['game/actors/player.gd'],
      'the guard sees the move',
    );
    assert.equal(gameOnly(changed), false, 'verify:game refuses a diff that removes lib/a.ts');
    assert.ok(ids(plan({ changed, workflows: {} })).includes('verify'));
  } finally {
    fs.rmSync(repo, { recursive: true, force: true });
  }
}

/** Audit B4: check:godot's tests read files outside game/; the final head always runs it. */
function testGodotOutsideGame({ routes, workflows }) {
  for (const file of [
    'scripts/art/kit/build.py',
    'scripts/art/house_palette.py',
    'scripts/review/kit_scene.py',
    'scripts/progression/weapon_lines.py',
    'art/house-palette.json',
  ])
    assert.ok(ids(plan({ changed: [file], routes, workflows })).includes('check:godot'), file);
  assert.ok(!ids(plan({ changed: ['scripts/a.cjs'], routes, workflows })).includes('check:godot'));
  for (const changed of [['docs/a.md'], ['scripts/a.cjs'], ['lib/a.ts'], []])
    assert.deepEqual(
      ids(plan({ changed, routes, workflows, mode: 'final' })).slice(0, 4),
      ['protected-paths', 'check:godot', 'verify', 'check:art-repro'],
      `--final with ${changed.join(', ')}`,
    );
}

/** Audit B5: files under docs/ that the art generators and steps of `check` read or compare. */
function testDocsThatChecksRead({ routes, workflows }) {
  for (const file of [
    'docs/vision/research/blockout/blockout-v52.json',
    'docs/vision/regions/route-meets.md',
    'docs/vision/cliff-core/demo.png',
    'docs/vision/icon-sheet.png',
    'docs/vision/icon-sheet-2x.png',
  ]) {
    assert.deepEqual(
      ids(plan({ changed: [file], routes, workflows })),
      ['protected-paths', 'verify', 'check:art-repro'],
      file,
    );
    assert.equal(gameOnly([file, 'game/a.gd']), false, `verify:game refuses ${file}`);
  }
  for (const file of [
    'docs/vision/asset-ledger.md',
    'docs/vision/prop-logic.md',
    'docs/vision/placement-audit.md',
    'docs/vision/regions/sunstone-basin-fire-country.md',
  ])
    assert.deepEqual(
      ids(plan({ changed: [file], routes, workflows })),
      ['protected-paths', 'verify'],
      file,
    );
  assert.deepEqual(ids(plan({ changed: ['docs/vision/art-style.md'], routes, workflows })), [
    'protected-paths',
  ]);
}

/** Audit B6: the summary says which mode ran and what is left to --final. */
function testModeAndLeftToFinal({ routes, workflows, game }) {
  const options = { changed: game, routes, workflows };
  assert.deepEqual(leftToFinal(options), [
    `verify (verify:game left out ${APP_ONLY.length} app-only steps and the two exports)`,
    'check:art-repro',
    'routes main',
  ]);
  // a game code change plays no route in the inner loop: every route is named as left
  assert.deepEqual(
    leftToFinal({ ...options, changed: ['game/actors/enemy.gd'] }).at(-1),
    'routes first_night, main',
  );
  assert.deepEqual(leftToFinal({ ...options, mode: 'final' }), []);
  assert.deepEqual(
    leftToFinal({ changed: [], routes, workflows, mode: 'routes', extra: ['main'] }),
    ['check:godot', 'verify', 'check:art-repro'],
  );
  assert.deepEqual(leftToFinal({ changed: ['docs/a.md'], routes, workflows }), [
    'check:godot',
    'verify',
    'check:art-repro',
  ]);
}
async function testSummaryNamesModeAndNothingSelected(folder) {
  const steps = plan({ changed: ['lib/a.ts'], workflows: {} });
  const { execute } = stub(new Set());
  const inner = chain(folder, 'mode', { steps, execute, left: ['check:art-repro', 'routes main'] });
  await runChain(inner.options);
  assert.match(inner.lines.at(-2), /^stream-checks: inner mode, tree t head h: \d+ passed/);
  assert.match(
    inner.lines.at(-1),
    /not the final chain\. Left to .*--final.*: check:art-repro; routes main$/,
  );
  const final = chain(folder, 'mode-final', { steps, execute, mode: 'final' });
  await runChain(final.options);
  assert.match(final.lines.at(-1), /^stream-checks: final mode, /);
  assert.ok(!final.lines.some((line) => line.includes('Left to')));
  // Audit N3: a plan with no check says so and counts nothing as passed
  const empty = chain(folder, 'empty', {
    steps: plan({ changed: [], workflows: { verify: '', godot: '', art: '', playtest: '' } }).slice(
      0,
      1,
    ),
    execute,
    left: ['verify'],
  });
  const got = await runChain(empty.options);
  assert.equal(got.nothing, true);
  assert.match(empty.lines.at(-2), /nothing selected for this diff, so no check ran/);
  assert.ok(!empty.lines.some((line) => /\d+ passed/.test(line)));
  const guarded = chain(folder, 'empty-guard', {
    steps: [{ id: 'protected-paths', kind: 'protected' }],
    execute,
    changed: ['game/actors/player.gd'],
  });
  assert.equal((await runChain(guarded.options)).ok, false, 'a protected path still fails it');
  assert.ok(guarded.lines.some((line) => /0 passed .*1 failed/.test(line)));
}

/** The opt-in fast mode: its own step id and cache key, labelled lines, never in a counted plan. */
function testFastPlan({ routes, workflows, game }) {
  const fast = plan({ changed: [], routes, mode: 'routes', extra: ['main'], fast: true });
  assert.deepEqual(
    ids(fast),
    ['protected-paths', 'route-fast:main#1'],
    'once: repeats prove nothing',
  );
  assert.equal(fast[1].fast, true);
  for (const mode of ['inner', 'final'])
    assert.ok(
      plan({ changed: game, routes, workflows, mode, fast: true }).every(
        (step) => !step.fast && !step.id.includes('fast'),
      ),
      `${mode} never plays in fixed step`,
    );
  assert.deepEqual(FAST_ARGS, ['--fixed-fps', '60', '--disable-render-loop']);
  // round 2, N1: a failing fast route would wait 900 s for a picture that is never drawn
  assert.deepEqual(routeEnv(fast[1], '/out'), {
    PLAYTEST_OUT: '/out',
    PLAYTEST_TIMEOUT: String(FAST_TIMEOUT),
  });
  assert.ok(FAST_TIMEOUT <= 300);
  assert.deepEqual(routeEnv({ kind: 'route' }, '/out'), { PLAYTEST_OUT: '/out' });
}
async function testFastRunsAreLabelledAndKeptApart(folder) {
  const routes = [{ name: 'main', files: [] }];
  const fastSteps = plan({ changed: [], routes, mode: 'routes', extra: ['main'], fast: true });
  const realSteps = plan({ changed: [], routes, mode: 'routes', extra: ['main'], repeat: 1 });
  const { calls, execute } = stub(new Set());
  const fast = chain(folder, 'fast', { steps: fastSteps, execute, mode: 'routes (FAST)' });
  await runChain(fast.options);
  const record = readRecords(fast.options.resultsFile).at(-1);
  assert.equal(record.id, 'route-fast:main#1');
  assert.equal(record.how, 'tools; fast --fixed-fps 60 --disable-render-loop');
  assert.ok(fast.lines.includes('[stream-checks] FAST PASS route-fast:main#1 (1s, waited 0s)'));
  assert.ok(fast.lines.some((line) => /^PASS +route-fast:main#1 +1s {2}FAST ran$/.test(line)));
  assert.ok(
    fast.lines.some((line) => /1 FAST route run .*not one of the counted repeats/.test(line)),
  );
  // a fast pass is never reused as a real run, nor a real pass as a fast one
  calls.length = 0;
  await runChain({ ...fast.options, steps: realSteps, mode: 'routes' });
  assert.deepEqual(calls, ['route:main#1']);
  assert.equal(
    reusableRecord([{ ...record, id: 'route:main#1' }], realSteps[1], 't', 'tools'),
    null,
  );
  calls.length = 0;
  fast.lines.length = 0;
  await runChain(fast.options);
  assert.equal(calls.length, 0);
  assert.ok(fast.lines.some((line) => / FAST reused, finished /.test(line)));
}

/** Audit N4: --base reaches the verify:game step, which would otherwise compare with origin/main. */
function testBasePassedToVerifyGame({ routes, workflows, game }) {
  const step = (base) =>
    plan({ changed: game, routes, workflows, base }).find((s) => s.id === 'verify:game');
  assert.deepEqual(step('HEAD~2').args, ['run', 'verify:game', '--', '--base=HEAD~2']);
  assert.deepEqual(step(undefined).args, ['run', 'verify:game']);
}

/** Audit N6: an empty budget starts nothing, not even the first step. */
async function testZeroBudgetStartsNothing(folder) {
  const { calls, execute } = stub(new Set());
  const { options } = chain(folder, 'budget', {
    steps: [{ id: 'verify', command: 'npm', args: ['run', 'verify'] }],
    execute,
    budget: 0,
  });
  const got = await runChain(options);
  assert.deepEqual([calls.length, got.complete, got.rows[0].note], [0, false, 'budget']);
}

/** Audit B7: every part of the toolchain is in the key a result is reused under. */
function testToolchainKey() {
  const python = {
    python: '3.12.3',
    pillow: '12.3.0',
    numpy: '2.5.3',
    scipy: '1.18.1',
    zlib: '1.3',
  };
  const tools = { node: '24.19.0', python, godot: 'sha256:aa' };
  const key = toolchainKey(tools);
  assert.equal(
    key,
    'node 24.19.0; python 3.12.3; Pillow 12.3.0; numpy 2.5.3; scipy 1.18.1; zlib 1.3; godot sha256:aa',
  );
  const others = [
    { ...tools, node: '24.22.3' },
    { ...tools, godot: 'sha256:bb' },
    { ...tools, godot: undefined },
    ...Object.keys(python).map((part) => ({ ...tools, python: { ...python, [part]: 'other' } })),
    { ...tools, python: { ...python, zlib: '1.3.1.zlib-ng' } },
  ].map(toolchainKey);
  assert.equal(new Set([key, ...others]).size, others.length + 1, 'each part changes the key');
  assert.match(toolchainKey({ node: '24.19.0' }), /python none; Pillow none; .*godot none$/);
  // round 2, N3: with PYTHON set, the Python that check:art-repro starts is in the key too
  const withEnv = toolchainKey({ ...tools, envPython: { ...python, zlib: '1.3.1.zlib-ng' } });
  assert.notEqual(withEnv, key);
  assert.match(
    withEnv,
    /zlib 1\.3; PYTHON 3\.12\.3 Pillow 12\.3\.0 numpy 2\.5\.3 scipy 1\.18\.1 zlib 1\.3\.1\.zlib-ng; godot/,
  );
}

/** The preflight for plans with an art or kit check: no byte comparison on a foreign PNG encoder. */
function testArtBytesPreflight() {
  const python = {
    python: '3.12.3',
    pillow: '12.3.0',
    numpy: '2.5.3',
    scipy: '1.18.1',
    zlib: '1.3',
  };
  assert.equal(artBytesProblem(python), null);
  assert.match(
    artBytesProblem({ ...python, zlib: '1.3.1.zlib-ng' }),
    /zlib 1\.3\.1\.zlib-ng.*kit\.build --check/,
  );
  assert.match(artBytesProblem({ ...python, zlib: null }), /unknown/);
  assert.match(artBytesProblem({ ...python, pillow: null }), /no Pillow/);
  assert.deepEqual(ART_BYTE_STEPS, ['verify', 'verify:game', 'check:art-repro']);
  assert.deepEqual(hostedPins("pip install 'Pillow==12.3.0' 'numpy==2.5.3' 'scipy==1.18.1'"), {
    pillow: '12.3.0',
    numpy: '2.5.3',
    scipy: '1.18.1',
  });
  assert.equal(hostedPins('run: npm ci'), null);
  // round 2, N3: `$PYTHON` is probed when set, and a bad one stops the plan like a bad python3
  const asked = [];
  const probe = (_run, command) => {
    asked.push(command);
    return command === 'python3' ? python : { ...python, zlib: '1.3.1.zlib-ng' };
  };
  assert.deepEqual(probePythons({}, probe), { python });
  const both = probePythons({ PYTHON: '/opt/py/bin/python' }, probe);
  assert.deepEqual(asked, ['python3', 'python3', '/opt/py/bin/python']);
  assert.match(artBytesProblems(both), /^PYTHON is set .*zlib 1\.3\.1\.zlib-ng/);
  assert.equal(artBytesProblems({ python, envPython: python }), null);
  assert.equal(artBytesProblems({ python }), null);
  assert.match(
    artBytesProblems({ python: { ...python, pillow: null }, envPython: python }),
    /no Pillow/,
  );
}

/** Audit N2: a repeat that is not a whole number of 1 or more is a usage error, not "passed". */
async function testRepeatMustBeAWholeNumber() {
  const error = console.error;
  const said = [];
  console.error = (line) => said.push(line);
  try {
    for (const bad of [
      '--repeat=abc',
      '--repeat=0',
      '--repeat=-1',
      '--repeat=1.5',
      '--budget=soon',
    ])
      assert.equal(await cli(['routes', 'main', bad]), 2, bad);
    assert.equal(await cli(['--fast']), 2, '--fast is not for the inner loop');
    assert.equal(await cli(['--final', '--fast']), 2, 'nor for the final chain');
    assert.equal(
      await cli(['routes', 'main', '--fast', '--repeat=3']),
      2,
      'fast runs are not repeated',
    );
    // round 2, N2: `routes` is never the final chain
    assert.equal(await cli(['routes', 'main', '--final']), 2);
    assert.equal(await cli(['routes', 'main', '--final', '--fast']), 2);
    assert.match(said.at(-1), /`routes` plays the named routes only and is never the final chain/);
  } finally {
    console.error = error;
  }
  assert.match(said[0], /--repeat takes a whole number of 1 or more, not "abc"/);
}

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
  testGodotOutsideGame({ routes, workflows });
  testDocsThatChecksRead({ routes, workflows });
  testModeAndLeftToFinal({ routes, workflows, game });
  testFastPlan({ routes, workflows, game });
  testBasePassedToVerifyGame({ routes, workflows, game });
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
      ['route:first_night#1', 'route:first_night#2', 'route:first_night#3'],
      'passes of other steps are not repeated; the failed route starts its count again',
    );
    assert.deepEqual([got.ok, got.complete], [true, true]);
    assert.equal(got.rows.filter((row) => row.note.startsWith('reused')).length, 2);
    assert.deepEqual(
      got.earlier.map((record) => record.id),
      ['route:first_night#2'],
    );
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
    await testNewestRecordDecides(folder);
    await testRouteFailureVoidsEveryRun(folder);
    await testSummaryNamesModeAndNothingSelected(folder);
    await testFastRunsAreLabelledAndKeptApart(folder);
    await testZeroBudgetStartsNothing(folder);
  } finally {
    fs.rmSync(folder, { recursive: true, force: true });
  }
  testRenamesShowBothPaths();
  testToolchainKey();
  testArtBytesPreflight();
  await testRepeatMustBeAWholeNumber();
  console.log(
    'Stream check runner: plans, hosted path filters, verify:game, resumed results, voided route runs, renames, the toolchain key and the fast mode pass.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
