/**
 * The world canvas, step 2 (docs/vision/region-canvas.md): walking and mounting on the
 * world tiles, checked against the walk over the whole region and against every phone and
 * window size.
 *
 * - the walk read from the tiles is the region's whole walk, and a cell is read the same
 *   one at a time as in a window;
 * - a walk searched in windows reaches wherever a search over the whole region reaches,
 *   and ends in the same cell; forced onto the route graph (a window too small for the
 *   walk) it still gets there;
 * - at every window size the mounted tiles cover the view, a phone mounts at most 12, and
 *   its pictures stay under 25 MiB at 2x as the camera crosses each region, the tiles kept
 *   for the margin included;
 * - tiles meet with no gap at every pixel scale;
 * - every prop whose picture reaches the view is drawn with the mounted tiles;
 * - the area under each stand is its zone, and the name holds along an edge.
 */
import assert from 'node:assert/strict';
import { makeWalkGrid, type Point } from './garden-path';
import { pixelScale, snapToDevice } from './pixel-scale';
import {
  regionBounds,
  regionTiles,
  regionWalk,
  tileAt,
  tileOrigin,
  TILE,
  type RegionId,
} from './region-walk';
import { WORLD_TILE, worldSeams, worldTiles } from './world-canvas';
import {
  areaAt,
  areaWithHysteresis,
  cellOpen,
  chunkFor,
  findWorldPath,
  mountedBytes,
  propsFor,
  routeVia,
  tileKeysNear,
  tilesToMount,
  windowRows,
  worldRegionWalk,
  type RegionBox,
} from './world-walk';
import { regionLayout, zoneMaps } from './zone-maps';

const S = WORLD_TILE.size;
const CELL = WORLD_TILE.cell;
const MiB = 1024 * 1024;
const regions = Object.keys(regionLayout).filter((k): k is RegionId =>
  Object.hasOwn(regionLayout, k),
);

// a small deterministic random, so failures repeat
let seed = 7;
const rand = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;

// ---- the walk read from the tiles ------------------------------------------------------
for (const region of regions) {
  const rows = worldRegionWalk(region);
  const b = regionBounds(region);
  assert.equal(rows.length, b.height / CELL, `${region}: one row per cell`);
  // (with the flag off, regionWalk is the zones' join; the tiles differ only at the seams)
  const joined = regionWalk(region);
  const seams = new Set(
    (worldSeams[region] ?? []).map(
      ([c, r]) =>
        `${c - chunkFor(region).origin[0] / CELL},${r - chunkFor(region).origin[1] / CELL}`,
    ),
  );
  rows.forEach((row, r) => {
    for (let c = 0; c < row.length; c++) {
      if (!seams.has(`${c},${r}`)) assert.equal(row[c], joined[r][c], `${region} ${c},${r}`);
      assert.equal(
        cellOpen(region, c, r),
        row[c] === '.',
        `${region}: cell ${c},${r} one at a time`,
      );
    }
  });
  const w = windowRows(region, -3, 5, 40, 9);
  assert.equal(w[0].slice(0, 3), '###', 'off the chunk is blocked');
  assert.equal(w[0].slice(3), rows[5].slice(0, 40), 'a window is the same cells');
}

// ---- finding a way -----------------------------------------------------------------------
const cellOf = (p: Point) => `${Math.floor(p.x / CELL)},${Math.floor(p.y / CELL)}`;
let pairs = 0;
let viaGraph = 0;
let longest = 0;
for (const region of regions) {
  const rows = worldRegionWalk(region);
  const b = regionBounds(region);
  const full = makeWalkGrid(rows, { cell: CELL, width: b.width, start: { x: 0, y: 0 } });
  const stands: Point[] = [];
  for (const t of regionTiles(region)) {
    if (t.id === 'garden') continue;
    const o = tileOrigin(region, t);
    for (const [x, y] of Object.values(zoneMaps[t.id].stands))
      stands.push({ x: o.x + x, y: o.y + y });
  }
  const points = [...stands];
  // and open ground anywhere (where a companion can stand: a walk never starts in a wall)
  for (let n = 0; points.length < stands.length + 24 && n < 5000; n++) {
    const p = { x: rand() * b.width, y: rand() * b.height };
    if (cellOpen(region, Math.floor(p.x / CELL), Math.floor(p.y / CELL))) points.push(p);
  }
  for (let i = 0; i < points.length; i++)
    for (let j = i + 1; j < points.length; j += 19) {
      const from = points[i];
      const to = points[j];
      const whole = full.findPath(from, to);
      const windowed = findWorldPath(region, from, to);
      pairs++;
      if (!whole.length) {
        assert.equal(windowed.length, 0, `${region}: no way there, and none found`);
        continue;
      }
      assert.ok(windowed.length, `${region}: a way from ${cellOf(from)} to ${cellOf(to)} is found`);
      assert.equal(
        cellOf(windowed[windowed.length - 1]),
        cellOf(whole[whole.length - 1]),
        `${region}: it ends where the whole search ends`,
      );
      longest = Math.max(longest, Math.hypot(to.x - from.x, to.y - from.y));
      // forced onto the route graph: no window can hold the walk
      if (Math.hypot(to.x - from.x, to.y - from.y) > 3 * S && pairs % 2 === 0) {
        const route = routeVia(region, from, to, S);
        if (!route) continue; // (a start the graph's nodes cannot be reached from in a tile)
        const graph = findWorldPath(region, from, to, [S]);
        assert.ok(graph.length, `${region}: the route graph finds a way`);
        assert.equal(
          cellOf(graph[graph.length - 1]),
          cellOf(whole[whole.length - 1]),
          `${region}: by the graph it ends where the whole search ends`,
        );
        viaGraph++;
      }
    }
}
assert.ok(viaGraph >= 10, `the route graph was exercised (${viaGraph} walks)`);

// ---- mounting --------------------------------------------------------------------------------
const sizes: [number, number, number][] = [
  [320, 568, 2],
  [375, 667, 2],
  [390, 844, 3],
  [402, 874, 3],
  [430, 932, 3],
  [768, 1024, 2],
  [1024, 768, 2],
  [1280, 800, 1],
  [1440, 900, 2],
];
let views = 0;
let worstPhone = 0;
let worstCount = 0;
for (const [width, height, dpr] of sizes) {
  const u = pixelScale(width, dpr);
  const vw = width / u;
  const vh = height / u;
  const phone = width <= 430;
  for (const region of regions) {
    const b = regionBounds(region);
    const ch = chunkFor(region);
    // the camera crossing the region in rows, carrying its mounted set (the kept margin)
    let mounted: string[] = [];
    for (let y = -64; y <= Math.max(0, b.height - vh) + 64; y += 56)
      for (let x = -64; x <= Math.max(0, b.width - vw) + 64; x += 56) {
        const view: RegionBox = { x0: x, y0: y, x1: x + vw, y1: y + vh };
        mounted = tilesToMount(region, view, mounted);
        views++;
        for (const k of tileKeysNear(region, view, 0))
          assert.ok(
            mounted.includes(k),
            `${region} at ${width}x${height}: tile ${k} in view is mounted`,
          );
        // every prop whose picture reaches the view draws (checked at phone sizes)
        if (!phone) continue;
        const drawn = new Set(propsFor(region, mounted).map((p) => p.id));
        for (const t of regionTiles(region)) {
          if (t.id === 'garden') continue;
          const o = tileOrigin(region, t);
          for (const [id, , px, py, pw, ph] of zoneMaps[t.id].objects) {
            const X = o.x + px;
            const Y = o.y + py;
            if (X < view.x1 && X + pw > view.x0 && Y < view.y1 && Y + ph > view.y0)
              assert.ok(
                drawn.has(`${t.id}:${id}`),
                `${region}: ${t.id}/${id} reaches the view and draws`,
              );
          }
        }
        if (phone) {
          worstCount = Math.max(worstCount, mounted.length);
          worstPhone = Math.max(worstPhone, mountedBytes(region, mounted));
        }
        void ch;
      }
  }
}
assert.ok(worstCount <= 12, `a phone mounts at most 12 tiles (${worstCount})`);
assert.ok(
  worstPhone <= 25 * MiB,
  `a phone's tiles stay under 25 MiB (${(worstPhone / MiB).toFixed(1)})`,
);

// ---- no gap between tiles at any scale ----------------------------------------------------
for (const [width, , dpr] of [...sizes, [402, 874, 2] as const, [600, 900, 1.5] as const]) {
  const u = pixelScale(width, dpr);
  for (const region of regions) {
    const [ox, oy] = chunkFor(region).origin;
    for (let c = -2; c < 30; c++) {
      const left = snapToDevice((c * S - ox) * u, dpr);
      const next = snapToDevice(((c + 1) * S - ox) * u, dpr);
      const w = snapToDevice(S * u, dpr);
      assert.ok(Math.abs(Math.round(left * dpr) - left * dpr) < 1e-6, 'on a device pixel');
      assert.ok(
        Math.abs(left + w - next) < 1e-6,
        `${region} at ${width}/${dpr}: tile ${c} meets the next`,
      );
      const top = snapToDevice((c * S - oy) * u, dpr);
      assert.ok(
        Math.abs(top + w - snapToDevice(((c + 1) * S - oy) * u, dpr)) < 1e-6,
        `${region}: rows meet`,
      );
    }
  }
}

// ---- areas -----------------------------------------------------------------------------------
for (const region of regions)
  for (const t of regionTiles(region)) {
    if (t.id === 'garden') continue;
    const o = tileOrigin(region, t);
    for (const [s, [x, y]] of Object.entries(zoneMaps[t.id].stands)) {
      assert.equal(
        areaAt(region, o.x + x, o.y + y)?.id,
        tileAt(region, o.x + x, o.y + y)?.id,
        `${t.id}/${s}: its area`,
      );
    }
    // along an edge the name holds within the margin, and changes past it
    const edge = o.x + TILE.width;
    if (tileAt(region, edge + 1, o.y + 100)) {
      assert.equal(
        areaWithHysteresis(region, t.id, edge + 6, o.y + 100, 12)?.id,
        t.id,
        `${t.id}: holds`,
      );
      assert.notEqual(
        areaWithHysteresis(region, t.id, edge + 20, o.y + 100, 12)?.id,
        t.id,
        `${t.id}: lets go`,
      );
    }
  }

const tiles = Object.values(worldTiles).reduce((n, p) => n + Object.keys(p).length, 0);
console.log(
  `world walk: ${pairs} walks searched in windows match the whole-region search (${viaGraph} also by the route graph, ` +
    `longest ${Math.round(longest)} px); ${views} views over ${tiles} tiles at ${sizes.length} window sizes covered; ` +
    `a phone mounts at most ${worstCount} tiles, ${(worstPhone / MiB).toFixed(1)} MiB at ${WORLD_TILE.scale}x.`,
);
