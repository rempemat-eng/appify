'use strict';

// C23's exported-data slice. This deliberately does not execute the renderer or
// infer missing rails, bridge supports, climate, doors or height from sprite names.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const TRUNKED = [
  'tree',
  'pine',
  'willow',
  'acacia',
  'palm',
  'snag',
  'lamp',
  'light',
  'pole',
  'post',
];
const PLACEMENTS = new Set(['ground', 'floating', 'wet', 'supported', 'overhead']);
const fail = (message) => {
  throw new Error('World logic export: ' + message);
};
const finite = (n) => typeof n === 'number' && Number.isFinite(n);
const point = (p) => Array.isArray(p) && p.length === 2 && p.every(finite);
const neighbours = (x, y) => [
  [x - 1, y],
  [x + 1, y],
  [x, y - 1],
  [x, y + 1],
];

function readWorld(root) {
  const file = path.join(root, 'lib/zone-maps.ts');
  const source = fs.readFileSync(file, 'utf8');
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    fileName: file,
  }).outputText;
  const exports = {};
  // Generated PNG imports are opaque data here, never decoded or executed.
  vm.runInNewContext(
    compiled,
    {
      exports,
      require: (name) => {
        if (name.startsWith('../assets/') && name.endsWith('.png')) return name;
        throw new Error('Unexpected generated-map import: ' + name);
      },
    },
    { filename: file, timeout: 5000 },
  );
  return exports;
}

function inspectWorld(data) {
  const {
    ZONE,
    zoneIds,
    zoneMaps,
    zoneTerrain,
    zonePlacement,
    regionLayout,
    zonePorts,
    zoneOverhead,
  } = data;
  if (
    !ZONE ||
    ![ZONE.width, ZONE.height, ZONE.cell].every((n) => Number.isSafeInteger(n) && n > 0) ||
    ZONE.width % ZONE.cell ||
    ZONE.height % ZONE.cell
  )
    fail('invalid dimensions');
  const cols = ZONE.width / ZONE.cell,
    rows = ZONE.height / ZONE.cell,
    cell = ZONE.cell;
  if (
    !Array.isArray(zoneIds) ||
    !zoneIds.length ||
    zoneIds.some((id) => typeof id !== 'string') ||
    new Set(zoneIds).size !== zoneIds.length
  )
    fail('invalid zone IDs');
  for (const [name, value] of Object.entries({
    zoneMaps,
    zoneTerrain,
    zonePlacement,
    regionLayout,
    zonePorts,
  })) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) fail('missing ' + name);
  }
  if (!Array.isArray(zoneOverhead) || zoneOverhead.some((id) => typeof id !== 'string'))
    fail('invalid overhead list');
  if (Object.values(zonePlacement).some((p) => !PLACEMENTS.has(p))) fail('unknown placement type');
  const ids = new Set(zoneIds),
    mapped = new Set(),
    adjacent = new Map(),
    findings = [];
  const overhead = new Set(zoneOverhead);
  const coverage = {
    zones: zoneIds.length,
    objects: 0,
    footprints: 0,
    pathComponents: 0,
    seams: 0,
    skippedSupported: 0,
    skippedWet: 0,
    skippedOverhead: 0,
    skippedEmptyFootprints: 0,
    missingTerrain: [],
    skippedSeams: [],
    unsupported: [
      'drawn bridge supports and both bridge abutments (rule 5 / part of 2)',
      'path endpoints, explicit nodes and frame/exit semantics (parts of 6/7)',
      'full climate/elevation/contact taxonomy (rule 9)',
      'rail/frame continuity, actual ground pixels and tone (parts of 10)',
      'door identities and interaction standing-point associations (rule 11)',
    ],
  };
  const add = (zone, kind, what, box, message) => findings.push({ zone, kind, what, box, message });
  const grid = (value, id, alphabet) => {
    if (
      !Array.isArray(value) ||
      value.length !== rows ||
      value.some(
        (row) =>
          typeof row !== 'string' ||
          row.length !== cols ||
          row.split('').some((ch) => !alphabet.includes(ch)),
      )
    )
      fail('invalid grid ' + id);
  };
  for (const [name, value] of Object.entries({ zoneMaps, zoneTerrain })) {
    if (Object.keys(value).some((id) => !ids.has(id))) fail('extra zone in ' + name);
  }
  for (const id of zoneIds) {
    const z = zoneMaps[id],
      terrain = zoneTerrain[id];
    if (!z) fail('missing zone ' + id);
    grid(z.walk, id + '.walk', '.#');
    // These are the five classes the current classifier actually exports. Fail
    // closed on a taxonomy change until the checks and coverage are updated.
    grid(terrain, id + '.terrain', '~!^=.');
    if (
      !z.stands ||
      typeof z.stands !== 'object' ||
      Array.isArray(z.stands) ||
      Object.values(z.stands).some(
        (p) => !point(p) || p[0] < 0 || p[0] >= ZONE.width || p[1] < 0 || p[1] >= ZONE.height,
      )
    )
      fail('invalid stands ' + id);
    if (!Array.isArray(z.objects)) fail('invalid objects ' + id);
    const objectIds = new Set();
    for (const obj of z.objects) {
      if (
        !Array.isArray(obj) ||
        obj.length !== 6 ||
        typeof obj[0] !== 'string' ||
        typeof obj[1] !== 'string' ||
        !obj.slice(2).every(finite) ||
        obj[4] <= 0 ||
        obj[5] <= 0 ||
        objectIds.has(obj[0])
      )
        fail('invalid object in ' + id);
      objectIds.add(obj[0]);
    }
  }
  for (const [region, layout] of Object.entries(regionLayout)) {
    if (!layout || typeof layout !== 'object' || Array.isArray(layout))
      fail('invalid layout ' + region);
    const occupied = new Set();
    for (const [id, pos] of Object.entries(layout)) {
      if (
        (!ids.has(id) && id !== 'garden') ||
        mapped.has(id) ||
        !point(pos) ||
        !pos.every(Number.isSafeInteger) ||
        occupied.has(pos.join(','))
      )
        fail('invalid tile ' + region + '/' + id);
      mapped.add(id);
      occupied.add(pos.join(','));
      if (!zoneTerrain[id]) coverage.missingTerrain.push(id);
    }
    for (const [a, pa] of Object.entries(layout))
      for (const [b, pb] of Object.entries(layout)) {
        const side =
          pb[0] === pa[0] + 1 && pb[1] === pa[1]
            ? 'east'
            : pb[0] === pa[0] && pb[1] === pa[1] + 1
              ? 'south'
              : null;
        if (side) adjacent.set(a + '|' + b, { a, b, side });
      }
  }
  if (zoneIds.some((id) => !mapped.has(id))) fail('unmapped zone');
  for (const [key, port] of Object.entries(zonePorts)) {
    const edge = adjacent.get(key);
    if (!edge || !port || typeof port.frame !== 'string') fail('invalid port ' + key);
    const limit = edge.side === 'east' ? ZONE.height : ZONE.width;
    if (
      port.span !== null &&
      (!point(port.span) ||
        !port.span.every(Number.isSafeInteger) ||
        port.span[0] < 0 ||
        port.span[1] > limit ||
        port.span[0] >= port.span[1])
    )
      fail('invalid port span ' + key);
  }
  if ([...adjacent.keys()].some((key) => !Object.hasOwn(zonePorts, key)))
    fail('undeclared adjacent seam');

  for (const id of zoneIds) {
    const z = zoneMaps[id],
      terrain = zoneTerrain[id],
      nearProp = new Set();
    for (const [oid, key, ox, y, ow, h] of z.objects) {
      coverage.objects++;
      // This node-proximity proxy is intentionally the same as world_lint.py,
      // not proof of a real door or purpose for an object.
      for (let cy = Math.floor((y + h - 10) / cell); cy < Math.floor((y + h + 12) / cell); cy++)
        for (let cx = Math.floor((ox - 8) / cell); cx < Math.floor((ox + ow + 8) / cell); cx++)
          nearProp.add(cx + ',' + cy);
      const placement = overhead.has(key) ? 'overhead' : (zonePlacement[key] ?? 'ground');
      if (placement === 'overhead') {
        coverage.skippedOverhead++;
        continue;
      }
      if (placement === 'supported') {
        coverage.skippedSupported++;
        continue;
      }
      if (placement === 'wet') {
        coverage.skippedWet++;
        continue;
      }
      let x = ox,
        w = ow,
        foot = w > 60 ? 20 : 6;
      if (TRUNKED.some((s) => key.includes(s))) {
        x += Math.floor((w * 3) / 8);
        w = Math.max(4, Math.floor(w / 4));
        foot = 8;
      }
      const cells = [];
      for (let cy = Math.floor((y + h - foot) / cell); cy < Math.floor((y + h) / cell); cy++)
        for (
          let cx = Math.floor((x + 1) / cell);
          cx < Math.max(Math.floor((x + 1) / cell) + 1, Math.floor((x + w - 1) / cell));
          cx++
        )
          if (cx >= 0 && cx < cols && cy >= 0 && cy < rows) cells.push(terrain[cy][cx]);
      if (!cells.length) {
        coverage.skippedEmptyFootprints++;
        continue;
      }
      coverage.footprints++;
      const wet = cells.filter((ch) => ch === '~').length / cells.length;
      const hot = cells.filter((ch) => ch === '!').length / cells.length;
      if (placement === 'floating' && wet < 0.5)
        add(id, 'floating-on-land', oid, [ox, y, ow, h], key + ' floats, but stands on land');
      else if (placement !== 'floating' && wet > 0.34)
        add(id, 'ground-on-water', oid, [ox, y, ow, h], key + ' stands in water');
      else if (placement !== 'floating' && hot > 0.2)
        add(id, 'ground-on-lava', oid, [ox, y, ow, h], key + ' stands in lava');
    }
    const nodes = new Set(
      Object.values(z.stands).map(([x, y]) => Math.floor(x / cell) + ',' + Math.floor(y / cell)),
    );
    const seen = new Set();
    for (let y = 0; y < rows; y++)
      for (let x = 0; x < cols; x++) {
        const key = x + ',' + y;
        if (terrain[y][x] !== '=' || seen.has(key)) continue;
        const q = [[x, y]];
        seen.add(key);
        for (let i = 0; i < q.length; i++)
          for (const [nx, ny] of neighbours(...q[i])) {
            const next = nx + ',' + ny;
            if (
              nx >= 0 &&
              nx < cols &&
              ny >= 0 &&
              ny < rows &&
              terrain[ny][nx] === '=' &&
              !seen.has(next)
            ) {
              seen.add(next);
              q.push([nx, ny]);
            }
          }
        coverage.pathComponents++;
        if (
          q.length < 12 ||
          q.some(
            ([cx, cy]) =>
              cx === 0 ||
              cy === 0 ||
              cx === cols - 1 ||
              cy === rows - 1 ||
              nodes.has(cx + ',' + cy) ||
              nearProp.has(cx + ',' + cy),
          )
        )
          continue;
        const xs = q.map((p) => p[0]),
          ys = q.map((p) => p[1]);
        const box = [
          Math.min(...xs) * cell,
          Math.min(...ys) * cell,
          (Math.max(...xs) - Math.min(...xs) + 1) * cell,
          (Math.max(...ys) - Math.min(...ys) + 1) * cell,
        ];
        add(
          id,
          'path-to-nowhere',
          'path@' + box[0] + ',' + box[1],
          box,
          'path component reaches no edge, stand or prop proxy',
        );
      }
  }
  const edgeStrip = (terrain, side) =>
    side === 'east'
      ? terrain.map((r) => new Set(r.slice(-3)))
      : side === 'west'
        ? terrain.map((r) => new Set(r.slice(0, 3)))
        : Array.from(
            { length: cols },
            (_, x) =>
              new Set(
                (side === 'south' ? terrain.slice(-3) : terrain.slice(0, 3)).map((r) => r[x]),
              ),
          );
  for (const [key, { a, b, side }] of adjacent) {
    if (!zoneTerrain[a] || !zoneTerrain[b]) {
      coverage.skippedSeams.push(key); // garden has no exported semantic layer
      continue;
    }
    coverage.seams++;
    const ea = edgeStrip(zoneTerrain[a], side),
      eb = edgeStrip(zoneTerrain[b], side === 'east' ? 'west' : 'north');
    for (const [ch, kind] of [
      ['~', 'seam-water'],
      ['=', 'seam-path'],
      ['!', 'seam-lava'],
    ]) {
      let start = null;
      for (let i = 0; i <= ea.length; i++) {
        const bad = i < ea.length && ea[i].has(ch) !== eb[i].has(ch);
        if (bad && start === null) start = i;
        if (!bad && start !== null) {
          if (i - start >= 4)
            add(
              a,
              kind,
              key,
              [side, [start * cell, i * cell]],
              ch + ' stops at the ' + side + ' seam with ' + b,
            );
          start = null;
        }
      }
    }
  }
  findings.sort((a, b) =>
    JSON.stringify([a.zone, a.kind, a.what, a.box]).localeCompare(
      JSON.stringify([b.zone, b.kind, b.what, b.box]),
    ),
  );
  return { findings, coverage };
}

function settleFindings(findings, known) {
  if (!Array.isArray(known)) fail('known findings must be a list');
  const used = new Set(),
    accepted = [],
    unexpected = [];
  for (const entry of known) {
    if (
      !entry ||
      typeof entry.reason !== 'string' ||
      !entry.reason.trim() ||
      typeof entry.zone !== 'string' ||
      !entry.zone ||
      typeof entry.kind !== 'string' ||
      !entry.kind ||
      typeof entry.what !== 'string' ||
      !entry.what ||
      !Array.isArray(entry.box)
    )
      fail('invalid known finding');
    const identity = JSON.stringify([entry.zone, entry.kind, entry.what, entry.box]);
    if (used.has(identity)) fail('duplicate known finding');
    used.add(identity);
  }
  for (const finding of findings) {
    const entry = known.find(
      (k) =>
        k.zone === finding.zone &&
        k.kind === finding.kind &&
        k.what === finding.what &&
        JSON.stringify(k.box) === JSON.stringify(finding.box),
    );
    (entry ? accepted : unexpected).push(finding);
  }
  const stale = known.filter(
    (k) =>
      !accepted.some(
        (f) =>
          f.zone === k.zone &&
          f.kind === k.kind &&
          f.what === k.what &&
          JSON.stringify(f.box) === JSON.stringify(k.box),
      ),
  );
  return { accepted, unexpected, stale };
}

function main() {
  try {
    const root = path.resolve(__dirname, '..');
    const report = inspectWorld(readWorld(root));
    const known = JSON.parse(
      fs.readFileSync(path.join(__dirname, 'world-logic-known.json'), 'utf8'),
    );
    const status = settleFindings(report.findings, known);
    if (process.argv.includes('--json'))
      console.log(JSON.stringify({ ...report, ...status }, null, 2));
    else {
      console.log(
        'World logic exported-data slice:',
        report.findings.length,
        'findings;',
        report.coverage.zones,
        'zones;',
        report.coverage.seams,
        'semantic seams.',
      );
      for (const f of report.findings) console.log(JSON.stringify(f));
      console.log('Coverage and limits:', JSON.stringify(report.coverage));
      for (const k of status.stale) console.error('Remove stale known finding:', JSON.stringify(k));
    }
    if (status.unexpected.length || status.stale.length) process.exitCode = 1;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
module.exports = { readWorld, inspectWorld, settleFindings };
if (require.main === module) main();
