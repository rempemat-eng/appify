/** Regenerate tracked artwork in a disposable copy, never in the caller's tree. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync, fork } = require('node:child_process');
const { mapLimit, concurrency } = require('./check-runner.cjs');
const { hashFiles, trackedFiles, fingerprint } = require('./art-repro-cache.cjs');

const generators = [
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
  // the cliff core's demos and random-outline proofs (docs/vision/cliff-core/)
  'cliff_core',
  // the shared 2x kit's golden scenes (art/golden/, scripts/art/native/)
  'kit_golden',
];
const generatedTypescript = [
  'lib/garden-map.ts',
  'lib/garden-growth-assets.ts',
  'lib/garden-hut-assets.ts',
  'lib/pet-sprites.ts',
  'lib/world-maps.ts',
  'lib/world-assets.ts',
  'lib/scene-assets.ts',
  'lib/icon-art.ts',
  'lib/mission-map.ts',
  'lib/zone-maps.ts',
  'lib/zone-assets.ts',
  'lib/journey-assets.ts',
  'lib/rocket-sizes.ts',
  'lib/rocket-assets.ts',
  'lib/resident-sprites.ts',
  'lib/resident-assets.ts',
  'lib/decor-assets.ts',
  'lib/decor-sizes.ts',
  // the world canvas (scripts/art/world_canvas.py), written at the end of zones.py's run
  'lib/world-canvas.ts',
  'lib/world-canvas-assets.ts',
  // the routes between the regions (scripts/art/world_routes.py, lane G)
  'lib/world-routes.ts',
  // the land between, the edges and the beyond (scripts/art/world_land.py, lane G)
  'lib/world-land.ts',
];
const splitPaths = (value) => value.split('\0').filter(Boolean);

function checkArtReproducibility({
  root,
  run = spawnSync,
  log = console.log,
  selected = generators,
  sprites = true,
}) {
  const failures = [];
  const owned = fs.mkdtempSync(path.join(os.tmpdir(), 'napattack-art-repro-'));
  const snapshot = path.join(owned, 'repo');
  const previews = path.join(owned, 'previews');
  const dependencies = path.join(snapshot, 'node_modules');
  const gitEnv = { ...process.env };
  // Inherited Git context must not redirect the temporary add/diff operations
  // into a caller's index or object database.
  for (const key of Object.keys(gitEnv)) if (key.startsWith('GIT_')) delete gitEnv[key];
  const env = {
    ...gitEnv,
    PYTHONDONTWRITEBYTECODE: '1',
    npm_config_offline: 'true',
    GARDEN_PREVIEW: path.join(previews, 'garden.png'),
    BATTLE_PREVIEW: path.join(previews, 'battle.png'),
    WORLD_PREVIEW: previews,
    MAP_PREVIEW: path.join(previews, 'mission-map.png'),
    ZONE_PREVIEW: previews,
    JOURNEY_PREVIEW: previews,
  };
  function command(executable, args, cwd, label) {
    const result = run(executable, args, {
      cwd,
      env,
      encoding: 'utf8',
      maxBuffer: 8 * 1024 * 1024,
      // zones.py paints the scenery past the world (scripts/art/scenery.py, Cogsworth's since
      // 20 Oct) and then cuts the world canvas into world tiles (scripts/art/world_canvas.py):
      // about 6 min on a 2-core machine, longer when another build runs alongside: allow 15 min
      timeout: 900_000,
    });
    if (result.stdout) log(result.stdout.trimEnd());
    if (result.stderr) log(result.stderr.trimEnd());
    if (result.error || result.signal || result.status !== 0)
      failures.push(
        `${label}: ${result.error?.message ?? result.signal ?? `exit ${result.status}`}`,
      );
    return result;
  }
  function git(args, cwd) {
    // Git setup/inspection is real even in the generator-boundary tests.
    const result = spawnSync('git', args, { cwd, env: gitEnv, encoding: 'utf8' });
    if (result.error || result.status !== 0)
      throw new Error(`git ${args[0]} failed: ${result.error?.message ?? result.stderr}`);
    return result.stdout;
  }
  try {
    fs.mkdirSync(snapshot);
    fs.mkdirSync(previews);
    const tracked = splitPaths(git(['ls-files', '-z'], root));
    if (!tracked.length)
      throw new Error('No tracked source files; run inside the project checkout.');
    for (const file of tracked) {
      const source = path.join(root, file);
      if (!fs.lstatSync(source).isFile()) throw new Error(`Not a regular tracked file: ${file}`);
      const target = path.join(snapshot, file);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(source, target);
    }
    git(['init', '-q'], snapshot);
    // Snapshot current tracked bytes, including legitimate unstaged local work.
    // Do this before linking dependencies: never add node_modules to the index.
    git(['add', '--all', '--force'], snapshot);
    // Atlas generators invoke npx oxfmt themselves. Use the already-installed
    // toolchain, offline, without staging dependencies or downloading packages.
    fs.symlinkSync(path.join(root, 'node_modules'), dependencies, 'dir');
    for (const name of selected) {
      log(`[art-repro] ${name}.py`);
      command(process.env.PYTHON || 'python3', [`scripts/art/${name}.py`], snapshot, `${name}.py`);
    }
    log(`[art-repro] format all ${generatedTypescript.length} generated TypeScript modules`);
    command(
      path.join(root, 'node_modules', '.bin', 'oxfmt'),
      ['--write', ...generatedTypescript],
      snapshot,
      'generated TypeScript formatting',
    );
    const changed = splitPaths(git(['diff', '--name-only', '-z'], snapshot));
    const intactDependencies =
      fs.lstatSync(dependencies, { throwIfNoEntry: false })?.isSymbolicLink() &&
      fs.readlinkSync(dependencies) === path.join(root, 'node_modules');
    if (!intactDependencies) failures.push('Installed toolchain link was replaced or removed');
    const untracked = splitPaths(
      git(['ls-files', '--others', '--exclude-standard', '-z'], snapshot),
    ).filter((file) => file !== 'node_modules' || !intactDependencies);
    if (changed.length) failures.push(`Tracked output drift: ${changed.join(', ')}`);
    if (untracked.length) failures.push(`Uncommitted generated files: ${untracked.join(', ')}`);
    // Ignore only our intact dependency symlink above, never generated outputs
    // with a similar name or a replacement at that path.
    if (sprites) {
      log('[art-repro] check regenerated sprite outlines');
      command(process.execPath, ['scripts/check-sprites.cjs'], snapshot, 'check:sprites');
    }
    for (const failure of failures) log(`FAIL: ${failure}`);
    if (!failures.length)
      log(
        `PASS: ${selected.length} art generators reproduce committed bytes${sprites ? '; sprite checks pass' : ''}.`,
      );
    return {
      ok: failures.length === 0,
      failures,
      changed,
      untracked,
      outputDigest: hashFiles(
        snapshot,
        tracked.filter((file) => fs.existsSync(path.join(snapshot, file))),
      ),
    };
  } finally {
    // Only the fresh directory owned by this invocation; no user checkout edits.
    fs.rmSync(owned, { recursive: true, force: true });
  }
}

// Each group has its own copy and index: even a new/overlapping output cannot race.
// Keep garden before zones because canvas generation reads its ground and walk data.
// Derive singleton groups from the canonical manifest so newly integrated
// generators cannot be omitted by a second hard-coded scheduling list.
const generatorGroups = generators
  .filter((name) => !['zones', 'rocket'].includes(name))
  .map((name) =>
    name === 'garden' ? ['garden', 'zones'] : name === 'journey' ? ['journey', 'rocket'] : [name],
  );

function groupWorker(root, selected, sprites, log) {
  return new Promise((resolve, reject) => {
    const child = fork(__filename, ['--worker'], {
      stdio: ['ignore', 'ignore', 'pipe', 'ipc'],
      env: { ...process.env, ART_REPRO_WORK: JSON.stringify({ root, selected, sprites }) },
    });
    let result,
      error,
      stderr = '';
    child.stderr.on('data', (chunk) => {
      stderr += chunk;
    });
    child.on('message', (message) => {
      if (message.log !== undefined) log(message.log);
      if (message.result) result = message.result;
      if (message.error) error = new Error(message.error);
    });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (error) reject(error);
      else if (code !== 0 || !result) reject(new Error(`art worker exited ${code}: ${stderr}`));
      else resolve(result);
    });
  });
}
async function checkArtParallel({
  root,
  jobs = concurrency(process.env.ART_REPRO_JOBS),
  cold = false,
  serial = false,
  log = console.log,
  worker = groupWorker,
  tools,
  fingerprintInputs = fingerprint,
}) {
  if (serial) return checkArtReproducibility({ root, log }); // Original full, ordered reference.
  jobs = concurrency(jobs);
  // A forced cold run trusts/publishes no certificate and needs no tool-cache scan.
  const coldFingerprint = () => {
    const files = trackedFiles(root);
    return { source: hashFiles(root, files) };
  };
  let before;
  try {
    before = cold ? coldFingerprint() : fingerprintInputs({ root, tools });
  } catch (error) {
    // Unreadable tools must never certify a cache hit. Full regeneration still
    // validates every output and propagates generator/formatter/sprite failures.
    log(`[art-repro] cache unavailable: ${error.message}; using full cold regeneration`);
    cold = true;
    before = coldFingerprint();
  }
  const cacheDir = path.join(root, '.cache', 'art-repro');
  const cacheFile = cold ? null : path.join(cacheDir, `${before.key}.json`);
  let hit = false;
  if (!cold) {
    try {
      const cert = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
      hit = cert.schema === 1 && cert.key === before.key && cert.outputDigest === before.source;
    } catch {
      /* Missing or corrupt certificate: full regeneration. */
    }
  }
  log(`[art-repro] ${hit ? 'verified input/tool cache hit' : 'full regeneration'}; jobs=${jobs}`);
  const results = hit
    ? []
    : await mapLimit(generatorGroups, jobs, (selected) => worker(root, selected, false, log));
  // Formatting and sprite validation ALWAYS execute, including warm checks.
  const final = await worker(root, [], true, log);
  const failures = results
    .flatMap((result) =>
      result.status === 'fulfilled' ? result.value.failures : [String(result.reason)],
    )
    .concat(final.failures);
  const after = cold ? coldFingerprint() : fingerprintInputs({ root, tools });
  if (before.source !== after.source || before.key !== after.key)
    failures.push('Source or installed tools changed during check; rerun');
  const changed = [
    ...new Set(results.flatMap((r) => r.value?.changed || []).concat(final.changed)),
  ].sort((a, b) => a.localeCompare(b));
  const untracked = [
    ...new Set(results.flatMap((r) => r.value?.untracked || []).concat(final.untracked)),
  ].sort((a, b) => a.localeCompare(b));
  const ok = failures.length === 0;
  if (ok && !cold) {
    fs.mkdirSync(cacheDir, { recursive: true });
    const temp = `${cacheFile}.${process.pid}.tmp`;
    fs.writeFileSync(
      temp,
      JSON.stringify({ schema: 1, key: before.key, outputDigest: final.outputDigest }),
    );
    fs.renameSync(temp, cacheFile);
  } else if (!ok) {
    if (cacheFile) fs.rmSync(cacheFile, { force: true });
    for (const failure of failures) log(`FAIL: ${failure}`);
  }
  log(`${ok ? 'PASS' : 'FAIL'}: art reproducibility (${hit ? 'warm' : 'cold'}, ${jobs} jobs)`);
  return { ok, failures, changed, untracked, outputDigest: final.outputDigest, cacheHit: hit };
}
module.exports = {
  checkArtReproducibility,
  checkArtParallel,
  generators,
  generatedTypescript,
  generatorGroups,
};
if (require.main === module) {
  if (process.argv.includes('--worker')) {
    try {
      const result = checkArtReproducibility({
        ...JSON.parse(process.env.ART_REPRO_WORK),
        log: (message) => process.send({ log: message }),
      });
      process.send({ result }, () => process.disconnect());
    } catch (error) {
      process.send({ error: error.stack }, () => process.disconnect());
    }
  } else {
    const args = process.argv.slice(2);
    if (args.some((arg) => arg !== '--cold' && arg !== '--serial')) {
      console.error('Usage: node scripts/check-art-repro.cjs [--cold] [--serial]');
      process.exitCode = 1;
    } else
      checkArtParallel({
        root: path.resolve(__dirname, '..'),
        cold: args.includes('--cold') || process.env.CI === 'true',
        serial: args.includes('--serial'),
      })
        .then((result) => {
          process.exitCode = result.ok ? 0 : 1;
        })
        .catch((error) => {
          console.error(error);
          process.exitCode = 1;
        });
  }
}
