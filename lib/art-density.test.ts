/**
 * Art density (lib/art-density.ts): the address switch and the measurement that reads a
 * picture's density from its pixels. `npm run check:art-density` runs the measurement over
 * every picture in assets/.
 */
import assert from 'node:assert/strict';
import {
  ART_DENSITIES,
  ART_DENSITY_DEFAULT,
  densityFromQuery,
  isArtDensity,
  measureDensity,
  type ArtDensity,
} from './art-density';
import { ART_DENSITY } from './art-density-setting';

assert.deepEqual(ART_DENSITIES, [1, 1.5, 2]);
assert.equal(ART_DENSITY, ART_DENSITY_DEFAULT, 'native reads the default');
assert.ok(isArtDensity(2) && isArtDensity(1.5) && !isArtDensity(3) && !isArtDensity(1.75));
assert.equal(densityFromQuery('?density=2'), 2);
assert.equal(densityFromQuery('?world=canvas&density=1.5'), 1.5);
assert.equal(densityFromQuery('?density=1&station=pier'), 1);
assert.equal(densityFromQuery('?density=3'), null);
assert.equal(densityFromQuery('?density=20'), null);
assert.equal(densityFromQuery('?xdensity=2'), null);
assert.equal(densityFromQuery(''), null);

/** A w x h world px picture drawn at `density` with seeded texels, exported at `scale`
 *  image px per world px by nearest neighbour (as scripts/art/pixel.py saves it). */
function picture(w: number, h: number, density: ArtDensity, scale: number, seed = 1) {
  const tw = w * density;
  const th = h * density;
  const per = scale / density;
  let s = seed;
  const texels = Array.from({ length: tw * th }, () => {
    s = (s * 1103515245 + 12345) % 2147483648;
    return [s & 255, (s >> 8) & 255, (s >> 16) & 255, s % 5 ? 255 : 0];
  });
  const W = tw * per;
  const H = th * per;
  const rgba = new Uint8Array(W * H * 4);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++)
      rgba.set(texels[Math.floor(y / per) * tw + Math.floor(x / per)], (y * W + x) * 4);
  return { rgba, W, H };
}

// Each density reads back on its own export: zones at 4 image px a world px (2x is 2 image
// px a texel), world tiles at 2 (2x is 1), and 1.5x at 3 or 6.
for (const [density, scale] of [
  [1, 4],
  [2, 4],
  [1, 2],
  [2, 2],
  [1, 1],
  [1.5, 3],
  [1.5, 6],
  [1, 6],
  [2, 6],
] as [ArtDensity, number][]) {
  const { rgba, W, H } = picture(12, 8, density, scale);
  assert.equal(measureDensity(rgba, W, H, scale), density, `${density}x at scale ${scale}`);
}
// A 2x picture whose texels pair up everywhere has no 2x detail: it reads as 1x.
{
  const { rgba, W, H } = picture(6, 4, 1, 4);
  assert.equal(measureDensity(rgba, W, H, 4), 1);
}
// One stray image px breaks the grid it sits in.
{
  const { rgba, W, H } = picture(6, 4, 1, 4);
  rgba[(1 * W + 1) * 4 + 3] ^= 1;
  assert.equal(measureDensity(rgba, W, H, 4), null, 'a lone image px is on no texel grid');
  const fine = picture(6, 4, 2, 4);
  fine.rgba[(2 * fine.W + 3) * 4 + 3] ^= 1;
  assert.equal(measureDensity(fine.rgba, fine.W, fine.H, 4), null);
}
// Transparent pixels count as one colour whatever their RGB.
{
  const { rgba, W, H } = picture(4, 4, 1, 4, 7);
  for (let i = 0; i < W * H; i++) if (rgba[i * 4 + 3] === 0) rgba[i * 4] = i & 255;
  assert.equal(measureDensity(rgba, W, H, 4), 1);
}
// A size that is not a whole number of texels fits no grid.
assert.equal(measureDensity(new Uint8Array(5 * 4 * 4), 5, 4, 4), null);

console.log("PASS: art densities read from the address and measured from a picture's pixels.");
