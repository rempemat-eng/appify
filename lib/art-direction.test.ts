import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import source from '../art/materials.json';
import { artGeometry, artGrid, artMaterials, artOutline, artSurface } from './art-direction';
import { cardIllustrations } from './card-art';
import { cardIds } from './cards';
import { isVisitorId } from './visitors';
import { worldCatalogue } from './world-catalogue';
import { isWorldId, worldIds, worldMaps } from './world-maps';

// Content contracts, rather than a visual-quality score: bad coordinates, stale
// IDs and missing/mis-sized exports should fail before a preview is published.
const hex = /^#[0-9A-F]{6}$/i;
const keys = (values: readonly string[]) => [...values].sort();
const luminance = (color: string) => {
  const linear = [1, 3, 5].map((offset) => {
    const value = parseInt(color.slice(offset, offset + 2), 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
};

assert.deepEqual(artMaterials, source.materials, 'TS materials use the canonical source');
assert.deepEqual(artSurface, source.surfaces, 'TS surfaces use the canonical source');
assert.deepEqual(artGeometry, source.geometry, 'TS geometry uses the canonical source');
assert.deepEqual(artGrid, source.grid, 'TS grids use the canonical source');
assert.equal(artOutline, source.outline, 'TS outline uses the canonical source');
assert.equal(artGrid.icon, 16, 'miniature artwork uses a 16×16 native grid');
assert.match(artOutline, hex, 'outline colour');
for (const [name, color] of Object.entries(artSurface))
  assert.match(color, hex, `${name} surface colour`);
// Pixel frames have square corners, so radii may be zero; grids must be positive.
for (const [name, size] of Object.entries(artGeometry))
  assert.ok(Number.isInteger(size) && size >= 0, `${name} is a whole number`);
for (const [name, size] of Object.entries(artGrid))
  assert.ok(Number.isInteger(size) && size > 0, `${name} is a positive integer`);
for (const [name, ramp] of Object.entries(artMaterials)) {
  assert.ok(ramp.length > 1, `${name} has a shade and a highlight`);
  ramp.forEach((color, index) => {
    assert.match(color, hex, `${name} shade ${index}`);
    if (index)
      assert.ok(
        luminance(color) > luminance(ramp[index - 1]),
        `${name} shades run from dark to light`,
      );
  });
}

assert.deepEqual(
  keys(Object.keys(cardIllustrations)),
  keys(cardIds),
  'one illustration per card ID',
);
const materialColors = new Set([artOutline, ...Object.values(artMaterials).flat()]);
let pixelCount = 0;
for (const [id, pixels] of Object.entries(cardIllustrations)) {
  assert.ok(pixels.length > 0, `${id} has artwork`);
  const coordinates = new Set<string>();
  for (const pixel of pixels) {
    assert.ok(
      Number.isInteger(pixel.x) && pixel.x >= 0 && pixel.x < artGrid.icon,
      `${id} pixel x fits the native icon grid`,
    );
    assert.ok(
      Number.isInteger(pixel.y) && pixel.y >= 0 && pixel.y < artGrid.icon,
      `${id} pixel y fits the native icon grid`,
    );
    const coordinate = `${pixel.x},${pixel.y}`;
    assert.ok(!coordinates.has(coordinate), `${id} has no duplicate pixel at ${coordinate}`);
    coordinates.add(coordinate);
    assert.match(pixel.color, hex, `${id} pixel colour`);
    assert.ok(materialColors.has(pixel.color), `${id} uses canonical material colours`);
    pixelCount++;
  }
}

// Compare ID sets and look up by key, so catalogue/map insertion order is free.
const mapIds = Object.keys(worldMaps);
assert.equal(new Set(worldIds).size, worldIds.length, 'generated world IDs are unique');
assert.deepEqual(keys(worldIds), keys(mapIds), 'generated IDs cover every world map');
assert.deepEqual(
  keys(Object.keys(worldCatalogue)),
  keys(mapIds),
  'catalogue covers every world map',
);
for (const id of mapIds.toReversed()) {
  assert.ok(isWorldId(id), `${id} is recognised by the generated world-ID guard`);
  const place = worldCatalogue[id];
  assert.ok(place.description.trim(), `${id} has a place description`);
  assert.ok(place.postcardTitle.trim(), `${id} has a postcard title`);
  assert.ok(isVisitorId(place.resident), `${id} resident is an existing visitor`);
}
assert.equal(isWorldId('__missing_world__'), false, 'unknown world IDs are rejected');

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const pngSize = (path: string) => {
  const png = readFileSync(path);
  assert.ok(png.length >= 33, `${path} contains a PNG header`);
  assert.deepEqual(
    png.subarray(0, 8),
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    `${path} PNG signature`,
  );
  assert.equal(png.toString('ascii', 12, 16), 'IHDR', `${path} starts with IHDR`);
  assert.equal(png.readUInt32BE(8), 13, `${path} IHDR length`);
  return [png.readUInt32BE(16), png.readUInt32BE(20)];
};
const sceneDirectory = resolve(root, 'assets/scenes');
const sceneFiles = readdirSync(sceneDirectory).filter((file) => file.endsWith('.png'));
assert.ok(sceneFiles.length > 0, 'generated scene artwork exists');
for (const file of sceneFiles)
  assert.deepEqual(
    pngSize(resolve(sceneDirectory, file)),
    [864, 600],
    `${file} preserves the 216×150 native scene at 4×`,
  );

// Inspect asset paths as data. Importing the manifest would execute PNG imports
// that the app bundler understands but Node's test runner does not.
const manifestPath = resolve(root, 'lib/scene-assets.ts');
const manifest = readFileSync(manifestPath, 'utf8');
const importedPngs = [...manifest.matchAll(/\bfrom\s+['"]([^'"]+\.png)['"]/g)].map(
  (match) => match[1],
);
assert.ok(importedPngs.length > 0, 'scene manifest declares its PNG assets');
for (const asset of importedPngs) {
  const path = asset.startsWith('@/')
    ? resolve(root, asset.slice(2))
    : resolve(dirname(manifestPath), asset);
  pngSize(path);
}
assert.deepEqual(
  pngSize(resolve(root, 'assets/battle/platform-night.png')),
  [192, 72],
  'night battle platform keeps its 48×18 native grid at 4× (step 7b close-up)',
);
for (const layer of ['sky', 'far', 'near'])
  for (const time of ['day', 'night'])
    assert.deepEqual(
      pngSize(resolve(root, `assets/battle/${layer}-${time}.png`)),
      [864, 600],
      `battle ${layer} layer (${time}) keeps the 216×150 field at 4×`,
    );

console.log(
  `PASS: art contracts (${Object.keys(artMaterials).length} material ramps, ${cardIds.length} card illustrations / ${pixelCount} pixels, ${mapIds.length} world identities, ${sceneFiles.length} scenes / ${importedPngs.length} asset imports, night battle platform).`,
);
