const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { auditFx, pngSize, report } = require('./check-fx.cjs');

let checks = 0;
function ok(value, message) {
  assert.ok(value, message);
  checks++;
}
function eq(actual, expected, message) {
  assert.deepEqual(actual, expected, message);
  checks++;
}

function pngHeader(width, height) {
  const bytes = Buffer.alloc(24);
  Buffer.from('89504e470d0a1a0a', 'hex').copy(bytes);
  bytes.writeUInt32BE(13, 8);
  bytes.write('IHDR', 12, 'ascii');
  bytes.writeUInt32BE(width, 16);
  bytes.writeUInt32BE(height, 20);
  return bytes;
}

function fixture({ width, height, rect, frameMs = 150, kind = 'world' }) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'napattack-fx-test-'));
  const file = kind === 'world' ? 'assets/world/test/f_0_0.png' : 'assets/zones/test/flow.png';
  fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true });
  fs.writeFileSync(path.join(root, file), pngHeader(width, height));
  const definitions = {
    zoneFlow: kind === 'zone' ? { test: rect } : {},
    zoneFrames: 8,
    zoneFrameMs: frameMs,
    worldTiles: kind === 'world' ? { test: { '0,0': { flow: rect } } } : {},
    worldFrames: 8,
    worldFrameMs: frameMs,
  };
  return { root, definitions, file };
}

function run(spec, isRetiring = () => false) {
  const made = fixture(spec);
  try {
    return auditFx(made.root, { definitions: made.definitions, isRetiring });
  } finally {
    fs.rmSync(made.root, { recursive: true, force: true });
  }
}

const passing = run({ width: 64, height: 32 * 8, rect: [3, 7, 64, 32] });
eq(passing.gatingFailures, []);
eq(passing.rows[0].frames, 8);
eq(passing.rows[0].scale, 1);
eq(passing.rows[0].perTileBytes, 64 * 32 * 8 * 4);
ok(!report(passing).includes('old zone: report'));

const nineFrames = run({ width: 64, height: 32 * 9, rect: [0, 0, 64, 32] });
ok(nineFrames.gatingFailures.some((line) => line.includes('9 frames')));

const sevenBy150 = run({ width: 64, height: 32 * 7, rect: [0, 0, 64, 32] });
ok(sevenBy150.gatingFailures.some((line) => line.includes('does not divide 36000 ms')));

const stored2x = run({ width: 128, height: 64 * 8, rect: [0, 0, 64, 32] });
ok(stored2x.gatingFailures.some((line) => line.includes('stored at 2 image px')));

const tooWide = run({ width: 4608, height: 8, rect: [0, 0, 4608, 1] });
ok(tooWide.gatingFailures.some((line) => line.includes('passes 4096 px')));
const retiring = run({ width: 4608, height: 8, rect: [0, 0, 4608, 1] }, () => true);
eq(retiring.gatingFailures, []);

const oldZone = run({ width: 64, height: 32 * 9, rect: [0, 0, 64, 32], kind: 'zone' });
eq(oldZone.gatingFailures, []);
ok(oldZone.failures.some((line) => line.startsWith('REPORT ONLY:')));

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'napattack-fx-header-'));
try {
  const file = path.join(root, 'header.png');
  fs.writeFileSync(file, pngHeader(17, 23));
  eq(pngSize(file), { width: 17, height: 23 });
  for (const bytes of [Buffer.from('bad'), Buffer.alloc(24)]) {
    fs.writeFileSync(file, bytes);
    assert.throws(() => pngSize(file), /Invalid PNG/);
    checks++;
  }
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}

console.log(
  `PASS ${checks} check:fx assertions (headers, four negative fixtures, retirement and gating).`,
);
