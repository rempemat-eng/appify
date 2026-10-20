import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import {
  TILE_SIZE,
  TILE_SCALE,
  PROBE_COLS,
  PROBE_ROWS,
  clampCamera,
  tileLayout,
  visibleTiles,
  summarizeCadence,
} from './native-pixels';
import { pixelScale } from './pixel-scale';

const require = createRequire(import.meta.url);
const {
  PNG,
}: {
  PNG: { sync: { read: (buffer: Buffer) => { width: number; height: number; data: Buffer } } };
} = require('pngjs');
const tiles = Array.from({ length: PROBE_COLS * PROBE_ROWS }, (_, index) => ({
  id: String(index),
  x: (index % PROBE_COLS) * TILE_SIZE,
  y: Math.floor(index / PROBE_COLS) * TILE_SIZE,
}));
const almostEqual = (a: number, b: number) => assert.ok(Math.abs(a - b) < 1e-8, `${a} ≈ ${b}`);

for (const width of [320, 375, 402]) {
  for (const dpr of [2, 3, 2.625]) {
    const pixel = pixelScale(width, dpr);
    const height = 655 * pixel;
    for (const x of [-100, 0, 0.123, 255.91, 256.13, 511.8, 5000]) {
      for (const y of [-100, 0, 255.91, 256.13, 700, 5000]) {
        const camera = clampCamera({ x, y }, width, height, pixel, dpr);
        almostEqual(camera.x * pixel * dpr, Math.round(camera.x * pixel * dpr));
        almostEqual(camera.y * pixel * dpr, Math.round(camera.y * pixel * dpr));
        assert.ok(camera.x >= 0 && camera.y >= 0);
        assert.ok(camera.x + width / pixel <= PROBE_COLS * TILE_SIZE + 1e-8);
        assert.ok(camera.y + height / pixel <= PROBE_ROWS * TILE_SIZE + 1e-8);

        const mounted = visibleTiles(tiles, camera, width, height, pixel);
        assert.ok(mounted.length > 0 && mounted.length <= 12);
        const layouts = tiles.map((tile) => tileLayout(tile, camera, pixel, dpr));
        for (let index = 0; index < tiles.length; index++) {
          const layout = layouts[index];
          for (const edge of [
            layout.left,
            layout.top,
            layout.left + layout.width,
            layout.top + layout.height,
          ]) {
            almostEqual(edge * dpr, Math.round(edge * dpr));
          }
          if (index % PROBE_COLS < PROBE_COLS - 1) {
            almostEqual(layout.left + layout.width, layouts[index + 1].left);
          }
          if (index + PROBE_COLS < tiles.length) {
            almostEqual(layout.top + layout.height, layouts[index + PROBE_COLS].top);
          }
          const coversView =
            layout.left < width &&
            layout.top < height &&
            layout.left + layout.width > 0 &&
            layout.top + layout.height > 0;
          if (coversView) assert.ok(mounted.includes(tiles[index]), 'culling must cover the view');
        }
      }
    }
  }
}

assert.deepEqual(clampCamera({ x: 500, y: 500 }, 2000, 2000, 1, 3), { x: 0, y: 0 });
assert.deepEqual(
  visibleTiles(tiles, { x: 0, y: 0 }, 128, 128, 1).map((tile) => tile.id),
  ['0'],
  'offscreen tiles are unmounted',
);
assert.deepEqual(
  visibleTiles(tiles, { x: 0, y: 0 }, 240, 240, 1).map((tile) => tile.id),
  ['0', '1', '3', '4'],
  'mount margin includes the next row and column before they enter the viewport',
);

assert.deepEqual(summarizeCadence([], 20), { count: 0, p50: 0, p95: 0, overBudget: 0 });
assert.deepEqual(summarizeCadence([NaN, Infinity, -3, 0, 50, 10, 20, 20], 20), {
  count: 4,
  p50: 20,
  p95: 50,
  overBudget: 1,
});
assert.deepEqual(
  summarizeCadence(
    Array.from({ length: 100 }, (_, index) => index + 1),
    16.67,
  ),
  {
    count: 100,
    p50: 50,
    p95: 95,
    overBudget: 84,
  },
);

// These are fixed device-probe specimens from PR #123, not newly authored game art.
for (let col = 0; col < PROBE_COLS; col++) {
  for (let row = 2; row < 2 + PROBE_ROWS; row++) {
    const name = `t_${col}_${row}.png`;
    const image = PNG.sync.read(
      readFileSync(new URL(`../assets/native-pixels/${name}`, import.meta.url)),
    );
    assert.equal(image.width, TILE_SIZE * TILE_SCALE, `${name}: 2x width`);
    assert.equal(image.height, TILE_SIZE * TILE_SCALE, `${name}: 2x height`);
    for (let y = 0; y < image.height; y += TILE_SCALE) {
      for (let x = 0; x < image.width; x += TILE_SCALE) {
        const origin = (y * image.width + x) * 4;
        for (let dy = 0; dy < TILE_SCALE; dy++) {
          for (let dx = 0; dx < TILE_SCALE; dx++) {
            const offset = ((y + dy) * image.width + x + dx) * 4;
            for (let channel = 0; channel < 4; channel++) {
              assert.equal(
                image.data[offset + channel],
                image.data[origin + channel],
                `${name}: authored pixel survives 2x enlargement`,
              );
            }
          }
        }
      }
    }
  }
}
console.log(
  'PASS: native-pixel geometry covers the view, has no shared-edge cracks, and fixtures preserve exact 2x blocks; cadence is JS callbacks only.',
);
