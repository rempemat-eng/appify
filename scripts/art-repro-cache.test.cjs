/** Exercise actual installed-tool traversal, without scanning a real dependency tree. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { toolFingerprint } = require('./art-repro-cache.cjs');
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'art-tools-fixture-'));
const prior = { PATH: process.env.PATH, PYTHON: process.env.PYTHON };
const write = (file, bytes) => {
  fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true });
  fs.writeFileSync(path.join(root, file), bytes);
};
try {
  write('node_modules/formatter/native.node', 'formatter-v1');
  write('runtime/site-packages/arbitrary_dependency.py', 'python-input-v1');
  write('npm/bin/npm-cli.js', '# fixture npm');
  write('git', '# fixture git');
  fs.chmodSync(path.join(root, 'git'), 0o755);
  fs.mkdirSync(path.join(root, 'bin'));
  for (const name of ['npm', 'npx']) {
    fs.chmodSync(path.join(root, 'npm/bin/npm-cli.js'), 0o755);
    fs.symlinkSync(path.join(root, 'npm/bin/npm-cli.js'), path.join(root, 'bin', name));
  }
  fs.symlinkSync(path.join(root, 'git'), path.join(root, 'bin/git'));
  const probe = path.join(root, 'probe');
  write(
    'probe',
    `#!${process.execPath}\nconsole.log(JSON.stringify([${JSON.stringify(probe)}, ${JSON.stringify(path.join(root, 'runtime'))}]));\n`,
  );
  fs.chmodSync(probe, 0o755);
  process.env.PATH = path.join(root, 'bin') + path.delimiter + prior.PATH;
  process.env.PYTHON = probe;
  let before = toolFingerprint(root);
  assert.equal(toolFingerprint(root), before, 'stable actual bytes give a stable tool fingerprint');
  for (const [file, bytes] of [
    ['node_modules/formatter/native.node', 'formatter-v2'],
    ['runtime/site-packages/arbitrary_dependency.py', 'python-input-v2'],
    ['runtime/site-packages/new_dependency.py', 'new input'],
    ['npm/bin/npm-cli.js', '# changed npm'],
    ['git', '# changed git'],
  ]) {
    write(file, bytes);
    const after = toolFingerprint(root);
    assert.notEqual(after, before, 'actual tool-tree input invalidates: ' + file);
    before = after;
  }
  fs.chmodSync(path.join(root, 'node_modules/formatter/native.node'), 0o700);
  assert.notEqual(toolFingerprint(root), before, 'tool executable mode invalidates');
  console.log(
    'PASS: actual Python search paths, arbitrary installed packages, formatter, npm/Git bytes and executable modes fingerprinted.',
  );
} finally {
  for (const [key, value] of Object.entries(prior)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  fs.rmSync(root, { recursive: true, force: true });
}
