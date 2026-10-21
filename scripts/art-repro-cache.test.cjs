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
  write('runtime/stdlib/json.py', 'stdlib-v1');
  write('runtime/stdlib/site-packages/unrelated.py', 'unrelated-v1');
  write('unrelated-sys-path/arbitrary_dependency.py', 'unrelated-v1');
  fs.symlinkSync('missing-lldb.so', path.join(root, 'unrelated-sys-path/lldb.so'));
  const packages = ['PIL', 'numpy', 'scipy'].map((name) => {
    const relative = `runtime/stdlib/site-packages/${name}`;
    write(`${relative}/__init__.py`, `${name}-v1`);
    return { name, version: '1', path: path.join(root, relative) };
  });
  fs.symlinkSync('missing.so', path.join(packages[0].path, 'optional.so'));
  write('runtime/stdlib/site-packages/numpy.libs/blas.so', 'blas-v1');
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
  const data = {
    version: 'fixture-python-1',
    inputs: [probe, path.join(root, 'runtime/stdlib')],
    excluded: [path.join(root, 'runtime/stdlib/site-packages')],
    packages,
  };
  write('probe', `#!${process.execPath}\nconsole.log(${JSON.stringify(JSON.stringify(data))});\n`);
  fs.chmodSync(probe, 0o755);
  process.env.PATH = path.join(root, 'bin') + path.delimiter + prior.PATH;
  process.env.PYTHON = probe;
  let before = toolFingerprint(root);
  assert.equal(toolFingerprint(root), before, 'stable actual bytes give a stable tool fingerprint');
  write('unrelated-sys-path/arbitrary_dependency.py', 'unrelated-v2');
  write('runtime/stdlib/site-packages/unrelated.py', 'unrelated-v2');
  assert.equal(toolFingerprint(root), before, 'unimported sys.path/site packages are excluded');
  for (const [file, bytes] of [
    ['node_modules/formatter/native.node', 'formatter-v2'],
    ['runtime/stdlib/json.py', 'stdlib-v2'],
    ['runtime/stdlib/site-packages/PIL/__init__.py', 'PIL-v2'],
    ['runtime/stdlib/site-packages/numpy/__init__.py', 'numpy-v2'],
    ['runtime/stdlib/site-packages/scipy/__init__.py', 'scipy-v2'],
    ['runtime/stdlib/site-packages/numpy.libs/blas.so', 'blas-v2'],
    ['runtime/stdlib/site-packages/PIL/missing.so', 'resolved target'],
    ['npm/bin/npm-cli.js', '# changed npm'],
    ['git', '# changed git'],
  ]) {
    write(file, bytes);
    const after = toolFingerprint(root);
    assert.notEqual(after, before, 'actual tool-tree input invalidates: ' + file);
    before = after;
  }
  fs.unlinkSync(path.join(packages[0].path, 'optional.so'));
  fs.symlinkSync('other-missing.so', path.join(packages[0].path, 'optional.so'));
  assert.notEqual(toolFingerprint(root), before, 'link target string is fingerprinted');
  before = toolFingerprint(root);
  fs.chmodSync(path.join(root, 'node_modules/formatter/native.node'), 0o700);
  assert.notEqual(toolFingerprint(root), before, 'tool executable mode invalidates');
  console.log(
    'PASS: scoped Python runtime/packages, dangling links, native libraries, formatter/npm/Git bytes and modes.',
  );
} finally {
  for (const [key, value] of Object.entries(prior)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  fs.rmSync(root, { recursive: true, force: true });
}
