/** A stream's resumable check chain (docs/stream-checks.md).
 * Additions only: every command it starts is an existing, unchanged check. It records each exit
 * against the exact tree, and on the same tree it does not rerun what already passed, so a
 * restarted container or a resumed agent loses one step at most. `--final` is the whole chain
 * for the head that is marked ready; the default is the inner loop for the paths that changed. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const { checkCommands } = require('./run-verification.cjs');
const { mapLimit, runProcess, concurrency } = require('./check-runner.cjs');

/** Steps of `check` that read nothing under game/ (traced file access, 13 Nov 2026) and take
 * 5 s or more. verify:game leaves these out; a step that is new or not listed here stays in. */
const APP_ONLY = [
  'typescript',
  'lint',
  'check:core',
  'check:world-canvas',
  'check:world-walk',
  'check:world',
  'check:clusters',
  'check:world-audit',
  'check:check-speed',
];
/** Paths a stream does not change unless its brief says so (`--allow=<path>` names the exception). */
const PROTECTED = [
  '.github/',
  'game/world/loop_fx.gd',
  'game/world/door.gd',
  'game/export_presets.cfg',
  'game/actors/player.gd',
];
/** The hosted workflow whose path filter decides whether a local check is needed for a diff. */
const WORKFLOWS = {
  verify: 'verify.yml',
  godot: 'godot.yml',
  playtest: 'mygame-godot-playtest.yml',
  art: 'art-reproducibility.yml',
};
/** Inputs of check:art-repro under game/ that the hosted filter does not list (scripts/art/sun.py). */
const ART_GAME_INPUTS = ['game/data/sun.json'];
const SOURCE = /\.(ts|tsx|js|jsx|cjs|mjs)$/;

function globToRegExp(glob) {
  const body = glob
    .split(/(\*\*\/|\*\*|\*|\?)/)
    .map((part) => {
      if (part === '**/') return '(?:.*/)?';
      if (part === '**') return '.*';
      if (part === '*') return '[^/]*';
      if (part === '?') return '[^/]';
      return part.replace(/[.+^${}()|[\]\\]/g, '\\$&');
    })
    .join('');
  return new RegExp(`^${body}$`);
}
/** The `paths` and `paths-ignore` lists of a workflow's pull_request trigger. */
function workflowPaths(text) {
  const got = { paths: null, ignore: null };
  let inside = false,
    key = null;
  for (const line of text.split('\n')) {
    if (/^ {2}pull_request:\s*$/.test(line)) inside = true;
    else if (/^ {0,2}\S/.test(line)) inside = false;
    else if (inside) {
      const list = /^ {4}(paths|paths-ignore):\s*$/.exec(line);
      const item = /^ {6}- ['"]?(.+?)['"]?\s*$/.exec(line);
      if (list) got[(key = list[1] === 'paths' ? 'paths' : 'ignore')] = [];
      else if (/^ {4}\S/.test(line)) key = null;
      else if (key && item) got[key].push(item[1]);
    }
  }
  return got;
}
/** Would this workflow run on a ready pull request with these changed paths? Unreadable or
 * unusual filters count as yes, so a parsing gap can add a check and never drop one. */
function hostedRuns(text, changed) {
  if (typeof text !== 'string') return true;
  const { paths, ignore } = workflowPaths(text);
  const all = [...(paths || []), ...(ignore || [])];
  if ((paths && ignore) || all.some((glob) => glob.startsWith('!'))) return true;
  const matches = (globs) => (file) => globs.some((glob) => globToRegExp(glob).test(file));
  if (paths) return paths.length === 0 || changed.some(matches(paths));
  if (ignore) return !changed.every(matches(ignore));
  return true;
}
/** Only the Godot game and prose changed: nothing the app's type check, lint or bundles read. */
function gameOnly(changed) {
  return (
    changed.length > 0 &&
    changed.every(
      (file) => file.endsWith('.md') || (/^(game|docs)\//.test(file) && !SOURCE.test(file)),
    )
  );
}
function gameSubset(checkScript) {
  const steps = checkCommands(checkScript);
  const stale = APP_ONLY.filter((label) => !steps.some((step) => step.label === label));
  if (stale.length)
    throw new Error(`APP_ONLY names steps that check no longer has: ${stale.join(', ')}`);
  return steps.filter((step) => !APP_ONLY.includes(step.label));
}
function touchedProtected(changed, allow = []) {
  return changed.filter(
    (file) =>
      PROTECTED.some((guard) => (guard.endsWith('/') ? file.startsWith(guard) : file === guard)) &&
      !allow.includes(file),
  );
}

/** The ordered steps for a diff. `workflows` maps WORKFLOWS keys to the workflow files' text.
 * `routes` is [{ name, files }]: a route and the files it is made of (its text, its save). */
function plan({ changed, routes = [], mode = 'inner', workflows = {}, repeat = 3, extra = [] }) {
  const final = mode === 'final';
  const steps = [{ id: 'protected-paths', kind: 'protected' }];
  const npm = (id) => steps.push({ id, command: 'npm', args: ['run', id] });
  if (mode !== 'routes') {
    if (hostedRuns(workflows.godot, changed)) npm('check:godot');
    if (final) npm('verify');
    else if (hostedRuns(workflows.verify, changed))
      npm(gameOnly(changed) ? 'verify:game' : 'verify');
    const art = changed.some((file) => ART_GAME_INPUTS.includes(file));
    if (final || art || hostedRuns(workflows.art, changed)) npm('check:art-repro');
  }
  const play = mode === 'routes' || hostedRuns(workflows.playtest, changed);
  for (const route of play ? routes : []) {
    const edited = extra.includes(route.name) || route.files.some((file) => changed.includes(file));
    // a new or changed route passes `repeat` times in a row; at the final head every route plays once
    const times = edited ? repeat : final ? 1 : 0;
    for (let run = 1; run <= times; run++)
      steps.push({
        id: `route:${route.name}#${run}`,
        kind: 'route',
        route: route.name,
        command: 'bash',
        args: ['game/tools/playtest.sh', `game/tools/routes/${route.name}.txt`],
      });
  }
  return steps;
}

function readRecords(file) {
  let text = '';
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch {
    return [];
  }
  const records = [];
  for (const line of text.split('\n')) {
    try {
      if (line.trim()) records.push(JSON.parse(line));
    } catch {
      /* a line cut off by a restart: that step has no result and runs again */
    }
  }
  return records;
}
/** Run the plan. A step counts as passed on this tree only through a finished record with exit 0
 * made by the same command and toolchain; started-but-unfinished and failed steps run again. */
async function runChain({
  steps,
  tree,
  head,
  how,
  resultsFile,
  execute,
  changed = [],
  allow = [],
  fresh = false,
  keepGoing = false,
  budget = Infinity,
  treeNow = () => tree,
  now = () => Date.now(),
  log = console.log,
}) {
  fs.mkdirSync(path.dirname(resultsFile), { recursive: true });
  const write = (record) => {
    // a line cut off by a restart must not swallow the record that follows it
    const cut = fs.existsSync(resultsFile) && !fs.readFileSync(resultsFile, 'utf8').endsWith('\n');
    fs.appendFileSync(resultsFile, `${cut ? '\n' : ''}${JSON.stringify(record)}\n`);
  };
  const began = now();
  const rows = [];
  let stopped = false;
  for (const step of steps) {
    if (step.kind === 'protected') {
      const touched = touchedProtected(changed, allow);
      rows.push({ id: step.id, state: touched.length ? 'FAIL' : 'PASS', note: touched.join(', ') });
      if (touched.length && !keepGoing) stopped = true;
      continue;
    }
    const same = (r) => r.id === step.id && r.tree === tree && r.how === how;
    const passed = fresh
      ? null
      : readRecords(resultsFile).findLast((r) => same(r) && r.state === 'done' && r.exit === 0);
    if (passed) {
      rows.push({ ...passed, state: 'PASS', note: `reused, finished ${passed.finished}` });
      continue;
    }
    if (stopped || (now() - began) / 1000 > budget) {
      rows.push({ id: step.id, state: 'NOT RUN', note: stopped ? 'after a failure' : 'budget' });
      continue;
    }
    const started = new Date(now()).toISOString();
    write({ id: step.id, tree, head, how, state: 'started', started });
    log(`[stream-checks] start ${step.id}`);
    const got = await execute(step);
    // an edit while a step ran: its result belongs to no tree, and neither would the next one's
    const moved = treeNow() !== tree;
    const record = {
      id: step.id,
      tree,
      head,
      how,
      state: moved ? 'moved' : 'done',
      exit: got.exit,
      seconds: got.seconds,
      waited: got.waited,
      started,
      finished: new Date(now()).toISOString(),
      log: got.log,
    };
    write(record);
    const ok = got.exit === 0 && !moved;
    const note = moved ? 'the working tree changed during the step: run again' : `exit ${got.exit}`;
    log(
      `[stream-checks] ${ok ? 'PASS' : 'FAIL'} ${step.id} (${got.seconds}s, waited ${got.waited}s)`,
    );
    rows.push({ ...record, state: ok ? 'PASS' : 'FAIL', note: ok ? 'ran' : note });
    if (moved || (!ok && !keepGoing)) stopped = true;
  }
  const count = (state) => rows.filter((row) => row.state === state).length;
  for (const row of rows)
    log(
      `${row.state.padEnd(7)} ${row.id.padEnd(28)} ${(row.seconds === undefined ? '' : `${row.seconds}s`).padStart(6)}  ${row.note || ''}${row.log && row.state === 'FAIL' ? `  ${row.log}` : ''}`,
    );
  const reused = rows.filter((row) => row.note?.startsWith('reused')).length;
  log(
    `stream-checks: tree ${tree} head ${head}: ${count('PASS')} passed (${reused} reused), ${count('FAIL')} failed, ${count('NOT RUN')} not run`,
  );
  return { ok: count('PASS') === rows.length, complete: count('NOT RUN') === 0, rows };
}

function git(root, args, env = process.env) {
  const got = spawnSync('git', args, { cwd: root, env, encoding: 'utf8' });
  if (got.status !== 0 || got.error)
    throw new Error(`git ${args[0]} failed: ${got.error?.message ?? got.stderr}`);
  return got.stdout.trim();
}
/** The tree of the working files as they are now: committed, edited and new (not ignored). */
function treeHash(root) {
  const index = path.join(os.tmpdir(), `stream-checks-index-${process.pid}`);
  const env = { ...process.env, GIT_INDEX_FILE: index };
  try {
    // start from the real index when there is one: its stat cache spares hashing every file again
    try {
      fs.copyFileSync(path.resolve(root, git(root, ['rev-parse', '--git-path', 'index'])), index);
    } catch {
      git(root, ['read-tree', 'HEAD'], env);
    }
    git(root, ['add', '--all'], env);
    return git(root, ['write-tree'], env);
  } finally {
    fs.rmSync(index, { force: true });
  }
}
const lines = (text) => text.split('\n').filter(Boolean);
function changedPaths(root, base) {
  const from = git(root, ['merge-base', base, 'HEAD']);
  return [
    ...new Set([
      ...lines(git(root, ['diff', '--name-only', from])),
      ...lines(git(root, ['ls-files', '--others', '--exclude-standard'])),
    ]),
  ]
    .filter((file) => file !== 'node_modules') // a worktree's link to the shared install
    .sort((a, b) => a.localeCompare(b));
}
function listRoutes(root) {
  const folder = path.join(root, 'game', 'tools', 'routes');
  return fs
    .readdirSync(folder)
    .filter((name) => name.endsWith('.txt'))
    .sort((a, b) => a.localeCompare(b))
    .map((file) => {
      const save = /^#! save: *(\S+)/m.exec(fs.readFileSync(path.join(folder, file), 'utf8'));
      const files = [file, ...(save ? [save[1]] : [])].map((name) => `game/tools/routes/${name}`);
      return { name: file.slice(0, -4), files };
    });
}
/** Start one step: under STREAM_LOCK when it is set (the wait is timed apart from the run), with
 * its output in its own log, and for a route on a display of its own that playtest.sh starts and
 * stops (a shared Xvfb outlives nothing: it is one more thing a restart or a time limit takes). */
function executeStep(root, folder, tree) {
  return (step) =>
    new Promise((resolve) => {
      const name = step.id.replace(/[^a-z0-9_-]+/gi, '-');
      const logFile = path.join(folder, tree.slice(0, 12), `${name}.log`);
      const stamp = `${logFile}.began`;
      fs.mkdirSync(path.dirname(logFile), { recursive: true });
      fs.rmSync(stamp, { force: true });
      const env = { ...process.env };
      let setup = 'date +%s > "$STAMP"; ';
      if (step.kind === 'route') {
        env.PLAYTEST_OUT = path.join(folder, tree.slice(0, 12), name);
        if (!env.STREAM_KEEP_DISPLAY)
          setup +=
            'unset DISPLAY; n=140; while [ -e /tmp/.X$n-lock ]; do n=$((n+1)); done; export PLAYTEST_DISPLAY=:$n; ';
      }
      const inner = [
        'bash',
        '-c',
        `${setup}exec "$@"`,
        'stream-checks',
        step.command,
        ...step.args,
      ];
      const lock = process.env.STREAM_LOCK;
      const [command, ...args] = lock ? ['flock', lock, ...inner] : inner;
      const out = fs.openSync(logFile, 'w');
      const asked = Date.now();
      const child = spawn(command, args, {
        cwd: root,
        env: { ...env, STAMP: stamp },
        stdio: ['ignore', out, out],
      });
      const done = (exit) => {
        fs.closeSync(out);
        const end = Date.now() / 1000;
        let began = end; // stays so when the step was stopped while it still waited for the lock
        try {
          began = Number(fs.readFileSync(stamp, 'utf8'));
          fs.rmSync(stamp, { force: true });
        } catch {
          /* the step never started */
        }
        resolve({
          exit,
          seconds: Math.round(end - began),
          waited: Math.max(0, Math.round(began - asked / 1000)),
          log: logFile,
        });
      };
      child.on('error', () => done(127));
      child.on('close', (status, signal) => done(signal ? 128 : status));
    });
}

/** `npm run verify:game`: the steps of `check` that can see a change under game/, in the same
 * runner format as verify. It refuses any other diff, where only the full `npm run verify` counts. */
async function verifyGame({ root, changed, run = runProcess, log = console.log }) {
  if (!gameOnly(changed)) {
    log('verify:game: this diff changes more than game/, docs/ and *.md. Run `npm run verify`.');
    return { ok: false, refused: true };
  }
  const scripts = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')).scripts;
  const steps = gameSubset(scripts.check);
  const env = {
    ...process.env,
    PATH: `${path.join(root, 'node_modules', '.bin')}${path.delimiter}${process.env.PATH}`,
  };
  const settled = await mapLimit(steps, concurrency(process.env.VERIFY_JOBS), async (step) => {
    const start = performance.now();
    const got = await run(step.command, step.args, { cwd: root, env, timeout: 900_000 });
    const ok = !got.error && !got.signal && got.status === 0;
    if (!ok) log(`[${step.label}]\n${got.stdout || ''}${got.stderr || ''}`.trimEnd());
    log(
      `[verify:game] ${ok ? 'PASS' : 'FAIL'} ${step.label} (${((performance.now() - start) / 1000).toFixed(2)}s)`,
    );
    return ok;
  });
  const failed = steps.filter((_, index) => settled[index].value !== true).map((s) => s.label);
  log(
    failed.length
      ? `[verify:game] failed: ${failed.join(', ')}`
      : `[verify:game] ${steps.length} steps passed; ${APP_ONLY.length} app-only steps and the two exports are left to \`npm run verify\` on the final head`,
  );
  return { ok: failed.length === 0, refused: false };
}

async function main(argv) {
  const root = path.resolve(__dirname, '..');
  const flags = argv.filter((arg) => arg.startsWith('--'));
  const words = argv.filter((arg) => !arg.startsWith('--'));
  const value = (name, fallback) =>
    flags.find((flag) => flag.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
  const known = /^--(final|plan|fresh|keep-going|(base|budget|repeat|allow)=.+)$/;
  const mode = words[0] === 'routes' ? 'routes' : flags.includes('--final') ? 'final' : 'inner';
  if (
    flags.some((flag) => !known.test(flag)) ||
    (words.length && !['routes', 'verify-game'].includes(words[0]))
  ) {
    console.error(
      'Usage: stream-checks.cjs [--final] [--plan] [--fresh] [--keep-going] [--budget=<s>] [--base=<ref>] [--allow=<path>]\n' +
        '       stream-checks.cjs routes <name>... [--repeat=<n>]\n       stream-checks.cjs verify-game',
    );
    return 2;
  }
  const hosted = (file) => {
    try {
      return fs.readFileSync(path.join(root, '.github', 'workflows', file), 'utf8');
    } catch {
      return undefined; // no readable filter: hostedRuns answers yes
    }
  };
  // `verify` fails on another Node major (tsx loader): say so now, not after twelve minutes
  const wanted = /node-version: *'?(\d+)/.exec(hosted(WORKFLOWS.verify) || '')?.[1];
  const here = process.versions.node.split('.')[0];
  if (wanted && wanted !== here) {
    console.error(
      `stream-checks: Node ${here} here, hosted Verify runs Node ${wanted}. Put it first on PATH.`,
    );
    return 2;
  }
  const changed = changedPaths(root, value('base', 'origin/main'));
  if (words[0] === 'verify-game') {
    const got = await verifyGame({ root, changed });
    return got.refused ? 2 : got.ok ? 0 : 1;
  }
  const workflows = {};
  for (const [key, file] of Object.entries(WORKFLOWS)) workflows[key] = hosted(file);
  const routes = listRoutes(root);
  const extra = words.slice(1);
  const missing = extra.filter((name) => !routes.some((route) => route.name === name));
  if (missing.length || (mode === 'routes' && !extra.length)) {
    console.error(
      `stream-checks: name routes from game/tools/routes (unknown: ${missing.join(', ')})`,
    );
    return 2;
  }
  const steps = plan({
    changed,
    routes,
    mode,
    workflows,
    repeat: Number(value('repeat', 3)),
    extra,
  });
  if (flags.includes('--plan')) {
    console.log(`${changed.length} changed paths; ${mode} plan:`);
    for (const step of steps) console.log(`  ${step.id}`);
    return 0;
  }
  const folder = path.join(root, '.cache', 'stream-checks');
  const tree = treeHash(root);
  const result = await runChain({
    steps,
    tree,
    head: git(root, ['rev-parse', 'HEAD']),
    how: `node ${process.versions.node.split('.')[0]}; GODOT=${process.env.GODOT || ''}`,
    resultsFile: path.join(folder, 'results.jsonl'),
    execute: executeStep(root, folder, tree),
    treeNow: () => treeHash(root),
    changed,
    allow: flags.filter((flag) => flag.startsWith('--allow=')).map((flag) => flag.slice(8)),
    fresh: flags.includes('--fresh'),
    keepGoing: flags.includes('--keep-going'),
    budget: Number(value('budget', Infinity)),
  });
  if (result.rows.some((row) => row.state === 'FAIL')) return 1;
  return result.complete ? 0 : 3;
}

module.exports = {
  APP_ONLY,
  PROTECTED,
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
};
if (require.main === module)
  main(process.argv.slice(2))
    .then((code) => {
      process.exitCode = code;
    })
    .catch((error) => {
      console.error(error);
      process.exitCode = 1;
    });
