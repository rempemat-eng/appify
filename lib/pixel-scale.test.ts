/**
 * The shared pixel grid (coherence plan, step 6) at every art density (lib/art-density.ts):
 * one texel is always a whole number of device pixels, a phone shows about 300 world pixels
 * across, and density 1 (the default) is exactly the grid the game had before densities.
 * The phones are the density research's (21 Oct): every iPhone and Android now sold is 1080
 * to 1440 device px wide.
 */
import assert from 'node:assert/strict';
import { ART_DENSITIES, ART_DENSITY_DEFAULT, type ArtDensity } from './art-density';
import {
  ART_ACROSS,
  ART_ACROSS_AT,
  WORLD_ACROSS,
  assetUnit,
  crispOn,
  pixelGrid,
  pixelScale,
  snapToDevice,
} from './pixel-scale';

const whole = (value: number) => Math.abs(value - Math.round(value)) < 1e-9;

/** name, CSS width, device pixel ratio (CSS width x ratio = device px across) */
const devices: [string, number, number][] = [
  ['iPhone 16e', 390, 3],
  ['iPhone 16', 393, 3],
  ['iPhone 17 Pro', 402, 3],
  ['iPhone Air', 420, 3],
  ['iPhone 17 Pro Max', 440, 3],
  ['iPhone SE (3rd)', 375, 2],
  ['iPhone SE (1st)', 320, 2],
  ['Pixel 9', 412, 2.625],
  ['Galaxy S25', 360, 3],
  ['Pixel 9 Pro', 410, 1280 / 410],
  ['Pixel 9 Pro XL', 448, 3],
  ['S25 Ultra QHD+', 412, 3.5],
  ['desktop', 1280, 1],
  ['retina desktop', 1440, 2],
];
/** The phones now sold: 1080 to 1440 device px across. */
const current = devices.filter(([, w, dpr]) => w * dpr >= 1079 && w * dpr <= 1443 && w <= 640);
assert.equal(current.length, 10);

// ---- density 1, the default: unchanged ------------------------------------------------------
assert.equal(ART_DENSITY_DEFAULT, 1, 'the game stays at density 1 until the pilot verdict');
assert.equal(ART_ACROSS, ART_ACROSS_AT[ART_DENSITY_DEFAULT]);
assert.equal(ART_ACROSS_AT[1], WORLD_ACROSS);
/** The grid before art densities existed (main at 02794e7), for the regression below. */
const before = (width: number, dpr: number) => {
  const ratio = dpr > 0 ? dpr : 1;
  return Math.max(1, Math.round((Math.min(width, 640) * ratio) / 300)) / ratio;
};
for (let width = 240; width <= 2000; width += 1)
  for (const dpr of [1, 1.25, 1.5, 2, 2.25, 2.625, 3, 3.5, 4])
    assert.equal(pixelScale(width, dpr), before(width, dpr), `${width}/${dpr}: unchanged`);

for (const [name, width, dpr] of devices) {
  if (name === 'iPhone SE (1st)' || width * dpr < 750) continue;
  const css = pixelScale(width, dpr, 1);
  const device = css * dpr;
  assert.ok(whole(device), `${name}: whole device pixels`);
  assert.ok(device >= 2, `${name}: at least two device pixels per art pixel`);
  const across = Math.min(width, 640) / css;
  assert.ok(
    across > WORLD_ACROSS * 0.75 && across < WORLD_ACROSS * 1.25,
    `${name}: ${across} across`,
  );
}
assert.equal(pixelScale(402, 3, 1), 4 / 3, 'a 3x phone uses 4 device pixels (1.33 CSS px)');
// A narrow window on a 1x screen keeps one device pixel per art pixel, so the
// interface designed for about 300 across still fits instead of overflowing.
for (const width of [320, 360, 402]) {
  const css = pixelScale(width, 1, 1);
  assert.equal(css, 1, `a ${width} px window at 1x uses one device pixel`);
  assert.ok(
    width / css >= WORLD_ACROSS,
    `a ${width} px window at 1x shows at least ${WORLD_ACROSS} across`,
  );
}

// ---- every density: whole device pixels per texel ------------------------------------------
const table: string[] = [];
for (const density of ART_DENSITIES)
  for (const [name, width, dpr] of devices) {
    const grid = pixelGrid(width, dpr, density);
    assert.equal(grid.density, density, `${name} at ${density}: no fallback on a real screen`);
    assert.ok(Number.isInteger(grid.deviceTexel) && grid.deviceTexel >= 1, `${name}: texel`);
    assert.ok(whole(grid.texel * dpr), `${name} at ${density}: a texel is whole device pixels`);
    assert.ok(Math.abs(grid.unit - grid.texel * density) < 1e-9, `${name}: unit = density texels`);
    assert.ok(Math.abs(grid.unit - pixelScale(width, dpr, density)) < 1e-9);
    // art of the grid's own density is always crisp, at one texel a pixel
    assert.ok(crispOn(grid, density), `${name} at ${density}: its own art is crisp`);
    assert.ok(Math.abs(assetUnit(grid, density) - grid.texel) < 1e-9);
    // the field of view stays about where it is: within -25% and +45% of 300 world px
    const across = Math.min(width, 640) / grid.unit;
    assert.ok(
      across >= WORLD_ACROSS * 0.75 && across < WORLD_ACROSS * 1.45,
      `${name} at ${density}: ${across.toFixed(0)} world px across`,
    );
    table.push(
      `${name.padEnd(18)} ${String(density).padEnd(4)} ${String(grid.deviceTexel).padStart(2)} dev/texel ` +
        `${(grid.unit * dpr).toFixed(1).padStart(4)} dev/world px ${across.toFixed(0).padStart(4)} across ` +
        `1x art ${crispOn(grid, 1) ? 'crisp' : 'uneven'}`,
    );
  }

// Density 2 (the research's recommendation): every current phone gets 2 device px a texel,
// 1x art (2 x 2 texels a pixel) and 2x art are both crisp on every screen, and the world
// unit, so the view, is exactly today's wherever the old grid gave 4 (or 2) device px.
for (const [name, width, dpr] of current) {
  assert.equal(pixelGrid(width, dpr, 2).deviceTexel, 2, `${name}: 2 device px a texel`);
  // within -10% and +20% of today's design width
  const across = width / pixelScale(width, dpr, 2);
  assert.ok(across >= 270 && across <= 361, `${name}: ${across} across at density 2`);
}
for (const [name, width, dpr] of devices) {
  const grid = pixelGrid(width, dpr, 2);
  assert.ok(crispOn(grid, 1) && crispOn(grid, 2), `${name}: 1x and 2x art crisp at density 2`);
  const old = pixelScale(width, dpr, 1) * dpr;
  if (old === 4 || old === 2)
    assert.equal(grid.unit, pixelScale(width, dpr, 1), `${name}: same view at density 2`);
}
assert.equal(pixelScale(402, 3, 2), 4 / 3, 'a 3x phone: still 1.33 CSS px a world pixel');
// an adult (25 world px) is 50 texels at density 2, the same height on screen
assert.equal(25 * 2 * pixelGrid(402, 3, 2).deviceTexel, Math.round(25 * pixelScale(402, 3, 1) * 3));
// the old 2x iPhone SE gets one device px a texel and sees its full width
assert.equal(pixelGrid(375, 2, 2).deviceTexel, 1);
assert.equal(pixelScale(375, 2, 2), 1);

// Density 1.5 (second choice): 420 across holds every current phone at 3 device px a texel
// (450 would split iPhones at 3 from 1080 Androids at 2), and 1x art is then uneven
// (4.5 device px a pixel) on all of them.
assert.equal(ART_ACROSS_AT[1.5], 420);
for (const [name, width, dpr] of current) {
  const grid = pixelGrid(width, dpr, 1.5);
  assert.equal(grid.deviceTexel, 3, `${name}: 3 device px a texel at 1.5`);
  assert.ok(!crispOn(grid, 1), `${name}: 1x art is uneven at 1.5`);
  assert.ok(!crispOn(grid, 2), `${name}: 2x art never fits 1.5`);
}
for (const [name, width, dpr] of devices) {
  const grid = pixelGrid(width, dpr, 1.5);
  assert.equal(crispOn(grid, 1), grid.deviceTexel % 2 === 0, `${name}: 1x art at 1.5`);
}
// 1.5x art does not sit on a 2x grid
assert.ok(!crispOn(pixelGrid(402, 3, 2), 1.5));

// A window too narrow for its density's texel steps down one device px a texel, and where a
// texel is already one device px (a 1x screen under 450 px at density 2) falls back to
// density 1 so the interface fits; finer art then draws smaller than its texels.
// (density 1 goes down to 225 across, in a 450 px window at 1x: the same floor)
for (const [density, width] of [
  [2, 320],
  [2, 360],
  [2, 402],
  [2, 449],
  [1.5, 320],
] as [ArtDensity, number][]) {
  const grid = pixelGrid(width, 1, density);
  assert.equal(grid.density, 1, `a ${width} px window at 1x falls back from ${density}`);
  assert.equal(grid.unit, 1);
  assert.ok(!crispOn(grid, density));
}
for (const [density, width] of [
  [2, 450],
  [2, 1280],
  [1.5, 360],
  [1.5, 640],
  [1.5, 1280],
] as [ArtDensity, number][]) {
  const grid = pixelGrid(width, 1, density);
  assert.equal(grid.density, density, `a ${width} px window at 1x keeps ${density}`);
  assert.ok(Math.min(width, 640) / grid.unit >= 225);
}
assert.equal(pixelGrid(1280, 1, 2).unit, 2, 'a desktop at density 2: 2 CSS px a world pixel');
assert.equal(pixelGrid(1280, 1, 1.5).deviceTexel, 1, 'at 1.5: stepped down from 2 to 1');

// Tiles and props placed at whole world pixels land on the texel grid at density 2.
for (const [name, width, dpr] of devices) {
  const grid = pixelGrid(width, dpr, 2);
  for (const x of [0, 1, 7, 256, 333]) {
    const left = snapToDevice(x * grid.unit, dpr) * dpr;
    assert.ok(whole(left / grid.deviceTexel), `${name}: world x ${x} on the texel grid`);
  }
}

if (process.argv.includes('--table')) console.log(table.join('\n'));
console.log(
  'PASS: the pixel grid keeps whole device pixels per texel at densities 1, 1.5 and 2 (2 device ' +
    'px a texel on every current phone at 2, 3 at 1.5), about 300 world px across, and density 1 ' +
    'unchanged.',
);
