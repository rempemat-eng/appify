import assert from 'node:assert/strict';
import { acknowledgeMapSeen, buildWorldMap, mapVisitedZones, restoreMapSeen } from './world-map';
import { regionTiles, tileOrigin, type RegionId } from './region-walk';
import { regionLayout } from './zone-maps';
import {
  doors,
  regionPasses,
  regionPoint,
  travelLinks,
  travelPoints,
  travelRoute,
} from './world-places';
import { restoreWorld, type WorldSpot } from './world-save';
import { readSave, SAVE_VERSION, writeSave } from './save-data';

let checks = 0;
const ok = (v: unknown, message: string) => {
  assert.ok(v, message);
  checks++;
};
const equal = (a: unknown, b: unknown, message: string) => {
  assert.deepEqual(a, b, message);
  checks++;
};
const regions = Object.keys(regionLayout).filter((id): id is RegionId =>
  Object.hasOwn(regionLayout, id),
);
const zones = regions.flatMap((r) => regionTiles(r).map((t) => t.id));
const park: WorldSpot = {
  region: 'valley',
  ...regionPoint({ region: 'valley', zone: 'park', at: [160, 200] }),
  visited: ['garden', 'town', 'park'],
};
const before = JSON.stringify(park);
Object.freeze(park.visited);
Object.freeze(park);
const map = buildWorldMap({ world: park, mapSeen: ['garden', 'town'] });
equal(park, JSON.parse(before), 'building never mutates save input');
equal(
  map.nodes.length,
  regions.length + zones.length + Object.keys(travelPoints).length,
  'one node per region, zone and real station',
);
equal(new Set(map.nodes.map((n) => n.id)).size, map.nodes.length, 'namespaced IDs are unique');
equal(
  map.nodes.filter((n) => n.kind === 'zone' && n.state === 'here').map((n) => n.zone),
  ['park'],
  'only the exact current zone is here',
);
equal(
  map.nodes.filter((n) => n.kind === 'region' && n.state === 'here').map((n) => n.region),
  ['valley'],
  'only its region is here',
);
equal(
  map.nodes.filter((n) => n.kind === 'zone' && n.isNew).map((n) => n.zone),
  ['park'],
  'new is a visited discovery since last open',
);
equal(map.nodes.find((n) => n.id === 'zone:town')?.state, 'visited', 'past zone is visited');
equal(map.nodes.find((n) => n.id === 'zone:lumen')?.state, 'unseen', 'unvisited remains outline');
ok(!map.nodes.find((n) => n.id === 'station:home'), 'no invented station in the hut');
equal(
  map.links.filter((l) => l.kind === 'line').length,
  travelLinks.length,
  'each existing line represented once',
);
equal(
  map.links.filter((l) => l.kind === 'door'),
  [{ from: doors.hut.zone, to: doors.inside.zone, kind: 'door' }],
  'hut uses its authored door',
);

equal(
  map.links.filter((l) => l.kind === 'pass'),
  regionPasses.map(({ a, b }) => ({ from: a.zone, to: b.zone, kind: 'pass' })),
  'inter-region walking passes retain their authored zone endpoints',
);
ok(
  map.links.some((l) => l.kind === 'pass' && l.from === 'gulch' && l.to === 'scorch'),
  'Gulch reaches Scorched Pass on foot',
);
ok(
  map.links.some((l) => l.kind === 'line' && l.from === 'gulch' && l.to === 'caldera'),
  'mine-cart shortcut stays distinct',
);
const legacyCoast: WorldSpot = {
  region: 'valley',
  ...regionPoint({ region: 'valley', zone: 'headland', at: [160, 200] }),
  visited: ['garden', 'castle'],
};
const legacySeen = restoreMapSeen(['garden', 'castle', 'headland', 'future-zone'], legacyCoast);
equal(
  legacySeen,
  ['garden', 'headland', 'future-zone'],
  'seen IDs share the world rename and keep future IDs',
);
const legacyMap = buildWorldMap({ world: legacyCoast, mapSeen: legacySeen });
equal(
  restoreMapSeen(['constructor', '__proto__', 'future-zone'], legacyCoast),
  ['constructor', '__proto__', 'future-zone'],
  'future IDs cannot resolve inherited object properties',
);
equal(
  legacyMap.nodes.find((n) => n.id === 'zone:headland')?.state,
  'here',
  'old coastal position stays on Headland',
);
equal(
  legacyMap.nodes.find((n) => n.id === 'zone:headland')?.isNew,
  false,
  'old seen coast is not a fresh discovery',
);
equal(
  legacyMap.nodes.find((n) => n.id === 'zone:hearthold')?.state,
  'unseen',
  'old castle never reveals far Hearthold',
);
ok(!legacyMap.nodes.some((n) => n.id === 'zone:castle'), 'retired castle node is absent');
equal(
  acknowledgeMapSeen(['future-zone', 'castle'], ['castle'], legacyCoast),
  ['future-zone', 'headland'],
  'old opening cannot restore retired ID',
);
const passWorld: WorldSpot = {
  region: 'west',
  ...regionPoint(travelPoints.west!),
  visited: zones.filter((id) => id !== 'scorch' && id !== 'hearthold'),
};
equal(
  buildWorldMap({ world: passWorld, mapSeen: [] }).suggestion,
  'scorch',
  'walking pass participates in suggestions',
);

// All transport regions reach one another along the existing lines; the interior
// reaches the atlas through the door, not a fabricated train or fast-travel rule.
for (const from of regions.filter((r) => travelPoints[r]))
  for (const to of regions.filter((r) => travelPoints[r]))
    if (from !== to)
      ok(travelRoute(from, to).at(-1) === to, `${from} reaches ${to} on existing lines`);
const reachable = new Set<string>(['garden']);
for (let i = 0; i < zones.length; i++)
  for (const link of map.links) {
    if (reachable.has(link.from)) reachable.add(link.to);
    if (reachable.has(link.to)) reachable.add(link.from);
  }
equal(
  [...reachable].sort(),
  [...zones].sort(),
  'all zones and every region join the authored schematic',
);
equal(travelRoute('valley', 'home'), [], 'map does not change transport rules for the interior');

for (const region of regions)
  for (const tile of regionTiles(region)) {
    const at = tileOrigin(region, tile);
    const world = { region, x: at.x + 160, y: at.y + 200, visited: [] };
    const atlas = buildWorldMap({ world, mapSeen: [] });
    equal(
      atlas.nodes.filter((n) => n.kind === 'zone' && n.state === 'here').map((n) => n.zone),
      [tile.id],
      `${tile.id}: legacy missing visited list still has current marker`,
    );
    equal(
      atlas.nodes.find((n) => n.id === `zone:${tile.id}`)?.col,
      tile.col,
      `${tile.id}: derived grid column`,
    );
    equal(
      atlas.nodes.find((n) => n.id === `zone:${tile.id}`)?.row,
      tile.row,
      `${tile.id}: derived grid row`,
    );
  }
for (const [region, station] of Object.entries(travelPoints)) {
  const world = { region: station.region, ...regionPoint(station), visited: [station.zone] };
  const atlas = buildWorldMap({ world, mapSeen: [] });
  equal(
    atlas.nodes.find((n) => n.id === `station:${region}`)?.state,
    'here',
    `${region}: station marker at its real stand`,
  );
  const away = buildWorldMap({ world, mapSeen: [], current: { ...world, x: world.x + 24 } });
  equal(
    away.nodes.find((n) => n.id === `station:${region}`)?.state,
    'visited',
    `${region}: being in a station's zone is not standing at station`,
  );
}
const home = buildWorldMap({ world: park, mapSeen: [], current: 'garden' });
equal(
  home.nodes.filter((n) => n.kind === 'zone' && n.state === 'here').map((n) => n.zone),
  ['garden'],
  'Home override does not mistake saved resume location for current screen',
);
equal(
  buildWorldMap({ world: null, mapSeen: [] }).nodes.find((n) => n.id === 'zone:garden')?.state,
  'here',
  'first account starts at the garden',
);
equal(
  buildWorldMap({ world: park, mapSeen: [], current: { region: 'valley', x: NaN, y: -1 } })
    .suggestion,
  null,
  'invalid explicit current location has no misleading suggestion',
);

const captured = [...map.visitedSnapshot];
equal(
  acknowledgeMapSeen([], captured, park),
  captured,
  'opening acknowledges captured discoveries',
);
const later = { ...park, visited: [...park.visited, 'ridge'] };
const acknowledged = acknowledgeMapSeen(['future-zone'], captured, later);
ok(!acknowledged.includes('ridge'), 'a later visit is not cleared by an older map opening');
ok(acknowledged.includes('future-zone'), 'unknown future seen IDs are not discarded');
equal(
  acknowledgeMapSeen(acknowledged, captured, later),
  acknowledged,
  'acknowledgement is idempotent',
);
equal(
  acknowledgeMapSeen([], ['lumen', 'future-zone'], park),
  [],
  'cannot mark unvisited or unknown discoveries seen',
);
equal(restoreMapSeen(undefined, park), mapVisitedZones(park), 'old save has no upgrade backlog');
equal(
  restoreMapSeen({ corrupt: true }, park),
  mapVisitedZones(park),
  'malformed optional field does not reset exploration',
);
equal(
  restoreMapSeen(['garden', 'garden', null, 4, '', 'future-zone'], park),
  ['garden', 'future-zone'],
  'deduplicate valid string IDs, retain future IDs',
);
equal(restoreMapSeen([], park), [], 'an explicit empty mapSeen remains an empty history');
const afterOpen = buildWorldMap({ world: later, mapSeen: acknowledged });
equal(
  afterOpen.nodes.filter((n) => n.kind === 'zone' && n.isNew).map((n) => n.zone),
  ['ridge'],
  'only later discovery stays new',
);
equal(
  buildWorldMap({ world: { ...park, visited: zones }, mapSeen: [] }).suggestion,
  null,
  'all known places visited gives no completion chore',
);
ok(
  map.suggestion && !park.visited.includes(map.suggestion),
  'suggestion points only to an unvisited place',
);
equal(
  buildWorldMap({ world: park, mapSeen: [] }).suggestion,
  map.suggestion,
  'seen badges do not change exploration suggestion',
);
equal(
  buildWorldMap({ world: park, mapSeen: [] }).suggestion,
  map.suggestion,
  'suggestion is deterministic',
);
map.nodes[0].state = 'unseen';
map.links.length = 0;
map.visitedSnapshot.length = 0;
ok(buildWorldMap({ world: park, mapSeen: [] }).links.length > 0, 'output is detached across reads');

// Save codec plus the actual additive helpers: no new version, reset or lost future fields.
for (const version of [undefined, 1]) {
  const fixture = {
    ...(version ? { saveVersion: version } : {}),
    world: { ...park, futureGround: { tide: 3 } },
    player: {
      grass: 87.25,
      level: 6,
      owned_hats: ['leaf'],
      deck: ['grass_blade'],
      collection: [{ id: 'future', memo: 'keep' }],
      guardian: 'future-companion',
    },
    futureField: { keep: [1, 2] },
  };
  const read = readSave(JSON.stringify(fixture), (v) => {
    if (typeof v !== 'object' || v === null || Array.isArray(v)) return v;
    const world = restoreWorld('world' in v ? v.world : undefined);
    return { ...v, world, mapSeen: restoreMapSeen('mapSeen' in v ? v.mapSeen : undefined, world) };
  });
  assert.ok(typeof read.data === 'object' && read.data !== null);
  const written = JSON.parse(writeSave(read.data, read.source).raw);
  equal(
    written.player,
    fixture.player,
    'old save balance, level, hats, cards, collection and companion unchanged',
  );
  equal(written.futureField, fixture.futureField, 'unknown top-level fields retained');
  equal(
    written.world,
    fixture.world,
    'world coordinates, visits and future nested fields unchanged',
  );
  equal(written.mapSeen, mapVisitedZones(park), 'old save gains only acknowledgement baseline');
  equal(written.saveVersion, SAVE_VERSION, 'stays in current v1 save format');
}
console.log(`World map: ${checks} checks passed (pure/source, not visual or device validation).`);
