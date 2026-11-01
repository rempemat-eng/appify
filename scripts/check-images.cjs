#!/usr/bin/env node
// Report-only RGBA estimates. Does not import/execute the app or decode image pixels.
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');

const extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'];
const surfaces = {
  'Onboarding / nap / welcome back': ['components/game-overlays.tsx'],
  'Menu / companions': ['components/game-menus.tsx'],
  Battle: ['components/game-battle.tsx'],
  'Mission worlds': ['components/world-scene.tsx'],
};
const firstLoadRoutes = {
  Hub: 'app/(tabs)/index.tsx',
  World: 'app/(tabs)/world.tsx',
};
const slash = (s) => s.split(path.sep).join('/');
const byPath = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
const sourceFile = (p) =>
  extensions.includes(path.extname(p)) && !/\.(test|spec|d)\.[^.]+$/.test(p);

function category(p) {
  if (/^assets\/garden\/ground[^/]*\.png$/i.test(p)) return 'Garden / ground';
  if (p.startsWith('assets/garden/water-')) return 'Garden / water frames';
  if (p.startsWith('assets/garden/light-')) return 'Garden / night lights';
  if (p.startsWith('assets/garden/growth/')) return 'Garden / growth sprites';
  if (p.startsWith('assets/garden/')) return 'Garden / prop sprites';
  if (p.startsWith('assets/worlds/props/')) return 'Worlds / shared prop sprites';
  if (p.startsWith('assets/worlds/')) return 'Worlds / ' + p.split('/')[2];
  if (p.startsWith('assets/world/')) return 'World tiles / ' + p.split('/')[2];
  if (p.startsWith('assets/battle/')) return 'Battle';
  if (p.startsWith('assets/scenes/')) return 'Scene vignettes';
  if (p.startsWith('art/icons/')) return 'UI icons';
  if (/^assets\/(pets|sprites|visitors)\//.test(p)) return 'Character sprites';
  return 'Other imported PNGs';
}

function pngSize(file) {
  const fd = fs.openSync(file, 'r');
  const header = Buffer.alloc(33);
  let count;
  try {
    count = fs.readSync(fd, header, 0, header.length, 0);
  } finally {
    fs.closeSync(fd);
  }
  if (
    count !== 33 ||
    !header.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex')) ||
    header.readUInt32BE(8) !== 13 ||
    header.toString('ascii', 12, 16) !== 'IHDR'
  ) {
    throw new Error('Invalid PNG header: ' + file);
  }
  const width = header.readUInt32BE(16),
    height = header.readUInt32BE(20);
  const decodedBytes = width * height * 4;
  if (
    !width ||
    !height ||
    width > 0x7fffffff ||
    height > 0x7fffffff ||
    !Number.isSafeInteger(decodedBytes)
  ) {
    throw new Error('Invalid/unsafe PNG dimensions: ' + file);
  }
  return { width, height, decodedBytes };
}

function inventory(root, options = {}) {
  root = path.resolve(root);
  const files = new Set();
  function visit(dir) {
    for (const item of fs.readdirSync(path.join(root, dir), { withFileTypes: true })) {
      const rel = slash(path.join(dir, item.name));
      if (item.isSymbolicLink()) throw new Error('Symlink in app source: ' + rel);
      if (item.isDirectory()) visit(rel);
      else if (sourceFile(rel)) files.add(rel);
    }
  }
  for (const dir of ['app', 'components', 'lib']) {
    if (fs.existsSync(path.join(root, dir))) visit(dir);
  }
  const graph = new Map(),
    images = new Map();
  function localPath(from, spec) {
    if (!spec.startsWith('@/') && !spec.startsWith('.')) return null; // packages excluded
    const full = spec.startsWith('@/')
      ? path.resolve(root, spec.slice(2))
      : path.resolve(root, path.dirname(from), spec);
    const rel = slash(path.relative(root, full));
    if (rel.startsWith('../') || path.isAbsolute(rel))
      throw new Error('Import outside repository: ' + spec);
    return rel;
  }
  function edges(from, spec) {
    const rel = localPath(from, spec);
    if (rel === null) return [];
    if (/\.png$/i.test(rel)) {
      const full = path.join(root, rel);
      if (!fs.existsSync(full) || !fs.lstatSync(full).isFile() || fs.realpathSync(full) !== full)
        throw new Error('Missing/non-file PNG: ' + rel);
      if (!images.has(rel))
        images.set(rel, {
          path: rel,
          category: category(rel),
          ...pngSize(full),
          diskBytes: fs.statSync(full).size,
          importedBy: [],
        });
      const owners = images.get(rel).importedBy;
      if (!owners.includes(from)) owners.push(from);
      return [rel];
    }
    // Include all Metro platform variants, not just this computer's platform.
    const found = new Set(files.has(rel) ? [rel] : []);
    for (const suffix of ['', '.web', '.native', '.ios', '.android']) {
      for (const ext of extensions) {
        for (const candidate of [rel + suffix + ext, rel + '/index' + suffix + ext]) {
          if (files.has(candidate)) found.add(candidate);
        }
      }
    }
    if (!found.size && !fs.existsSync(path.join(root, rel)))
      throw new Error('Unresolved local import in ' + from + ': ' + spec);
    return [...found]; // non-code CSS/JSON/audio/etc do not have PNG dependencies
  }
  for (const file of [...files].sort(byPath)) {
    const source = ts.createSourceFile(
      file,
      fs.readFileSync(path.join(root, file), 'utf8'),
      ts.ScriptTarget.Latest,
      true,
    );
    if (source.parseDiagnostics.length) throw new Error('Cannot parse ' + file);
    const refs = new Set();
    function add(spec) {
      for (const edge of edges(file, spec)) refs.add(edge);
    }
    function walk(node) {
      if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) {
        const clause = node.importClause;
        const named = clause?.namedBindings;
        const typeOnly =
          node.isTypeOnly ||
          clause?.isTypeOnly ||
          (!clause?.name &&
            named &&
            ts.isNamedImports(named) &&
            named.elements.length > 0 &&
            named.elements.every((e) => e.isTypeOnly)) ||
          (node.exportClause &&
            ts.isNamedExports(node.exportClause) &&
            node.exportClause.elements.length > 0 &&
            node.exportClause.elements.every((e) => e.isTypeOnly));
        if (!typeOnly && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier))
          add(node.moduleSpecifier.text);
      } else if (
        ts.isImportEqualsDeclaration(node) &&
        !node.isTypeOnly &&
        ts.isExternalModuleReference(node.moduleReference)
      ) {
        const expr = node.moduleReference.expression;
        if (expr && ts.isStringLiteral(expr)) add(expr.text);
      } else if (
        ts.isCallExpression(node) &&
        ((ts.isIdentifier(node.expression) && node.expression.text === 'require') ||
          node.expression.kind === ts.SyntaxKind.ImportKeyword)
      ) {
        const arg = node.arguments[0];
        if (!arg || !(ts.isStringLiteral(arg) || ts.isNoSubstitutionTemplateLiteral(arg))) {
          throw new Error('Dynamic module path cannot be audited: ' + file);
        }
        add(arg.text);
      }
      ts.forEachChild(node, walk);
    }
    walk(source);
    graph.set(file, refs);
  }
  function reachable(roots) {
    const seen = new Set(),
      pngs = new Set();
    function follow(file) {
      if (seen.has(file)) return;
      seen.add(file);
      if (images.has(file)) pngs.add(file);
      else for (const dep of graph.get(file) || []) follow(dep);
    }
    for (const file of roots) {
      if (!files.has(file)) throw new Error('Missing report entry point: ' + file);
      follow(file);
    }
    return [...pngs].sort(byPath);
  }
  const routes = [...files]
    .filter((p) => p.startsWith('app/') && !path.basename(p).startsWith('_'))
    .sort(byPath);
  const shared = [...files].filter((p) => p === 'app/_layout.tsx' || p === 'app/_layout.ts');
  const groups = (paths) => {
    const sums = new Map();
    for (const p of paths) {
      const img = images.get(p),
        row = sums.get(img.category) || {
          category: img.category,
          count: 0,
          decodedBytes: 0,
          diskBytes: 0,
        };
      row.count++;
      row.decodedBytes += img.decodedBytes;
      row.diskBytes += img.diskBytes;
      sums.set(img.category, row);
    }
    return [...sums.values()].sort((a, b) => a.category.localeCompare(b.category));
  };
  const summarize = (name, roots) => {
    const paths = reachable(roots);
    return {
      name,
      roots,
      paths,
      count: paths.length,
      decodedBytes: paths.reduce((n, p) => n + images.get(p).decodedBytes, 0),
      diskBytes: paths.reduce((n, p) => n + images.get(p).diskBytes, 0),
      groups: groups(paths),
      largest: paths
        .map((p) => images.get(p))
        .sort((a, b) => b.diskBytes - a.diskBytes || byPath(a.path, b.path))
        .slice(0, 10)
        .map(({ path: imagePath, diskBytes, decodedBytes }) => ({
          path: imagePath,
          diskBytes,
          decodedBytes,
        })),
    };
  };
  const screens = routes.map((route) => {
    let dir = path.posix.dirname(route);
    const layouts = [];
    while (dir === 'app' || dir.startsWith('app/')) {
      for (const ext of extensions)
        if (files.has(dir + '/_layout' + ext)) layouts.push(dir + '/_layout' + ext);
      dir = path.posix.dirname(dir);
    }
    return summarize(route, [...new Set([route, ...layouts])]);
  });
  for (const [name, roots] of Object.entries(options.surfaces ?? surfaces))
    screens.push(summarize(name, [...new Set([...roots, ...shared])]));
  const firstLoad = Object.entries(firstLoadRoutes).flatMap(([name, route]) => {
    const screen = screens.find((candidate) => candidate.name === route);
    return screen
      ? [
          {
            name,
            route,
            count: screen.count,
            diskBytes: screen.diskBytes,
            decodedBytes: screen.decodedBytes,
            largest: screen.largest,
          },
        ]
      : [];
  });
  const firstLoadBudget = options.firstLoadBudget ?? null;
  if (firstLoadBudget !== null && (!Number.isSafeInteger(firstLoadBudget) || firstLoadBudget < 0))
    throw new Error('firstLoadBudget must be a non-negative safe integer');
  const overBudget = firstLoad.filter((entry) => entry.diskBytes > firstLoadBudget);
  if (firstLoadBudget !== null && overBudget.length)
    throw new Error(
      `First-load PNG budget ${firstLoadBudget} bytes exceeded: ` +
        overBudget.map((entry) => `${entry.name} ${entry.diskBytes}`).join(', '),
    );
  const all = [...images.keys()].sort(byPath);
  return {
    schemaVersion: 2,
    estimate:
      'PNG file bytes and RGBA8 width x height x 4; conservative static import closure, not measured transfer or resident memory',
    images: all.map((p) => ({
      ...images.get(p),
      importedBy: images.get(p).importedBy.sort(byPath),
    })),
    groups: groups(all),
    totalDiskBytes: all.reduce((n, p) => n + images.get(p).diskBytes, 0),
    totalDecodedBytes: all.reduce((n, p) => n + images.get(p).decodedBytes, 0),
    screens,
    firstLoad,
    firstLoadBudget,
  };
}

const mib = (n) => (n / 1048576).toFixed(3);
const mb = (n) => (n / 1000000).toFixed(3);
const cell = (s) => String(s).replaceAll('|', '\\|').replaceAll('\n', ' ');
function markdown(report) {
  const lines = [
    '# Imported PNG decoded-memory report',
    '',
    'Report only — no production first-load budget exists. PNG MB = file bytes / 1,000,000; RGBA8 = width × height × 4 bytes; MiB = 1,048,576 bytes.',
    '',
    'Static import closure includes all catalog entries, animation frames, day/night variants and platform variants. Each path counts once per screen; shared assets count again on other screens. Screen totals are **not additive** and are not measured resident/GPU memory. Shared layouts and global overlays are included. No tree-shaking or conditional-render analysis.',
    '',
    'Repository-owned PNG imports in app/, components/ and lib/ only. Excludes packages, config/splash icons, remote/data URI images and SVG/vector companions and icons; PNG header dimensions only, not pixel/CRC validation or device profiling. Identical screen totals mean shared modules reach the same asset catalogues, not that each screen draws all of them.',
    '',
    '## Unique imported inventory',
    '',
    '| Group | PNGs | PNG bytes | MB | RGBA bytes | MiB |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',
    ...report.groups.map(
      (g) =>
        `| ${cell(g.category)} | ${g.count} | ${g.diskBytes} | ${mb(g.diskBytes)} | ${g.decodedBytes} | ${mib(g.decodedBytes)} |`,
    ),
    `| **Unique total** | **${report.images.length}** | **${report.totalDiskBytes}** | **${mb(report.totalDiskBytes)}** | **${report.totalDecodedBytes}** | **${mib(report.totalDecodedBytes)}** |`,
    '',
    '## Per-screen import envelopes',
    '',
    '| Screen / surface | PNGs | PNG bytes | MB | RGBA bytes | MiB |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',
    ...report.screens.map(
      (s) =>
        `| ${cell(s.name)} | ${s.count} | ${s.diskBytes} | ${mb(s.diskBytes)} | ${s.decodedBytes} | ${mib(s.decodedBytes)} |`,
    ),
    '',
    '## Before the first tap: static PNG upper bounds',
    '',
    'Lane R measured the hub fetching 7–9 MB of pictures within four seconds. The table puts that network observation beside the repository PNG file bytes reachable from each route. The static closure is an upper bound: it includes every catalogue branch and platform variant imported by the route, whether or not the first render requests it. Conversely, the 7–9 MB observation is transferred data and may reflect cache state and non-PNG resources. These quantities diagnose import coupling; neither is a resident-memory measurement.',
    '',
    '| Route | PNGs | Static PNG MB | Decoded MiB | Review measurement | Budget |',
    '| --- | ---: | ---: | ---: | --- | --- |',
    ...report.firstLoad.map(
      (entry) =>
        `| ${cell(entry.name)} (${cell(entry.route)}) | ${entry.count} | ${mb(entry.diskBytes)} | ${mib(entry.decodedBytes)} | ${entry.name === 'Hub' ? '7–9 MB within 4 s' : 'not measured'} | report only |`,
    ),
    '',
  ];
  for (const entry of report.firstLoad)
    lines.push(
      `### ${cell(entry.name)}: ten largest statically reachable PNGs`,
      '',
      '| Path | PNG bytes | MB | Decoded MiB |',
      '| --- | ---: | ---: | ---: |',
      ...entry.largest.map(
        (image) =>
          `| ${cell(image.path)} | ${image.diskBytes} | ${mb(image.diskBytes)} | ${mib(image.decodedBytes)} |`,
      ),
      '',
    );
  for (const s of report.screens)
    lines.push(
      `<details><summary>${cell(s.name)}: categories</summary>`,
      '',
      '| Group | PNGs | PNG bytes | MB | RGBA bytes | MiB |',
      '| --- | ---: | ---: | ---: | ---: | ---: |',
      ...s.groups.map(
        (g) =>
          `| ${cell(g.category)} | ${g.count} | ${g.diskBytes} | ${mb(g.diskBytes)} | ${g.decodedBytes} | ${mib(g.decodedBytes)} |`,
      ),
      '',
      '</details>',
      '',
    );
  lines.push(
    '## Every imported PNG',
    '',
    '| Path | Pixels | PNG bytes | MB | RGBA bytes | MiB | Importers |',
    '| --- | ---: | ---: | ---: | ---: | ---: | --- |',
    ...report.images.map(
      (i) =>
        `| ${cell(i.path)} | ${i.width} × ${i.height} | ${i.diskBytes} | ${mb(i.diskBytes)} | ${i.decodedBytes} | ${mib(i.decodedBytes)} | ${cell(i.importedBy.join(', '))} |`,
    ),
    '',
  );
  return lines.join('\n');
}

function main(args = process.argv.slice(2)) {
  if (args.some((a) => a !== '--json'))
    throw new Error('Usage: node scripts/check-images.cjs [--json]');
  const report = inventory(path.resolve(__dirname, '..'));
  const summary = markdown(report);
  if (process.env.GITHUB_STEP_SUMMARY)
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, summary + '\n');
  process.stdout.write(args.includes('--json') ? JSON.stringify(report, null, 2) + '\n' : summary);
}
if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
module.exports = { category, pngSize, inventory, markdown };
