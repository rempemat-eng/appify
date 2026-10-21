/**
 * The asset ledger check (docs/vision/asset-ledger.md, `npm run check:assets`).
 *
 * Matt, 20 Oct 20:16: "can u make sure no old assets are reused that dont fit the soft grid,
 * level of detail etc. established for the newest version". scripts/art/asset_ledger.json
 * grades every picture under assets/ KEEP, REWORK or RETIRE. This check fails when:
 *
 * 1. a picture exists under assets/ that the ledger does not list, by name or by one of its
 *    few `rules` (the world canvas's tiles, graded by the grounds they are cut from); new art
 *    is measured and graded before it ships (`python3 scripts/art/asset_ledger.py --redo
 *    <file>`); or the ledger lists a picture that is gone;
 * 2. a region build uses anything that is not KEEP. A region build is the world canvas
 *    (lib/world-canvas*.ts, scripts/art/world_canvas.py), a kit (scripts/art/*_kit.py,
 *    *_kits.py, terrace.py) or any file under a regions/ or kits/ folder outside docs/. It
 *    "uses" an asset by naming its path (an import, a require or a string), by joining a path
 *    under 'assets' in Python (os.path.join(ROOT, 'assets', 'residents', f'{n}-0.png')), or by
 *    importing an old generator module (valley_props, scenery, frost_zones ...): then every
 *    sprite it names from that module (props()['bench'], vp.bench(...)) must be KEEP, and an
 *    import that names none counts as using the whole module.
 *
 * A line that only shows old art beside new for comparison or as a scale line-up carries the
 * marker `ledger: compare` (in a comment on that line or the line above) and is skipped.
 *
 *   node scripts/check-assets.cjs            the check
 *   node scripts/check-assets.cjs --summary  also print the grades per lane
 *   node scripts/check-assets.cjs --self-test
 */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const IMAGE = /\.(png|jpe?g|webp|gif)$/i;
const MARKER = 'ledger: compare';
// Shared helpers that draw nothing old by themselves (the house kit, the toolkit, the checks).
const HELPERS = new Set([
  'style',
  'pixel',
  'materials',
  'detail',
  'house_palette',
  'house_kits',
  'style_sheet',
  'style_lint',
  'detail_bar',
  'size_check',
  'terrace',
  'water_flow',
  'world_lint',
  'frames',
  'asset_ledger',
  'dry_kit',
  'river_kit',
  'mountain_kit',
  'world_canvas',
]);

function walk(
  dir,
  out = [],
  skip = new Set(['node_modules', '.git', '.expo', 'dist', 'web-build']),
) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    if (skip.has(e.name)) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out, skip);
    else out.push(p);
  }
  return out;
}

const posix = (p) => p.split(path.sep).join('/');

function globToRegExp(glob) {
  let re = '';
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];
    if (c === '*' && glob[i + 1] === '*') {
      re += '.*';
      i++;
      if (glob[i + 1] === '/') i++;
    } else if (c === '*') re += '[^/]*';
    else if (c === '?') re += '[^/]';
    else re += c.replace(/[.+^${}()|[\]\\]/g, '\\$&');
  }
  return new RegExp(`^${re}$`);
}

function loadLedger(root) {
  const file = path.join(root, 'scripts', 'art', 'asset_ledger.json');
  const doc = JSON.parse(fs.readFileSync(file, 'utf8'));
  const byFile = new Map();
  const byModule = new Map();
  for (const [id, e] of Object.entries(doc.assets)) {
    for (const f of e.files) byFile.set(f, { id, ...e });
    const mod = (e.generator || '').replace(/^scripts\/art\//, '').replace(/\.py$/, '');
    if (!byModule.has(mod)) byModule.set(mod, []);
    byModule.get(mod).push({ id, ...e });
  }
  const rules = (doc.rules || []).map((r) => ({ ...r, re: globToRegExp(r.glob) }));
  const lookup = (f) => {
    if (byFile.has(f)) return byFile.get(f);
    const r = rules.find((x) => x.re.test(f));
    return r ? { id: r.glob, name: r.glob, ...r } : undefined;
  };
  return { doc, byFile, byModule, lookup };
}

function regionBuildFiles(root, doc) {
  const globs = (doc.region_builds && doc.region_builds.globs) || [];
  const res = globs.map(globToRegExp);
  return walk(root)
    .map((p) => posix(path.relative(root, p)))
    .filter((p) => !p.startsWith('docs/') && !p.startsWith('assets/') && !IMAGE.test(p))
    .filter((p) => /\.(ts|tsx|js|cjs|mjs|py|json)$/.test(p))
    .filter((p) => !p.endsWith('asset_ledger.json') && !p.endsWith('asset_ledger.py'))
    .filter((p) => res.some((r) => r.test(p)));
}

/** Every asset a file uses, as [{ line, what, files }] where files are ledger paths. */
function references(text, ledger, allFiles) {
  const lines = text.split('\n');
  const refs = [];
  const skip = (i) => lines[i].includes(MARKER) || (i > 0 && lines[i - 1].includes(MARKER));
  const imported = new Map(); // alias -> module
  lines.forEach((line, i) => {
    if (skip(i)) return;
    // 1. a path written out
    for (const m of line.matchAll(/(?:^|[^\w])(assets\/[\w\-./]+?\.(?:png|jpe?g|webp|gif))/gi)) {
      refs.push({ line: i + 1, what: m[1], files: [m[1]] });
    }
    // 2. a path joined from parts in Python: 'assets', 'zones', z, 'ground.png'
    const j = line.match(/['"]assets['"]\s*,\s*(.+?)\)/);
    if (j) {
      const parts = [];
      for (const raw of j[1].split(',')) {
        const t = raw.trim();
        const lit = t.match(/^f?(['"])(.*)\1$/);
        if (lit) parts.push(t.startsWith('f') ? lit[2].replace(/\{[^}]*\}/g, '*') : lit[2]);
        else if (t) parts.push('*');
      }
      if (parts.length) {
        const glob = 'assets/' + parts.join('/');
        const re = globToRegExp(glob);
        const files = allFiles.filter((f) => re.test(f));
        refs.push({ line: i + 1, what: glob, files });
      }
    }
    // 3. an old generator imported
    const im =
      line.match(/^\s*import\s+([a-z_][\w]*)(?:\s+as\s+([\w]+))?/) ||
      line.match(/^\s*from\s+([a-z_][\w]*)\s+import\s+(.+)$/) ||
      line.match(/import_module\(\s*['"]([a-z_][\w]*)['"]\s*\)()/);
    if (im) {
      const mod = im[1];
      if (!HELPERS.has(mod) && ledger.byModule.has(mod)) {
        const alias = im[0].trim().startsWith('from') ? null : im[2] || mod;
        imported.set(alias || mod, {
          mod,
          line: i + 1,
          fromNames: im[0].trim().startsWith('from') ? im[2] : null,
        });
      }
    }
  });
  // 3b. which sprites of each imported module the file names
  for (const [alias, { mod, line, fromNames }] of imported) {
    const entries = ledger.byModule.get(mod);
    const names = new Set(entries.map((e) => e.name));
    const used = new Set();
    let unresolvedPropsUse = false;
    lines.forEach((l, i) => {
      if (skip(i)) return;
      const directProps = [
        ...l.matchAll(new RegExp(`\\b${alias}\\.props\\(\\)\\[['"](\\w+)['"]\\]`, 'g')),
      ];
      const propsCalls = [...l.matchAll(new RegExp(`\\b${alias}\\.props\\(\\)`, 'g'))];
      // Narrowing an old module to literal names is safe only when every props() call is a
      // direct literal lookup. A dynamic key, or assigning the dictionary to an alias, must
      // retain the conservative whole-module fallback. Otherwise one nearby KEEP lookup can
      // hide an unresolved REWORK/RETIRE use.
      if (propsCalls.length !== directProps.length) unresolvedPropsUse = true;
      for (const m of l.matchAll(
        new RegExp(`\\b${alias}\\.(?:props\\(\\)\\[['"](\\w+)['"]\\]|(\\w+)\\()`, 'g'),
      )) {
        const n = m[1] || m[2];
        if (names.has(n)) used.add(n);
        else if (m[2] && m[2] !== 'props') used.add(`${mod}.${m[2]}`);
      }
    });
    if (fromNames) {
      for (const n of fromNames.split(',').map((s) => s.trim().split(/\s+as\s+/)[0])) {
        if (names.has(n)) used.add(n);
        else if (n && n !== '*' && n !== '(') used.add(`${mod}.${n}`);
      }
    }
    const named = [...used].filter((n) => names.has(n));
    if (named.length && named.length === used.size && !unresolvedPropsUse) {
      for (const n of named) {
        const files = entries.filter((e) => e.name === n).flatMap((e) => e.files);
        refs.push({ line, what: `${mod}: ${n}`, files });
      }
    } else {
      refs.push({
        line,
        what: `import ${mod} (an old generator: everything it draws)`,
        files: entries.flatMap((e) => e.files),
      });
    }
  }
  return refs;
}

function checkAssets({
  root = path.resolve(__dirname, '..'),
  log = console.log,
  summary = false,
} = {}) {
  const errors = [];
  const ledger = loadLedger(root);
  const onDisk = walk(path.join(root, 'assets'))
    .filter((p) => IMAGE.test(p))
    .map((p) => posix(path.relative(root, p)))
    .sort((x, y) => x.localeCompare(y));
  const disk = new Set(onDisk);
  for (const f of onDisk) {
    if (!ledger.lookup(f)) {
      errors.push(
        `not in the ledger: ${f} (measure and grade it: python3 scripts/art/asset_ledger.py --redo ${f})`,
      );
    }
  }
  for (const f of ledger.byFile.keys()) {
    if (!disk.has(f))
      errors.push(`in the ledger but not on disk: ${f} (rebuild the ledger, or --redo its entry)`);
  }
  const builds = regionBuildFiles(root, ledger.doc);
  let used = 0;
  for (const b of builds) {
    const text = fs.readFileSync(path.join(root, b), 'utf8');
    for (const r of references(text, ledger, onDisk)) {
      if (!r.files.length) continue;
      const bad = [];
      for (const f of r.files) {
        const e = ledger.lookup(f);
        used++;
        if (!e) bad.push(`${f} (not in the ledger)`);
        else if (e.grade !== 'KEEP') bad.push(`${e.id} ${e.grade}${e.fix ? ` (${e.fix})` : ''}`);
      }
      if (bad.length) {
        const ids = [...new Set(bad)];
        const shown =
          ids.slice(0, 6).join(', ') + (ids.length > 6 ? `, and ${ids.length - 6} more` : '');
        errors.push(`${b}:${r.line} uses ${r.what}: not KEEP: ${shown}`);
      }
    }
  }
  if (summary) {
    const lanes = {};
    for (const e of Object.values(ledger.doc.assets)) {
      const l = (lanes[e.owner] ||= { KEEP: 0, REWORK: 0, RETIRE: 0 });
      l[e.grade]++;
    }
    for (const [lane, c] of Object.entries(lanes).sort((x, y) => x[0].localeCompare(y[0]))) {
      log(`  lane ${lane}: KEEP ${c.KEEP}, REWORK ${c.REWORK}, RETIRE ${c.RETIRE}`);
    }
    if (process.env.GITHUB_STEP_SUMMARY) {
      const rows = Object.entries(lanes)
        .sort((x, y) => x[0].localeCompare(y[0]))
        .map(
          ([lane, c]) =>
            `| ${lane.replaceAll('|', '\\|')} | ${c.KEEP} | ${c.REWORK} | ${c.RETIRE} |`,
        );
      fs.appendFileSync(
        process.env.GITHUB_STEP_SUMMARY,
        [
          '# Asset-ledger report',
          '',
          'Report-only current-tree scan. The negative-fixture self-test is blocking; this inventory is not yet a blocking gate.',
          '',
          `Status: **${errors.length ? `FAIL (${errors.length} problem${errors.length === 1 ? '' : 's'})` : 'PASS'}**`,
          '',
          '| Lane | KEEP | REWORK | RETIRE |',
          '| --- | ---: | ---: | ---: |',
          ...rows,
          '',
          `Pictures on disk: ${onDisk.length}; ledger entries: ${ledger.byFile.size}; checked uses: ${used}.`,
          ...(errors.length
            ? [
                '',
                '<details><summary>Problems</summary>',
                '',
                ...errors.map((e) => `- ${e}`),
                '',
                '</details>',
                '',
              ]
            : ['']),
          '',
        ].join('\n'),
      );
    }
  }
  log(
    `asset ledger: ${onDisk.length} pictures under assets/, ${ledger.byFile.size} in the ledger; ` +
      `${builds.length} region build file(s) checked (${builds.join(', ') || 'none yet'}), ${used} uses`,
  );
  for (const e of errors) log(`  FAIL ${e}`);
  log(errors.length ? `check:assets failed: ${errors.length} problem(s)` : 'check:assets passed');
  return errors;
}

const quiet = () => {};
const testEntry = (files, grade, gen, name) => ({
  files,
  grade,
  generator: `scripts/art/${gen}.py`,
  name,
  owner: 'A',
});

function selfTest() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'check-assets-'));
  const w = (p, s) => {
    fs.mkdirSync(path.dirname(path.join(root, p)), { recursive: true });
    fs.writeFileSync(path.join(root, p), s);
  };
  const png = Buffer.from('89504e470d0a1a0a', 'hex');
  w('assets/zones/props/keepme.png', png);
  w('assets/zones/props/old.png', png);
  w('assets/zones/hollow/ground.png', png);
  w('assets/residents/hiker-0.png', png);
  const e = testEntry;
  w(
    'scripts/art/asset_ledger.json',
    JSON.stringify({
      region_builds: { globs: ['scripts/art/*_kit.py', 'lib/world-canvas*.ts', '**/regions/**'] },
      assets: {
        'prop/keepme': e(['assets/zones/props/keepme.png'], 'KEEP', 'castle_props', 'keepme'),
        'prop/old': e(['assets/zones/props/old.png'], 'REWORK', 'castle_props', 'old'),
        'zone/hollow': e(['assets/zones/hollow/ground.png'], 'RETIRE', 'frost_zones', 'hollow'),
        'resident/hiker': e(['assets/residents/hiker-0.png'], 'REWORK', 'residents', 'hiker'),
      },
    }),
  );
  let errs = checkAssets({ root, log: quiet });
  if (errs.length) throw new Error(`clean tree should pass: ${errs.join('; ')}`);
  w('assets/zones/props/stray.png', png);
  errs = checkAssets({ root, log: quiet });
  if (!errs.some((x) => x.includes('not in the ledger: assets/zones/props/stray.png')))
    throw new Error('stray file missed');
  fs.rmSync(path.join(root, 'assets/zones/props/stray.png'));
  w('scripts/art/snow_kit.py', "import castle_props as cp\nx = cp.props()['keepme']\n");
  errs = checkAssets({ root, log: quiet });
  if (errs.length) throw new Error(`a KEEP sprite by name should pass: ${errs.join('; ')}`);
  w('scripts/art/snow_kit.py', "import castle_props as cp\nx = cp.props()['old']\n");
  errs = checkAssets({ root, log: quiet });
  if (!errs.some((x) => x.includes('prop/old REWORK')))
    throw new Error(`a REWORK sprite was missed: ${errs.join('; ')}`);
  w(
    'scripts/art/snow_kit.py',
    "import castle_props as cp\nx = cp.props()['keepme']\nname = 'old'\ny = cp.props()[name]\n",
  );
  errs = checkAssets({ root, log: quiet });
  if (!errs.some((x) => x.includes('prop/old REWORK')))
    throw new Error(`a dynamic lookup beside a KEEP sprite was missed: ${errs.join('; ')}`);
  w(
    'scripts/art/snow_kit.py',
    "import castle_props as cp\nx = cp.props()['keepme']\npool = cp.props()\ny = pool['old']\n",
  );
  errs = checkAssets({ root, log: quiet });
  if (!errs.some((x) => x.includes('prop/old REWORK')))
    throw new Error(`an aliased catalogue beside a KEEP sprite was missed: ${errs.join('; ')}`);
  w('scripts/art/snow_kit.py', 'import frost_zones\n');
  errs = checkAssets({ root, log: quiet });
  if (!errs.some((x) => x.includes('zone/hollow RETIRE')))
    throw new Error(`an old painter import was missed: ${errs.join('; ')}`);
  w('scripts/art/snow_kit.py', "p = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')\n");
  errs = checkAssets({ root, log: quiet });
  if (!errs.some((x) => x.includes('resident/hiker')))
    throw new Error(`a joined path was missed: ${errs.join('; ')}`);
  w(
    'scripts/art/snow_kit.py',
    "p = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')  # ledger: compare\n",
  );
  errs = checkAssets({ root, log: quiet });
  if (errs.length) throw new Error(`a marked line-up should pass: ${errs.join('; ')}`);
  w('lib/world-canvas-assets.ts', "import a from '@/assets/zones/hollow/ground.png';\n");
  errs = checkAssets({ root, log: quiet });
  if (!errs.some((x) => x.includes('lib/world-canvas-assets.ts:1')))
    throw new Error(`a canvas import was missed: ${errs.join('; ')}`);
  fs.rmSync(path.join(root, 'lib/world-canvas-assets.ts'));
  w('scripts/art/snow_kit.py', "import castle_props as cp\nx = cp.props()['keepme']\n");
  const summaryPath = path.join(root, 'summary.md');
  const priorSummary = process.env.GITHUB_STEP_SUMMARY;
  process.env.GITHUB_STEP_SUMMARY = summaryPath;
  try {
    errs = checkAssets({ root, log: quiet, summary: true });
  } finally {
    if (priorSummary === undefined) delete process.env.GITHUB_STEP_SUMMARY;
    else process.env.GITHUB_STEP_SUMMARY = priorSummary;
  }
  if (errs.length) throw new Error(`summary fixture should pass: ${errs.join('; ')}`);
  const summary = fs.readFileSync(summaryPath, 'utf8');
  if (!summary.includes('# Asset-ledger report') || !summary.includes('| A | 1 | 2 | 1 |'))
    throw new Error('CI asset summary is missing its lane inventory');
  fs.rmSync(root, { recursive: true, force: true });
  console.log('check-assets self-test passed (10 cases)');
}

if (require.main === module) {
  if (process.argv.includes('--self-test')) {
    selfTest();
  } else {
    const errors = checkAssets({ summary: process.argv.includes('--summary') });
    process.exit(errors.length ? 1 : 0);
  }
}

module.exports = { checkAssets, references, globToRegExp };
