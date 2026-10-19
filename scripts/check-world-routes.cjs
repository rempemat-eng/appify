/* C27: named walking circuits on the real combined grids, not an atlas graph.
 * Only image-free generated data and actual pure movement helpers are loaded.
 * This does not certify painted bridges/rails, runtime navigation or device input.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const root = path.join(__dirname, '..');
const allowed = new Set(['garden-map', 'garden-path', 'zone-maps', 'region-walk']);
const cache = new Map();
function load(name) {
  assert.ok(allowed.has(name), 'no UI, asset or network module substitution: ' + name);
  if (cache.has(name)) return cache.get(name).exports;
  const file = path.join(root, 'lib', name + '.ts');
  const module = { exports: {} };
  cache.set(name, module);
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  vm.runInNewContext(
    code,
    {
      module,
      exports: module.exports,
      require(id) {
        assert.match(id, /^(\.\/|@\/lib\/)[a-z-]+$/);
        return load(id.replace(/^(\.\/|@\/lib\/)/, ''));
      },
    },
    { filename: file },
  );
  return module.exports;
}
const { makeWalkGrid } = load('garden-path');
const { gardenAnchors } = load('garden-map');
const { zoneMaps, zonePorts } = load('zone-maps');
const { regionWalk, regionTiles, tileOrigin, TILE } = load('region-walk');

// Names are the approved itinerary. Geometry is always read from current exports.
const circuits = [
  ['valley-west', 'valley', ['garden', 'woodland', 'halt', 'town', 'garden']],
  ['valley-east', 'valley', ['garden', 'riverside', 'park', 'town', 'garden']],
  ['valley-coast', 'valley', ['town', 'park', 'headland', 'harbour', 'town']],
  ['frostline', 'valley', ['ridge', 'hollow', 'snowmelt', 'saddle', 'ridge']],
  ['summit-spur', 'valley', ['saddle', 'summit', 'saddle']],
  ['sunstone', 'west', ['oasis', 'gulch', 'scorch', 'hearthold', 'caldera', 'springs']],
  ['isles', 'isles', ['landing', 'rainforest', 'headwaters', 'cove', 'landing']],
];
const anchors = {
  garden: 'start',
  woodland: 'clearing',
  halt: 'platform',
  town: 'well',
  riverside: 'mill',
  park: 'fountain',
  headland: 'tower',
  harbour: 'market',
  ridge: 'tarn',
  hollow: 'clearing',
  snowmelt: 'shore',
  saddle: 'fork',
  summit: 'scope',
  oasis: 'pool',
  gulch: 'street',
  scorch: 'track',
  hearthold: 'courtyard',
  caldera: 'forge',
  springs: 'pools',
  landing: 'pier',
  rainforest: 'bridge',
  headwaters: 'pool',
  cove: 'beach',
};
function realRegion(region) {
  const tiles = regionTiles(region).map((tile) => ({ ...tile, ...tileOrigin(region, tile) }));
  const points = Object.fromEntries(
    tiles.map((tile) => {
      const name = anchors[tile.id];
      const local = tile.id === 'garden' ? gardenAnchors.start : zoneMaps[tile.id].stands[name];
      return [
        tile.id,
        local && {
          x: tile.x + (Array.isArray(local) ? local[0] : local.x),
          y: tile.y + (Array.isArray(local) ? local[1] : local.y),
        },
      ];
    }),
  );
  return { rows: regionWalk(region), tiles, points, ports: zonePorts, ...TILE };
}
function tileFor(data, cx, cy) {
  const x = cx * data.cell + data.cell / 2;
  const y = cy * data.cell + data.cell / 2;
  return data.tiles.find(
    (t) => x >= t.x && x < t.x + data.width && y >= t.y && y < t.y + data.height,
  )?.id;
}
function portFor(data, a, b) {
  return data.ports[a + '|' + b] ?? data.ports[b + '|' + a];
}
function leg(data, a, b) {
  const label = a + ' -> ' + b;
  const ta = data.tiles.find((t) => t.id === a);
  const tb = data.tiles.find((t) => t.id === b);
  assert.ok(ta && tb, label + ': both zones exist');
  assert.equal(
    Math.abs(ta.col - tb.col) + Math.abs(ta.row - tb.row),
    1,
    label + ': consecutive zones must share an edge',
  );
  const port = portFor(data, a, b);
  assert.ok(
    port && port.span !== null && port.span[1] > port.span[0],
    label + ': a positive open port must be declared',
  );
  const from = data.points[a],
    to = data.points[b];
  assert.ok(
    from && to && [from.x, from.y, to.x, to.y].every(Number.isFinite),
    label + ': named stands must exist',
  );
  // A route cannot silently go round the far side of the loop to pass a broken seam.
  const rows = data.rows.map((row, cy) =>
    [...row].map((ch, cx) => ([a, b].includes(tileFor(data, cx, cy)) ? ch : '#')).join(''),
  );
  const cols = rows[0].length;
  assert.ok(
    rows.every((row) => row.length === cols && /^[.#]+$/.test(row)),
    label + ': rectangular walk rows',
  );
  const grid = makeWalkGrid(rows, { cell: data.cell, width: cols * data.cell, start: from });
  const fc = grid.toCell(from),
    tc = grid.toCell(to);
  // findPath intentionally snaps blocked taps. A check of a stand must not do that.
  for (const [zone, point, cell] of [
    [a, from, fc],
    [b, to, tc],
  ]) {
    assert.ok(
      point.x >= 0 &&
        point.y >= 0 &&
        point.x < cols * data.cell &&
        point.y < rows.length * data.cell &&
        tileFor(data, cell.cx, cell.cy) === zone &&
        grid.walkable(cell.cx, cell.cy),
      label + ': ' + zone + ' named stand is open, without snapping',
    );
  }
  const route = grid.findPath(from, to);
  assert.ok(route.length, label + ': no direct walk through the two zones');
  const end = grid.toCell(route[route.length - 1]);
  assert.ok(end.cx === tc.cx && end.cy === tc.cy, label + ': path ends in exact target cell');
  let prev = fc,
    crossings = 0;
  for (const p of route) {
    const next = grid.toCell(p);
    const dx = next.cx - prev.cx,
      dy = next.cy - prev.cy;
    assert.ok(
      dx === 0 || dy === 0 || Math.abs(dx) === Math.abs(dy),
      label + ': path segments follow grid directions',
    );
    const sx = Math.sign(dx),
      sy = Math.sign(dy);
    const steps = Math.max(Math.abs(dx), Math.abs(dy));
    for (let step = 0; step < steps; step++) {
      const nx = prev.cx + sx,
        ny = prev.cy + sy;
      assert.ok(grid.walkable(nx, ny), label + ': each path cell is open');
      if (sx && sy)
        assert.ok(
          grid.walkable(prev.cx + sx, prev.cy) && grid.walkable(prev.cx, prev.cy + sy),
          label + ': no diagonal corner cutting',
        );
      const before = tileFor(data, prev.cx, prev.cy),
        after = tileFor(data, nx, ny);
      if (before !== after) {
        assert.ok(
          [a, b].includes(before) && [a, b].includes(after),
          label + ': never detours into another zone',
        );
        const along =
          ta.col !== tb.col
            ? ny * data.cell + data.cell / 2 - ta.y
            : nx * data.cell + data.cell / 2 - ta.x;
        assert.ok(
          along >= port.span[0] && along < port.span[1],
          label + ': crossing lies inside declared port',
        );
        crossings++;
      }
      prev = { cx: nx, cy: ny };
    }
  }
  assert.ok(crossings > 0, label + ': path really crosses intended seam');
  return crossings;
}

// The same auditor must reject hand-made bad maps before it sees production data.
let fixtures = 0;
function reject(data, a, b, reason) {
  assert.throws(() => leg(data, a, b), reason);
  fixtures++;
}
function square() {
  return {
    cell: 4,
    width: 16,
    height: 16,
    rows: Array(8).fill('.'.repeat(8)),
    tiles: [
      { id: 'a', col: 0, row: 0, x: 0, y: 0 },
      { id: 'b', col: 1, row: 0, x: 16, y: 0 },
      { id: 'c', col: 0, row: 1, x: 0, y: 16 },
      { id: 'd', col: 1, row: 1, x: 16, y: 16 },
    ],
    points: { a: { x: 6, y: 6 }, b: { x: 26, y: 6 }, d: { x: 26, y: 26 } },
    ports: { 'a|b': { span: [0, 16] }, 'a|d': { span: [0, 16] } },
  };
}
{
  const good = square();
  assert.ok(leg(good, 'a', 'b') > 0);
  fixtures++;
  assert.ok(leg(good, 'b', 'a') > 0);
  fixtures++;
  const blocked = square();
  blocked.rows = blocked.rows.map((row, y) => (y < 4 ? row.slice(0, 4) + '#' + row.slice(5) : row));
  const full = makeWalkGrid(blocked.rows, { cell: 4, width: 32, start: blocked.points.a });
  assert.ok(
    full.findPath(blocked.points.a, blocked.points.b).length,
    'blocked-seam control still reaches b by a c/d detour',
  );
  fixtures++;
  reject(blocked, 'a', 'b', /no direct walk/);
  reject(blocked, 'b', 'a', /no direct walk/);
  const target = square();
  target.rows[1] = '......#.';
  reject(target, 'a', 'b', /without snapping/);
  const start = square();
  start.rows[1] = '.#......';
  reject(start, 'a', 'b', /without snapping/);
  const closed = square();
  closed.ports['a|b'].span = null;
  reject(closed, 'a', 'b', /positive open port/);
  const missing = square();
  delete missing.ports['a|b'];
  reject(missing, 'a', 'b', /positive open port/);
  const narrow = square();
  narrow.ports['a|b'].span = [8, 16];
  reject(narrow, 'a', 'b', /inside declared port/);
  const absent = square();
  delete absent.points.b;
  reject(absent, 'a', 'b', /named stands/);
  reject(square(), 'a', 'd', /share an edge/);
  const outside = square();
  outside.points.b.x = 1000;
  reject(outside, 'a', 'b', /without snapping/);
  const corner = square();
  corner.rows = Array(8).fill('########');
  corner.rows[1] = '###.####';
  corner.rows[2] = '####.###';
  corner.points = { a: { x: 14, y: 6 }, b: { x: 18, y: 10 } };
  reject(corner, 'a', 'b', /no direct walk/);
  const invalid = square();
  invalid.rows[0] = '...';
  reject(invalid, 'a', 'b', /rectangular walk rows/);
}
console.log('World route diagnostics: ' + fixtures + ' positive/negative controls pass.');
const regions = new Map();
const failures = [];
let legs = 0;
for (const [name, region, zones] of circuits) {
  if (!regions.has(region)) regions.set(region, realRegion(region));
  const data = regions.get(region);
  for (let i = 1; i < zones.length; i++) {
    // Both directions: each named itinerary must also let the player walk back.
    for (const [a, b] of [
      [zones[i - 1], zones[i]],
      [zones[i], zones[i - 1]],
    ]) {
      try {
        leg(data, a, b);
        legs++;
      } catch (error) {
        failures.push(name + ' (' + region + '): ' + error.message);
      }
    }
  }
  console.log(name + ': ' + zones.join(' -> '));
}
if (failures.length) {
  console.error('World route FAIL:\n' + failures.map((s) => '- ' + s).join('\n'));
  process.exitCode = 1;
} else {
  console.log(
    'World routes: ' +
      circuits.length +
      ' itineraries, ' +
      legs +
      ' directed legs pass on current generated grids.',
  );
}
