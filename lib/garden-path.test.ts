import assert from 'node:assert/strict';
import { GARDEN, gardenHotspots, gardenObjects } from './garden-map';
import {
  GARDEN_START,
  findPath,
  nearestWalkable,
  randomSpot,
  toCell,
  walkable,
} from './garden-path';

const onGrid = (p: { x: number; y: number }) => {
  const { cx, cy } = toCell(p);
  return walkable(cx, cy);
};

// The Grassling starts somewhere it can move from.
assert.ok(onGrid(GARDEN_START), 'start point is walkable');

// Every interactive object can be reached on foot from the start.
for (const [action, spot] of Object.entries(gardenHotspots)) {
  const path = findPath(GARDEN_START, spot);
  assert.ok(path.length > 0, `path to ${action}`);
  const end = path[path.length - 1];
  assert.ok(
    Math.hypot(end.x - spot.x, end.y - spot.y) <= 12 * GARDEN.cell,
    `${action} end near hotspot`,
  );
  for (const p of path) assert.ok(onGrid(p), `${action} waypoint walkable`);
}

// Every object action has a hotspot.
for (const o of gardenObjects)
  if (o.action) assert.ok(o.action in gardenHotspots, `${o.id} hotspot`);

// Taps on water or off the map snap to the nearest walkable cell instead of failing.
const pond = { x: 42, y: 132 };
assert.ok(findPath(GARDEN_START, pond).length > 0, 'tap in the pond still walks to its edge');
const snapped = nearestWalkable({ x: -50, y: 999 });
assert.ok(walkable(snapped.cx, snapped.cy), 'off-map tap snaps onto the grid');

// Bad input (e.g. a web click without coordinates) never throws or moves the pet.
assert.deepEqual(findPath(GARDEN_START, { x: Number.NaN, y: 10 }), [], 'NaN target is ignored');
assert.deepEqual(findPath(GARDEN_START, GARDEN_START), [], 'no path to where we already are');

// Random strolls stay on walkable ground (deterministic random).
let seed = 1;
const random = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
for (let i = 0; i < 200; i++)
  assert.ok(onGrid(randomSpot(GARDEN_START, 40, random)), 'stroll target walkable');

console.log('PASS: garden pathfinding reaches every object, avoids water, ignores bad taps.');
