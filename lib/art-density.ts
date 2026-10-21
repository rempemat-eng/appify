/**
 * Art density: how many art texels a picture holds per world pixel (Matt, 21 Oct: move
 * toward Eastward's pixel density, an adult about 50 art px instead of 25, decided after a
 * pilot).
 *
 * The density research (21 Oct) recommends exactly 2: 600 texels across, so every phone
 * now sold (1080 to 1440 device px wide) shows 2 device px a texel and today's view, and an
 * adult is 50 texels against Eastward's 54. 1.5 is the second choice (420 across, 3 device
 * px a texel on all those phones). lib/pixel-scale.ts has the grid.
 *
 * The world is measured in world pixels and stays so at every density: positions, walk
 * masks, navigation, hit areas, zones (320 x 576), touch targets and every rule. Only the
 * drawing changes. The game draws on one texel grid, `ART_DENSITY` texels per world pixel
 * (lib/pixel-scale.ts), and every picture is drawn at its world size, so pictures of
 * different densities stand side by side: a 1x picture under a 2x grid is scaled up by
 * nearest neighbour (each of its pixels is 2 x 2 texels), exactly as it looks today.
 *
 * A picture's density is a property of its pixels, so it is measured, not declared: a
 * picture exported at `scale` image px per world px (zones 4, world tiles 2) is made of
 * uniform blocks `scale / density` image px square (`measureDensity`, checked by
 * `npm run check:art-density`). The generators draw a finer picture on a canvas of that
 * density (`Canvas(w, h, density=2)` in scripts/art/pixel.py) and keep the folder's
 * export scale per world px, so a 2x zone picture is 2 image px a texel, one image px a
 * device px on a 3x phone as today, and decodes to the same bytes as a 1x one. No picture
 * may pass 4096 px on a side.
 *
 * Pure, so the checks can read it.
 */
export type ArtDensity = 1 | 1.5 | 2;

/** The densities the engine supports, coarsest first. */
export const ART_DENSITIES: readonly ArtDensity[] = [1, 1.5, 2];

/** The game's density until Matt's pilot verdict. Switch it here (or try another on the
 *  web with `?density=2`, lib/art-density-setting.web.ts). */
export const ART_DENSITY_DEFAULT: ArtDensity = 1;

export function isArtDensity(value: number): value is ArtDensity {
  return (ART_DENSITIES as readonly number[]).includes(value);
}

/** `?density=1`, `1.5` or `2` in an address's query, or null. */
export function densityFromQuery(query: string): ArtDensity | null {
  const match = /[?&]density=([0-9.]+)(?:&|$)/.exec(query);
  const value = match ? Number(match[1]) : NaN;
  return isArtDensity(value) ? value : null;
}

/**
 * The density of a picture from its pixels: the finest of ART_DENSITIES whose texels are
 * needed, that is the coarsest texel (a whole number of image px, `scale / density`) for
 * which every aligned block is one colour. `rgba` is the decoded picture, 4 bytes a pixel;
 * `scale` is its export scale in image px per world px. A picture with no detail finer
 * than its 1x grid measures 1, whatever it was drawn at. Null when no density fits (the
 * picture is not on a whole texel grid, or its size is not a whole number of texels).
 */
export function measureDensity(
  rgba: Uint8Array,
  width: number,
  height: number,
  scale: number,
): ArtDensity | null {
  for (const density of ART_DENSITIES) {
    const k = scale / density;
    if (!Number.isInteger(k) || width % k || height % k) continue;
    if (k === 1 || uniformBlocks(rgba, width, height, k)) return density;
  }
  return null;
}

/** Whether every aligned k x k block of the picture is one colour (alpha 0 counts as one
 *  colour whatever its RGB). */
function uniformBlocks(rgba: Uint8Array, width: number, height: number, k: number) {
  const same = (a: number, b: number) =>
    (rgba[a + 3] === 0 && rgba[b + 3] === 0) ||
    (rgba[a] === rgba[b] &&
      rgba[a + 1] === rgba[b + 1] &&
      rgba[a + 2] === rgba[b + 2] &&
      rgba[a + 3] === rgba[b + 3]);
  for (let y = 0; y < height; y++) {
    const top = y - (y % k);
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      const o = (top * width + (x - (x % k))) * 4;
      if (i !== o && !same(i, o)) return false;
    }
  }
  return true;
}
