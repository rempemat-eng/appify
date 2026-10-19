'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const { inspectWorld, readWorld, settleFindings } = require('./check-world-logic.cjs');
let checks = 0;
const check = (value, message) => {
  checks++;
  assert.ok(value, message);
};
const eq = (a, b, message) => {
  checks++;
  assert.deepEqual(a, b, message);
};
const bad = (fn, message) => {
  checks++;
  assert.throws(fn, /World logic export:/, message);
};
const clone = (value) => JSON.parse(JSON.stringify(value));
const blank = (ch = '.') => Array(32).fill(ch.repeat(32));
function fixture() {
  return {
    ZONE: { width: 128, height: 128, cell: 4 },
    zoneIds: ['a', 'b'],
    zoneMaps: {
      a: { walk: blank(), objects: [], stands: { entry: [64, 64] } },
      b: { walk: blank(), objects: [], stands: { entry: [64, 64] } },
    },
    zoneTerrain: { a: blank(), b: blank() },
    zonePlacement: {},
    zoneOverhead: [],
    regionLayout: { test: { a: [-2, -3], b: [-1, -3] } },
    zonePorts: { 'a|b': { span: [0, 128], frame: 'open' } },
  };
}
const findings = (d) => inspectWorld(d).findings;
function put(d, id, x, y, ch) {
  const r = d.zoneTerrain[id][y];
  d.zoneTerrain[id][y] = r.slice(0, x) + ch + r.slice(x + 1);
}
function atFoot(d, id, ch) {
  d.zoneMaps[id].objects = [['obj', 'crate', 20, 20, 20, 20]];
  for (let y = 8; y < 10; y++) for (let x = 5; x < 10; x++) put(d, id, x, y, ch);
}
eq(findings(fixture()), [], 'plain adjacent fields need no frame or gate');
let d = fixture();
d.zonePorts['a|b'] = { span: null, frame: 'cliff' };
eq(findings(d), [], 'closed declared border does not fabricate a walking or rail edge');
d = fixture();
atFoot(d, 'a', '~');
eq(
  findings(d).map((f) => f.kind),
  ['ground-on-water'],
  'ground prop in water',
);
d = fixture();
atFoot(d, 'a', '!');
eq(
  findings(d).map((f) => f.kind),
  ['ground-on-lava'],
  'ground prop in lava',
);
d = fixture();
atFoot(d, 'a', '.');
d.zonePlacement.crate = 'floating';
eq(
  findings(d).map((f) => f.kind),
  ['floating-on-land'],
  'floater on dry ground',
);
d = fixture();
atFoot(d, 'a', '~');
d.zonePlacement.crate = 'floating';
eq(findings(d), [], 'floater on water is valid');
for (const [ch, count, expected] of [
  ['~', 2, []],
  ['~', 3, ['ground-on-water']],
  ['!', 1, []],
  ['!', 2, ['ground-on-lava']],
]) {
  d = fixture();
  d.zoneMaps.a.objects = [['obj', 'crate', 20, 20, 20, 20]];
  for (let x = 5; x < 5 + count; x++) put(d, 'a', x, 8, ch);
  eq(
    findings(d).map((f) => f.kind),
    expected,
    'footprint threshold: ' + ch + count,
  );
}
d = fixture();
d.zoneMaps.a.objects = [['obj', 'crate', 20, 20, 20, 20]];
d.zonePlacement.crate = 'floating';
for (let x = 5; x < 9; x++) put(d, 'a', x, 8, '~');
eq(findings(d), [], 'exactly half-water floater is accepted');
put(d, 'a', 8, 8, '.');
eq(
  findings(d).map((f) => f.kind),
  ['floating-on-land'],
  'below-half-water floater is rejected',
);
for (const [placement, counter] of [
  ['supported', 'skippedSupported'],
  ['wet', 'skippedWet'],
  ['overhead', 'skippedOverhead'],
]) {
  d = fixture();
  atFoot(d, 'a', '~');
  d.zonePlacement.crate = placement;
  const r = inspectWorld(d);
  eq(r.findings, [], placement + ' is not falsely claimed as checked');
  eq(r.coverage[counter], 1, placement + ' omission is explicit');
}
d = fixture();
atFoot(d, 'a', '~');
d.zoneOverhead = ['crate'];
eq(inspectWorld(d).coverage.skippedOverhead, 1, 'explicit overhead takes precedence');
d = fixture();
d.zoneMaps.a.objects = [['outside', 'crate', -100, -100, 12, 12]];
eq(
  inspectWorld(d).coverage.skippedEmptyFootprints,
  1,
  'off-tile footprint is reported, never claimed checked',
);
d = fixture();
d.zoneMaps.a.objects = [['tree', 'tree', 20, 20, 32, 32]];
// Wet crown edges do not mean a wet trunk.
for (let y = 11; y < 13; y++) for (let x = 5; x < 7; x++) put(d, 'a', x, y, '~');
eq(findings(d), [], 'trunked props use their narrow footing, not their crown');
for (let y = 11; y < 13; y++) for (let x = 8; x < 10; x++) put(d, 'a', x, y, '~');
check(
  findings(d).some((f) => f.kind === 'ground-on-water'),
  'wet trunk is caught',
);

d = fixture();
for (let x = 5; x < 17; x++) put(d, 'a', x, 10, '=');
const disconnected = clone(d);
eq(
  findings(d).map((f) => f.kind),
  ['path-to-nowhere'],
  '12-cell disconnected path component',
);
d.zoneMaps.a.stands.entry = [20, 40];
eq(findings(d), [], 'component reaches a named stand');
d = clone(disconnected);
d.zoneMaps.a.objects = [['bench', 'bench', 20, 20, 44, 20]];
eq(findings(d), [], 'component reaches generator-equivalent prop proxy, not certified door');
d = fixture();
for (let x = 0; x < 12; x++) put(d, 'a', x, 10, '=');
eq(findings(d), [], 'component reaches tile edge; endpoint semantics remain unproved');
d = fixture();
for (let x = 5; x < 16; x++) put(d, 'a', x, 10, '=');
eq(findings(d), [], '11-cell component follows generator threshold');

for (const [ch, kind] of [
  ['~', 'seam-water'],
  ['!', 'seam-lava'],
  ['=', 'seam-path'],
]) {
  d = fixture();
  for (let y = 5; y < 9; y++) put(d, 'a', 31, y, ch);
  check(
    findings(d).some((f) => f.kind === kind && f.box[1][0] === 20 && f.box[1][1] === 36),
    kind + ' four-cell run',
  );
  for (let y = 5; y < 9; y++) put(d, 'b', 0, y, ch);
  eq(findings(d), [], kind + ' continuous');
  // The three-cell strip tolerates a shaded/slanted edge as in the generator.
  for (let y = 5; y < 9; y++) {
    put(d, 'b', 0, y, '.');
    put(d, 'b', 2, y, ch);
  }
  eq(findings(d), [], kind + ' three-cell strip');
}
d = fixture();
for (let y = 4; y < 7; y++) put(d, 'a', 31, y, '~');
eq(findings(d), [], 'short three-cell mismatch follows generator tolerance');
d = fixture();
for (let y = 28; y < 32; y++) put(d, 'a', 31, y, '!');
check(
  findings(d).some((f) => f.kind === 'seam-lava'),
  'run ending at final edge position is checked',
);
d = fixture();
d.regionLayout.test.b = [-2, -2];
for (let x = 5; x < 9; x++) put(d, 'a', x, 31, '~');
check(
  findings(d).some((f) => f.kind === 'seam-water' && f.box[0] === 'south'),
  'north/south seam',
);
for (let x = 5; x < 9; x++) put(d, 'b', x, 0, '~');
eq(findings(d), [], 'north/south continuity');
d = fixture();
d.regionLayout.test.garden = [-3, -3];
d.zonePorts['garden|a'] = { span: [0, 128], frame: 'open' };
eq(inspectWorld(d).coverage.missingTerrain, ['garden'], 'garden semantic gap is explicit');
eq(inspectWorld(d).coverage.seams, 1, 'no fake garden terrain');
eq(inspectWorld(d).coverage.skippedSeams, ['garden|a'], 'omitted seam is named');

for (const mutate of [
  (x) => {
    x.ZONE.cell = 0;
  },
  (x) => {
    x.ZONE.width = 127;
  },
  (x) => {
    x.zoneIds.push('a');
  },
  (x) => {
    delete x.zoneMaps.a;
  },
  (x) => {
    delete x.zoneTerrain.a;
  },
  (x) => {
    x.zoneTerrain.a[0] = '.';
  },
  (x) => {
    x.zoneTerrain.a[0] = 'R'.repeat(32);
  },
  (x) => {
    x.zoneMaps.a.walk[0] = '='.repeat(32);
  },
  (x) => {
    x.zoneMaps.a.stands.entry = [Infinity, 0];
  },
  (x) => {
    x.zoneMaps.a.stands.entry = [-1, 0];
  },
  (x) => {
    x.zoneMaps.a.objects = [['x', 'crate', 0, 0, -1, 1]];
  },
  (x) => {
    x.zoneMaps.a.objects = [
      ['x', 'crate', 0, 0, 1, 1],
      ['x', 'crate', 5, 5, 1, 1],
    ];
  },
  (x) => {
    x.zonePlacement.crate = 'mystery';
  },
  (x) => {
    x.zoneMaps.extra = x.zoneMaps.a;
  },
  (x) => {
    delete x.regionLayout.test.a;
  },
  (x) => {
    x.regionLayout.test.b = [-2, -3];
  },
  (x) => {
    x.regionLayout.other = { a: [0, 0] };
  },
  (x) => {
    delete x.zonePorts['a|b'];
  },
  (x) => {
    x.zonePorts['b|a'] = x.zonePorts['a|b'];
  },
  (x) => {
    x.zonePorts['a|b'].span = [100, 50];
  },
  (x) => {
    x.zonePorts['a|b'].span = [0, 129];
  },
]) {
  d = fixture();
  mutate(d);
  bad(() => inspectWorld(d), 'malformed data fails closed');
}
d = fixture();
atFoot(d, 'a', '~');
const f = findings(d),
  entry = { ...f[0], reason: 'Named test exception, not a production waiver.' };
eq(settleFindings(f, []).unexpected.length, 1, 'new findings fail');
eq(settleFindings(f, [entry]).accepted.length, 1, 'exact reasoned finding accepted');
eq(settleFindings([], [entry]).stale.length, 1, 'stale waiver fails');
eq(
  settleFindings(f, [{ ...entry, box: [0, 0, 1, 1] }]).unexpected.length,
  1,
  'changed footprint is not waived',
);
bad(() => settleFindings(f, [{ ...entry, reason: ' ' }]), 'blank waiver rejected');
bad(() => settleFindings(f, [entry, entry]), 'duplicate waiver rejected');
bad(() => settleFindings(f, [{ ...entry, reason: 4 }]), 'non-text waiver reason rejected');
bad(() => settleFindings(f, {}), 'malformed waiver registry rejected');
const before = JSON.stringify(d);
inspectWorld(d);
eq(JSON.stringify(d), before, 'inspection never mutates data');
eq(findings(d), findings(clone(d)), 'findings deterministic and detached');
const root = path.resolve(__dirname, '..'),
  actual = readWorld(root);
const real = inspectWorld(actual),
  known = require('./world-logic-known.json');
eq(settleFindings(real.findings, known).unexpected, [], 'no unexplained current findings');
eq(settleFindings(real.findings, known).stale, [], 'no stale current waivers');
eq(real.coverage.zones, actual.zoneIds.length, 'all exported zones inspected');
check(
  real.coverage.footprints > 0 && real.coverage.seams > 0,
  'real footprints and seams exercised',
);
check(
  real.coverage.unsupported.length > 0,
  'partial coverage cannot masquerade as complete world validation',
);
const cli = spawnSync(process.execPath, [path.join(__dirname, 'check-world-logic.cjs'), '--json'], {
  cwd: root,
  encoding: 'utf8',
});
eq(cli.status, 0, 'actual CLI success');
eq(JSON.parse(cli.stdout).findings, real.findings, 'CLI uses the same actual collector');
// Exercise the real CLI's exit status against disposable generated exports, not
// just the pure checker. Never touch the repository's actual generated files.
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'napattack-world-logic-'));
try {
  fs.mkdirSync(path.join(temporary, 'scripts'));
  fs.mkdirSync(path.join(temporary, 'lib'));
  const script = path.join(temporary, 'scripts/check-world-logic.cjs');
  fs.copyFileSync(path.join(__dirname, 'check-world-logic.cjs'), script);
  const runFixture = (data, waivers = []) => {
    fs.writeFileSync(
      path.join(temporary, 'lib/zone-maps.ts'),
      Object.entries(data)
        .map(([key, value]) => 'export const ' + key + ' = ' + JSON.stringify(value) + ';')
        .join('\n'),
    );
    fs.writeFileSync(
      path.join(temporary, 'scripts/world-logic-known.json'),
      JSON.stringify(waivers),
    );
    return spawnSync(process.execPath, [script, '--json'], {
      cwd: temporary,
      encoding: 'utf8',
      env: { ...process.env, NODE_PATH: path.join(root, 'node_modules') },
    });
  };
  d = fixture();
  atFoot(d, 'a', '~');
  const rejected = runFixture(d);
  eq(rejected.status, 1, 'CLI rejects a real bad exported map');
  eq(
    JSON.parse(rejected.stdout).unexpected[0].kind,
    'ground-on-water',
    'CLI reports the failing rule',
  );
  const waiver = { ...findings(d)[0], reason: 'Disposable CLI test only.' };
  eq(runFixture(d, [waiver]).status, 0, 'CLI accepts only an exact documented finding');
  eq(runFixture(fixture(), [waiver]).status, 1, 'CLI rejects stale exceptions');
  d = fixture();
  delete d.zoneTerrain.a;
  const malformed = runFixture(d);
  eq(malformed.status, 1, 'CLI rejects missing terrain rather than silently skipping it');
  check(malformed.stderr.includes('World logic export:'), 'CLI identifies malformed exports');
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
console.log(
  'World logic:',
  checks,
  'checks passed (exported-data diagnostics; not visual/physical-route certification).',
);
