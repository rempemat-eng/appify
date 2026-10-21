import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import { pixelScale } from './pixel-scale';
import {
  cellsNear,
  regionBounds,
  regionTiles,
  regionWalk,
  TILE,
  type RegionId,
} from './region-walk';
import { regionLayout } from './zone-maps';
import { BACKDROP_ALLOWED, landBox, regionOpensOut } from './world-view';
import type { ArtDensity } from './art-density';

// Load the real generated image map with bundled imports represented by their paths.
// Checking existence keeps a missing import from masquerading as a painted boundary.
const source = readFileSync(new URL('./zone-assets.ts', import.meta.url), 'utf8');
const imageModule = { exports: {} };
runInNewContext(
  ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText,
  {
    module: imageModule,
    exports: imageModule.exports,
    require: (name: string) => {
      assert.match(name, /^@\/assets\/.+\.png$/);
      assert.ok(existsSync(new URL(`../${name.slice(2)}`, import.meta.url)), name);
      return name;
    },
  },
);
const pictures = imageModule.exports as {
  zoneBeyond: string;
  zoneBeyondByRegion: Readonly<Record<string, string>>;
  zoneBeyondAsh: string;
  zoneBeyondPeaks: string;
  zoneBeyondRegolith: string;
  zoneScenery: Readonly<Record<string, string>>;
};
const { zoneBeyondByRegion: beyondByRegion, zoneScenery: scenery } = pictures;
const renderer = readFileSync(new URL('../components/atlas-walk.tsx', import.meta.url), 'utf8');
const beyondStart = renderer.indexOf('function beyondAt(');
assert.ok(beyondStart >= 0, 'the renderer still supplies beyondAt');
const beyondEnd = renderer.indexOf('\n}', beyondStart) + 2;
const beyondAt = runInNewContext(
  ts.transpileModule(renderer.slice(beyondStart, beyondEnd), {}).outputText + '\nbeyondAt;',
  pictures,
) as (region: RegionId, col: number, row: number) => string | undefined;
assert.match(
  renderer,
  /const opensOut = regionOpensOut\(region, zoneBeyondByRegion, zoneScenery\)/,
);

const regions = Object.keys(regionLayout).filter((region): region is RegionId =>
  Object.hasOwn(regionLayout, region),
);

assert.ok(
  BACKDROP_ALLOWED.every(({ reason }) => reason.length > 0),
  'each backdrop has a reason',
);
assert.deepEqual(
  regions.filter((region) => regionOpensOut(region, beyondByRegion, scenery)).sort(),
  ['isles', 'moon', 'steam', 'valley', 'west'],
  'open country, region beyond pictures and per-cell scenery all open out',
);

assert.deepEqual(
  landBox(['####', '#..#', '####'], 4, { width: 16, height: 12 }, 2),
  { x0: 2, x1: 14, y0: 2, y1: 10 },
  'the walkable box includes its requested margin',
);
assert.deepEqual(
  landBox(['##', '##'], 4, { width: 8, height: 8 }, 2),
  { x0: 0, x1: 8, y0: 0, y1: 8 },
  'a fully blocked hand-made grid safely uses its bounds',
);

type Edge = 'top' | 'right' | 'bottom' | 'left';
const allowed = (region: RegionId, edge: Edge) =>
  BACKDROP_ALLOWED.some(
    (entry) => entry.region === region && (entry.edge === 'all' || entry.edge === edge),
  );

function visibleEdges(region: RegionId, width: number, height: number, unit: number): Edge[] {
  const bounds = regionBounds(region);
  const land = landBox(
    regionWalk(region),
    TILE.cell * unit,
    { width: bounds.width * unit, height: bounds.height * unit },
    40 * unit,
  );
  const roomAbove = region === 'valley' || Object.hasOwn(beyondByRegion, region) ? 96 : 0;
  const top = Math.max(-roomAbove, land.y0 - roomAbove);
  const x = land.x1 - land.x0 <= width ? (land.x0 + land.x1 - width) / 2 : land.x0;
  const y = land.y1 - top <= height ? (top + land.y1 - height) / 2 : top;
  const edges: Edge[] = [];
  if (y < 0) edges.push('top');
  if (x + width > bounds.width * unit) edges.push('right');
  if (y + height > bounds.height * unit) edges.push('bottom');
  if (x < 0) edges.push('left');
  return edges;
}

function assertPictures(region: RegionId, edges: readonly Edge[], opensOut: boolean) {
  for (const edge of edges) {
    const picture = opensOut && !(region === 'moon' && edge === 'top');
    assert.ok(picture || allowed(region, edge), `${region}: ${edge} past the land has a picture`);
  }
}

const screens: readonly [number, number, number][] = [
  [320, 568, 2],
  [375, 667, 2],
  [375, 812, 2],
  [402, 874, 3],
  [412, 915, 3.5],
  [440, 956, 3],
];
let cases = 0;
for (const region of regions)
  for (const [width, height, dpr] of screens)
    for (const density of [1, 2] as const satisfies readonly ArtDensity[]) {
      const edges = visibleEdges(region, width, height, pixelScale(width, dpr, density));
      assertPictures(region, edges, regionOpensOut(region, beyondByRegion, scenery));
      cases++;
    }

assert.equal(
  regionOpensOut('steam', {}, { 'steam:0:0': 'synthetic scenery' }),
  true,
  'a hand-made region with only scenery opens out',
);

const steamEdges = visibleEdges('steam', 375, 667, pixelScale(375, 2, 2));
assert.ok(steamEdges.length > 0, 'the hand-made scenery case sees past its land');
assert.throws(
  () => assertPictures('steam', steamEdges, false),
  /steam: .* past the land has a picture/,
  'a region with scenery fails when opensOut is false',
);

// Exercise the renderer's actual camera arithmetic and beyondAt implementation, rather
// than assuming that opensOut itself guarantees an image. Corners and centre cover the
// extrema of the clamped camera; cellsNear enumerates every visible grid cell.
const cameraStart = renderer.indexOf('const cameraAt = (');
const cameraEnd = renderer.indexOf('\n  };', cameraStart) + '\n  };'.length;
assert.ok(cameraStart >= 0 && cameraEnd > cameraStart);
const cameraSource = ts.transpileModule(renderer.slice(cameraStart, cameraEnd), {}).outputText;
let views = 0;
let paintedCells = 0;
for (const region of regions) {
  const bounds = regionBounds(region);
  const tiles = regionTiles(region);
  for (const [width, height, dpr] of screens) {
    for (const density of [1, 2] as const) {
      const u = pixelScale(width, dpr, density);
      const land = landBox(
        regionWalk(region),
        TILE.cell * u,
        { width: bounds.width * u, height: bounds.height * u },
        40 * u,
      );
      const roomAbove = region === 'valley' || Object.hasOwn(beyondByRegion, region) ? 96 : 0;
      const top = Math.max(-roomAbove, land.y0 - roomAbove);
      const cameraAt = runInNewContext(cameraSource + '\ncameraAt;', {
        land,
        top,
        width,
        height,
        u,
      }) as (x: number, y: number, focus: number, bottom: number) => { x: number; y: number };
      for (const x of [land.x0, (land.x0 + land.x1) / 2, land.x1]) {
        for (const y of [land.y0, (land.y0 + land.y1) / 2, land.y1]) {
          const camera = cameraAt(x / u, y / u, 0.55, 0);
          const cells = cellsNear(
            region,
            {
              x0: camera.x / u,
              y0: camera.y / u,
              x1: (camera.x + width) / u,
              y1: (camera.y + height) / u,
            },
            0,
          );
          for (const { col, row } of cells) {
            if (tiles.some((t) => t.col === col && t.row === row)) continue;
            const inside =
              col >= bounds.minCol &&
              row >= bounds.minRow &&
              col < bounds.minCol + bounds.tileCols &&
              row < bounds.minRow + bounds.tileRows;
            const drawn =
              inside ||
              (regionOpensOut(region, beyondByRegion, scenery) && !(region === 'moon' && row < 0));
            if (drawn) {
              assert.ok(
                beyondAt(region, col, row),
                `${region} ${col},${row} at ${width}x${height}@${dpr} density ${density}: real image`,
              );
              paintedCells++;
            } else {
              const edges: Edge[] = [];
              if (col < bounds.minCol) edges.push('left');
              if (col >= bounds.minCol + bounds.tileCols) edges.push('right');
              if (row < bounds.minRow) edges.push('top');
              if (row >= bounds.minRow + bounds.tileRows) edges.push('bottom');
              assert.ok(
                edges.length > 0 &&
                  ((region === 'moon' && row < 0 && allowed(region, 'top')) ||
                    edges.every((edge) => allowed(region, edge))),
                `${region} ${col},${row}: flat backdrop must be explicitly allowed`,
              );
            }
          }
          views++;
        }
      }
    }
  }
}
assert.ok(paintedCells > 0);
console.log(
  `PASS: ${views} real-camera views, ${paintedCells} visible scenery cells have real images.`,
);

console.log(`PASS: world-view pictures cover ${cases} region/screen/density cases.`);
