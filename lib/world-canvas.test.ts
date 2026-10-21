/**
 * The world canvas, step 1 (docs/vision/region-canvas.md): the chunks scripts/art/world_canvas.py
 * assembles from today's zones are those zones, exactly. Nothing in the game reads them yet, so
 * this is what keeps them honest until step 2 switches the renderer over.
 *
 * - every region is a chunk the size of its zone grid, on the 8 px grid, and chunks on a
 *   plane never overlap;
 * - the areas are its zones (and the garden), and every walkable cell lies in one;
 * - the walk read back from the world tiles is the zones' walks joined, as lib/region-walk.ts
 *   joins them today, except at the reported seam cells, which lie at seams and are settled
 *   by the walk over the whole chunk;
 * - terrain, props and stands read back from the tiles are the zones' own, in world px, each
 *   prop and stand listed once;
 * - the tiles' pictures reassemble the zones' ground pixel for pixel, scaled by nearest
 *   neighbour, with a picture for exactly the tiles that have ground (a one-colour tile
 *   matches its fill);
 * - the tiles' moving water is the zones' moving water, frame for frame.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  tileRows,
  worldAreas,
  worldChunks,
  worldDecks,
  worldPlanes,
  worldSeams,
  worldTiles,
  WORLD_FLOW,
  WORLD_TILE,
  type WorldObject,
  type WorldPlane,
} from './world-canvas';
import {
  regionBounds,
  regionTiles,
  regionWalk,
  tileOrigin,
  TILE,
  type RegionId,
} from './region-walk';
import { regionLayout, zoneDecks, zoneFlow, zoneMaps, zoneTerrain } from './zone-maps';

type Decoded = { width: number; height: number; data: Buffer };
type PngModule = { PNG: { sync: { read: (b: Buffer) => Decoded } } };
const isPngModule = (m: unknown): m is PngModule =>
  typeof m === 'object' && m !== null && 'PNG' in m && typeof m.PNG === 'function';
const pngjs: unknown = createRequire(import.meta.url)('pngjs');
assert.ok(isPngModule(pngjs), 'pngjs loads');
const { PNG } = pngjs;
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const decode = (rel: string): Decoded => PNG.sync.read(readFileSync(resolve(root, rel)));

const S = WORLD_TILE.size;
const CELL = WORLD_TILE.cell;
const N = S / CELL;
const key = (c: number, r: number) => `${c},${r}`;
const tag = (n: number) => String(n).replace('-', 'm');
const mod = (v: number, m: number) => ((v % m) + m) % m;
const regions = Object.keys(regionLayout).filter((k): k is RegionId =>
  Object.hasOwn(regionLayout, k),
);

// --- chunks and areas -----------------------------------------------------------------
const chunkOf = (id: string) => {
  const ch = worldChunks.find((c) => c.id === id);
  assert.ok(ch, `a chunk for ${id}`);
  return ch;
};
assert.deepEqual(
  worldChunks.map((c) => c.id).sort(),
  [...regions].sort(),
  'today: one chunk per region',
);
for (const ch of worldChunks) {
  for (const v of [...ch.origin, ...ch.size, ch.margin])
    assert.equal(v % WORLD_TILE.grid, 0, `${ch.id}: on the ${WORLD_TILE.grid} px grid`);
  for (const o of worldChunks) {
    if (o === ch || o.plane !== ch.plane) continue;
    const apart =
      ch.origin[0] + ch.size[0] <= o.origin[0] ||
      o.origin[0] + o.size[0] <= ch.origin[0] ||
      ch.origin[1] + ch.size[1] <= o.origin[1] ||
      o.origin[1] + o.size[1] <= ch.origin[1];
    assert.ok(apart, `${ch.id} and ${o.id} do not overlap on the ${ch.plane} plane`);
  }
}

// --- reading the tiles back -----------------------------------------------------------
const rowsCache = new Map<string, string[]>();
function cellAt(plane: WorldPlane, layer: 'walk' | 'terrain', wc: number, wr: number): string {
  const c = Math.floor(wc / N);
  const r = Math.floor(wr / N);
  const t = worldTiles[plane][key(c, r)];
  if (!t) return layer === 'walk' ? '#' : '-';
  const id = `${plane}/${layer}/${c},${r}`;
  let rows = rowsCache.get(id);
  if (!rows) rowsCache.set(id, (rows = tileRows(t[layer])));
  return rows[mod(wr, N)][mod(wc, N)];
}
for (const plane of worldPlanes)
  for (const [k, t] of Object.entries(worldTiles[plane])) {
    for (const layer of ['walk', 'terrain'] as const)
      assert.equal(
        tileRows(t[layer]).join('').length,
        N * N,
        `${plane} ${k}: ${N} x ${N} ${layer} cells`,
      );
    assert.equal(t.tiers, undefined, `${plane} ${k}: no terraces yet`);
  }
const allObjects: { plane: WorldPlane; tile: string; o: WorldObject }[] = [];
const allStands = new Map<string, readonly [number, number]>();
for (const plane of worldPlanes)
  for (const [k, t] of Object.entries(worldTiles[plane])) {
    for (const o of t.objects) allObjects.push({ plane, tile: k, o });
    for (const [s, p] of Object.entries(t.stands)) {
      assert.ok(!allStands.has(`${plane}:${s}`), `stand ${s} listed once`);
      allStands.set(`${plane}:${s}`, p);
      assert.equal(key(Math.floor(p[0] / S), Math.floor(p[1] / S)), k, `stand ${s} in its tile`);
    }
  }
assert.equal(
  new Set(allObjects.map((x) => `${x.plane}:${x.o[0]}`)).size,
  allObjects.length,
  'each prop listed once',
);

let pixels = 0;
let flowPixels = 0;
let seamCells = 0;
const seamReport = new Map<string, number>();

for (const plane of worldPlanes) {
  const expected = new Map<string, Uint8Array>();
  const expectedFlow = new Map<string, Uint8Array[]>();
  const tile = (c: number, r: number) => {
    let t = expected.get(key(c, r));
    if (!t) expected.set(key(c, r), (t = new Uint8Array(S * S * 4)));
    return t;
  };
  for (const region of regions) {
    const ch = chunkOf(region);
    if (ch.plane !== plane) continue;
    const b = regionBounds(region);
    const [ox, oy] = ch.origin;
    assert.deepEqual(ch.size, [b.width, b.height], `${region}: the chunk is its zone grid`);
    assert.equal(ch.margin, 0, `${region}: assembled from zones, no blend margin`);

    // areas: one per zone, at its place; together they hold every walkable cell
    const areas = worldAreas.filter((a) => a.chunk === region);
    const tiles = regionTiles(region);
    assert.equal(areas.length, tiles.length, `${region}: one area per zone`);
    for (const t of tiles) {
      const o = tileOrigin(region, t);
      const area = areas.find((a) => a.id === t.id);
      assert.ok(area, `${region}: an area for ${t.id}`);
      assert.deepEqual(area.rect, [ox + o.x, oy + o.y, TILE.width, TILE.height], `${t.id}'s area`);
      assert.equal(area.kind, t.id === 'garden' ? 'garden' : 'zone', `${t.id}'s kind`);
      assert.equal(area.plane, plane, `${t.id}'s plane`);
    }

    // the walk: today's joined grids, the seams settled by the walk over the whole chunk
    const oc = ox / CELL;
    const or = oy / CELL;
    const seams = new Map((worldSeams[region] ?? []).map(([c, r, k]) => [key(c, r), k]));
    const joined = regionWalk(region);
    const W = TILE.width;
    const H = TILE.height;
    const reach = 20; // the deepest foot band (a wide prop's), in px
    joined.forEach((row, r) => {
      for (let c = 0; c < row.length; c++) {
        const got = cellAt(plane, 'walk', oc + c, or + r);
        const seam = seams.get(key(oc + c, or + r));
        if (seam) {
          assert.equal(
            got,
            seam === 'shut' ? '#' : '.',
            `${region}: seam ${c},${r} settled ${seam}`,
          );
          assert.notEqual(got, row[c], `${region}: seam ${c},${r} is a real difference`);
          const x = c * CELL;
          const y = r * CELL;
          const nearV =
            Math.min(x % W, W - (x % W) - CELL) < reach && x >= reach && x < b.width - reach;
          const nearH =
            Math.min(y % H, H - (y % H) - CELL) < reach && y >= reach && y < b.height - reach;
          assert.ok(nearV || nearH, `${region}: seam cell ${c},${r} lies at a zone seam`);
          seamCells++;
          seamReport.set(`${region} ${seam}`, (seamReport.get(`${region} ${seam}`) ?? 0) + 1);
        } else assert.equal(got, row[c], `${region}: walk cell ${c},${r} is the zones' own`);
        if (got === '.') {
          const inArea = areas.some(
            (a) =>
              ox + c * CELL >= a.rect[0] &&
              ox + c * CELL < a.rect[0] + a.rect[2] &&
              oy + r * CELL >= a.rect[1] &&
              oy + r * CELL < a.rect[1] + a.rect[3],
          );
          assert.ok(inArea, `${region}: walkable cell ${c},${r} in an area`);
        }
      }
    });
    assert.equal(seams.size, [...seams.keys()].length, `${region}: seams listed once`);

    for (const t of tiles) {
      const o = tileOrigin(region, t);
      const wx = ox + o.x;
      const wy = oy + o.y;
      if (t.id !== 'garden') {
        const z = t.id;
        zoneTerrain[z].forEach((row, r) => {
          let got = '';
          for (let c = 0; c < row.length; c++)
            got += cellAt(plane, 'terrain', wx / CELL + c, wy / CELL + r);
          assert.equal(got, row, `${z}: terrain row ${r}`);
        });
        const mine = allObjects
          .filter((x) => x.plane === plane && x.o[0].startsWith(`${z}:`))
          .map((x) => x.o)
          .sort((a, b2) => (a[0] < b2[0] ? -1 : 1));
        const want = zoneMaps[z].objects
          .map(([id, k, x, y, w, h]): WorldObject => [`${z}:${id}`, k, wx + x, wy + y, w, h])
          .sort((a, b2) => (a[0] < b2[0] ? -1 : 1));
        assert.deepEqual(mine, want, `${z}: its props, in world px`);
        for (const [s, [x, y]] of Object.entries(zoneMaps[z].stands))
          assert.deepEqual(
            allStands.get(`${plane}:${z}:${s}`),
            [wx + x, wy + y],
            `${z}/${s} in world px`,
          );
        assert.equal(
          worldDecks.some((d) => d.rect[0] === wx && d.rect[1] === wy),
          Boolean(zoneDecks[z]),
          `${z}: its deck, if it has one`,
        );
      }
      // the ground, pixel for pixel (the zone pictures are 4x; sample each art pixel)
      const src = decode(
        t.id === 'garden' ? 'assets/garden/ground.png' : `assets/zones/${t.id}/ground.png`,
      );
      const k = src.width / TILE.width;
      assert.equal(src.height, TILE.height * k, `${t.id}: ground at ${k}x`);
      for (let y = 0; y < TILE.height; y++)
        for (let x = 0; x < TILE.width; x++) {
          const X = wx + x;
          const Y = wy + y;
          const at = (y * k * src.width + x * k) * 4;
          tile(Math.floor(X / S), Math.floor(Y / S)).set(
            src.data.subarray(at, at + 4),
            (mod(Y, S) * S + mod(X, S)) * 4,
          );
        }
      // and its moving water, frame for frame
      const rect = t.id === 'garden' ? undefined : zoneFlow[t.id];
      if (rect) {
        const [fx, fy, fw, fh] = rect;
        const sheet = decode(`assets/zones/${t.id}/flow.png`);
        assert.equal(sheet.height, fh * WORLD_FLOW.frames, `${t.id}: flow frames`);
        for (let f = 0; f < WORLD_FLOW.frames; f++)
          for (let y = 0; y < fh; y++)
            for (let x = 0; x < fw; x++) {
              const X = wx + fx + x;
              const Y = wy + fy + y;
              const k2 = key(Math.floor(X / S), Math.floor(Y / S));
              let frames = expectedFlow.get(k2);
              if (!frames)
                expectedFlow.set(
                  k2,
                  (frames = Array.from(
                    { length: WORLD_FLOW.frames },
                    () => new Uint8Array(S * S * 4),
                  )),
                );
              const at = ((f * fh + y) * fw + x) * 4;
              frames[f].set(sheet.data.subarray(at, at + 4), (mod(Y, S) * S + mod(X, S)) * 4);
            }
      }
    }
  }

  // the pictures: exactly the tiles with ground, holding exactly that ground
  const tiles = worldTiles[plane];
  for (const [k, want] of expected) {
    const opaque = want.some((v, i) => i % 4 === 3 && v > 0);
    const art = tiles[k]?.art;
    assert.equal(Boolean(art), opaque, `${plane} tile ${k}: a picture iff it has ground`);
    if (!art) continue;
    const png = decode(`assets/world/${art}.png`);
    const sc = WORLD_TILE.scale;
    assert.deepEqual([png.width, png.height], [S * sc, S * sc], `${art}: ${S * sc} px square`);
    for (let y = 0; y < S; y++)
      for (let x = 0; x < S; x++) {
        const at = (y * sc * png.width + x * sc) * 4;
        for (let dy = 0; dy < sc; dy++)
          for (let dx = 0; dx < sc; dx++)
            if (
              png.data.readUInt32BE(((y * sc + dy) * png.width + x * sc + dx) * 4) !==
              png.data.readUInt32BE(at)
            )
              assert.fail(`${art}: art pixel (${x}, ${y}) is not one colour (nearest neighbour)`);
        const i = (y * S + x) * 4;
        const same =
          png.data[at + 3] === want[i + 3] &&
          (want[i + 3] === 0 ||
            (png.data[at] === want[i] &&
              png.data[at + 1] === want[i + 1] &&
              png.data[at + 2] === want[i + 2]));
        if (!same) assert.fail(`${plane} tile ${k}: pixel (${x}, ${y}) differs from its zone`);
        pixels++;
      }
    const fill = tiles[k]?.fill;
    if (fill) {
      const hex = [...want.subarray(0, 4)].map((v) => v.toString(16).padStart(2, '0')).join('');
      assert.ok(
        want.every((v, i) => v === want[i % 4]),
        `${plane} tile ${k}: one colour`,
      );
      assert.equal(fill.toLowerCase(), `#${hex}`, `${plane} tile ${k}: its fill`);
    }
  }
  for (const [k, t] of Object.entries(tiles))
    if (t.art) assert.ok(expected.has(k), `${plane} tile ${k} lies on a chunk`);

  // moving water per tile
  for (const k of new Set([
    ...Object.keys(tiles).filter((t) => tiles[t].flow),
    ...expectedFlow.keys(),
  ])) {
    const want = expectedFlow.get(k);
    const moving = want?.some((fr) => fr.some((v, i) => i % 4 === 3 && v > 0)) ?? false;
    const box = tiles[k]?.flow;
    assert.equal(Boolean(box), moving, `${plane} tile ${k}: a flow picture iff its water moves`);
    if (!moving || !want || !box) continue;
    const [bx, by, bw, bh] = box;
    const [c, r] = k.split(',').map(Number);
    const sheet = decode(`assets/world/${plane}/f_${tag(c)}_${tag(r)}.png`);
    assert.deepEqual(
      [sheet.width, sheet.height],
      [bw, bh * WORLD_FLOW.frames],
      `${plane} flow ${k}: box`,
    );
    for (let f = 0; f < WORLD_FLOW.frames; f++)
      for (let y = 0; y < S; y++)
        for (let x = 0; x < S; x++) {
          const i = (y * S + x) * 4;
          const inBox = x >= bx && x < bx + bw && y >= by && y < by + bh;
          const at = ((f * bh + (y - by)) * bw + (x - bx)) * 4;
          for (let ch = 0; ch < 4; ch++)
            if ((inBox ? sheet.data[at + ch] : 0) !== want[f][i + ch])
              assert.fail(`${plane} flow ${k} frame ${f}: (${x}, ${y}) differs`);
          flowPixels++;
        }
  }
}

const tileCount = worldPlanes.reduce(
  (n, p) => n + Object.values(worldTiles[p]).filter((t) => t.art).length,
  0,
);
console.log(
  `world canvas: ${worldChunks.length} chunks, ${tileCount} tiles at ${WORLD_TILE.scale}x match their zones ` +
    `(${pixels} px, ${flowPixels} flow values; ${allObjects.length} props, ${allStands.size} stands); ` +
    `${seamCells} seam cells settled by the walk over the whole chunk${seamCells ? ':' : '.'}`,
);
for (const [k, n] of seamReport) console.log(`  ${k}: ${n}`);
