import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { regionLayout } from './zone-maps';
import { regionBounds, regionTiles, tileOrigin, TILE, type RegionId } from './region-walk';
import { regionPoint, travelPoints } from './world-places';
import {
  cameraOffset,
  mountedNeighbours,
  regionEdges,
  screenToWorld,
  beginJourney,
  cancelJourney,
  finishJourney,
  idleJourney,
  skipJourney,
} from './world-travel';

let checks = 0;
const ok = (v: unknown, label: string) => {
  assert.ok(v, label);
  checks++;
};
const regions = Object.keys(regionLayout) as RegionId[];
// Execute only the actual pure camera worklet body at a substituted boundary.
// This catches drift while Claude's renderer still owns the inline calculation.
const cameraBody = readFileSync(
  new URL('../components/atlas-walk.tsx', import.meta.url),
  'utf8',
).match(/const cameraStyle = useAnimatedStyle\(\(\) => \{([\s\S]*?)\n  \}\);/)?.[1];
assert.ok(cameraBody, 'AtlasWalk camera worklet must be covered or its adapter updated');
for (const region of regions) {
  const tiles = regionTiles(region);
  const bounds = regionBounds(region);
  const all = JSON.stringify(tiles);
  for (const tile of tiles) {
    const neighbours = mountedNeighbours(region, tile.id);
    ok(
      neighbours.length > 0 && neighbours.length <= 9,
      `${region}/${tile.id}: bounded 3x3 neighbourhood`,
    );
    ok(
      neighbours.some((n) => n.id === tile.id),
      'current zone remains mounted',
    );
    for (const other of tiles)
      ok(
        neighbours.some((n) => n.id === other.id) ===
          (Math.abs(other.col - tile.col) <= 1 && Math.abs(other.row - tile.row) <= 1),
        'neighbours derive from the actual grid, including diagonals',
      );
    const o = tileOrigin(region, tile);
    ok(
      o.x >= 0 &&
        o.y >= 0 &&
        o.x + TILE.width <= bounds.width &&
        o.y + TILE.height <= bounds.height,
      'negative layout coordinates normalize into region pixels',
    );
  }
  ok(
    mountedNeighbours(region, 'not-a-zone' as never).length === 0,
    'unknown zone does not mount unrelated art',
  );
  const edges = regionEdges(region);
  ok(
    new Set(edges.map(({ a, b }) => [a.id, b.id].sort().join(':'))).size === edges.length,
    'each physical edge occurs once',
  );
  if (tiles.length === 1) ok(edges.length === 0, 'singleton region has no imaginary foot edge');
  for (const { a, b, direction } of edges) {
    const o = tileOrigin(region, a);
    const border =
      direction === 'east'
        ? { x: o.x + TILE.width, y: o.y + TILE.height / 2 }
        : { x: o.x + TILE.width / 2, y: o.y + TILE.height };
    const axis = direction === 'east' ? 'x' : 'y';
    const other = axis === 'x' ? 'y' : 'x';
    ok(
      mountedNeighbours(region, a.id).some((t) => t.id === b.id) &&
        mountedNeighbours(region, b.id).some((t) => t.id === a.id),
      'both sides are pre-mounted across each border',
    );
    for (const width of [320, 402, 768])
      for (const scale of [1, 4 / 3, 2])
        for (const padBottom of [0, 240]) {
          const view = { width, height: 640, scale, padBottom, focusY: padBottom ? 0.3 : 0.55 };
          const left = cameraOffset(region, { ...border, [axis]: border[axis] - 0.01 }, view);
          const right = cameraOffset(region, { ...border, [axis]: border[axis] + 0.01 }, view);
          ok(
            Math.abs(right[axis] - left[axis]) <= 0.02 * scale + 1e-8 &&
              right[other] === left[other],
            'crossing a tile border cannot reset the camera origin',
          );
          const centre = cameraOffset(region, border, view);
          const rendered = runInNewContext(`(() => {${cameraBody}})()`, {
            regionW: bounds.width * scale,
            regionH: bounds.height * scale,
            width,
            height: view.height,
            padBottom,
            focusY: view.focusY,
            px: { value: border.x },
            py: { value: border.y },
            u: scale,
          });
          ok(
            rendered.transform[0].translateX === -Math.round(centre.x) &&
              rendered.transform[1].translateY === -Math.round(centre.y),
            'actual camera worklet and pure model agree after the renderer pixel snap',
          );
          const tap = screenToWorld(region, border, view, {
            x: border.x * scale - centre.x,
            y: border.y * scale - centre.y,
          });
          ok(
            Math.abs(tap.x - border.x) < 1e-8 && Math.abs(tap.y - border.y) < 1e-8,
            'tap conversion shares the rendered camera with card padding',
          );
        }
  }
  ok(JSON.stringify(tiles) === all, 'geometry inspection never mutates generated data');
}
for (const view of [
  { width: 0, height: 640, scale: 1 },
  { width: 320, height: 640, scale: 0 },
  { width: 320, height: 640, scale: NaN },
  { width: 320, height: 640, scale: 1, focusY: 2 },
  { width: 320, height: 640, scale: 1, padBottom: -1 },
]) {
  assert.throws(() => cameraOffset('valley', { x: 0, y: 0 }, view), RangeError);
  checks++;
}
const destinations = regions.filter((r) => travelPoints[r]);
for (const from of destinations)
  for (const to of destinations) {
    let state = beginJourney(idleJourney(), from, to, true);
    if (from === to) {
      ok(!state.pending, 'same-region selection is not a vehicle trip');
      continue;
    }
    const ticket = state.pending!;
    const saved = { region: from, ...regionPoint(travelPoints[from]!), visited: ['town'] };
    const original = JSON.stringify(saved);
    const expected = regionPoint(travelPoints[to]!);
    const complete = finishJourney(state, ticket, { region: from, enabled: true }, saved);
    ok(
      complete.arrival?.region === to &&
        complete.arrival.x === Math.round(expected.x) &&
        complete.arrival.y === Math.round(expected.y),
      'journeys use the existing generated arrival station',
    );
    ok(
      complete.arrival?.visited.includes('town') && !complete.state.pending,
      'arrival keeps visits and consumes the ticket',
    );
    ok(
      !finishJourney(complete.state, ticket, { region: from, enabled: true }, saved).arrival,
      'late timer after finish cannot arrive twice',
    );
    ok(
      !skipJourney(complete.state, ticket, { region: from, enabled: true }, saved).arrival,
      'skip after timer cannot arrive twice',
    );
    ok(
      skipJourney(state, ticket, { region: from, enabled: true }, saved).arrival?.region === to,
      'skip uses the same arrival',
    );
    ok(
      !finishJourney(cancelJourney(state), ticket, { region: from, enabled: true }, saved).arrival,
      'Back/background/unmount cancellation rejects queued callbacks',
    );
    ok(
      !finishJourney(state, ticket, { region: from, enabled: false }, saved).arrival,
      'late completion rechecks active/focused/awake eligibility',
    );
    ok(
      !finishJourney(state, ticket, { region: to, enabled: true }, saved).arrival,
      'another region entry rejects a stale source',
    );
    ok(
      !finishJourney(state, { ...ticket }, { region: from, enabled: true }, saved).arrival,
      'a structural ticket copy cannot impersonate this trip',
    );
    const replacement = beginJourney(state, from, to, true);
    const stale = finishJourney(replacement, ticket, { region: from, enabled: true }, saved);
    ok(
      !stale.arrival && stale.state === replacement,
      'an old callback cannot cancel or complete a replacement trip',
    );
    ok(
      !finishJourney(
        beginJourney(idleJourney(), from, to, true),
        ticket,
        { region: from, enabled: true },
        saved,
      ).arrival,
      'remounting does not reuse a ticket identity',
    );
    ok(
      beginJourney(state, from, to, false) === state,
      'disabled requests leave an active trip unchanged',
    );
    ok(JSON.stringify(saved) === original, 'trip decisions never mutate existing world history');
  }
ok(
  !beginJourney(idleJourney(), 'home', 'valley', true).pending,
  'hut door is not a fabricated station',
);
ok(
  !beginJourney(idleJourney(), 'valley', 'home', true).pending,
  'hut remains a door, not a vehicle destination',
);
console.log(
  `World travel model: ${checks} geometry and stale-journey assertions passed; renderer integration not claimed.`,
);
