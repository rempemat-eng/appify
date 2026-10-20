/**
 * Region canvases, step 1 (docs/vision/region-canvas.md): the canvases scripts/art/regions.py
 * assembles from today's zones are those zones, exactly. Nothing in the game reads them yet,
 * so this is what keeps them honest until step 2 switches the renderer over.
 *
 * - every region has a canvas the size of its zone grid, on the 8 px grid, at its origin;
 * - its areas are its zones (and the garden), and every walkable cell lies in one;
 * - its walk is the zones' walks joined, as lib/region-walk.ts joins them today; its
 *   terrain, props and stands are the zones' own, moved to world coordinates;
 * - its world tiles reassemble the zones' ground pictures pixel for pixel, scaled by
 *   nearest neighbour, with a picture for exactly the tiles that have ground;
 * - its tiles' moving water is the zones' moving water, frame for frame;
 * - where a walk over the whole canvas would differ from the joined grids (the seam
 *   rules), the difference is reported, and it lies at a seam.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  regionCanvases,
  worldTileDecks,
  worldTileFlow,
  worldPlanes,
  worldTiles,
  WORLD_TILE,
  type RegionCanvas,
  type WorldPlane,
} from './region-canvas';
import {
  regionBounds,
  regionTiles,
  regionWalk,
  tileOrigin,
  TILE,
  type RegionId,
} from './region-walk';
import {
  FLOW_FRAMES,
  regionLayout,
  zoneDecks,
  zoneFlow,
  zoneMaps,
  zoneTerrain,
  type ZoneId,
} from './zone-maps';

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
const canvases = regionCanvases as Record<string, RegionCanvas>;
const regions = Object.keys(regionLayout).filter((k): k is RegionId =>
  Object.hasOwn(regionLayout, k),
);
assert.deepEqual(Object.keys(canvases).sort(), [...regions].sort(), 'one canvas per region');

/** A tile picture at 1x, checking that each scale x scale block is one colour. */
function tileAt1x(plane: WorldPlane, prefix: string, c: number, r: number): Uint8Array {
  const name = `assets/world/${plane}/${prefix}_${String(c).replace('-', 'm')}_${String(r).replace('-', 'm')}.png`;
  const png = decode(name);
  const k = WORLD_TILE.scale;
  assert.equal(png.width, S * k, `${name} is ${S * k} px wide`);
  assert.equal(png.height, S * k, `${name} is ${S * k} px tall`);
  const out = new Uint8Array(S * S * 4);
  for (let y = 0; y < S; y++)
    for (let x = 0; x < S; x++) {
      const at = (y * k * png.width + x * k) * 4;
      for (let dy = 0; dy < k; dy++)
        for (let dx = 0; dx < k; dx++) {
          const p = ((y * k + dy) * png.width + x * k + dx) * 4;
          if (png.data.readUInt32BE(p) !== png.data.readUInt32BE(at))
            assert.fail(
              `${name}: art pixel (${x}, ${y}) is not one colour (scaled by nearest neighbour)`,
            );
        }
      out.set(png.data.subarray(at, at + 4), (y * S + x) * 4);
    }
  return out;
}

const key = (c: number, r: number) => `${c},${r}`;
let pixels = 0;
let flowPixels = 0;
const seamReport: string[] = [];

for (const plane of worldPlanes) {
  const onPlane = regions.filter((r) => canvases[r].plane === plane);
  // what each world tile should hold: every zone's ground (and the garden's), at 1x
  const expected = new Map<string, Uint8Array>();
  const expectedFlow = new Map<string, Uint8Array[]>();
  const tile = (m: Map<string, Uint8Array>, c: number, r: number) => {
    let t = m.get(key(c, r));
    if (!t) m.set(key(c, r), (t = new Uint8Array(S * S * 4)));
    return t;
  };
  for (const region of onPlane) {
    const cv = canvases[region];
    const b = regionBounds(region);
    const [ox, oy] = cv.origin;
    assert.deepEqual(cv.size, [b.width, b.height], `${region}: the canvas is its zone grid`);
    for (const v of [ox, oy, ...cv.size])
      assert.equal(v % WORLD_TILE.grid, 0, `${region}: on the ${WORLD_TILE.grid} px grid`);
    for (const other of onPlane) {
      if (other === region) continue;
      const o = canvases[other];
      const apart =
        ox + cv.size[0] <= o.origin[0] ||
        o.origin[0] + o.size[0] <= ox ||
        oy + cv.size[1] <= o.origin[1] ||
        o.origin[1] + o.size[1] <= oy;
      assert.ok(apart, `${region} and ${other} do not overlap on the ${plane} plane`);
    }

    // areas: one per zone, at its place; together they hold every walkable cell
    const tiles = regionTiles(region);
    assert.equal(cv.areas.length, tiles.length, `${region}: one area per zone`);
    for (const t of tiles) {
      const o = tileOrigin(region, t);
      const area = cv.areas.find((a) => a.id === t.id);
      assert.ok(area, `${region}: an area for ${t.id}`);
      assert.deepEqual(area.rect, [ox + o.x, oy + o.y, TILE.width, TILE.height], `${t.id}'s area`);
      assert.equal(area.kind, t.id === 'garden' ? 'garden' : 'zone', `${t.id}'s kind`);
    }
    const inArea = (x: number, y: number) =>
      cv.areas.some(
        (a) =>
          x >= a.rect[0] &&
          x < a.rect[0] + a.rect[2] &&
          y >= a.rect[1] &&
          y < a.rect[1] + a.rect[3],
      );
    const cell = WORLD_TILE.cell;
    cv.walk.forEach((row, r) => {
      for (let c = 0; c < row.length; c++)
        if (row[c] === '.')
          assert.ok(
            inArea(ox + c * cell, oy + r * cell),
            `${region}: walkable cell ${c},${r} in an area`,
          );
    });

    // the walk is the zones' walks joined, exactly as the game joins them today
    assert.deepEqual(cv.walk, regionWalk(region), `${region}: walk = the zones' walks joined`);

    for (const t of tiles) {
      const o = tileOrigin(region, t);
      const wx = ox + o.x;
      const wy = oy + o.y;
      const cols = TILE.width / cell;
      if (t.id !== 'garden') {
        const z: ZoneId = t.id;
        // terrain, props and stands: the zone's own, in world coordinates
        zoneTerrain[z].forEach((row, r) =>
          assert.equal(
            cv.terrain[o.y / cell + r].slice(o.x / cell, o.x / cell + cols),
            row,
            `${z} terrain row ${r}`,
          ),
        );
        const mine = cv.objects.filter((ob) => ob[0].startsWith(`${z}:`));
        assert.deepEqual(
          mine,
          zoneMaps[z].objects.map(([id, k, x, y, w, h]) => [`${z}:${id}`, k, wx + x, wy + y, w, h]),
          `${z}: its props, in world px`,
        );
        for (const [s, [x, y]] of Object.entries(zoneMaps[z].stands))
          assert.deepEqual(cv.stands[`${z}:${s}`], [wx + x, wy + y], `${z}/${s} in world px`);
        assert.equal(
          cv.decks.some((d) => d.rect[0] === wx && d.rect[1] === wy),
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
          const dst = tile(expected, Math.floor(X / S), Math.floor(Y / S));
          const at = (y * k * src.width + x * k) * 4;
          dst.set(
            src.data.subarray(at, at + 4),
            ((((Y % S) + S) % S) * S + (((X % S) + S) % S)) * 4,
          );
        }
      // and its moving water, frame for frame
      const rect = t.id === 'garden' ? undefined : zoneFlow[t.id];
      if (rect) {
        const [fx, fy, fw, fh] = rect;
        const sheet = decode(`assets/zones/${t.id}/flow.png`);
        assert.equal(sheet.height, fh * FLOW_FRAMES, `${t.id}: flow frames`);
        for (let f = 0; f < FLOW_FRAMES; f++)
          for (let y = 0; y < fh; y++)
            for (let x = 0; x < fw; x++) {
              const X = wx + fx + x;
              const Y = wy + fy + y;
              const k2 = key(Math.floor(X / S), Math.floor(Y / S));
              let frames = expectedFlow.get(k2);
              if (!frames)
                expectedFlow.set(
                  k2,
                  (frames = Array.from({ length: FLOW_FRAMES }, () => new Uint8Array(S * S * 4))),
                );
              const at = ((f * fh + y) * fw + x) * 4;
              frames[f].set(
                sheet.data.subarray(at, at + 4),
                ((((Y % S) + S) % S) * S + (((X % S) + S) % S)) * 4,
              );
            }
      }
    }

    // the seam report: where one walk over the whole canvas differs, and it is at a seam
    const W = TILE.width;
    const H = TILE.height;
    const reach = 20; // the deepest foot band (a wide prop's), in px
    for (const [c, r, kind] of cv.seams) {
      const x = c * cell;
      const y = r * cell;
      const nearV =
        Math.min(x % W, W - (x % W) - cell) < reach && x >= reach && x < cv.size[0] - reach;
      const nearH =
        Math.min(y % H, H - (y % H) - cell) < reach && y >= reach && y < cv.size[1] - reach;
      assert.ok(nearV || nearH, `${region}: seam difference at cell ${c},${r} lies at a seam`);
      seamReport.push(`${region} ${c},${r} ${kind}`);
    }
  }

  // the tiles: a picture for exactly the tiles with ground, holding exactly that ground
  const listed = new Set(worldTiles[plane].map(([c, r]) => key(c, r)));
  for (const [k, want] of expected) {
    const opaque = want.some((v, i) => i % 4 === 3 && v > 0);
    assert.equal(listed.has(k), opaque, `${plane} tile ${k}: a picture iff it has ground`);
    if (!opaque) continue;
    const [c, r] = k.split(',').map(Number);
    const got = tileAt1x(plane, 't', c, r);
    for (let i = 0; i < want.length; i += 4) {
      const same =
        got[i + 3] === want[i + 3] &&
        (want[i + 3] === 0 ||
          (got[i] === want[i] && got[i + 1] === want[i + 1] && got[i + 2] === want[i + 2]));
      if (!same) {
        const p = i / 4;
        assert.fail(
          `${plane} tile ${k}: pixel (${p % S}, ${Math.floor(p / S)}) differs from its zone`,
        );
      }
      pixels++;
    }
  }
  for (const k of listed) assert.ok(expected.has(k), `${plane} tile ${k} lies on a canvas`);

  // moving water per tile
  const flows = worldTileFlow[plane];
  for (const k of new Set([...Object.keys(flows), ...expectedFlow.keys()])) {
    const want = expectedFlow.get(k);
    const moving = want?.some((fr) => fr.some((v, i) => i % 4 === 3 && v > 0)) ?? false;
    assert.equal(
      Boolean(flows[k]),
      moving,
      `${plane} tile ${k}: a flow picture iff its water moves`,
    );
    if (!moving || !want) continue;
    const [bx, by, bw, bh] = flows[k];
    const [c, r] = k.split(',').map(Number);
    const sheet = decode(
      `assets/world/${plane}/f_${String(c).replace('-', 'm')}_${String(r).replace('-', 'm')}.png`,
    );
    assert.deepEqual(
      [sheet.width, sheet.height],
      [bw, bh * FLOW_FRAMES],
      `${plane} flow ${k}: box`,
    );
    for (let f = 0; f < FLOW_FRAMES; f++)
      for (let y = 0; y < S; y++)
        for (let x = 0; x < S; x++) {
          const i = (y * S + x) * 4;
          const inBox = x >= bx && x < bx + bw && y >= by && y < by + bh;
          const at = ((f * bh + (y - by)) * bw + (x - bx)) * 4;
          for (let ch = 0; ch < 4; ch++) {
            const g = inBox ? sheet.data[at + ch] : 0;
            if (g !== want[f][i + ch])
              assert.fail(`${plane} flow ${k} frame ${f}: (${x}, ${y}) differs`);
          }
          flowPixels++;
        }
  }
  const decked = regions.some((r) => canvases[r].plane === plane && canvases[r].decks.length > 0);
  assert.equal(worldTileDecks[plane].length > 0, decked, `${plane}: deck tiles iff a deck`);
}

const tileCount = Object.values(worldTiles).reduce((n, t) => n + t.length, 0);
console.log(
  `region canvases: ${regions.length} regions, ${tileCount} tiles at ${WORLD_TILE.scale}x match their zones ` +
    `(${pixels} px, ${flowPixels} flow px); ${seamReport.length} seam cells where one walk over the canvas ` +
    `would differ from the zones' grids${seamReport.length ? ':' : '.'}`,
);
const bySeam = new Map<string, number>();
for (const s of seamReport) {
  const [region, , kind] = s.split(' ');
  bySeam.set(`${region} ${kind}`, (bySeam.get(`${region} ${kind}`) ?? 0) + 1);
}
for (const [k, n] of bySeam) console.log(`  ${k}: ${n}`);
