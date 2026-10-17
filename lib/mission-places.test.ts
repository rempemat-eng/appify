import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import {
  getMissionPlaces,
  missionPlaceShortcuts,
  type MissionPlaceId,
  type MissionRule,
} from './mission-places';
import { worldCatalogue } from './world-catalogue';

// Read only the actual declaration: loading the native-backed store is neither
// needed nor useful for a pure map contract. No copied mission fixtures or rules.
const source = ts.createSourceFile(
  'game.ts',
  readFileSync(new URL('./game.ts', import.meta.url), 'utf8'),
  ts.ScriptTarget.Latest,
  true,
);
const declaration = source.statements.find(
  (statement) =>
    ts.isVariableStatement(statement) &&
    statement.declarationList.declarations.some(
      (item) => ts.isIdentifier(item.name) && item.name.text === 'missions',
    ),
);
assert.ok(declaration, 'read the current mission rules from the game store');
const compiled = ts.transpileModule(declaration.getText(source), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const boundary: { missions?: MissionRule[] } = {};
runInNewContext(compiled, { exports: boundary });
assert.ok(Array.isArray(boundary.missions), 'mission declaration exports its current rules');
// Move arrays out of the VM realm so ordinary deep equality remains meaningful.
const rules: readonly MissionRule[] = Object.freeze(
  Array.from(boundary.missions, (mission) => Object.freeze({ ...mission })),
);
const before = JSON.stringify(rules);
const places = getMissionPlaces(rules, 1);
const ids = Object.values(places).map((place) => place.id);
const worldIds = Object.keys(worldCatalogue).sort();
assert.deepEqual(
  rules.map((mission) => mission.id).sort(),
  worldIds,
  'every current mission has exactly one catalogued world',
);
assert.deepEqual(
  ids.filter((id) => places[id].opens.kind === 'select-mission').sort(),
  worldIds,
  'every mission world is a selectable map place',
);
assert.deepEqual(
  [...ids].sort(),
  ['garden', 'arena', 'shop', ...worldIds].sort(),
  'the graph includes the garden gate, worlds, battle zone and shop',
);

const paths = new Set<string>();
for (const id of ids) {
  const place = places[id];
  assert.equal(place.id, id, 'place lookup and stable ID agree');
  assert.equal(
    new Set(place.neighbours).size,
    place.neighbours.length,
    `${id}: no duplicate roads`,
  );
  assert.ok(!place.neighbours.includes(id), `${id}: no road leads only to itself`);
  for (const neighbour of place.neighbours) {
    assert.ok(places[neighbour], `${id}: ${neighbour} exists`);
    assert.ok(places[neighbour].neighbours.includes(id), `${id}: its road has a way back`);
  }
  const seen = new Set<MissionPlaceId>([id]);
  const pending = [id];
  for (let index = 0; index < pending.length; index++)
    for (const neighbour of places[pending[index]].neighbours)
      if (!seen.has(neighbour)) {
        seen.add(neighbour);
        pending.push(neighbour);
      }
  assert.deepEqual([...seen].sort(), [...ids].sort(), `${id}: every destination remains reachable`);

  const { path } = place.opens;
  paths.add(path);
  const screen = path === '/' ? 'index' : path.slice(1);
  assert.ok(
    existsSync(new URL(`../app/(tabs)/${screen}.tsx`, import.meta.url)),
    `${id}: opens an existing app screen`,
  );
  if (place.opens.kind === 'select-mission') {
    assert.equal(place.opens.missionId, id, `${id}: selects its own mission, not its list index`);
    assert.ok('mission' in place, `${id}: has its existing mission rules`);
    assert.equal(
      place.mission,
      rules.find((mission) => mission.id === id),
    );
    assert.equal(place.world, worldCatalogue[place.id], `${id}: uses existing catalogue metadata`);
  } else assert.equal(place.locked, false, `${id}: no new route unlock`);
}
assert.deepEqual(
  [...paths].sort(),
  ['/', '/arena', '/missions', '/shop'],
  'all four tab screens stay reachable',
);
assert.deepEqual(
  missionPlaceShortcuts,
  ['arena', 'shop'],
  'both requested one-tap shortcuts remain',
);
assert.deepEqual(
  missionPlaceShortcuts.map((id) => places[id].opens),
  [
    { kind: 'route', path: '/arena' },
    { kind: 'route', path: '/shop' },
  ],
  'shortcuts open screens directly without starting a mission',
);
assert.deepEqual(
  [places.park.locked, places.book.locked, places.mountain.locked],
  [false, false, true],
  'level one retains Park and Book access with Mountain visible but locked',
);
assert.ok(
  Object.values(getMissionPlaces(rules, 2)).every((place) => !place.locked),
  'level two retains access to every current place',
);
assert.deepEqual(
  getMissionPlaces(rules.toReversed(), 1),
  places,
  'rule order never assigns identities or gates',
);
const changedRules = rules.map((mission) =>
  mission.id === 'mountain' ? { ...mission, level: 4, reward: 321 } : mission,
);
const changedPlaces = getMissionPlaces(changedRules, 2);
assert.equal(
  changedPlaces.mountain.locked,
  true,
  'level gates derive from the supplied existing rules',
);
assert.ok('mission' in changedPlaces.mountain);
assert.equal(
  changedPlaces.mountain.mission.reward,
  321,
  'rewards are carried from rules, never duplicated',
);
assert.equal(
  JSON.stringify(rules),
  before,
  'constructing places leaves the existing rules untouched',
);

assert.throws(
  () =>
    getMissionPlaces(
      rules.filter((mission) => mission.id !== 'book'),
      1,
    ),
  /book needs exactly one mission rule/,
  'a missing mission cannot silently strand a place',
);
assert.throws(
  () => getMissionPlaces([...rules, rules[0]], 1),
  /needs exactly one mission rule; found 2/,
  'duplicate rules cannot ambiguously assign a destination',
);
assert.throws(
  () => getMissionPlaces([...rules, { ...rules[0], id: 'uncatalogued' }], 1),
  /uncatalogued needs a world catalogue entry/,
  'a new mission needs an explicit place rather than disappearing from the map',
);
console.log(
  'PASS: mission places preserve mission rules, screen reachability, return roads and direct shortcuts.',
);
