/** Regenerate tracked artwork in a disposable copy, never in the caller's tree. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

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
];
const splitPaths = (value) => value.split('\0').filter(Boolean);

function checkArtReproducibility({ root, run = spawnSync, log = console.log }) {
  const failures = [];
  const owned = fs.mkdtempSync(path.join(os.tmpdir(), 'napattack-art-repro-'));
  const snapshot = path.join(owned, 'repo');
  const previews = path.join(owned, 'previews');
  const dependencies = path.join(snapshot, 'node_modules');
  const gitEnv = { ...process.env };
  // Inherited Git context must not redirect the temporary add/diff operations
  // into a caller's index or object database.
  for (const key of [
    'GIT_DIR',
    'GIT_WORK_TREE',
    'GIT_INDEX_FILE',
    'GIT_OBJECT_DIRECTORY',
    'GIT_ALTERNATE_OBJECT_DIRECTORIES',
    'GIT_COMMON_DIR',
  ])
    delete gitEnv[key];
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
      // zones.py paints the scenery past the world too (scripts/art/scenery.py) and takes about
      // 6 min on a 2-core machine, longer when another build runs alongside: allow 15 min
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
    for (const name of generators) {
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
    log('[art-repro] check regenerated sprite outlines');
    command(process.execPath, ['scripts/check-sprites.cjs'], snapshot, 'check:sprites');
    for (const failure of failures) log(`FAIL: ${failure}`);
    if (!failures.length)
      log(
        `PASS: all ${generators.length} art generators reproduce committed bytes; sprite checks pass.`,
      );
    return { ok: failures.length === 0, failures, changed, untracked };
  } finally {
    // Only the fresh directory owned by this invocation; no user checkout edits.
    fs.rmSync(owned, { recursive: true, force: true });
  }
}

module.exports = { checkArtReproducibility, generators, generatedTypescript };
if (require.main === module) {
  try {
    const result = checkArtReproducibility({ root: path.resolve(__dirname, '..') });
    process.exitCode = result.ok ? 0 : 1;
  } catch (error) {
    console.error(error);
    process.exitCode = 1;
  }
}
