import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { pixelScale } from './pixel-scale';
import { regionBounds, regionWalk, TILE, type RegionId } from './region-walk';
import { regionLayout } from './zone-maps';
import { BACKDROP_ALLOWED, landBox, regionOpensOut } from './world-view';
import type { ArtDensity } from './art-density';

const source = readFileSync(new URL('./zone-assets.ts', import.meta.url), 'utf8');
const between = (start: string, end: string) => source.split(start, 2)[1].split(end, 1)[0];
const beyondSource = between('export const zoneBeyondByRegion', 'export const zoneBeyondAsh');
const scenerySource = source.split('export const zoneScenery', 2)[1];
const beyondByRegion = Object.fromEntries(
  [...beyondSource.matchAll(/^\s*([a-z]+):/gm)].map((match) => [match[1], true]),
);
const scenery = Object.fromEntries(
  [...scenerySource.matchAll(/^\s*'([^']+)':/gm)].map((match) => [match[1], true]),
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

const steamEdges = visibleEdges('steam', 375, 667, pixelScale(375, 2, 2));
assert.ok(steamEdges.length > 0, 'the hand-made scenery case sees past its land');
assert.throws(
  () => assertPictures('steam', steamEdges, false),
  /steam: .* past the land has a picture/,
  'a region with scenery fails when opensOut is false',
);

console.log(`PASS: world-view pictures cover ${cases} region/screen/density cases.`);
