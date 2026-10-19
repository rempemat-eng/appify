/**
 * Sprite outline check (npm run check:sprites), coherence plan step 2.
 *
 * Reads the committed sprite PNGs (generated at 6x) and measures, on each side of
 * every silhouette, the share of edge pixels that are outlined: very dark, or
 * clearly darker than the pixel just inside them (outlines are tinted by material).
 * Tiny detached specks (spray, petals) are exempt, as in the generator. Every side
 * of every sprite must be at least 95% outlined.
 *
 * This proves the files, not how they look on a phone.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { PNG } = require('pngjs');

const root = path.join(__dirname, '..');
// Export scale per folder: the garden is exported at 4x since step 6, the rest at 6x.
const SCALE_OF = {
  'assets/garden': 4,
  'assets/garden/growth': 4,
  'assets/garden/hut': 4,
  'assets/worlds/props': 4,
};
const MIN_COVERAGE = 0.95;
const folders = [
  'assets/garden',
  'assets/garden/growth',
  'assets/garden/hut',
  'assets/worlds/props',
  'art/icons',
];
// ground layers (the hut path's flagstones lie flat on the earth path) carry no outline
const skip = /^(ground|water|path|sky|backdrop|platform)/;

function nativePixels(file, SCALE) {
  const png = PNG.sync.read(fs.readFileSync(file));
  const w = png.width / SCALE;
  const h = png.height / SCALE;
  assert.ok(Number.isInteger(w) && Number.isInteger(h), `${file} is a whole 6x sprite`);
  const at = (x, y) => {
    const i = (y * SCALE * png.width + x * SCALE) * 4;
    return png.data.slice(i, i + 4);
  };
  return { w, h, at };
}

const lum = (c) => 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2];

function coverage({ w, h, at }) {
  const solid = (x, y) => x >= 0 && y >= 0 && x < w && y < h && at(x, y)[3] === 255;
  // specks: 8-connected clusters of three pixels or fewer
  const group = new Int32Array(w * h).fill(-1);
  const sizes = [];
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      if (!solid(x, y) || group[y * w + x] >= 0) continue;
      const id = sizes.length;
      const stack = [[x, y]];
      group[y * w + x] = id;
      let size = 0;
      while (stack.length) {
        const [cx, cy] = stack.pop();
        size++;
        for (let dy = -1; dy <= 1; dy++)
          for (let dx = -1; dx <= 1; dx++) {
            const nx = cx + dx;
            const ny = cy + dy;
            if (solid(nx, ny) && group[ny * w + nx] < 0) {
              group[ny * w + nx] = id;
              stack.push([nx, ny]);
            }
          }
      }
      sizes.push(size);
    }
  const counted = (x, y) => solid(x, y) && sizes[group[y * w + x]] > 3;
  const sides = { top: [0, -1], bottom: [0, 1], left: [-1, 0], right: [1, 0] };
  const result = {};
  for (const [side, [dx, dy]] of Object.entries(sides)) {
    let edges = 0;
    let outlined = 0;
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        if (!counted(x, y) || solid(x + dx, y + dy)) continue;
        edges++;
        const value = lum(at(x, y));
        const inside = solid(x - dx, y - dy) ? lum(at(x - dx, y - dy)) : null;
        if (value < 70 || (inside !== null && value <= 0.62 * inside)) outlined++;
      }
    result[side] = edges ? outlined / edges : 1;
  }
  return result;
}

let sprites = 0;
for (const folder of folders)
  for (const name of fs.readdirSync(path.join(root, folder)).sort()) {
    if (!name.endsWith('.png') || skip.test(name)) continue;
    const sides = coverage(nativePixels(path.join(root, folder, name), SCALE_OF[folder] ?? 6));
    for (const [side, share] of Object.entries(sides))
      assert.ok(
        share >= MIN_COVERAGE,
        `${folder}/${name}: ${side} edge only ${Math.round(share * 100)}% outlined`,
      );
    sprites++;
  }
assert.ok(sprites >= 90, `expected the full sprite set, measured ${sprites}`);
console.log(
  `Sprites: ${sprites} sprites outlined on every side (≥ ${MIN_COVERAGE * 100}% of each silhouette edge; files only, not on-device appearance).`,
);
