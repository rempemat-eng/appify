const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { mapLimit, runProcess, concurrency } = require('./check-runner.cjs');
const { verify, checkCommands } = require('./run-verification.cjs');
async function main() {
  assert.throws(() => concurrency(0));
  assert.throws(() => concurrency(1.5));
  let active = 0,
    maximum = 0;
  const settled = await mapLimit([0, 1, 2, 3], 2, async (value) => {
    maximum = Math.max(maximum, ++active);
    await new Promise((resolve) => setTimeout(resolve, 20));
    active--;
    if (value === 1) throw new Error('fixture failure');
    return value;
  });
  assert.equal(maximum, 2);
  assert.equal(active, 0);
  assert.equal(settled[1].status, 'rejected');
  assert.equal(settled[3].value, 3, 'later checks are not dropped');
  assert.equal((await runProcess(process.execPath, ['-e', 'process.exit(7)'])).status, 7);
  assert.ok(
    (await runProcess(process.execPath, ['-e', 'setTimeout(()=>{},1000)'], { timeout: 20 })).error,
  );
  assert.ok(
    (await runProcess(process.execPath, ['-e', 'console.log("x".repeat(100))'], { maxBuffer: 5 }))
      .error,
  );
  assert.ok((await runProcess('missing-napattack-fixture-command', [])).error);
  assert.throws(() => checkCommands('npm run a; true'), /Unsupported/);
  const actual = JSON.parse(fs.readFileSync(path.join(__dirname, '../package.json'))).scripts;
  const list = checkCommands(actual.check);
  assert.equal(list.length, actual.check.split(' && ').length);
  assert.equal(new Set(list.map((s) => s.label)).size, list.length);
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'verify-runner-test-'));
  try {
    fs.writeFileSync(
      path.join(root, 'package.json'),
      JSON.stringify({
        scripts: {
          check: 'tsc --noEmit && npm run check:a && npm run check:b',
          'export:web': 'web',
          'export:ios': 'ios',
        },
      }),
    );
    for (const failure of [null, 'check:a', 'export:web', 'export:ios', 'throw']) {
      const calls = [];
      const result = await verify({
        root,
        jobs: 2,
        log() {},
        run: async (cmd, args) => {
          const name = cmd === 'tsc' ? 'typescript' : args[1];
          calls.push(name);
          if (failure === 'throw' && name === 'check:a')
            throw new Error('synthetic spawn exception');
          return { status: name === failure ? 1 : 0, stdout: '', stderr: '' };
        },
      });
      assert.equal(result.ok, failure === null);
      for (const name of ['typescript', 'check:a', 'check:b']) assert.ok(calls.includes(name));
      if (failure === 'check:a' || failure === 'throw') assert.ok(!calls.includes('export:web'));
      else assert.equal(calls.indexOf('export:web'), 3, 'exports wait for all checks');
      if (failure === 'export:web') assert.ok(!calls.includes('export:ios'));
      if (failure === null) assert.deepEqual(calls.slice(-2), ['export:web', 'export:ios']);
    }
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
  console.log(
    'PASS: bounded jobs, complete canonical list, failures/timeouts and ordered exports.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
