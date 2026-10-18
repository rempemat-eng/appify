import assert from 'node:assert/strict';
import { gardenAnchors } from './garden-map';
import { makeWalkGrid } from './garden-path';
import { regionTiles, regionWalk, tileOrigin, regionBounds, TILE } from './region-walk';
import { zoneIds } from './zone-maps';
import {
  worldZoneIds,
  worldRegionIds,
  worldExits,
  worldZoneStart,
  freshWorldProgress,
  restoreWorldProgress,
  currentWorldZone,
  canEnterWorldZone,
  exitsFromWorldZone,
  createWorldWalkGuard,
  enterWorldZone,
  type WorldZoneId,
} from './world-zones';

const access = { level: 4, mountainLevel: 2 };
let assertions = 0;
function equal(actual: unknown, expected: unknown, label: string) {
  assert.deepEqual(actual, expected, label);
  assertions++;
}
equal(
  [...worldZoneIds].sort(),
  ['garden', ...zoneIds].sort(),
  'catalogue follows every generated zone',
);
equal(worldZoneStart('garden'), gardenAnchors.start, 'garden spawn comes from art data');
equal(worldExits.length > 0, true, 'walking graph exists');
equal(new Set(worldExits.map((e) => e.id)).size, worldExits.length, 'exit ids unique');
for (const exit of worldExits) {
  const back = worldExits.find(
    (e) =>
      e.from === exit.to &&
      e.to === exit.from &&
      e.departure.x === exit.entry.x &&
      e.departure.y === exit.entry.y,
  );
  equal(back?.entry, exit.departure, `${exit.id}: exact matching entry and return`);
  const region = worldRegionIds.find((r) => regionTiles(r).some((t) => t.id === exit.from))!;
  const tiles = regionTiles(region),
    rows = regionWalk(region),
    b = regionBounds(region);
  const from = tiles.find((t) => t.id === exit.from)!,
    to = tiles.find((t) => t.id === exit.to)!;
  const a = tileOrigin(region, from),
    z = tileOrigin(region, to);
  const departure = { x: a.x + exit.departure.x, y: a.y + exit.departure.y };
  const entry = { x: z.x + exit.entry.x, y: z.y + exit.entry.y };
  equal(
    Math.hypot(departure.x - entry.x, departure.y - entry.y),
    TILE.cell,
    `${exit.id}: continuous boundary`,
  );
  for (const p of [departure, entry])
    equal(
      rows[Math.floor(p.y / TILE.cell)][Math.floor(p.x / TILE.cell)],
      '.',
      `${exit.id}: open cell`,
    );
  const spawn = worldZoneStart(exit.from);
  const start = { x: a.x + spawn.x, y: a.y + spawn.y };
  const grid = makeWalkGrid(rows, { cell: TILE.cell, width: b.width, start });
  const path = grid.findPath(start, departure);
  const last = path.at(-1)!;
  equal(
    !!last && Math.hypot(last.x - departure.x, last.y - departure.y) < TILE.cell,
    true,
    `${exit.id}: reachable departure`,
  );
}
for (const [a, b] of [
  ['station', 'lumen'],
  ['park', 'castle'],
  ['woodland', 'halt'],
  ['halt', 'junction'],
] as const)
  equal(
    worldExits.some((e) => e.from === a && e.to === b),
    false,
    `${a}/${b}: adjacency never invents a trip`,
  );
const reached = new Set<WorldZoneId>(['garden']);
for (let i = 0; i < worldZoneIds.length; i++)
  for (const e of worldExits) if (reached.has(e.from)) reached.add(e.to);
equal(
  [...reached].sort(),
  regionTiles('valley')
    .map((t) => t.id)
    .sort(),
  'all valley zones reachable, no invented vehicles',
);
for (const level of [0, 1, 2, 4, NaN, Infinity]) {
  equal(
    canEnterWorldZone('ridge', { level, mountainLevel: 2 }),
    Number.isFinite(level) && level >= 2,
    `ridge level ${level}`,
  );
  equal(
    exitsFromWorldZone('garden', { level, mountainLevel: 2 }).some((e) => e.to === 'ridge'),
    Number.isFinite(level) && level >= 2,
    'gate applied to exit listing',
  );
}
equal(canEnterWorldZone('missing', access), false, 'unknown zone never navigates');
equal(
  currentWorldZone({ currentZone: 'ridge', visitedZones: ['ridge'] }, { ...access, level: 1 }),
  'garden',
  'locked resume is safe',
);
const unknown = {
  currentZone: 'future-moon',
  visitedZones: ['future-grotto', 'garden', 'future-grotto'],
  future: 4,
};
const restored = restoreWorldProgress(unknown);
equal(
  restored,
  { currentZone: 'future-moon', visitedZones: ['garden', 'future-grotto', 'future-moon'] },
  'unknown ids retained without rendering them',
);
equal(currentWorldZone(restored, access), 'garden', 'unknown saved destination renders garden');
equal(restoreWorldProgress(restored), restored, 'restoration idempotent');
for (const invalid of [null, undefined, 3, [], { currentZone: 8, visitedZones: [false] }])
  equal(
    restoreWorldProgress(invalid),
    freshWorldProgress(),
    'bad exploration metadata does not reset account',
  );

const gardenExits = exitsFromWorldZone('garden', access);
for (let i = 0; i < 200; i++) {
  const guard = createWorldWalkGuard();
  const exit = gardenExits[i % gardenExits.length];
  const walk = guard.begin('garden', exit.id, 'account', access)!;
  equal(guard.finish({ ...walk }, 'garden', 'account', access), null, 'forged token rejected');
  equal(guard.finish(walk, 'garden', 'account', access), exit.to, 'real callback commits once');
  equal(guard.finish(walk, 'garden', 'account', access), null, 'duplicate callback rejected');
  const stale = guard.begin('garden', exit.id, 'account', access)!;
  guard.cancel();
  equal(guard.finish(stale, 'garden', 'account', access), null, 'cancelled callback rejected');
  const a = guard.begin('garden', exit.id, 'account', access)!;
  const b = guard.begin('garden', exit.id, 'account', access)!;
  equal(guard.finish(a, 'garden', 'account', access), null, 'superseded callback rejected');
  equal(guard.finish(b, 'garden', 'other-account', access), null, 'account replacement rejected');
  const moved = guard.begin('garden', exit.id, 'account', access)!;
  equal(guard.finish(moved, 'town', 'account', access), null, 'leaving mid-walk rejects arrival');
  const invalidated = guard.begin('garden', exit.id, 'account', access)!;
  equal(guard.begin('garden', 'unknown', 'account', access), null, 'invalid tap rejected');
  equal(
    guard.finish(invalidated, 'garden', 'account', access),
    null,
    'invalid new intent cancels old one',
  );
}
const gate = gardenExits.find((e) => e.to === 'ridge')!,
  guard = createWorldWalkGuard();
const gated = guard.begin('garden', gate.id, 'account', access)!;
equal(
  guard.finish(gated, 'garden', 'account', { ...access, level: 1 }),
  null,
  'gate rechecked at arrival',
);
const before = freshWorldProgress();
const after = enterWorldZone(before, 'town');
equal(before, freshWorldProgress(), 'arrival does not mutate previous save');
equal(
  enterWorldZone(after, 'garden').visitedZones,
  ['garden', 'town'],
  'visits are a set, not repeat rewards',
);
console.log(`World zones: ${assertions} assertions passed.`);
