/** A stream's resumable check chain (docs/stream-checks.md).
 * Additions only: every command it starts is an existing, unchanged check. It records each exit
 * against the exact tree, and on the same tree it does not rerun what already passed, so a
 * restarted container or a resumed agent loses one step at most. `--final` is the whole chain
 * for the head that is marked ready; the default is the inner loop for the paths that changed. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
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
/** Inputs and compared outputs of check:art-repro that the hosted Art filter does not list, so the
 * local choice is stricter than the hosted one: scripts/art/sun.py reads game/data/sun.json;
 * world_routes.py and regions/tidebloom_plan.py read the block-out and world_routes.py writes
 * route-meets.md; cliff_core.py writes docs/vision/cliff-core/; icons.py writes the icon sheets. */
const ART_DOCS_INPUTS = [
  'docs/vision/research/blockout/**',
  'docs/vision/regions/route-meets.md',
  'docs/vision/cliff-core/**',
  'docs/vision/icon-sheet*.png',
];
const ART_EXTRA_INPUTS = ['game/data/sun.json', ...ART_DOCS_INPUTS];
/** Files under docs/ that steps of `check` open (hosted Verify ignores docs/): the ledger and audit
 * pages of scripts/art/world_audit.py, asset_ledger.py and kit/placement_audit.py, and the brief
 * that regions/sunstone_plan.py parses. A change to one asks for the full `verify`. */
const VERIFY_DOCS_INPUTS = [
  'docs/vision/asset-ledger.md',
  'docs/vision/prop-logic.md',
  'docs/vision/placement-audit.md',
  'docs/vision/regions/sunstone-basin-fire-country.md',
];
/** Files outside game/ that check:godot's tests pin or run (game/test/test_terrain.gd,
 * test_kit_rules.gd, test_weapon_lines.gd); the hosted Godot filter lists none of them. */
const GODOT_OUTSIDE_INPUTS = [
  'scripts/art/**',
  'scripts/review/**',
  'scripts/progression/**',
  'art/**',
];
/** Steps that compare generated PNG bytes with committed ones (check:kit and check:review are
 * inside verify and verify:game). They need the PNG encoder hosted CI has. */
const ART_BYTE_STEPS = ['verify', 'verify:game', 'check:art-repro'];
/** The opt-in fast playtest: fixed 60 steps a second and no render loop. Never a counted run. */
const FAST_ARGS = ['--fixed-fps', '60', '--disable-render-loop'];
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
const matchesAny = (globs) => (file) => globs.some((glob) => globToRegExp(glob).test(file));
/** Only the Godot game and prose changed: nothing the app's type check, lint or bundles read,
 * and none of the files under docs/ that a generator or a step of `check` opens. */
function gameOnly(changed) {
  return (
    changed.length > 0 &&
    !changed.some(matchesAny([...ART_DOCS_INPUTS, ...VERIFY_DOCS_INPUTS])) &&
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
 * `routes` is [{ name, files }]: a route and the files it is made of (its text, its save).
 * `fast` (routes mode only) plays each named route once in fixed step, under an id of its own. */
function plan({
  changed,
  routes = [],
  mode = 'inner',
  workflows = {},
  repeat = 3,
  extra = [],
  base,
  fast = false,
}) {
  const final = mode === 'final';
  const steps = [{ id: 'protected-paths', kind: 'protected' }];
  const npm = (id, args = []) =>
    steps.push({ id, command: 'npm', args: ['run', id, ...(args.length ? ['--', ...args] : [])] });
  if (mode !== 'routes') {
    // the final head always passes check:godot; before that, whenever a file its tests read changed
    if (
      final ||
      hostedRuns(workflows.godot, changed) ||
      changed.some(matchesAny(GODOT_OUTSIDE_INPUTS))
    )
      npm('check:godot');
    const artInput = changed.some(matchesAny(ART_EXTRA_INPUTS));
    const checkInput = artInput || changed.some(matchesAny(VERIFY_DOCS_INPUTS));
    if (final) npm('verify');
    else if (checkInput || hostedRuns(workflows.verify, changed)) {
      if (gameOnly(changed)) npm('verify:game', base ? [`--base=${base}`] : []);
      else npm('verify');
    }
    if (final || artInput || hostedRuns(workflows.art, changed)) npm('check:art-repro');
  }
  const play = mode === 'routes' || hostedRuns(workflows.playtest, changed);
  const quick = fast && mode === 'routes';
  for (const route of play ? routes : []) {
    const edited = extra.includes(route.name) || route.files.some((file) => changed.includes(file));
    // a new or changed route passes `repeat` times in a row; at the final head every route plays once
    const times = quick ? (edited ? 1 : 0) : edited ? repeat : final ? 1 : 0;
    const group = `${quick ? 'route-fast' : 'route'}:${route.name}`;
    for (let run = 1; run <= times; run++)
      steps.push({
        id: `${group}#${run}`,
        kind: 'route',
        group,
        route: route.name,
        ...(quick ? { fast: true } : {}),
        command: 'bash',
        args: ['game/tools/playtest.sh', `game/tools/routes/${route.name}.txt`],
      });
  }
  return steps;
}
/** What the head still owes after this plan: the steps of the final chain that are not in it. */
function leftToFinal(options) {
  if (options.mode === 'final') return [];
  const mine = new Set(plan(options).map((step) => step.id));
  const rest = plan({ ...options, mode: 'final', fast: false, extra: [] }).filter(
    (step) => !mine.has(step.id),
  );
  const names = [...new Set(rest.filter((step) => step.kind === 'route').map((s) => s.route))];
  const left = rest.filter((step) => step.kind !== 'route').map((step) => step.id);
  if (mine.has('verify:game') && left.includes('verify'))
    left[left.indexOf('verify')] =
      `verify (verify:game left out ${APP_ONLY.length} app-only steps and the two exports)`;
  if (names.length) left.push(`routes ${names.join(', ')}`);
  return left;
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
const passedRecord = (record) => record.state === 'done' && record.exit === 0;
/** The record that lets a step be skipped on this tree and toolchain, or null. Only the NEWEST
 * finished record of the step counts, so a pass never outlives a later failure. For a route, a
 * failure of any of its runs voids every run before it: the passes that count come after the last
 * failure, so three of three cannot be collected over retries. */
function reusableRecord(records, step, tree, how) {
  const group = step.group ? `${step.group}#` : null;
  let newest = -1,
    lastFailure = -1;
  records.forEach((record, index) => {
    if (record.tree !== tree || record.how !== how || !record.state || record.state === 'started')
      return;
    const mine = record.id === step.id;
    if (mine) newest = index;
    if ((mine || (group && String(record.id).startsWith(group))) && !passedRecord(record))
      lastFailure = index;
  });
  return newest > lastFailure ? records[newest] : null;
}
/** Run the plan. A step counts as passed on this tree only through its newest finished record,
 * with exit 0, made by the same command and toolchain; started-but-unfinished and failed steps
 * run again, and earlier failures of the plan's steps on this tree are named in the summary. */
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
  mode = 'inner',
  left = [],
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
  const stepHow = (step) => (step.fast ? `${how}; fast ${FAST_ARGS.join(' ')}` : how);
  const began = now();
  const rows = [];
  // failures recorded on this tree before this start, with any toolchain: a later pass hides none
  const inPlan = (record) =>
    steps.some(
      (step) =>
        record.id === step.id || (step.group && String(record.id).startsWith(`${step.group}#`)),
    );
  const earlier = readRecords(resultsFile).filter(
    (record) =>
      record.tree === tree &&
      record.state &&
      record.state !== 'started' &&
      !passedRecord(record) &&
      inPlan(record),
  );
  let stopped = false;
  for (const step of steps) {
    if (step.kind === 'protected') {
      const touched = touchedProtected(changed, allow);
      rows.push({
        id: step.id,
        kind: step.kind,
        state: touched.length ? 'FAIL' : 'PASS',
        note: touched.join(', '),
      });
      if (touched.length && !keepGoing) stopped = true;
      continue;
    }
    const label = step.fast ? 'FAST ' : '';
    const passed = fresh
      ? null
      : reusableRecord(readRecords(resultsFile), step, tree, stepHow(step));
    if (passed) {
      rows.push({
        ...passed,
        fast: step.fast,
        state: 'PASS',
        note: `${label}reused, finished ${passed.finished}`,
      });
      continue;
    }
    if (stopped || (now() - began) / 1000 >= budget) {
      rows.push({ id: step.id, state: 'NOT RUN', note: stopped ? 'after a failure' : 'budget' });
      continue;
    }
    const started = new Date(now()).toISOString();
    write({ id: step.id, tree, head, how: stepHow(step), state: 'started', started });
    log(`[stream-checks] start ${step.id}`);
    const got = await execute(step);
    // an edit while a step ran: its result belongs to no tree, and neither would the next one's
    const moved = treeNow() !== tree;
    const record = {
      id: step.id,
      tree,
      head,
      how: stepHow(step),
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
      `[stream-checks] ${label}${ok ? 'PASS' : 'FAIL'} ${step.id} (${got.seconds}s, waited ${got.waited}s)`,
    );
    rows.push({
      ...record,
      fast: step.fast,
      state: ok ? 'PASS' : 'FAIL',
      note: `${label}${ok ? 'ran' : note}`,
    });
    if (moved || (!ok && !keepGoing)) stopped = true;
  }
  // the path comparison is listed but is not a check: only a failed one enters the counts
  const count = (state) =>
    rows.filter((row) => row.state === state && (row.kind !== 'protected' || state === 'FAIL'))
      .length;
  for (const row of rows)
    log(
      `${row.state.padEnd(7)} ${row.id.padEnd(28)} ${(row.seconds === undefined ? '' : `${row.seconds}s`).padStart(6)}  ${row.note || ''}${row.log && row.state === 'FAIL' ? `  ${row.log}` : ''}`,
    );
  for (const record of earlier)
    log(
      `EARLIER ${String(record.id).padEnd(28)} failed on this tree (${record.state === 'moved' ? 'the tree changed during the step' : `exit ${record.exit}`}, finished ${record.finished})${record.log ? `  ${record.log}` : ''}`,
    );
  const reused = rows.filter((row) => /^(FAST )?reused/.test(row.note || '')).length;
  const fastRows = rows.filter((row) => row.fast).length;
  const nothing = rows.every((row) => row.kind === 'protected');
  if (nothing && count('FAIL') === 0)
    log(
      `stream-checks: ${mode} mode, tree ${tree} head ${head}: nothing selected for this diff, so no check ran (protected-paths is a path comparison, not a check)`,
    );
  else
    log(
      `stream-checks: ${mode} mode, tree ${tree} head ${head}: ${count('PASS')} passed (${reused} reused), ${count('FAIL')} failed, ${count('NOT RUN')} not run${earlier.length ? `, ${earlier.length} earlier failure${earlier.length === 1 ? '' : 's'} on this tree (listed above)` : ''}`,
    );
  if (fastRows)
    log(
      `stream-checks: ${fastRows} FAST route run${fastRows === 1 ? '' : 's'} (fixed step, no render loop): deterministic, so not one of the counted repeats, and no evidence for an audit`,
    );
  if (mode !== 'final')
    log(
      `stream-checks: this was not the final chain. Left to \`npm run stream:checks -- --final\`: ${left.length ? left.join('; ') : 'nothing that this plan did not already run'}`,
    );
  return {
    ok: rows.every((row) => row.state === 'PASS'),
    complete: count('NOT RUN') === 0,
    nothing,
    earlier,
    rows,
  };
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
      // --no-renames: a moved file is its old path removed and its new path added, and both count
      ...lines(git(root, ['diff', '--name-only', '--no-renames', from])),
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
      const text = fs.readFileSync(path.join(folder, file), 'utf8');
      return { name: file.slice(0, -4), files, shots: /^\s*shot\b/m.test(text) };
    });
}
/** Where a command name leads: a path as it is, a bare name through PATH. Null when nothing is there. */
function resolveBinary(name, env = process.env) {
  if (!name) return null;
  const candidates = name.includes(path.sep)
    ? [path.resolve(name)]
    : (env.PATH || '').split(path.delimiter).map((folder) => path.join(folder, name));
  for (const file of candidates) {
    try {
      fs.accessSync(file, fs.constants.X_OK);
      if (fs.statSync(file).isFile()) return file;
    } catch {
      /* not here */
    }
  }
  return null;
}
/** The Python that `python3` starts, with the packages the art checks draw and encode with. */
function probePython(run = spawnSync, command = 'python3') {
  const code = [
    'import sys, json',
    'out = {"python": sys.version.split()[0]}',
    'for key, name in (("pillow", "PIL"), ("numpy", "numpy"), ("scipy", "scipy")):',
    '    try: out[key] = __import__(name).__version__',
    '    except Exception: out[key] = None',
    'try:',
    '    from PIL import features',
    '    out["zlib"] = features.version("zlib")',
    'except Exception: out["zlib"] = None',
    'print(json.dumps(out))',
  ].join('\n');
  const got = run(command, ['-c', code], { encoding: 'utf8' });
  try {
    return JSON.parse(got.stdout);
  } catch {
    return { python: null, pillow: null, numpy: null, scipy: null, zlib: null };
  }
}
/** Every Python the checks start: `python3` (the npm scripts) and `$PYTHON` when it is set
 * (check:art-repro and three Godot tests use it in place of python3). */
function probePythons(env = process.env, probe = probePython) {
  const python = probe(spawnSync, 'python3');
  return env.PYTHON ? { python, envPython: probe(spawnSync, env.PYTHON) } : { python };
}
/** The first reason one of those Pythons cannot be trusted with PNG bytes, or null. */
function artBytesProblems({ python, envPython }) {
  const first = artBytesProblem(python);
  if (first || !envPython) return first;
  const second = artBytesProblem(envPython);
  return second && `PYTHON is set and check:art-repro starts it in place of python3: ${second}`;
}
/** A fast route's time limit in seconds. A failing step waits for a picture of the failure, and
 * no frame is drawn in fixed step, so it would otherwise sit under the lock for 900 s. */
const FAST_TIMEOUT = 180;
/** What a route step adds to its environment (the engine launcher of a fast step apart). */
function routeEnv(step, out) {
  return { PLAYTEST_OUT: out, ...(step.fast ? { PLAYTEST_TIMEOUT: String(FAST_TIMEOUT) } : {}) };
}
/** The Godot binary's bytes: the same path with another binary behind it is another toolchain. */
function probeGodot(name = process.env.GODOT || 'godot') {
  const file = resolveBinary(name);
  if (!file) return 'none';
  return `sha256:${crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')}`;
}
/** What a result was made with. A result is reused only when every part is the same. */
const part = (value) => value || 'none';
function toolchainKey({ node, python = {}, envPython, godot }) {
  return [
    `node ${part(node)}`,
    `python ${part(python.python)}`,
    `Pillow ${part(python.pillow)}`,
    `numpy ${part(python.numpy)}`,
    `scipy ${part(python.scipy)}`,
    `zlib ${part(python.zlib)}`,
    ...(envPython
      ? [
          `PYTHON ${part(envPython.python)} Pillow ${part(envPython.pillow)} numpy ${part(envPython.numpy)} scipy ${part(envPython.scipy)} zlib ${part(envPython.zlib)}`,
        ]
      : []),
    `godot ${part(godot)}`,
  ].join('; ');
}
/** Why PNG bytes written by this Python cannot be compared with the committed ones, or null.
 * Pillow links the machine's zlib; zlib-ng deflates the same pixels to other bytes, and then
 * `python3 -m scripts.art.kit.build --check` fails on an unchanged main. */
function artBytesProblem(python) {
  if (!python.pillow)
    return 'python3 has no Pillow, so the art and kit checks cannot run. Install the versions hosted Verify pins (docs/stream-checks.md, "The Python the art checks need").';
  if (!python.zlib || /zlib-ng/i.test(python.zlib))
    return `python3's Pillow ${python.pillow} writes PNGs with zlib ${python.zlib || '(unknown)'}, not the original zlib that hosted CI and the committed PNGs use. The same pixels come out as other bytes, so \`python3 -m scripts.art.kit.build --check\`, check:kit, check:review and check:art-repro would fail on an unchanged main. Put a python3 with the pinned wheels and the distribution's own libz first on PATH (docs/stream-checks.md, "The Python the art checks need").`;
  return null;
}
/** The package versions hosted Verify installs, read from its workflow (null when it has none). */
function hostedPins(text) {
  const pins = {};
  for (const [, name, version] of (text || '').matchAll(/'(Pillow|numpy|scipy)==([^']+)'/g))
    pins[name.toLowerCase()] = version;
  return Object.keys(pins).length ? pins : null;
}
/** A private copy of the engine with a launcher that adds the fixed-step arguments; playtest.sh
 * takes it as GODOT, so nothing under game/ changes for the fast mode. */
function fastEngine(folder) {
  const real = resolveBinary(process.env.GODOT || 'godot');
  if (!real) return null;
  fs.rmSync(folder, { recursive: true, force: true });
  fs.mkdirSync(folder, { recursive: true });
  const copy = path.join(folder, 'godot.bin');
  fs.copyFileSync(real, copy);
  fs.chmodSync(copy, 0o700);
  const launcher = path.join(folder, 'godot');
  fs.writeFileSync(launcher, `#!/bin/sh\nexec '${copy}' ${FAST_ARGS.join(' ')} "$@"\n`, {
    mode: 0o700,
  });
  return launcher;
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
        Object.assign(env, routeEnv(step, path.join(folder, tree.slice(0, 12), name)));
        if (step.fast) {
          const launcher = fastEngine(path.join(folder, tree.slice(0, 12), 'fast-engine'));
          if (launcher) env.GODOT = launcher; // without one playtest.sh reports the missing binary
        }
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
        if (step.fast)
          fs.rmSync(path.join(folder, tree.slice(0, 12), 'fast-engine'), {
            recursive: true,
            force: true,
          });
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

function usage(why) {
  console.error(
    (why ? `stream-checks: ${why}\n` : '') +
      'Usage: stream-checks.cjs [--final] [--plan] [--fresh] [--keep-going] [--budget=<s>] [--base=<ref>] [--allow=<path>]\n' +
      '       stream-checks.cjs routes <name>... [--repeat=<n> | --fast]\n       stream-checks.cjs verify-game [--base=<ref>]',
  );
  return 2;
}
async function main(argv) {
  const root = path.resolve(__dirname, '..');
  const flags = argv.filter((arg) => arg.startsWith('--'));
  const words = argv.filter((arg) => !arg.startsWith('--'));
  const value = (name, fallback) =>
    flags.find((flag) => flag.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
  const known = /^--(final|plan|fresh|keep-going|fast|(base|budget|repeat|allow)=.+)$/;
  const mode = words[0] === 'routes' ? 'routes' : flags.includes('--final') ? 'final' : 'inner';
  const fast = flags.includes('--fast');
  if (
    flags.some((flag) => !known.test(flag)) ||
    (words.length && !['routes', 'verify-game'].includes(words[0]))
  )
    return usage();
  // a count that is not a whole number of 1 or more would play nothing and still say "passed"
  if (!/^[1-9]\d*$/.test(value('repeat', '3')))
    return usage(`--repeat takes a whole number of 1 or more, not "${value('repeat')}"`);
  if (!/^\d+(\.\d+)?$/.test(value('budget', '0')))
    return usage(`--budget takes seconds, not "${value('budget')}"`);
  if (mode === 'routes' && flags.includes('--final'))
    return usage(
      '`routes` plays the named routes only and is never the final chain: leave --final out, or run `stream:checks -- --final` without `routes`',
    );
  if (fast && mode !== 'routes')
    return usage(
      '--fast is only for `playtest:repeat -- <route> --fast`; the inner loop and --final never play in fixed step',
    );
  if (fast && value('repeat') !== undefined)
    return usage(
      '--fast plays a route once: fixed-step runs are identical, so a repeat proves nothing. For the counted repeats leave --fast out',
    );
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
  const base = value('base');
  const changed = changedPaths(root, base ?? 'origin/main');
  let pythons = null;
  // art and kit checks compare PNG bytes: stop before minutes are spent on an encoder that differs
  const artReady = () => {
    pythons = probePythons();
    const problem = artBytesProblems(pythons);
    if (problem) {
      console.error(`stream-checks: ${problem}`);
      return false;
    }
    const pins = hostedPins(hosted(WORKFLOWS.verify));
    for (const [label, python] of Object.entries(pythons)) {
      const off = Object.entries(pins || {}).filter(([name, version]) => python[name] !== version);
      if (off.length)
        console.error(
          `stream-checks: warning: hosted Verify pins ${off.map(([name, version]) => `${name} ${version} (here ${String(python[name])})`).join(', ')} (${label === 'python' ? 'python3' : '$PYTHON'}); generated art can differ.`,
        );
    }
    return true;
  };
  if (words[0] === 'verify-game') {
    if (gameOnly(changed) && !artReady()) return 2;
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
  // `shot` waits for a drawn frame, and the fast mode draws none: such a route would hang
  const pictured = fast ? routes.filter((r) => extra.includes(r.name) && r.shots) : [];
  if (pictured.length) {
    console.error(
      `stream-checks: --fast cannot play a route that takes pictures (${pictured.map((r) => r.name).join(', ')}): pictures are not supported in fixed step. Play it without --fast.`,
    );
    return 2;
  }
  const options = { changed, routes, mode, workflows, repeat: Number(value('repeat', 3)), extra };
  const steps = plan({ ...options, base, fast });
  const left = leftToFinal({ ...options, base, fast });
  if (flags.includes('--plan')) {
    console.log(`${changed.length} changed paths; ${mode} plan:`);
    for (const step of steps) console.log(`  ${step.id}${step.fast ? '  (FAST)' : ''}`);
    if (steps.length === 1) console.log('  nothing selected for this diff: no check would run');
    if (mode !== 'final')
      console.log(`left to --final: ${left.length ? left.join('; ') : 'nothing more'}`);
    return 0;
  }
  if (steps.some((step) => ART_BYTE_STEPS.includes(step.id)) && !artReady()) return 2;
  const folder = path.join(root, '.cache', 'stream-checks');
  const tree = treeHash(root);
  const result = await runChain({
    steps,
    tree,
    head: git(root, ['rev-parse', 'HEAD']),
    how: toolchainKey({
      node: process.versions.node,
      ...(pythons ?? probePythons()),
      godot: probeGodot(),
    }),
    resultsFile: path.join(folder, 'results.jsonl'),
    execute: executeStep(root, folder, tree),
    treeNow: () => treeHash(root),
    changed,
    allow: flags.filter((flag) => flag.startsWith('--allow=')).map((flag) => flag.slice(8)),
    fresh: flags.includes('--fresh'),
    keepGoing: flags.includes('--keep-going'),
    budget: Number(value('budget', Infinity)),
    mode: fast ? 'routes (FAST)' : mode,
    left,
  });
  if (result.rows.some((row) => row.state === 'FAIL')) return 1;
  return result.complete ? 0 : 3;
}

module.exports = {
  APP_ONLY,
  PROTECTED,
  FAST_ARGS,
  ART_BYTE_STEPS,
  leftToFinal,
  reusableRecord,
  changedPaths,
  toolchainKey,
  probePython,
  artBytesProblem,
  artBytesProblems,
  probePythons,
  routeEnv,
  FAST_TIMEOUT,
  hostedPins,
  main,
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
