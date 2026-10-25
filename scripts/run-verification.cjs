/** Run the unchanged canonical check list in bounded parallel jobs.
 * Web and iOS exports stay ordered: they share Metro/Expo state. */
const fs = require('node:fs');
const path = require('node:path');
const { mapLimit, runProcess, concurrency } = require('./check-runner.cjs');

function checkCommands(script) {
  return script.split(' && ').map((command) => {
    if (command === 'tsc --noEmit')
      return { label: 'typescript', command: 'tsc', args: ['--noEmit'] };
    const match = /^npm run ([a-z0-9:-]+)$/.exec(command);
    if (!match) throw new Error(`Unsupported check command; preserve it explicitly: ${command}`);
    return { label: match[1], command: 'npm', args: ['run', match[1]] };
  });
}
async function verify({
  root,
  jobs = concurrency(process.env.VERIFY_JOBS),
  checkOnly = false,
  run = runProcess,
  log = console.log,
}) {
  const scripts = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')).scripts;
  const commands = checkCommands(scripts.check);
  // Start the long read-only world audit early; retain canonical order in the summary.
  const ordered = [...commands].sort(
    (a, b) => Number(b.label === 'check:world-audit') - Number(a.label === 'check:world-audit'),
  );
  const env = {
    ...process.env,
    PATH: `${path.join(root, 'node_modules', '.bin')}${path.delimiter}${process.env.PATH}`,
  };
  async function execute(step) {
    const start = performance.now();
    log(`[verify] start ${step.label}`);
    const result = await run(step.command, step.args, { cwd: root, env, timeout: 900_000 });
    if (result.stdout) log(`[${step.label}]\n${result.stdout.trimEnd()}`);
    if (result.stderr) log(`[${step.label}]\n${result.stderr.trimEnd()}`);
    const ok = !result.error && !result.signal && result.status === 0;
    log(
      `[verify] ${ok ? 'PASS' : 'FAIL'} ${step.label} (${((performance.now() - start) / 1000).toFixed(2)}s)`,
    );
    return {
      label: step.label,
      ok,
      error: result.error?.message || result.signal || result.status,
    };
  }
  const settled = await mapLimit(ordered, jobs, execute);
  const results = settled.map((r, index) =>
    r.status === 'fulfilled'
      ? r.value
      : { label: ordered[index].label, ok: false, error: String(r.reason) },
  );
  if (results.every((r) => r.ok) && !checkOnly) {
    for (const name of ['export:web', 'export:ios']) {
      if (!scripts[name]) throw new Error(`Missing required ${name} command`);
      const result = await execute({ label: name, command: 'npm', args: ['run', name] });
      results.push(result);
      if (!result.ok) break;
    }
  }
  const failed = results.filter((r) => !r.ok);
  if (failed.length)
    log(`[verify] failed: ${failed.map((r) => `${r.label} (${r.error})`).join(', ')}`);
  return { ok: failed.length === 0, results };
}
module.exports = { verify, checkCommands };
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.some((arg) => arg !== '--check-only')) {
    console.error('Usage: run-verification.cjs [--check-only]');
    process.exitCode = 1;
  } else
    verify({ root: path.resolve(__dirname, '..'), checkOnly: args.includes('--check-only') })
      .then((result) => {
        process.exitCode = result.ok ? 0 : 1;
      })
      .catch((error) => {
        console.error(error);
        process.exitCode = 1;
      });
}
