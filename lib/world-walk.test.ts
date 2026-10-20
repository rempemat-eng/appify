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
 * - at every tested window size, cold or warm, the mounted tiles cover the view and stay
 *   within TILE_BUDGET (12 tiles, 25 MiB at 2x, the tiles kept for the margin included):
 *   checked for every set of tiles a view can touch, along both axes through every place a
 *   tile enters or leaves the view, the margin or twice it, on a seeded random walk, at the
 *   warm camera Codex found on #126, and to and fro across tile edges (which settles);
 * - past the tested sizes (a large desktop window) the view is covered, and where its own
 *   tiles reach the budget they are all that mount;
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
  TILE_BUDGET,
  TILE_MOUNT_MARGIN,
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
// The tested window sizes: phones, a tablet both ways round, laptops. TILE_BUDGET holds at
// every one of them.
const sizes: [number, number, number][] = [
  [320, 568, 2],
  [375, 667, 2],
  [375, 812, 2],
  [390, 844, 3],
  [402, 874, 3],
  [430, 932, 3],
  [768, 1024, 2],
  [1024, 768, 2],
  [1280, 800, 1],
  [1440, 900, 2],
];
/** Every tile of the region's plane that a view overlaps (by any area), worked out here
 *  apart from lib/world-walk.ts. `slack` grows the view: the camera is drawn at a whole
 *  CSS px, up to half an art px off the view the tiles are chosen for. */
function tilesInView(region: string, view: RegionBox, slack = 0.5): string[] {
  const ch = chunkFor(region);
  const [ox, oy] = ch.origin;
  const out: string[] = [];
  for (let r = Math.floor((view.y0 - slack + oy) / S); r * S < view.y1 + slack + oy; r++)
    for (let c = Math.floor((view.x0 - slack + ox) / S); c * S < view.x1 + slack + ox; c++)
      if (worldTiles[ch.plane][`${c},${r}`]) out.push(`${c},${r}`);
  return out;
}
let worstCount = 0;
let worstBytes = 0;
/** The budget (TILE_BUDGET) and full cover of the view, at one camera position. */
function checkMounted(region: string, view: RegionBox, mounted: string[], where: string) {
  for (const k of tilesInView(region, view))
    assert.ok(mounted.includes(k), `${where}: tile ${k} in view is mounted`);
  const bytes = mountedBytes(region, mounted);
  assert.ok(
    mounted.length <= TILE_BUDGET.tiles,
    `${where}: ${mounted.length} tiles mounted, at most ${TILE_BUDGET.tiles}`,
  );
  assert.ok(
    bytes <= TILE_BUDGET.bytes,
    `${where}: ${(bytes / MiB).toFixed(3)} MiB mounted, at most ${TILE_BUDGET.bytes / MiB}`,
  );
  assert.equal(new Set(mounted).size, mounted.length, `${where}: no tile twice`);
  worstCount = Math.max(worstCount, mounted.length);
  worstBytes = Math.max(worstBytes, bytes);
}
const viewOf = (width: number, height: number, dpr: number) => {
  const u = pixelScale(width, dpr);
  return [width / u, height / u];
};
/** The camera's range along one axis of a region (a view of length `len` over a span), a
 *  tile past each end. */
const rangeOf = (span: number, len: number): [number, number] => [-S, Math.max(0, span - len) + S];
/**
 * Camera positions along one axis, for a view of length `len` over [lo, hi]: every place
 * where a view edge is `t` px from a tile edge, for each t in `ts` (on either side of the
 * view), and the midpoints between them, sorted. Along that axis, the tiles a view
 * touches, or has within the margin or twice it, change only at those places.
 */
function axisStops(origin: number, len: number, [lo, hi]: [number, number], ts: number[]) {
  const at = new Set([lo, hi]);
  for (let k = Math.floor((lo - 2 * S + origin) / S); k * S - origin <= hi + len + 2 * S; k++) {
    const edge = k * S - origin;
    for (const t of ts) for (const p of [edge + t, edge - len - t]) if (p > lo && p < hi) at.add(p);
  }
  const stops = [...at].sort((a, b) => a - b);
  return stops.flatMap((p, i) => (i ? [(stops[i - 1] + p) / 2, p] : [p]));
}

// What a view alone needs (the tiles within VIEW_SLACK of it, as tilesToMount takes them),
// at every place it can be: every set of tiles a view can touch, at every tested size and
// in every region, fits the budget. (The sets change only where a view edge is 1 px from a
// tile edge, so the stops along each axis, crossed, reach every one of them.)
const viewNeed = { tiles: 0, bytes: 0 };
let viewSets = 0;
for (const [width, height, dpr] of sizes) {
  const [vw, vh] = viewOf(width, height, dpr);
  for (const region of regions) {
    const b = regionBounds(region);
    const [ox, oy] = chunkFor(region).origin;
    const xs = axisStops(ox, vw, rangeOf(b.width, vw), [1]);
    const ys = axisStops(oy, vh, rangeOf(b.height, vh), [1]);
    for (const x of xs)
      for (const y of ys) {
        const own = tilesInView(region, { x0: x, y0: y, x1: x + vw, y1: y + vh }, 1);
        const bytes = mountedBytes(region, own);
        assert.ok(
          own.length <= TILE_BUDGET.tiles && bytes <= TILE_BUDGET.bytes,
          `${region} at ${width}x${height}, view at ${x},${y}: the view alone needs ` +
            `${own.length} tiles and ${(bytes / MiB).toFixed(3)} MiB, past TILE_BUDGET; raise ` +
            'the budget to the largest tested view (lib/world-walk.ts, docs/vision/region-canvas.md)',
        );
        viewNeed.tiles = Math.max(viewNeed.tiles, own.length);
        viewNeed.bytes = Math.max(viewNeed.bytes, bytes);
        viewSets++;
      }
  }
}

// The warm camera Codex found on #126 (430 x 932, DPR 3; u = 4/3, a 322.5 x 699 view): the
// isles' camera moving 23 px down. Mounted at 279 it kept its top row (within twice the
// margin) while the margin reached the next row: 15 tiles, 30.234375 MiB, over the budget.
{
  const [vw, vh] = viewOf(430, 932, 3);
  assert.deepEqual([vw, vh], [322.5, 699], 'the 430 x 932 view at DPR 3');
  const box = (y: number): RegionBox => ({ x0: 168, y0: y, x1: 168 + vw, y1: y + vh });
  const before = tilesToMount('isles', box(279));
  const cold = tilesToMount('isles', box(302));
  const warm = tilesToMount('isles', box(302), before);
  assert.equal(before.length, 12, 'warm camera: 12 tiles at 279');
  assert.equal(cold.length, 12, 'warm camera: 12 tiles at 302, mounted afresh');
  checkMounted('isles', box(279), before, 'warm camera at 279');
  checkMounted('isles', box(302), cold, 'warm camera at 302, cold');
  checkMounted('isles', box(302), warm, 'warm camera at 302 after 279');
}

let views = 0;
for (const [width, height, dpr] of sizes) {
  const [vw, vh] = viewOf(width, height, dpr);
  const phone = width <= 430;
  for (const region of regions) {
    const b = regionBounds(region);
    // the camera crossing the region in rows, carrying its mounted set (the kept margin)
    let mounted: string[] = [];
    for (let y = -64; y <= Math.max(0, b.height - vh) + 64; y += 56)
      for (let x = -64; x <= Math.max(0, b.width - vw) + 64; x += 56) {
        const view: RegionBox = { x0: x, y0: y, x1: x + vw, y1: y + vh };
        mounted = tilesToMount(region, view, mounted);
        views++;
        checkMounted(region, view, mounted, `${region} at ${width}x${height}`);
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
      }
  }
}

// The camera moving along each axis, one way and back, carrying its mounted set, at a few
// places across (each end, the middle, and just before, a margin before and well past a
// tile edge): through every place where a tile enters or leaves the view, the margin or
// twice the margin, and the midpoints between. At each: the budget, and the whole view
// covered.
let sweepViews = 0;
for (const [width, height, dpr] of sizes) {
  const [vw, vh] = viewOf(width, height, dpr);
  for (const region of regions) {
    const b = regionBounds(region);
    const [ox, oy] = chunkFor(region).origin;
    for (const across of [true, false]) {
      // (along the x axis when across)
      const range = across ? rangeOf(b.width, vw) : rangeOf(b.height, vh);
      const cross = across ? rangeOf(b.height, vh) : rangeOf(b.width, vw);
      const stops = axisStops(across ? ox : oy, across ? vw : vh, range, [
        0,
        0.5,
        1,
        TILE_MOUNT_MARGIN,
        2 * TILE_MOUNT_MARGIN,
      ]);
      const o = across ? oy : ox;
      const edge = Math.round(((cross[0] + cross[1]) / 2 + o) / S) * S - o;
      const places = [cross[0], cross[1], (cross[0] + cross[1]) / 2, edge - 0.5, edge - 30];
      for (const c of [...places, edge + 100].filter((p) => p >= cross[0] && p <= cross[1])) {
        let mounted: string[] = [];
        for (const p of [...stops, ...stops.toReversed()]) {
          const x = across ? p : c;
          const y = across ? c : p;
          const view: RegionBox = { x0: x, y0: y, x1: x + vw, y1: y + vh };
          mounted = tilesToMount(region, view, mounted);
          checkMounted(region, view, mounted, `${region} at ${width}x${height}, at ${x},${y}`);
          sweepViews++;
        }
      }
    }
  }
}

// A randomized camera (its own seed, so failures repeat): walks a step of a fraction of a
// pixel to a few blocks at a time in a heading that drifts, turns back now and then (to and
// fro across tile edges), and is now and then set down somewhere new; the mounted set is
// carried throughout. At every step: the budget, and the whole view covered.
let walkSeed = 126;
const walkRand = () => {
  // (mulberry32)
  walkSeed = (walkSeed + 0x6d2b79f5) | 0;
  let t = Math.imul(walkSeed ^ (walkSeed >>> 15), 1 | walkSeed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
let walkSteps = 0;
for (const [width, height, dpr] of sizes) {
  const [vw, vh] = viewOf(width, height, dpr);
  for (const region of regions) {
    const b = regionBounds(region);
    const xs = [-S, Math.max(0, b.width - vw) + S];
    const ys = [-S, Math.max(0, b.height - vh) + S];
    const anywhere = () => ({
      x: xs[0] + walkRand() * (xs[1] - xs[0]),
      y: ys[0] + walkRand() * (ys[1] - ys[0]),
    });
    let at = anywhere();
    let heading = walkRand() * 2 * Math.PI;
    let mounted: string[] = [];
    for (let i = 0; i < 1500; i++) {
      const roll = walkRand();
      if (roll < 0.004) at = anywhere();
      else {
        if (roll < 0.1) heading += Math.PI;
        heading += (walkRand() - 0.5) * 0.6;
        const step = roll < 0.7 ? walkRand() * 4 : walkRand() * 32;
        at = {
          x: Math.max(xs[0], Math.min(xs[1], at.x + Math.cos(heading) * step)),
          y: Math.max(ys[0], Math.min(ys[1], at.y + Math.sin(heading) * step)),
        };
      }
      const view: RegionBox = { x0: at.x, y0: at.y, x1: at.x + vw, y1: at.y + vh };
      mounted = tilesToMount(region, view, mounted);
      walkSteps++;
      checkMounted(region, view, mounted, `${region} at ${width}x${height}, step ${i}`);
    }
  }
}

// To and fro across a tile edge: with a view edge near a tile edge (and near the margin's
// and twice the margin's distance from one), a camera swinging up to 11 px either way (less
// than half the margin) settles on one set after the first swing and never mounts or
// unmounts again.
let swings = 0;
for (const [width, height, dpr] of sizes) {
  const [vw, vh] = viewOf(width, height, dpr);
  for (const region of regions) {
    const b = regionBounds(region);
    const [ox, oy] = chunkFor(region).origin;
    for (let n = 0; n < 24; n++) {
      // an edge of the view, a tile edge it is near, and how near
      const across = walkRand() < 0.5; // (the x axis)
      const side = walkRand() < 0.5 ? 0 : across ? vw : vh;
      const span = across ? b.width : b.height;
      const edge = Math.floor(walkRand() * (span / S + 2)) * S - (across ? ox % S : oy % S);
      const offsets = [0, 1, TILE_MOUNT_MARGIN, 2 * TILE_MOUNT_MARGIN];
      const off =
        offsets[Math.floor(walkRand() * offsets.length)] * (walkRand() < 0.5 ? -1 : 1) +
        (walkRand() - 0.5);
      const along = walkRand() * Math.max(1, (across ? b.height : b.width) - (across ? vh : vw));
      const base = edge + off - side;
      const amp = 1 + walkRand() * 10;
      const step = Math.max(0.25, amp / (4 + Math.floor(walkRand() * 8)));
      const at = (t: number): RegionBox => {
        const x = across ? t : along;
        const y = across ? along : t;
        return { x0: x, y0: y, x1: x + vw, y1: y + vh };
      };
      let mounted = tilesToMount(region, at(base));
      const where = `${region} at ${width}x${height}, swinging ${amp.toFixed(2)} px about ${base.toFixed(2)} (${across ? 'x' : 'y'})`;
      // the positions of one swing: out one way, back through the middle, out the other
      const swing: number[] = [];
      for (let t = 0; t <= amp; t += step) swing.push(base + t);
      for (let t = amp; t >= -amp; t -= step) swing.push(base + t);
      for (let t = -amp; t <= 0; t += step) swing.push(base + t);
      let settled: string[][] = [];
      for (let k = 0; k < 4; k++) {
        const sets: string[][] = [];
        for (const p of swing) {
          mounted = tilesToMount(region, at(p), mounted);
          checkMounted(region, at(p), mounted, where);
          sets.push(mounted);
        }
        if (k >= 2)
          sets.forEach((s, i) =>
            assert.deepEqual(s, settled[i], `${where}: swing ${k + 1} mounts as the one before`),
          );
        if (k >= 1)
          for (let i = 1; i < sets.length; i++)
            assert.deepEqual(sets[i], sets[0], `${where}: swing ${k + 1} mounts nothing new`);
        settled = sets;
      }
      swings++;
    }
  }
}

// Past the tested sizes: a desktop window larger than 1440 x 900 can need more than the
// budget for its view alone. Its view is still covered; where its own tiles reach the
// budget they are all that mount, and otherwise the budget holds.
const large: [number, number, number][] = [
  [1920, 1080, 1],
  [2560, 1440, 2],
];
const largeNeed = new Map<string, { tiles: number; bytes: number }>();
for (const [width, height, dpr] of large) {
  const [vw, vh] = viewOf(width, height, dpr);
  const need = { tiles: 0, bytes: 0 };
  for (const region of regions) {
    const b = regionBounds(region);
    let mounted: string[] = [];
    for (let y = -64; y <= Math.max(0, b.height - vh) + 64; y += 23)
      for (let x = -64; x <= Math.max(0, b.width - vw) + 64; x += 37) {
        const view: RegionBox = { x0: x, y0: y, x1: x + vw, y1: y + vh };
        const where = `${region} at ${width}x${height}, at ${x},${y}`;
        mounted = tilesToMount(region, view, mounted);
        for (const k of tilesInView(region, view))
          assert.ok(mounted.includes(k), `${where}: tile ${k} in view is mounted`);
        const own = tilesInView(region, view, 1);
        const ownBytes = mountedBytes(region, own);
        need.tiles = Math.max(need.tiles, own.length);
        need.bytes = Math.max(need.bytes, ownBytes);
        if (own.length >= TILE_BUDGET.tiles || ownBytes > TILE_BUDGET.bytes)
          assert.deepEqual(mounted, own.slice().sort(), `${where}: only the view's own tiles`);
        else {
          assert.ok(mounted.length <= TILE_BUDGET.tiles, `${where}: at most the budget's tiles`);
          assert.ok(mountedBytes(region, mounted) <= TILE_BUDGET.bytes, `${where}: and bytes`);
        }
      }
  }
  largeNeed.set(`${width} x ${height}`, need);
}
assert.ok(
  [...largeNeed.values()].some((n) => n.tiles > TILE_BUDGET.tiles),
  'a large desktop window does need more than the budget for its view alone',
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
const mib = (bytes: number) => `${(bytes / MiB).toFixed(2)} MiB`;
console.log(
  `world walk: ${pairs} walks searched in windows match the whole-region search (${viaGraph} also by the route graph, ` +
    `longest ${Math.round(longest)} px); ${views + sweepViews + walkSteps} camera positions over ${tiles} tiles at ` +
    `${sizes.length} window sizes covered (${views} crossing, ${sweepViews} swept, ${walkSteps} walked) and ` +
    `${swings} swings settled, ` +
    `with at most ${worstCount} tiles and ${mib(worstBytes)} mounted at ${WORLD_TILE.scale}x ` +
    `(budget ${TILE_BUDGET.tiles}, ${mib(TILE_BUDGET.bytes)}; a view alone, of ${viewSets} sets: ` +
    `${viewNeed.tiles} tiles, ${mib(viewNeed.bytes)}); a view alone past the tested sizes: ` +
    [...largeNeed].map(([k, n]) => `${k}, ${n.tiles} tiles, ${mib(n.bytes)}`).join('; ') +
    '.',
);
