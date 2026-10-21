/** Real subprocesses and Git snapshots; tiny JS generators avoid Python/art costs. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const {
  generators,
  generatedTypescript,
  generatorGroups,
  checkArtReproducibility,
  checkArtParallel,
} = require('./check-art-repro.cjs');
const { fingerprint } = require('./art-repro-cache.cjs');
async function main() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'art-parallel-fixture-'));
  const priorPython = process.env.PYTHON,
    priorDensity = process.env.ART_DENSITY;
  const write = (file, value) => {
    fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true });
    fs.writeFileSync(path.join(root, file), value);
  };
  const git = (args) => {
    const r = spawnSync('git', args, { cwd: root, encoding: 'utf8' });
    assert.equal(r.status, 0, r.stderr);
    return r.stdout;
  };
  try {
    process.env.PYTHON = process.execPath;
    write('.gitignore', 'node_modules/\n.cache/\n');
    write('density.json', '{"density":2}\n');
    write('shared.txt', 'stable\n');
    for (const file of generatedTypescript) write(file, '// stable fixture\n');
    write('node_modules/.bin/oxfmt', '#!/usr/bin/env node\n');
    fs.chmodSync(path.join(root, 'node_modules/.bin/oxfmt'), 0o755);
    write('scripts/check-sprites.cjs', '/* validation fixture */\n');
    const scripts = new Map();
    for (const name of generators) {
      const script = `const fs = require('node:fs');\nfs.writeFileSync('assets/${name}.png', '${name}');\nfs.writeFileSync('shared.txt', 'stable\\n');\n`;
      scripts.set(name, script);
      write(`assets/${name}.png`, name);
      write(`scripts/art/${name}.py`, script);
    }
    git(['init', '-q']);
    git(['add', '--all']);
    assert.deepEqual(
      generatorGroups.flat().sort(),
      [...generators].sort(),
      'exactly every generator is scheduled once',
    );
    const options = { root, tools: 'fixture-tool-v1', log() {} };
    const reference = checkArtReproducibility({ root, log() {} });
    assert.ok(reference.ok);
    const cold = await checkArtParallel({ ...options, cold: true, jobs: 2 });
    assert.ok(cold.ok);
    assert.equal(cold.cacheHit, false);
    assert.equal(
      cold.outputDigest,
      reference.outputDigest,
      'parallel output bytes/modes equal ordered cold output',
    );
    assert.ok(
      !fs.existsSync(path.join(root, '.cache/art-repro')),
      'forced cold never publishes a certificate',
    );
    const seed = await checkArtParallel({ ...options, jobs: 2 });
    assert.ok(seed.ok);
    assert.equal(seed.cacheHit, false);
    const warm = await checkArtParallel({ ...options, jobs: 2 });
    assert.ok(warm.ok);
    assert.ok(warm.cacheHit);
    assert.equal(
      warm.outputDigest,
      reference.outputDigest,
      'warm output bytes/modes equal full cold output',
    );
    assert.equal(
      (await checkArtParallel({ ...options, cold: true, jobs: 1 })).cacheHit,
      false,
      'cold ignores a valid certificate',
    );
    assert.equal(
      (await checkArtParallel({ ...options, tools: 'fixture-tool-v2' })).cacheHit,
      false,
      'tool version/content change invalidates',
    );
    process.env.ART_DENSITY = '2';
    assert.equal(
      (await checkArtParallel(options)).cacheHit,
      false,
      'actual density environment invalidates',
    );
    write('density.json', '{"density":1.5}\n');
    assert.equal(
      (await checkArtParallel(options)).cacheHit,
      false,
      'tracked density/config input invalidates',
    );
    const cert = path.join(root, '.cache/art-repro', fingerprint(options).key + '.json');
    fs.writeFileSync(cert, 'broken JSON');
    assert.equal((await checkArtParallel(options)).cacheHit, false, 'corruption takes cold path');
    for (const mode of ['drift', 'new', 'deleted', 'failed', 'format', 'sprites']) {
      const script = scripts.get('garden');
      if (mode === 'drift') write('assets/garden.png', 'wrong committed bytes');
      if (mode === 'new')
        write('scripts/art/garden.py', script + "fs.writeFileSync('assets/new.png', 'new');\n");
      if (mode === 'deleted')
        write('scripts/art/garden.py', script + "fs.unlinkSync('assets/garden.png');\n");
      if (mode === 'failed') write('scripts/art/garden.py', script + 'process.exit(7);\n');
      if (mode === 'format')
        write('node_modules/.bin/oxfmt', '#!/usr/bin/env node\nprocess.exit(9);\n');
      if (mode === 'sprites') write('scripts/check-sprites.cjs', 'process.exit(8);\n');
      const serial = checkArtReproducibility({ root, log() {} });
      const parallel = await checkArtParallel(options);
      assert.equal(serial.ok, false, mode + ': full cold fails');
      assert.equal(parallel.ok, false, mode + ': parallel/cache cannot conceal failure');
      assert.ok(parallel.failures.length);
      assert.ok(
        !fs.existsSync(path.join(root, '.cache/art-repro', fingerprint(options).key + '.json')),
        mode + ': no failure certificate',
      );
      write('assets/garden.png', 'garden');
      write('scripts/art/garden.py', script);
      write('node_modules/.bin/oxfmt', '#!/usr/bin/env node\n');
      write('scripts/check-sprites.cjs', '/* validation fixture */\n');
    }
    const exception = await checkArtParallel({
      ...options,
      cold: true,
      worker: async () => {
        throw new Error('worker failed');
      },
    }).catch((error) => error);
    assert.ok(exception instanceof Error, 'exception cannot pass');
    assert.equal(
      fs.readFileSync(path.join(root, 'shared.txt'), 'utf8'),
      'stable\n',
      'overlapping generator writes never reach caller',
    );
    assert.ok(!fs.existsSync(path.join(root, 'assets/new.png')));
    console.log(
      'PASS: real-process cold/parallel/warm equivalence, input/tool/density invalidation, corruption and failure detection.',
    );
  } finally {
    if (priorPython === undefined) delete process.env.PYTHON;
    else process.env.PYTHON = priorPython;
    if (priorDensity === undefined) delete process.env.ART_DENSITY;
    else process.env.ART_DENSITY = priorDensity;
    fs.rmSync(root, { recursive: true, force: true });
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
