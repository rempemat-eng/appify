import assert from 'node:assert/strict';
import { worldLand } from './world-land';
import { ROUTES_BETWEEN, routeFootprints, worldRoutes } from './world-routes';

/**
 * Lane G's land plan (lib/world-land.ts, from scripts/art/world_land.py): the land
 * between the regions, the world's edges in three layers and the land beyond (world plan
 * v5.3, 5.5; docs/vision/regions/routes-thresholds-edges.md, section 4). Measured again
 * here from the exported rows.
 */

const { cell, size, kinds, grounds } = worldLand;
const [W, H] = size;

function unpack(rows: readonly string[]): Int16Array {
  const out = new Int16Array(W * H);
  rows.forEach((row, y) => {
    let x = 0;
    for (const run of row.split('.')) {
      const [v, n] = run.split('x');
      const count = n === undefined ? 1 : Number(n);
      out.fill(Number(v) - 1, y * W + x, y * W + x + count);
      x += count;
    }
    assert.equal(x, W, `row ${y} is ${W} cells`);
  });
  assert.equal(rows.length, H, `${H} rows`);
  return out;
}

const kind = unpack(worldLand.kindRows);
const ground = unpack(worldLand.groundRows);
const K = Object.fromEntries(kinds.map((k, i) => [k, i])) as Record<string, number>;
const at = (x: number, y: number) => y * W + x;
const walkable = (k: number) => k === K.land || k === K.fade;

function ownerAt(px: number, py: number): string {
  for (const f of routeFootprints) {
    const [x0, y0, x1, y1] = f.box;
    if (px >= x0 && px < x1 && py >= y0 && py < y1) return f.owner;
  }
  return ROUTES_BETWEEN;
}

// --- a lane's cells are its own; lane G's cells are classified ---
let laneG = 0;
for (let y = 0; y < H; y++)
  for (let x = 0; x < W; x++) {
    const own = ownerAt(x * cell + cell / 2, y * cell + cell / 2);
    const k = kind[at(x, y)];
    if (own === ROUTES_BETWEEN) {
      laneG++;
      assert.notEqual(k, K.lane, `cell (${x}, ${y}) is lane G's and classified`);
      assert.ok(
        ground[at(x, y)] >= 0 && ground[at(x, y)] < grounds.length,
        `cell (${x}, ${y}) has a ground`,
      );
    } else assert.equal(k, K.lane, `cell (${x}, ${y}) is ${own}'s, not lane G's`);
  }
assert.ok(laneG > 0, 'lane G has land');

// --- every route vertex on lane G's land stands on walkable ground ---
for (const r of worldRoutes)
  for (const [px, py] of r.points) {
    const cx = Math.min(W - 1, Math.floor(px / cell));
    const cy = Math.min(H - 1, Math.floor(py / cell));
    if (ownerAt(cx * cell + cell / 2, cy * cell + cell / 2) !== ROUTES_BETWEEN) continue;
    assert.ok(walkable(kind[at(cx, cy)]), `${r.name}: (${px}, ${py}) on walkable land`);
  }

// --- the layers: the walkable land never touches the thin-out or the beyond; the wall is
// at least 64 px deep between them (plan 5.5) ---
const INF = 1e9;
// chamfer distance in cells (steps 1 and sqrt 2), two sweeps: the generator's own metric
const dist = new Float64Array(W * H).fill(INF);
for (let i = 0; i < W * H; i++) if (walkable(kind[i])) dist[i] = 0;
const R2 = Math.SQRT2;
for (let y = 0; y < H; y++)
  for (let x = 0; x < W; x++) {
    let d = dist[at(x, y)];
    if (x > 0) d = Math.min(d, dist[at(x - 1, y)] + 1);
    if (y > 0) {
      d = Math.min(d, dist[at(x, y - 1)] + 1);
      if (x > 0) d = Math.min(d, dist[at(x - 1, y - 1)] + R2);
      if (x < W - 1) d = Math.min(d, dist[at(x + 1, y - 1)] + R2);
    }
    dist[at(x, y)] = d;
  }
for (let y = H - 1; y >= 0; y--)
  for (let x = W - 1; x >= 0; x--) {
    let d = dist[at(x, y)];
    if (x < W - 1) d = Math.min(d, dist[at(x + 1, y)] + 1);
    if (y < H - 1) {
      d = Math.min(d, dist[at(x, y + 1)] + 1);
      if (x < W - 1) d = Math.min(d, dist[at(x + 1, y + 1)] + R2);
      if (x > 0) d = Math.min(d, dist[at(x - 1, y + 1)] + R2);
    }
    dist[at(x, y)] = d;
  }
for (let i = 0; i < W * H; i++) {
  if (kind[i] !== K.thin && kind[i] !== K.beyond) continue;
  assert.ok(
    dist[i] * cell >= 64,
    `the wall is 64 px or more before the beyond (cell ${i % W}, ${Math.floor(i / W)})`,
  );
}

// --- the fade stays within 160 px of the walkable land's edge, and only where there is a wall ---
for (let y = 1; y < H - 1; y++)
  for (let x = 1; x < W - 1; x++) {
    if (kind[at(x, y)] !== K.fade) continue;
    let near = false;
    for (let dy = -21; dy <= 21 && !near; dy++)
      for (let dx = -21; dx <= 21 && !near; dx++) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const k = kind[at(nx, ny)];
        if (k === K.wall || k === K.sea) near = true;
      }
    assert.ok(near, `fade at (${x}, ${y}) is near its wall or the sea`);
  }

// --- the edges: who draws each, on a lane's side, and a thin-out or the sea behind it ---
const lanes = new Set([...routeFootprints.map((f) => f.owner), ROUTES_BETWEEN]);
for (const e of worldLand.edges) {
  assert.ok(lanes.has(e.by), `${e.id}: drawn by a lane`);
  assert.ok(grounds.includes(e.ground), `${e.id}: its ground is known`);
  if (!e.line) continue;
  for (const [x, y] of e.line) assert.ok(x % 8 === 0 && y % 8 === 0, `${e.id}: on the grid`);
}

const counts = Object.fromEntries(kinds.map((k) => [k, 0])) as Record<string, number>;
for (let i = 0; i < W * H; i++) counts[kinds[kind[i]]]++;
console.log(
  `world-land: ${laneG} cells of lane G: ` +
    kinds
      .filter((k) => k !== 'lane')
      .map((k) => `${k} ${counts[k]}`)
      .join(', ') +
    ': ok',
);
