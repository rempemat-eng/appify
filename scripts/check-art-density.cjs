/**
 * Art density check (npm run check:art-density), lib/art-density.ts.
 *
 * Measures every picture under assets/ from its pixels: on its folder's export scale (image
 * px per world px), the coarsest whole texel grid it is drawn on, as 1x, 1.5x or 2x. Fails
 * when a picture is on no supported grid, when 1.5x and 2x pictures are both present (they
 * never share a grid, lib/pixel-scale.ts), or when a picture passes 4096 px on a side (the
 * texture size every phone supports; the old zones' moving-water strips are listed and
 * retire with the zones). Prints how many pictures there are at each density per folder.
 *
 * `--cost` also prints the decoded memory of the world's pictures per zone and per region,
 * today and redrawn at density 2 and 1.5 under the export rule in lib/art-density.ts.
 *
 * Decodes about 1,300 PNGs (about 25 s), so it runs on its own, not in `npm run check`.
 * This proves the files, not how they look on a phone.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const { PNG } = require('pngjs');

const root = path.join(__dirname, '..');
const load = (file) => {
  const module = { exports: {} };
  const source = ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  vm.runInNewContext(source, { module, exports: module.exports, require });
  return module.exports;
};
const { ART_DENSITIES, measureDensity } = load('lib/art-density.ts');

/** Export scale (image px per world px) by picture: the generators' own constants. */
function exportScale(file) {
  if (/^assets\/zones\/[^/]+\/flow\.png$/.test(file)) return 1; // zones.py: native, pixelated
  if (/^assets\/world\/[^/]+\/f_/.test(file)) return 1; // world_canvas.py: moving water at 1x
  if (file.startsWith('assets/world/')) return 2; // WORLD_TILE.scale
  if (file.startsWith('assets/zones/scenery/')) return 2; // zones.py SCENERY_SCALE
  if (file === 'assets/journeys/rocket/sky.png') return 1; // rocket.py SKY_SCALE
  if (file.startsWith('assets/journeys/rocket/')) return 2; // rocket.py SCALE
  if (file.startsWith('assets/scenes/')) return 2; // vignettes.py: exported at 2x
  return 4; // garden, zones, worlds, residents, journeys, battle, decor, missions
}
/** Pictures past 4096 px today: the zones' moving water, 8 frames stacked (retire with the
 *  zones, docs/vision/region-canvas.md step 3). */
const legacyTall = /^assets\/zones\/[^/]+\/flow\.png$/;
const MAX_SIDE = 4096;
/** Image px a texel under the export rule in cost(). */
const perTexel = (density, scale) => (scale === 4 ? (density === 2 ? 2 : 3) : 1);

const pictures = [];
(function walk(dir) {
  for (const name of fs.readdirSync(dir).sort()) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) walk(full);
    else if (name.endsWith('.png'))
      pictures.push(path.relative(root, full).split(path.sep).join('/'));
  }
})(path.join(root, 'assets'));

const failures = [];
const counts = new Map();
const measured = new Map();
for (const file of pictures) {
  const png = PNG.sync.read(fs.readFileSync(path.join(root, file)));
  const scale = exportScale(file);
  const density = measureDensity(png.data, png.width, png.height, scale);
  measured.set(file, { w: png.width, h: png.height, scale, density });
  if (density === null)
    failures.push(`${file}: not on a whole 1x, 1.5x or 2x texel grid at ${scale} px a world px`);
  if (Math.max(png.width, png.height) > MAX_SIDE && !legacyTall.test(file))
    failures.push(`${file}: ${png.width} x ${png.height} passes ${MAX_SIDE} px`);
  const folder = path.posix.dirname(file).replace(/^assets\//, '');
  const key = /^zones\/(?!props|scenery)[^/]+$/.test(folder)
    ? 'zones/<zone>'
    : folder.startsWith('world/')
      ? 'world/<plane>'
      : folder;
  const row = counts.get(key) ?? { 1: 0, 1.5: 0, 2: 0, none: 0 };
  row[density ?? 'none']++;
  counts.set(key, row);
}
const finer = new Set([...measured.values()].map((m) => m.density).filter((d) => d && d > 1));
if (finer.size > 1) failures.push(`1.5x and 2x pictures are both present: they never share a grid`);

console.log('Pictures by measured density (texels per world px):');
console.log('  folder                 1x   1.5x  2x');
for (const [key, row] of [...counts].sort(([a], [b]) => a.localeCompare(b)))
  console.log(
    `  ${key.padEnd(20)} ${String(row[1]).padStart(4)} ${String(row[1.5]).padStart(5)} ${String(row[2]).padStart(4)}` +
      (row.none ? `  ${row.none} on no grid` : ''),
  );
const tall = pictures.filter(
  (f) => legacyTall.test(f) && Math.max(measured.get(f).w, measured.get(f).h) > MAX_SIDE,
);
console.log(
  `  ${tall.length} old moving-water strips pass ${MAX_SIDE} px (listed; they retire with the zones)`,
);

if (process.argv.includes('--cost')) cost();

assert.deepEqual(failures, [], failures.join('\n'));
assert.ok(ART_DENSITIES.length === 3);
console.log(
  `PASS: ${pictures.length} pictures, each on a whole texel grid, none new past ${MAX_SIDE} px.`,
);

/**
 * Decoded memory (w x h x 4) of the world's pictures, per zone and per region: today, and
 * redrawn at density d with p image px a texel, (d p / scale)^2 times today's. The export
 * rule (lib/art-density.ts): pictures that are one image px a device px on a 3x phone today
 * (scale 4) stay so (p = the phone's device px a texel: 2 at density 2, 3 at 1.5); world
 * tiles and scenery (scale 2) and moving water (scale 1) keep one image px a texel. "Naive"
 * keeps today's image px a texel (p = scale): d^2 times today's.
 */
function cost() {
  const MiB = 1024 * 1024;
  const maps = load('lib/zone-maps.ts');
  const at = (file, density, naive = false) => {
    const m = measured.get(file);
    const f = naive || density === 1 ? density : (density * perTexel(density, m.scale)) / m.scale;
    return m.w * m.h * 4 * f * f;
  };
  const zoneFiles = (zone) => {
    if (zone === 'garden') return pictures.filter((f) => f.startsWith('assets/garden/'));
    const own = ['ground', 'top', 'flow', 'deck', 'deck-shadow']
      .map((n) => `assets/zones/${zone}/${n}.png`)
      .filter((f) => measured.has(f));
    const sprites = new Set(maps.zoneMaps[zone].objects.map((o) => o[1]));
    const props = pictures.filter((f) => {
      const m = /^assets\/zones\/props\/(.+?)(_f\d+)?\.png$/.exec(f);
      return m && sprites.has(m[1]);
    });
    return [...own, ...props];
  };
  const columns = [
    ['today', (f) => at(f, 1)],
    ['2x', (f) => at(f, 2)],
    ['2x naive', (f) => at(f, 2, true)],
    ['1.5x', (f) => at(f, 1.5)],
    ['1.5x naive', (f) => at(f, 1.5, true)],
  ];
  const sum = (files, fn) => files.reduce((a, f) => a + fn(f), 0) / MiB;
  const line = (label, files) =>
    `  ${label.padEnd(22)}` +
    columns.map(([, fn]) => sum(files, fn).toFixed(1).padStart(11)).join('');
  console.log('\nDecoded MiB (ground, top, deck, moving water and the props each zone places):');
  console.log('  ' + ''.padEnd(22) + columns.map(([n]) => n.padStart(11)).join(''));
  const perZone = [];
  for (const [region, zones] of Object.entries(maps.regionLayout)) {
    const all = new Set();
    for (const zone of Object.keys(zones)) {
      const files = zoneFiles(zone);
      files.forEach((f) => all.add(f));
      perZone.push([zone, files]);
      console.log(line(`${region}/${zone}`, files));
    }
    console.log(line(`${region} (all loaded)`, [...all]));
  }
  const totals = perZone.map(([, files]) => columns.map(([, fn]) => sum(files, fn)));
  const median = columns.map(
    (_, i) => totals.map((t) => t[i]).sort((a, b) => a - b)[totals.length >> 1],
  );
  console.log(
    '  ' + 'median zone'.padEnd(22) + median.map((v) => v.toFixed(1).padStart(11)).join(''),
  );
  const water = pictures.filter((f) => measured.get(f).scale === 1 && /flow|\/f_/.test(f));
  console.log(line('moving water, all', water));
  const tiles = pictures.filter((f) => /^assets\/world\/[^/]+\/t_/.test(f));
  console.log(line('world tiles, all', tiles));
  console.log(line('every picture', pictures));
  const tallAt2 = pictures.filter((f) => {
    const m = measured.get(f);
    const k = (2 * perTexel(2, m.scale)) / m.scale;
    return Math.max(m.w, m.h) * k > MAX_SIDE;
  });
  console.log(
    `  at 2x, ${tallAt2.length} pictures would pass ${MAX_SIDE} px: ${tallAt2.slice(0, 4).join(', ')}${tallAt2.length > 4 ? ', ...' : ''}`,
  );
}
