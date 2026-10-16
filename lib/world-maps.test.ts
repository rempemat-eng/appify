import assert from 'node:assert/strict';
import { WORLD, worldMaps } from './world-maps';
import { makeWalkGrid } from './garden-path';

// Every mission world is a sound map: the companion can stroll its whole route
// (each leg has a path) and the resident visitor stands on reachable ground.
for (const [id, map] of Object.entries(worldMaps)) {
  const grid = makeWalkGrid(map.walk, {
    cell: WORLD.cell,
    width: WORLD.width,
    start: map.route[0],
  });
  assert.equal(map.walk.length, WORLD.height / WORLD.cell, `${id} grid rows`);
  assert.ok(map.route.length >= 4, `${id} has a real route`);
  const { cx, cy } = grid.toCell(map.route[0]);
  assert.ok(grid.walkable(cx, cy), `${id} route starts on walkable ground`);
  map.route.forEach((p, i) => {
    const next = map.route[(i + 1) % map.route.length];
    const path = grid.findPath(p, next);
    const near = Math.hypot(p.x - next.x, p.y - next.y) < WORLD.cell * 2;
    assert.ok(near || path.length > 0, `${id} leg ${i} is walkable`);
  });
  assert.ok(grid.findPath(map.route[0], map.visitor).length > 0, `${id} visitor reachable`);
  const ids = new Set(map.objects.map((o) => o.id));
  assert.equal(ids.size, map.objects.length, `${id} object ids unique`);
}
console.log(
  'PASS: mission worlds (park, book town, mountain) have walkable routes and reachable visitors.',
);
