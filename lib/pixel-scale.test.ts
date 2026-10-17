/**
 * The shared pixel grid (coherence plan, step 6): one art pixel is always a whole
 * number of device pixels, and a phone shows about 300 art pixels across.
 */
import assert from 'node:assert/strict';
import { ART_ACROSS, pixelScale } from './pixel-scale';

const devices: [string, number, number][] = [
  ['iPhone SE (1st)', 320, 2],
  ['iPhone SE', 375, 2],
  ['iPhone 15', 393, 3],
  ['iPhone 16 Pro', 402, 3],
  ['iPhone Pro Max', 430, 3],
  ['Pixel 8', 412, 2.625],
  ['small Android', 360, 3],
  ['desktop', 1280, 1],
  ['retina desktop', 1440, 2],
];
for (const [name, width, dpr] of devices) {
  const css = pixelScale(width, dpr);
  const device = css * dpr;
  assert.ok(Math.abs(device - Math.round(device)) < 1e-9, `${name}: whole device pixels`);
  assert.ok(device >= 2, `${name}: at least two device pixels per art pixel`);
  const across = Math.min(width, 640) / css;
  assert.ok(across > ART_ACROSS * 0.75 && across < ART_ACROSS * 1.25, `${name}: ${across} across`);
}
assert.equal(pixelScale(402, 3), 4 / 3, 'a 3x phone uses 4 device pixels (1.33 CSS px)');
console.log(
  'PASS: pixel scale keeps whole device pixels and about 300 art pixels across on phones and desktop.',
);
