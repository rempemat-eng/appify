const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { PNG } = require('pngjs');
const { inventory, pngSize, category, markdown } = require('./check-images.cjs');

let checks = 0;
function eq(actual, expected) {
  assert.deepEqual(actual, expected);
  checks++;
}
function throws(fn, pattern) {
  assert.throws(fn, pattern);
  checks++;
}
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'napattack-images-test-'));
function write(file, data) {
  const full = path.join(root, file);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, data);
  return full;
}
function png(file, width, height) {
  return write(file, PNG.sync.write(new PNG({ width, height })));
}
const run = () => inventory(root, { surfaces: {} });
try {
  const ground = png('assets/garden/ground.png', 10, 20);
  png('assets/garden/water-0.png', 3, 2);
  png('assets/worlds/park/ground.png', 7, 4);
  png('assets/battle/platform.png', 2, 2);
  png('assets/scenes/unused.png', 100, 100);
  png('assets/other.png', 1, 1);
  eq(pngSize(ground), { width: 10, height: 20, decodedBytes: 800 });
  const cases = {
    'assets/garden/ground.png': 'Garden / ground',
    'assets/garden/ground-top.png': 'Garden / ground',
    'assets/garden/water-stream-0.png': 'Garden / water frames',
    'assets/garden/light-lantern-pool.png': 'Garden / night lights',
    'assets/garden/growth/plot.png': 'Garden / growth sprites',
    'assets/garden/tree.png': 'Garden / prop sprites',
    'assets/worlds/park/ground.png': 'Worlds / park',
    'assets/worlds/props/tree.png': 'Worlds / shared prop sprites',
    'assets/battle/far-night.png': 'Battle',
    'assets/scenes/park.png': 'Scene vignettes',
    'assets/pets/bob.png': 'Character sprites',
    'art/icons/nap.png': 'UI icons',
    'other/file.png': 'Other imported PNGs',
  };
  for (const [p, expected] of Object.entries(cases)) eq(category(p), expected);
  write('app/_layout.tsx', "import '@/lib/common';");
  write('app/(tabs)/_layout.tsx', "import '../../assets/garden/water-0.png';");
  write(
    'app/(tabs)/index.tsx',
    "import { value } from '@/lib/cycle'; import type { X } from '@/missing'; export type { Y } from '@/also-missing'; // import '@/assets/scenes/unused.png'\n const s = '@/assets/scenes/unused.png';",
  );
  write('app/journal.tsx', "export * from '../lib/platform';");
  write(
    'lib/common.ts',
    "import g from '@/assets/garden/ground.png'; export { default as duplicate } from '../assets/garden/ground.png';",
  );
  write(
    'lib/cycle.ts',
    "import './again'; const image = require('../assets/garden/ground.png'); export const value = image;",
  );
  write('lib/again.ts', "import './cycle'; import { type X } from './absent';");
  write('lib/platform.ts', 'export const value = 1;');
  write('lib/platform.web.ts', "const value = import('../assets/worlds/park/ground.png');");
  write('lib/platform.native.ts', "import image = require('../assets/battle/platform.png');");
  write('lib/old.test.ts', "require('../not-a-file.png');");
  write('lib/types.d.ts', "import '../not-a-file.png';");
  const report = run();
  eq(report.images.length, 4);
  eq(report.totalDecodedBytes, 800 + 24 + 112 + 16);
  eq(
    report.totalDiskBytes,
    report.images.reduce((n, image) => n + image.diskBytes, 0),
  );
  eq(report.images.find((i) => i.path.endsWith('garden/ground.png')).importedBy, [
    'lib/common.ts',
    'lib/cycle.ts',
  ]);
  eq(report.screens.length, 2);
  const home = report.screens.find((s) => s.name.includes('(tabs)/index'));
  const journal = report.screens.find((s) => s.name.endsWith('journal.tsx'));
  eq(home.count, 2);
  eq(home.decodedBytes, 824);
  eq(
    home.diskBytes,
    home.paths.reduce((n, p) => n + report.images.find((i) => i.path === p).diskBytes, 0),
  );
  eq(home.roots, ['app/(tabs)/index.tsx', 'app/(tabs)/_layout.tsx', 'app/_layout.tsx']);
  eq(journal.count, 3);
  eq(journal.decodedBytes, 928);
  eq(
    home.groups.reduce((n, g) => n + g.decodedBytes, 0),
    home.decodedBytes,
  );
  eq(
    report.groups.reduce((n, g) => n + g.decodedBytes, 0),
    report.totalDecodedBytes,
  );
  eq(
    report.groups.reduce((n, g) => n + g.diskBytes, 0),
    report.totalDiskBytes,
  );
  eq(
    report.firstLoad.map((entry) => entry.name),
    ['Hub'],
  );
  eq(report.firstLoad[0].diskBytes, home.diskBytes);
  eq(
    report.firstLoad[0].largest.map((image) => image.diskBytes),
    report.firstLoad[0].largest
      .map((image) => image.diskBytes)
      .slice()
      .sort((a, b) => b - a),
  );
  throws(() => inventory(root, { surfaces: {}, firstLoadBudget: 1 }), /First-load PNG budget.*Hub/);
  eq(run(), report); // stable ordering
  const text = markdown(report);
  eq(text.includes('width × height × 4'), true);
  eq(text.includes('not measured resident/GPU memory'), true);
  eq(text.includes('| assets/garden/ground.png | 10 × 20 |'), true);
  eq(text.includes('7–9 MB within 4 s'), true);
  eq(text.includes('ten largest statically reachable PNGs'), true);
  eq(text.includes('unique.png'), false);
  const onlyType = write(
    'lib/type-only.ts',
    "export { type Missing } from './absent'; import type Alias = require('./absent');",
  );
  eq(run().totalDecodedBytes, report.totalDecodedBytes);
  fs.unlinkSync(onlyType);
  const orphan = write('lib/orphan.ts', "import '../assets/other.png';");
  eq(run().images.length, 5); // inventory retains imports even when a route doesn't reach them
  eq(run().screens[0].count, 2);
  fs.unlinkSync(orphan);
  write('lib/side-effect.ts', "import {} from './side-directory';");
  write('lib/side-directory/index.ts', "export {} from '../../assets/other.png';");
  write('app/side.tsx', "import '../lib/side-effect';");
  eq(run().screens.find((s) => s.name === 'app/side.tsx').decodedBytes, 804);
  fs.unlinkSync(path.join(root, 'app/side.tsx'));
  fs.unlinkSync(path.join(root, 'lib/side-effect.ts'));
  fs.unlinkSync(path.join(root, 'lib/side-directory/index.ts'));
  fs.symlinkSync(ground, path.join(root, 'assets/link.png'));
  write('lib/link.ts', "import '../assets/link.png';");
  throws(run, /Missing\/non-file PNG/);
  fs.unlinkSync(path.join(root, 'lib/link.ts'));
  fs.unlinkSync(path.join(root, 'assets/link.png'));
  const bad = write('lib/bad.ts', "import '../assets/missing.png';");
  throws(run, /Missing\/non-file PNG/);
  fs.writeFileSync(bad, "require('../assets/' + kind + '.png');");
  throws(run, /Dynamic module path/);
  fs.writeFileSync(bad, "import image from '../../escape.png';");
  throws(run, /outside repository/);
  fs.writeFileSync(bad, "import { thing } from './not-there';");
  throws(run, /Unresolved local import/);
  fs.writeFileSync(bad, 'const = broken');
  throws(run, /Cannot parse/);
  fs.unlinkSync(bad);
  fs.symlinkSync(ground, path.join(root, 'lib/symlink.ts'));
  throws(run, /Symlink in app source/);
  fs.unlinkSync(path.join(root, 'lib/symlink.ts'));
  throws(
    () => inventory(root, { surfaces: { Missing: ['components/missing.tsx'] } }),
    /Missing report entry/,
  );
  const buffer = fs.readFileSync(ground);
  for (const bytes of [Buffer.from('bad'), Buffer.alloc(33), buffer.subarray(0, 30)]) {
    write('bad.png', bytes);
    throws(() => pngSize(path.join(root, 'bad.png')), /Invalid PNG header/);
  }
  const invalid = Buffer.from(buffer);
  invalid.writeUInt32BE(0, 16);
  write('bad.png', invalid);
  throws(() => pngSize(path.join(root, 'bad.png')), /dimensions/);
  invalid.writeUInt32BE(0x7fffffff, 16);
  invalid.writeUInt32BE(0x7fffffff, 20);
  write('bad.png', invalid);
  throws(() => pngSize(path.join(root, 'bad.png')), /dimensions/);

  // The real CLI's JSON agrees with the library, and publishes Markdown in a CI summary.
  const actual = inventory(path.resolve(__dirname, '..'));
  const summaryPath = path.join(root, 'summary.md');
  const cli = spawnSync(process.execPath, [path.join(__dirname, 'check-images.cjs'), '--json'], {
    encoding: 'utf8',
    env: { ...process.env, GITHUB_STEP_SUMMARY: summaryPath },
  });
  eq(cli.status, 0);
  eq(JSON.parse(cli.stdout), actual);
  eq(fs.readFileSync(summaryPath, 'utf8'), markdown(actual) + '\n');
  for (const image of actual.images) eq(image.decodedBytes, image.width * image.height * 4);
  for (const screen of actual.screens) {
    eq(new Set(screen.paths).size, screen.count);
    eq(
      screen.groups.reduce((n, g) => n + g.decodedBytes, 0),
      screen.decodedBytes,
    );
    eq(
      screen.groups.reduce((n, g) => n + g.diskBytes, 0),
      screen.diskBytes,
    );
  }
  eq(
    actual.firstLoad.map((entry) => entry.name),
    ['Hub', 'World'],
  );
  const badCli = spawnSync(
    process.execPath,
    [path.join(__dirname, 'check-images.cjs'), '--unknown'],
    { encoding: 'utf8' },
  );
  eq(badCli.status, 1);
  eq(badCli.stderr.includes('Usage:'), true);
  console.log(
    `PASS ${checks} image-memory report assertions (fixture graph + real inventory + CI summary).`,
  );
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
