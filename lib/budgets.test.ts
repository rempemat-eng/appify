/**
 * The phone budgets at densities 1 and 2 (lib/budgets.ts) as checks: world tiles in view,
 * pictures and sound on disk. Source and files only; nothing here ran on a phone.
 *
 * Tiles: every tested phone and window size, in every region, at camera positions every
 * 16 world px plus a tile past each end, at density 1 and at density 2 (whose 2x phones see a
 * wider view). The view alone must fit the density's budget; the density-1 budget must stay
 * TILE_BUDGET (lib/world-walk.ts), which world-walk.test.ts checks in full.
 */
import assert from 'node:assert/strict';
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { ART_DENSITY_DEFAULT, type ArtDensity } from './art-density';
import { BUDGETS, SOUND_BUDGET } from './budgets';
import { pixelScale } from './pixel-scale';
import { regionBounds, type RegionId } from './region-walk';
import { WORLD_TILE, worldTiles } from './world-canvas';
import { chunkFor, mountedBytes, TILE_BUDGET } from './world-walk';
import { regionLayout } from './zone-maps';

const S = WORLD_TILE.size;
const MiB = 1024 * 1024;
const regions = Object.keys(regionLayout).filter((k): k is RegionId =>
  Object.hasOwn(regionLayout, k),
);
const sizes: [string, number, number, number][] = [
  ['iPhone SE (1st)', 320, 568, 2],
  ['iPhone SE (3rd)', 375, 667, 2],
  ['375x812@2', 375, 812, 2],
  ['iPhone 14', 390, 844, 3],
  ['iPhone 17 Pro', 402, 874, 3],
  ['Pixel 9', 412, 915, 2.625],
  ['S25 Ultra QHD+', 412, 915, 3.5],
  ['iPhone 17 Pro Max', 440, 956, 3],
];

assert.deepEqual(
  { tiles: BUDGETS[1].tiles, bytes: BUDGETS[1].tileBytes },
  { tiles: TILE_BUDGET.tiles, bytes: TILE_BUDGET.bytes },
  'density 1: the tile budget is TILE_BUDGET',
);

/** Every tile of the region's plane a view touches. */
function tilesInView(region: string, x0: number, y0: number, x1: number, y1: number) {
  const ch = chunkFor(region);
  const [ox, oy] = ch.origin;
  const out: string[] = [];
  for (let r = Math.floor((y0 - 1 + oy) / S); r * S < y1 + 1 + oy; r++)
    for (let c = Math.floor((x0 - 1 + ox) / S); c * S < x1 + 1 + ox; c++)
      if (worldTiles[ch.plane][`${c},${r}`]) out.push(`${c},${r}`);
  return out;
}

const lines: string[] = [];
for (const density of [1, 2] as ArtDensity[]) {
  const budget = BUDGETS[density];
  for (const [name, width, height, dpr] of sizes) {
    const u = pixelScale(width, dpr, density);
    const vw = Math.min(width, 640) / u;
    const vh = height / u;
    let worstTiles = 0;
    let worstBytes = 0;
    for (const region of regions) {
      const b = regionBounds(region);
      for (let x = -S; x <= Math.max(0, b.width - vw) + S; x += 16)
        for (let y = -S; y <= Math.max(0, b.height - vh) + S; y += 16) {
          const own = tilesInView(region, x, y, x + vw, y + vh);
          const bytes = mountedBytes(region, own);
          worstTiles = Math.max(worstTiles, own.length);
          worstBytes = Math.max(worstBytes, bytes);
          assert.ok(
            own.length <= budget.tiles && bytes <= budget.tileBytes,
            `density ${density}, ${name}, ${region} at ${x},${y}: the view needs ${own.length} tiles ` +
              `and ${(bytes / MiB).toFixed(1)} MiB, past ${budget.tiles} and ${budget.tileBytes / MiB} MiB`,
          );
        }
    }
    lines.push(
      `density ${density}  ${name.padEnd(18)} view ${vw.toFixed(0)} x ${vh.toFixed(0)} world px: ` +
        `at most ${worstTiles} tiles, ${(worstBytes / MiB).toFixed(1)} MiB (budget ${budget.tiles}, ${budget.tileBytes / MiB})`,
    );
  }
}

// ---- on disk ---------------------------------------------------------------------------------
function bytesUnder(dir: string, ext: string): number {
  let total = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) total += bytesUnder(path, ext);
    else if (entry.name.endsWith(ext)) total += statSync(path).size;
  }
  return total;
}
const pictures = bytesUnder('assets', '.png');
const sounds = bytesUnder('assets/sounds', '.wav');
const MB = 1000 * 1000;
assert.ok(
  pictures <= BUDGETS[ART_DENSITY_DEFAULT].pictures,
  `pictures: ${(pictures / MB).toFixed(1)} MB, past the density-${ART_DENSITY_DEFAULT} budget of ` +
    `${BUDGETS[ART_DENSITY_DEFAULT].pictures / MB} MB`,
);
assert.ok(
  sounds <= SOUND_BUDGET,
  `sounds: ${(sounds / MiB).toFixed(2)} MiB, past the sound budget`,
);
lines.push(
  `pictures ${(pictures / MB).toFixed(1)} MB (budget ${BUDGETS[1].pictures / MB} MB at 1x, ${BUDGETS[2].pictures / MB} MB at 2x); ` +
    `sounds ${(sounds / MiB).toFixed(2)} MiB (budget ${(SOUND_BUDGET / MiB).toFixed(2)} MiB)`,
);

if (process.argv.includes('--table')) console.log(lines.join('\n'));
console.log(
  'PASS: budgets — world tiles in view fit 12 tiles / 25 MiB at density 1 and 15 / 31 MiB at ' +
    'density 2 on every tested phone; pictures and sounds fit on disk (source and files only).',
);
