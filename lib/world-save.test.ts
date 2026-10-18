import assert from 'node:assert/strict';
import { moveTo, restoreWorld } from './world-save';
import { regionWalk, TILE } from './region-walk';
import {
  doors,
  exits,
  missionPlaces,
  regionPoint,
  rings,
  travelPoints,
  travelRoute,
} from './world-places';
import { makeWalkGrid } from './garden-path';
import { regionBounds } from './region-walk';
import { readSave, writeSave } from './save-data';
import { residentLines, residentRoutes } from './resident-routes';
import { zoneMaps, zoneWindows } from './zone-maps';

let checks = 0;
const ok = (value: unknown, message: string) => {
  assert.ok(value, message);
  checks++;
};

// restoring: only a whole spot inside its region survives
ok(restoreWorld(null) === null, 'no spot stays none');
ok(restoreWorld({ region: 'nowhere', x: 1, y: 1 }) === null, 'an unknown region is dropped');
ok(
  restoreWorld({ region: 'valley', x: -5, y: 10 }) === null,
  'a spot outside its region is dropped',
);
ok(restoreWorld({ region: 'valley', x: Number.NaN, y: 10 }) === null, 'a broken number is dropped');
const good = restoreWorld({
  region: 'valley',
  x: 480,
  y: 900,
  visited: ['town', 'town', 'atlantis', 4],
});
ok(good && good.region === 'valley' && good.x === 480, 'a good spot is kept');
ok(good && good.visited.join() === 'town', 'visited keeps known zones once');
ok(
  restoreWorld({ region: 'west', x: 10, y: 10 })?.visited.length === 0,
  'visited defaults to none',
);

// moving records the zone underfoot once
const a = moveTo(null, 'valley', 480, 1200);
ok(a.visited.length === 1, 'the first zone is seen');
const b = moveTo(a, 'valley', 490, 1210);
ok(b.visited.length === 1, 'the same zone is not added twice');

// the save keeps the spot, and an old save without one loads as none
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);
const restore = (v: unknown) => {
  if (isRecord(v)) v.world = restoreWorld(v.world);
  return v;
};
const worldOf = (data: unknown) => (isRecord(data) ? data.world : undefined);
const raw = writeSave({ world: a }, null).raw;
const back = { world: worldOf(readSave(raw, restore).data) };
ok(JSON.stringify(back.world) === JSON.stringify(a), 'the spot round-trips through the save');
const old = { world: worldOf(readSave(JSON.stringify({ saveVersion: 1 }), restore).data) };
ok(old.world === null, 'a save from before the world loads with no spot');

// every place, station, door and exit is open ground reachable in its region
const places = [
  ...Object.entries(missionPlaces).map(([k, p]) => [`mission ${k}`, p] as const),
  ...Object.entries(travelPoints).map(([k, p]) => [`station ${k}`, p] as const),
  ...Object.entries(doors).map(([k, p]) => [`door ${k}`, p] as const),
  ...Object.entries(exits).map(([k, p]) => [`exit ${k}`, p] as const),
  ...rings.map((p, i) => [`ring ${i}`, p] as const),
];
for (const [name, place] of places) {
  const at = regionPoint(place);
  const rows = regionWalk(place.region);
  const grid = makeWalkGrid(rows, {
    cell: TILE.cell,
    width: regionBounds(place.region).width,
    start: at,
  });
  const c = grid.toCell(at);
  ok(grid.walkable(c.cx, c.cy), `${name} stands on open ground`);
  // reachable from the region's travel point (the valley: from the gate exit)
  const from =
    place.region === 'home'
      ? regionPoint(doors.inside)
      : place.region === 'valley'
        ? regionPoint(exits.gate)
        : regionPoint(travelPoints[place.region]!);
  if (Math.hypot(from.x - at.x, from.y - at.y) < TILE.cell) continue;
  const path = grid.findPath(from, at);
  ok(path.length > 0, `${name} can be walked to`);
  const end = path[path.length - 1];
  ok(Math.hypot(end.x - at.x, end.y - at.y) < 12, `${name}: the walk ends there`);
}
console.log(`World save and places: ${checks} checks passed.`);

// every resident has something to say when the companion stops beside them
for (const who of Object.keys(residentRoutes)) ok(residentLines[who], `${who} has a line`);
console.log(`Residents: ${Object.keys(residentRoutes).length} have a line each.`);

// lit windows: every pane sits inside the sprite it belongs to, wherever that sprite stands
let panes = 0;
for (const zone of Object.values(zoneMaps)) {
  for (const [id, sprite, , , w, h] of zone.objects) {
    for (const [x, y, pw, ph] of zoneWindows[sprite] ?? []) {
      ok(
        x >= 0 && y >= 0 && x + pw <= w && y + ph <= h && pw > 0 && ph > 0,
        `${id}: a pane inside ${sprite}`,
      );
      panes++;
    }
  }
}
ok(panes > 20, 'the valley houses have lit windows');
console.log(`Lit windows: ${panes} panes inside their buildings.`);

// travel follows the lines: every station reaches every other, neighbours in one leg
const stations = ['valley', 'steam', 'west', 'lava', 'neon', 'space', 'moon'] as const;
for (const from of stations)
  for (const to of stations) {
    if (from === to) continue;
    const route = travelRoute(from, to);
    ok(route.length > 0 && route[route.length - 1] === to, `${from} reaches ${to}`);
    ok(
      route.every((r) => travelPoints[r]),
      `${from} to ${to} stops only at stations`,
    );
  }
ok(travelRoute('valley', 'steam').join() === 'steam', 'the valley train goes to Cogsworth');
ok(
  travelRoute('valley', 'moon').join() === 'steam,neon,space,moon',
  'Lumen is four legs from the valley',
);
ok(
  travelRoute('lava', 'neon').join() === 'west,steam,neon',
  'the caldera to the city changes twice',
);
ok(travelRoute('valley', 'valley').length === 0, 'no trip to where you are');
console.log('Travel: every station reaches every other along the lines.');
