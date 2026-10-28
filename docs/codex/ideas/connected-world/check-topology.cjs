'use strict';

// Design prototype only. Nothing here is imported by the application or writes a save.
// The masks below are SYNTHETIC: passing is not generated-terrain or browser proof.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const spec = JSON.parse(fs.readFileSync(path.join(__dirname, 'topology.json'), 'utf8'));
const root = path.resolve(__dirname, '../../../..');
const { zoneWidth: W, zoneHeight: H, cell: CELL, arrivalInset: INSET } = spec.coordinates;
const opposite = { north: 'south', south: 'north', west: 'east', east: 'west' };
const delta = { north: [0, -1], south: [0, 1], west: [-1, 0], east: [1, 0] };
const clone = (value) => structuredClone(value);
const pairKey = (a, b) => [a, b].sort((left, right) => left.localeCompare(right)).join('|');
const cellKey = ([x, y]) => `${x},${y}`;
const zoneSource = fs.readFileSync(path.join(root, 'lib/zone-maps.ts'), 'utf8');
const placesSource = fs.readFileSync(path.join(root, 'lib/world-places.ts'), 'utf8');
const record = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const inside = ([x, y]) =>
  Number.isFinite(x) && Number.isFinite(y) && x >= 0 && y >= 0 && x < W && y < H;
let checks = 0;
const check = (value, message) => {
  assert.ok(value, message);
  checks += 1;
};

function graph(data, kinds = ['walk', 'door', 'transit']) {
  const out = new Map(data.zones.map((zone) => [zone.id, new Set()]));
  for (const link of data.connections) {
    if (!kinds.includes(link.kind)) continue;
    out.get(link.a.zone)?.add(link.b.zone);
    out.get(link.b.zone)?.add(link.a.zone);
  }
  return out;
}

function reachable(edges, start) {
  const found = new Set([start]);
  const queue = [start];
  for (let i = 0; i < queue.length; i += 1) {
    for (const next of edges.get(queue[i]) ?? []) {
      if (found.has(next)) continue;
      found.add(next);
      queue.push(next);
    }
  }
  return found;
}

// Read the current snapshot's literal declarations without importing runtime modules.
// Fail closed if their shape changes; this parser is deliberately not a TS interpreter.
function sourceTransitContract() {
  const stops = [];
  const points = placesSource.match(/export const travelPoints:[\s\S]*?= \{([\s\S]*?)\n\};/)?.[1];
  assert.ok(points, 'current source travel-point declaration');
  for (const match of points.matchAll(
    /(\w+): \{ region: '(\w+)', zone: '(\w+)', at: stand\('(\w+)', '([^']+)'\) \}/g,
  )) {
    const [, id, , zone, standZone, standName] = match;
    assert.equal(zone, standZone, 'source stand belongs to its zone');
    const start = zoneSource.indexOf(`  ${zone}: {`, zoneSource.indexOf('export const zoneMaps'));
    assert.ok(start >= 0, 'source travel zone exists');
    const block = zoneSource.slice(start, zoneSource.indexOf('\n  },', start) + 5);
    const standText = block.slice(block.indexOf('stands:'));
    const at = standText.match(new RegExp(`\\b${standName}: \\[(-?\\d+),\\s*(-?\\d+)\\]`));
    assert.ok(at, `source standing point ${id}`);
    stops.push({ id, zone, at: [Number(at[1]), Number(at[2])] });
  }
  assert.equal(stops.length, 7, 'all seven source service stops parsed');
  const linkLiteral = placesSource.match(
    /export const travelLinks:[\s\S]*?= (\[[\s\S]*?\n\]);/,
  )?.[1];
  assert.ok(linkLiteral, 'source travel links parsed');
  const links = JSON.parse(linkLiteral.replaceAll("'", '"').replace(/,\s*]/g, ']'));
  const vehicleText = placesSource.slice(
    placesSource.indexOf('export function travelVehicle('),
    placesSource.indexOf('export function travelRoute('),
  );
  const priorities = [...vehicleText.matchAll(/if \(pair.has\('(\w+)'\)\) return '(\w+)';/g)].map(
    (m) => [m[1], m[2]],
  );
  assert.equal(priorities.length, 4, 'source vehicle priority cases parsed');
  const fallback = vehicleText.match(/\n  return '(\w+)';/)?.[1];
  assert.ok(fallback, 'source vehicle fallback parsed');
  return {
    stops,
    links: links.map(([a, b]) => ({
      endpoints: [a, b],
      vehicle: priorities.find(([id]) => id === a || id === b)?.[1] ?? fallback,
    })),
  };
}

const currentTransit = sourceTransitContract();

function stopRoute(data, from, to) {
  if (from === to) return [];
  const stops = new Set(data.transitStops.map((stop) => stop.id));
  if (!stops.has(from) || !stops.has(to)) return [];
  const previous = new Map([[from, from]]);
  const queue = [from];
  for (let i = 0; i < queue.length; i += 1) {
    for (const link of data.connections.filter((candidate) => candidate.kind === 'transit')) {
      const [a, b] = link.serviceEndpoints ?? [];
      const next = a === queue[i] ? b : b === queue[i] ? a : null;
      if (next && stops.has(next) && !previous.has(next)) {
        previous.set(next, queue[i]);
        queue.push(next);
      }
    }
  }
  if (!previous.has(to)) return [];
  const route = [];
  for (let at = to; at !== from; at = previous.get(at)) route.unshift(at);
  return route;
}

function independentCycles(data) {
  const edgeIds = new Map(
    data.connections
      .filter((link) => link.kind === 'walk')
      .map((link, i) => [pairKey(link.a.zone, link.b.zone), i]),
  );
  const basis = new Map();
  for (const loop of data.loops) {
    let vector = 0n;
    for (let i = 1; i < loop.zones.length; i += 1) {
      const index = edgeIds.get(pairKey(loop.zones[i - 1], loop.zones[i]));
      if (index !== undefined) vector ^= 1n << BigInt(index);
    }
    while (vector !== 0n) {
      const pivot = vector.toString(2).length - 1;
      if (!basis.has(pivot)) {
        basis.set(pivot, vector);
        break;
      }
      vector ^= basis.get(pivot);
    }
  }
  return basis.size;
}

function validate(data) {
  const errors = [];
  const demand = (value, label) => {
    if (!value) errors.push(label);
  };
  const zones = new Map(data.zones.map((zone) => [zone.id, zone]));
  const regions = new Set(data.regions.map((region) => region.id));
  const occupied = new Set();
  const ids = new Set();
  const seams = new Set();
  const widthRange = data.coordinates.portWidthRangeInclusive;
  const validRange =
    Array.isArray(widthRange) &&
    widthRange.length === 2 &&
    widthRange.every((n) => Number.isInteger(n) && n > 0 && n % CELL === 0) &&
    widthRange[0] <= widthRange[1] &&
    widthRange[1] <= Math.min(W, H);
  demand(validRange, 'valid declared port-width range');
  demand(data.status === 'proposal-not-runtime', 'proposal status');
  demand(data.policies.runtimeImported === false, 'not runtime imported');
  for (const policy of [
    'changesGameRules',
    'addsTravelCosts',
    'addsLevelGates',
    'addsRewards',
    'resetsPlayerData',
    'weatherAffectsRoutes',
    'discoveryRequiredForTravel',
  ]) {
    demand(data.policies[policy] === false, `policy ${policy}`);
  }
  demand(zones.size === data.zones.length, 'unique zone IDs');
  demand(regions.size === data.regions.length, 'unique region IDs');
  for (const zone of data.zones) {
    demand(regions.has(zone.region), `region ${zone.id}`);
    demand(Number.isInteger(zone.col) && Number.isInteger(zone.row), `tile position ${zone.id}`);
    const key = `${zone.region}:${zone.col},${zone.row}`;
    demand(!occupied.has(key), `tile overlap ${zone.id}`);
    occupied.add(key);
  }
  for (const link of data.connections) {
    demand(!ids.has(link.id), `duplicate connection ${link.id}`);
    ids.add(link.id);
    const a = zones.get(link.a.zone);
    const b = zones.get(link.b.zone);
    demand(a && b && a !== b, `link endpoints ${link.id}`);
    if (!a || !b) continue;
    demand(['walk', 'door', 'transit'].includes(link.kind), `link kind ${link.id}`);
    if (link.kind === 'walk') {
      const direction = delta[link.a.side];
      demand(direction && opposite[link.a.side] === link.b.side, `reciprocal side ${link.id}`);
      demand(a.region === b.region, `same-region walk ${link.id}`);
      demand(
        direction && b.col === a.col + direction[0] && b.row === a.row + direction[1],
        `cardinal adjacency ${link.id}`,
      );
      const lateralLimit = ['north', 'south'].includes(link.a.side) ? W : H;
      const span = link.span;
      const validSpan = Array.isArray(span) && span.length === 2 && span.every(Number.isFinite);
      demand(validSpan, `span shape ${link.id}`);
      if (validSpan) {
        const width = span[1] - span[0];
        demand(
          span.every((n) => Number.isInteger(n) && n % CELL === 0),
          `cell-aligned span ${link.id}`,
        );
        demand(span[0] >= 0 && span[1] <= lateralLimit, `span bounds ${link.id}`);
        demand(
          validRange && width >= widthRange[0] && width <= widthRange[1],
          `clearance ${link.id}`,
        );
      }
      const seam = pairKey(a.id, b.id);
      demand(!seams.has(seam), `duplicate walk seam ${link.id}`);
      seams.add(seam);
      demand(link.grade === 1, `primary route grade ${link.id}`);
      demand(
        a.tier === b.tier
          ? link.gradeChange === 'level'
          : ['ramp', 'stairs'].includes(link.gradeChange),
        `elevation transition ${link.id}`,
      );
      demand(typeof link.frame === 'string' && link.frame.length > 12, `framed seam ${link.id}`);
      demand(typeof link.corridor === 'string' && link.corridor.length > 12, `corridor ${link.id}`);
    } else {
      demand(Array.isArray(link.a.at) && inside(link.a.at), `point a ${link.id}`);
      demand(Array.isArray(link.b.at) && inside(link.b.at), `point b ${link.id}`);
      if (link.kind === 'transit')
        demand(
          ['train', 'maglev', 'carts', 'capsule', 'shuttle'].includes(link.vehicle),
          `vehicle ${link.id}`,
        );
      else demand(link.activation === 'explicit-door-action', `explicit door ${link.id}`);
    }
  }
  for (const blocked of data.blockedAdjacencies) {
    demand(zones.has(blocked.a) && zones.has(blocked.b), `blocked endpoints ${blocked.a}`);
    demand(!seams.has(pairKey(blocked.a, blocked.b)), `blocked seam ${blocked.a}/${blocked.b}`);
    demand(blocked.reason.length > 20, `blocked reason ${blocked.a}`);
  }
  const walking = graph(data, ['walk']);
  const valley = data.zones.filter((zone) => zone.region === 'valley').map((zone) => zone.id);
  const valleyEdges = data.connections.filter(
    (link) => link.kind === 'walk' && zones.get(link.a.zone)?.region === 'valley',
  );
  demand(valleyEdges.length - valley.length + 1 === 3, 'three valley cycles');
  demand(
    valley.every((zone) => reachable(walking, 'garden').has(zone)),
    'valley connected',
  );
  demand(data.loops.length === 3, 'three named loops');
  demand(
    new Set(data.loops.map((loop) => loop.id)).size === data.loops.length,
    'unique named-loop IDs',
  );
  demand(independentCycles(data) === 3, 'three independent named cycles');
  for (const loop of data.loops) {
    demand(loop.zones.length >= 4 && loop.zones[0] === loop.zones.at(-1), `closed loop ${loop.id}`);
    demand(
      new Set(loop.zones.slice(0, -1)).size === loop.zones.length - 1,
      `simple loop ${loop.id}`,
    );
    for (let i = 1; i < loop.zones.length; i += 1)
      demand(walking.get(loop.zones[i - 1])?.has(loop.zones[i]), `loop edge ${loop.id}`);
  }
  demand(
    walking.get('castle')?.size === 1 && walking.get('castle')?.has('lava_bridge'),
    'castle sole approach',
  );
  demand(!walking.get('castle')?.has('springs'), 'no springs-castle entrance');
  const ascent = data.connections.find((link) => link.id === 'lava-bridge-caldera');
  demand(ascent?.span[0] >= 248 && ascent?.span[1] <= 296, 'caldera branch on east abutment');
  const all = graph(data);
  demand(reachable(all, 'garden').size === zones.size, 'whole graph reachable');
  const missionIds = data.bindings
    .filter((binding) => binding.kind === 'mission')
    .map((binding) => binding.missionId)
    .sort();
  demand(
    JSON.stringify(missionIds) === JSON.stringify(['book', 'mountain', 'park']),
    'existing mission IDs only',
  );
  const bindingIds = new Set();
  for (const binding of data.bindings) {
    demand(!bindingIds.has(binding.id), `duplicate binding ${binding.id}`);
    bindingIds.add(binding.id);
    demand(zones.has(binding.zone) && inside(binding.at), `binding point ${binding.id}`);
    demand(reachable(all, 'garden').has(binding.zone), `reachable binding ${binding.id}`);
    demand(
      !Object.hasOwn(binding, 'reward') &&
        !Object.hasOwn(binding, 'level') &&
        !Object.hasOwn(binding, 'duration'),
      `no copied rules ${binding.id}`,
    );
    if (binding.kind === 'mission')
      demand(
        binding.activation === 'select-then-explicit-departure' &&
          binding.rulesRef === 'lib/game.ts#missions',
        `existing departure ${binding.id}`,
      );
  }
  demand(
    data.bindings.find((binding) => binding.id === 'shop')?.path === '/shop',
    'shop binding retained',
  );
  demand(
    data.bindings.find((binding) => binding.id === 'arena')?.path === '/arena',
    'arena binding retained',
  );
  const stops = new Map(data.transitStops.map((stop) => [stop.id, stop]));
  demand(stops.size === data.transitStops.length, 'unique stable service-stop IDs');
  demand(
    JSON.stringify(data.transitStops.map(({ id, zone, at }) => ({ id, zone, at }))) ===
      JSON.stringify(currentTransit.stops),
    'source-derived service-stop points',
  );
  for (const stop of data.transitStops)
    demand(
      zones.get(stop.zone)?.region === stop.physicalRegion,
      `physical region for service stop ${stop.id}`,
    );
  const actualTransit = data.connections.filter((link) => link.kind === 'transit');
  demand(
    JSON.stringify(
      actualTransit.map((link) => ({
        endpoints: link.serviceEndpoints,
        vehicle: link.vehicle,
      })),
    ) === JSON.stringify(currentTransit.links),
    'source-derived service links and vehicles',
  );
  for (const link of actualTransit) {
    const [a, b] = (link.serviceEndpoints ?? []).map((id) => stops.get(id));
    demand(a && b && a.id !== b.id, `distinct service endpoints ${link.id}`);
    demand(
      a?.zone === link.a.zone &&
        b?.zone === link.b.zone &&
        JSON.stringify(a?.at) === JSON.stringify(link.a.at) &&
        JSON.stringify(b?.at) === JSON.stringify(link.b.at),
      `exact existing transit endpoints ${link.id}`,
    );
  }
  return errors;
}

function portsFor(data, zoneId) {
  return data.connections.flatMap((link) => {
    if (link.kind !== 'walk') return [];
    if (link.a.zone === zoneId)
      return [
        {
          link: link.id,
          side: link.a.side,
          span: link.span,
          to: link.b.zone,
          arrivalSide: link.b.side,
        },
      ];
    if (link.b.zone === zoneId)
      return [
        {
          link: link.id,
          side: link.b.side,
          span: link.span,
          to: link.a.zone,
          arrivalSide: link.a.side,
        },
      ];
    return [];
  });
}

function crossing(data, zoneId, side, lateral) {
  const port = portsFor(data, zoneId).find(
    (p) => p.side === side && lateral >= p.span[0] && lateral < p.span[1],
  );
  if (!port || !Number.isFinite(lateral)) return null;
  const at =
    port.arrivalSide === 'north'
      ? [lateral, INSET]
      : port.arrivalSide === 'south'
        ? [lateral, H - INSET]
        : port.arrivalSide === 'west'
          ? [INSET, lateral]
          : [W - INSET, lateral];
  return { zone: port.to, at, link: port.link };
}

function attemptCross(data, zoneId, from, to) {
  if (!inside(from) || !to.every(Number.isFinite)) return null;
  const sides = [
    to[0] < 0 && 'west',
    to[0] >= W && 'east',
    to[1] < 0 && 'north',
    to[1] >= H && 'south',
  ].filter(Boolean);
  if (sides.length !== 1) return null; // no diagonal region/corner teleport
  if (Math.abs(to[0] - from[0]) > CELL || Math.abs(to[1] - from[1]) > CELL) return null;
  const side = sides[0];
  return crossing(data, zoneId, side, ['north', 'south'].includes(side) ? to[0] : to[1]);
}

function syntheticMask(data, zoneId) {
  const cols = W / CELL;
  const rows = H / CELL;
  const mask = Array.from({ length: rows }, (_row, y) =>
    Array.from({ length: cols }, (_col, x) => x > 0 && x < cols - 1 && y > 0 && y < rows - 1),
  );
  if (zoneId === data.syntheticMaskExample.lavaBridge.zone) {
    const lava = data.syntheticMaskExample.lavaBridge;
    for (let y = 0; y < rows; y += 1)
      for (let x = 0; x < cols; x += 1) {
        const px = x * CELL + CELL / 2;
        const py = y * CELL + CELL / 2;
        if (
          px >= lava.blockedLavaColumns[0] &&
          px < lava.blockedLavaColumns[1] &&
          !(py >= lava.supportedBridgeRows[0] && py < lava.supportedBridgeRows[1])
        )
          mask[y][x] = false;
      }
  }
  for (const port of portsFor(data, zoneId)) {
    for (let p = port.span[0] / CELL; p < port.span[1] / CELL; p += 1) {
      if (port.side === 'north') mask[0][p] = true;
      if (port.side === 'south') mask[rows - 1][p] = true;
      if (port.side === 'west') mask[p][0] = true;
      if (port.side === 'east') mask[p][cols - 1] = true;
    }
  }
  return mask;
}

function canStep(mask, a, b) {
  const open = ([x, y]) => mask[y]?.[x] === true;
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  return (
    open(a) &&
    open(b) &&
    Math.abs(dx) <= 1 &&
    Math.abs(dy) <= 1 &&
    (dx !== 0 || dy !== 0) &&
    (!dx || !dy || (open([a[0] + dx, a[1]]) && open([a[0], a[1] + dy])))
  );
}

function maskReachable(mask, from, to) {
  const start = from.map((n) => Math.floor(n / CELL));
  const goal = to.map((n) => Math.floor(n / CELL));
  if (!mask[start[1]]?.[start[0]] || !mask[goal[1]]?.[goal[0]]) return false;
  const found = new Set([cellKey(start)]);
  const queue = [start];
  for (let i = 0; i < queue.length; i += 1) {
    const here = queue[i];
    if (cellKey(here) === cellKey(goal)) return true;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
      [1, 1],
      [1, -1],
      [-1, 1],
      [-1, -1],
    ]) {
      const next = [here[0] + dx, here[1] + dy];
      if (!found.has(cellKey(next)) && canStep(mask, here, next)) {
        found.add(cellKey(next));
        queue.push(next);
      }
    }
  }
  return false;
}

// A deliberately small owner/generation demonstration, not an app lifecycle patch.
function intent(state, event) {
  if (event.type === 'start')
    return {
      ...state,
      generation: state.generation + 1,
      pending: event.target,
    };
  if (event.type === 'cancel') return { ...state, generation: state.generation + 1, pending: null };
  if (event.type === 'finish' && state.pending && event.generation === state.generation) {
    return {
      ...state,
      pending: null,
      position: state.pending,
      settlements: state.settlements + 1,
    };
  }
  return state;
}

function origin(layout, zoneId) {
  const positions = Object.values(layout);
  const minCol = Math.min(...positions.map(([col]) => col));
  const minRow = Math.min(...positions.map(([, row]) => row));
  const [col, row] = layout[zoneId];
  return [(col - minCol) * W, (row - minRow) * H];
}

function proposedLayouts(data) {
  return Object.fromEntries(
    data.regions.map((region) => [
      region.id,
      Object.fromEntries(
        data.zones.filter((z) => z.region === region.id).map((z) => [z.id, [z.col, z.row]]),
      ),
    ]),
  );
}

function migrateFixture(data, input) {
  const save = clone(input);
  const world = save.world;
  if (!record(world)) return { status: 'unchanged', save };
  const migration = data.migrationPrototype;
  if (world.layoutVersion === migration.toLayoutVersion)
    return { status: 'already-migrated', save };
  if (world.layoutVersion !== undefined && world.layoutVersion !== migration.fromLayoutVersion)
    return { status: 'unresolved-layout-version', save };
  const old = migration.oldLayout[world.region];
  if (!old || !Number.isFinite(world.x) || !Number.isFinite(world.y) || world.x < 0 || world.y < 0)
    return { status: 'unresolved-old-position', save };
  const oldZone = Object.keys(old).find((id) => {
    const [ox, oy] = origin(old, id);
    return world.x >= ox && world.x < ox + W && world.y >= oy && world.y < oy + H;
  });
  if (!oldZone) return { status: 'unresolved-old-position', save };
  const alias = (id) =>
    Object.hasOwn(migration.legacyZoneToProposedZone, id)
      ? migration.legacyZoneToProposedZone[id]
      : id;
  const proposedId = alias(oldZone);
  const zone = data.zones.find((z) => z.id === proposedId);
  if (!zone) return { status: 'unresolved-proposed-zone', save };
  const oldOrigin = origin(old, oldZone);
  const nextOrigin = origin(proposedLayouts(data)[zone.region], zone.id);
  const oldVisited = Array.isArray(world.visited) ? clone(world.visited) : [];
  save.world = {
    ...world,
    layoutVersion: migration.toLayoutVersion,
    region: zone.region,
    x: nextOrigin[0] + world.x - oldOrigin[0],
    y: nextOrigin[1] + world.y - oldOrigin[1],
    visited: [...new Set(oldVisited.map(alias))],
    legacyDiscovery: {
      ...(record(world.legacyDiscovery) ? world.legacyDiscovery : {}),
      layoutVersion: migration.fromLayoutVersion,
      visited: oldVisited,
    },
  };
  return { status: 'demonstrated-position-only', save };
}

check(validate(spec).length === 0, `valid proposal: ${validate(spec).join('; ')}`);
check(spec.zones.length === 23 && spec.regions.length === 7, '23 zones in seven proposed regions');
const walks = spec.connections.filter((link) => link.kind === 'walk');
check(walks.length === 19, '19 declared walk connections');
check(
  spec.connections.filter((link) => link.kind === 'transit').length === 6,
  'six existing transit links retained',
);
check(
  spec.transitStops.find((stop) => stop.id === 'west').physicalRegion ===
    spec.transitStops.find((stop) => stop.id === 'lava').physicalRegion,
  'west and lava service stops share the proposed physical Sunreach region',
);
assert.deepEqual(
  stopRoute(spec, 'west', 'lava'),
  ['lava'],
  'mine cart remains routable inside one physical region',
);
checks += 1;
assert.deepEqual(stopRoute(spec, 'lava', 'west'), ['west'], 'reverse mine cart remains routable');
checks += 1;
assert.deepEqual(
  stopRoute(spec, 'valley', 'moon'),
  ['steam', 'neon', 'space', 'moon'],
  'legacy valley-to-moon service route remains four legs',
);
checks += 1;
check(
  stopRoute(spec, 'west', 'west').length === 0,
  'only identical service-stop ID yields a zero-leg trip',
);
check(
  stopRoute(spec, 'sunreach', 'lava').length === 0,
  'physical-region ID is not silently treated as a service stop',
);
for (const from of spec.transitStops)
  for (const to of spec.transitStops) {
    if (from.id !== to.id)
      check(
        stopRoute(spec, from.id, to.id).at(-1) === to.id,
        `service routing ${from.id} to ${to.id}`,
      );
  }
check(
  new Set(walks.map((link) => link.span.join(','))).size >= 8,
  'varied port alignments rather than every path centred',
);

let crossingSamples = 0;
for (const link of walks) {
  for (const [a, b] of [
    [link.a, link.b],
    [link.b, link.a],
  ]) {
    for (const lateral of [
      link.span[0] + CELL / 2,
      (link.span[0] + link.span[1]) / 2,
      link.span[1] - CELL / 2,
    ]) {
      const result = crossing(spec, a.zone, a.side, lateral);
      check(result?.zone === b.zone, `${link.id}: forward endpoint`);
      const reverse = crossing(spec, b.zone, b.side, lateral);
      check(reverse?.zone === a.zone, `${link.id}: reverse endpoint`);
      check(
        result.at[['north', 'south'].includes(b.side) ? 0 : 1] === lateral,
        `${link.id}: lateral alignment preserved`,
      );
      check(inside(result.at), `${link.id}: arrival inside target`);
      check(
        result.at[['north', 'south'].includes(b.side) ? 1 : 0] ===
          (['north', 'west'].includes(b.side)
            ? INSET
            : ['north', 'south'].includes(b.side)
              ? H - INSET
              : W - INSET),
        `${link.id}: 16px inset`,
      );
      crossingSamples += 1;
    }
    check(
      crossing(spec, a.zone, a.side, link.span[0] - CELL / 2) === null,
      `${link.id}: before span blocked`,
    );
    check(
      crossing(spec, a.zone, a.side, link.span[1]) === null,
      `${link.id}: exclusive end blocked`,
    );
  }
}
check(
  attemptCross(spec, 'garden', [318, 220], [322, 220])?.zone === 'riverside',
  'one-cell east crossing',
);
check(
  attemptCross(spec, 'garden', [318, 574], [322, 578]) === null,
  'diagonal seam teleport rejected',
);
check(attemptCross(spec, 'garden', [160, 220], [322, 220]) === null, 'large seam leap rejected');
check(attemptCross(spec, 'garden', [318, 574], [322, 574]) === null, 'unlisted east span blocked');
check(crossing(spec, 'castle', 'north', 160) === null, 'castle north cannot enter springs');
check(crossing(spec, 'springs', 'south', 160) === null, 'springs south cannot enter castle');
check(
  crossing(spec, 'lava_bridge', 'north', 160) === null,
  'no north path over the central lava channel',
);
check(
  crossing(spec, 'lava_bridge', 'north', 270)?.zone === 'caldera',
  'north path uses east abutment',
);
check(
  !canStep(
    [
      [true, false],
      [false, true],
    ],
    [0, 0],
    [1, 1],
  ),
  'diagonal cannot cut between blocked orthogonals',
);

let maskEndpoints = 0;
for (const zone of spec.zones) {
  const mask = syntheticMask(spec, zone.id);
  for (const side of ['north', 'south', 'east', 'west']) {
    const count = ['north', 'south'].includes(side) ? W / CELL : H / CELL;
    check(
      Array.from({ length: count }, (_, i) => {
        const actual =
          side === 'north'
            ? mask[0][i]
            : side === 'south'
              ? mask[H / CELL - 1][i]
              : side === 'west'
                ? mask[i][0]
                : mask[i][W / CELL - 1];
        const expected = crossing(spec, zone.id, side, i * CELL + CELL / 2) !== null;
        return actual === expected;
      }).every(Boolean),
      `${zone.id}/${side}: every unlisted border cell closed`,
    );
  }
  const endpoints = portsFor(spec, zone.id).map(
    (port) => crossing(spec, port.to, port.arrivalSide, (port.span[0] + port.span[1]) / 2).at,
  );
  for (const link of spec.connections.filter((candidate) => candidate.kind !== 'walk')) {
    if (link.a.zone === zone.id) endpoints.push(link.a.at);
    if (link.b.zone === zone.id) endpoints.push(link.b.at);
  }
  endpoints.push(
    ...spec.bindings.filter((binding) => binding.zone === zone.id).map((binding) => binding.at),
  );
  for (const endpoint of endpoints) {
    check(maskReachable(mask, endpoints[0], endpoint), `${zone.id}: synthetic endpoints connected`);
    maskEndpoints += 1;
  }
}
const bridge = syntheticMask(spec, 'lava_bridge');
check(!bridge[30][40] && bridge[75][40], 'synthetic lava blocked except supported bridge strip');
check(
  maskReachable(bridge, [16, 300], [270, 16]),
  'synthetic west bridge reaches east-abutment north branch',
);

let state = {
  generation: 0,
  pending: null,
  position: 'garden',
  settlements: 0,
};
state = intent(state, { type: 'start', target: 'woodland' });
const staleGeneration = state.generation;
state = intent(state, { type: 'cancel' });
check(
  intent(state, { type: 'finish', generation: staleGeneration }) === state,
  'cancelled completion ignored',
);
state = intent(state, { type: 'start', target: 'town' });
check(
  intent(state, { type: 'finish', generation: staleGeneration }) === state,
  'superseded completion ignored',
);
state = intent(state, { type: 'finish', generation: state.generation });
check(
  state.position === 'town' && state.settlements === 1 && state.pending === null,
  'current completion settles once',
);
check(
  intent(state, { type: 'finish', generation: state.generation }) === state,
  'duplicate current callback ignored',
);

// Verify the legacy origin table against this exact snapshot, not memory or an old atlas.
const layoutLiteral = zoneSource.match(/export const regionLayout = (\{[\s\S]*?\}) as const;/)?.[1];
check(
  typeof layoutLiteral === 'string' &&
    layoutLiteral
      .replace(/[\w\s:,{}-]/g, '')
      .replaceAll('[', '')
      .replaceAll(']', '') === '',
  'legacy layout is a literal numeric grid',
);
const actualLayout = JSON.parse(
  layoutLiteral.replace(/(\w+)\s*:/g, '"$1":').replace(/,\s*([}\]])/g, '$1'),
);
const reviewedSourceLayout = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'reviewed-source-layout.json'), 'utf8'),
);
// The older migration demonstration stays frozen. New main already moved the castle;
// do not pretend its current layout is the legacy input. Reject unreviewed new shapes.
check(
  JSON.stringify(actualLayout) === JSON.stringify(spec.migrationPrototype.oldLayout) ||
    JSON.stringify(actualLayout) === JSON.stringify(reviewedSourceLayout.layout),
  'source layout matches the original baseline or explicitly reviewed newer main',
);
check(
  origin(actualLayout.valley, 'garden').join(',') === '320,576',
  'old valley origin includes minCol=-1 and minRow=-1',
);
const fixture = {
  saveVersion: 1,
  player: {
    id: 'fixture-only',
    level: 9,
    grass: 1234.75,
    owned_hats: ['CROWN'],
    deck: ['fixture-card'],
    collection: [{ id: 'visitor', future: 'kept' }],
    guardian: 'visitor',
    postcards: [{ id: 'memory' }],
    futurePlayer: { value: 7 },
  },
  history: [{ id: 'break', grass: 20 }],
  quietView: true,
  missionReturnPending: true,
  futureRoot: { nested: [1, 2, 3] },
  world: {
    region: 'valley',
    x: 700,
    y: 1850,
    visited: ['garden', 'castle', 'future-zone', '__proto__', 'toString'],
    futureWorld: { untouched: true },
  },
};
const before = JSON.stringify(fixture);
const migrated = migrateFixture(spec, fixture);
check(
  migrated.status === 'demonstrated-position-only',
  'migration clearly labelled position-only demonstration',
);
check(JSON.stringify(fixture) === before, 'migration never mutates original input');
check(
  migrated.save.world.region === 'valley' &&
    migrated.save.world.x === 700 &&
    migrated.save.world.y === 1850,
  'old coastal castle position remains on headland footprint',
);
check(
  migrated.save.world.visited.includes('headland') &&
    !migrated.save.world.visited.includes('castle'),
  'old castle discovery does not discover relocated castle',
);
check(
  migrated.save.world.legacyDiscovery.visited.includes('castle'),
  'original castle discovery separately preserved',
);
check(migrated.save.world.visited.includes('future-zone'), 'unknown visited string kept');
check(
  migrated.save.world.visited.includes('__proto__') &&
    migrated.save.world.visited.includes('toString'),
  'unknown names never resolve inherited alias properties',
);
assert.deepEqual(migrated.save.player, fixture.player, 'all player fields preserved');
checks += 1;
assert.deepEqual(migrated.save.history, fixture.history, 'history preserved');
checks += 1;
assert.deepEqual(migrated.save.futureRoot, fixture.futureRoot, 'unknown root fields preserved');
checks += 1;
assert.deepEqual(
  migrated.save.world.futureWorld,
  fixture.world.futureWorld,
  'unknown world fields preserved',
);
checks += 1;
check(
  migrated.save.quietView === true && migrated.save.missionReturnPending === true,
  'Quiet view and protected return untouched',
);
assert.deepEqual(migrateFixture(spec, migrated.save).save, migrated.save, 'migration idempotent');
checks += 1;
const oldLava = clone(fixture);
oldLava.world = { region: 'lava', x: 44, y: 300, visited: ['caldera'] };
const lavaMoved = migrateFixture(spec, oldLava).save.world;
check(
  lavaMoved.region === 'sunreach' && lavaMoved.x === 1004 && lavaMoved.y === 300,
  'old caldera local coordinates survive changed region origin',
);
const oldWest = clone(fixture);
oldWest.world = { region: 'west', x: 448, y: 70, visited: ['gulch'] };
const gulchMoved = migrateFixture(spec, oldWest).save.world;
check(
  gulchMoved.region === 'sunreach' && gulchMoved.x === 448 && gulchMoved.y === 646,
  'old gulch local coordinates survive new negative row',
);
for (const badWorld of [
  { region: 'future', x: 1, y: 1 },
  { region: 'valley', x: -1, y: 1 },
  { region: 'valley', x: 1, y: 1 },
  { layoutVersion: 99, region: 'valley', x: 400, y: 600 },
]) {
  const badSave = { ...clone(fixture), world: badWorld };
  const result = migrateFixture(spec, badSave);
  check(result.status.startsWith('unresolved'), 'unresolvable/future position flagged');
  assert.deepEqual(result.save, badSave, 'unresolved save left unchanged');
  checks += 1;
}

const negatives = [
  [
    'declared narrower width range',
    (s) => {
      s.coordinates.portWidthRangeInclusive = [64, 64];
    },
    'clearance',
  ],
  [
    'reversed width range',
    (s) => {
      s.coordinates.portWidthRangeInclusive = [64, 48];
    },
    'valid declared port-width range',
  ],
  [
    'duplicate named-loop IDs',
    (s) => {
      s.loops = [s.loops[0], s.loops[0], s.loops[0]];
    },
    'unique named-loop IDs',
  ],
  [
    'distinct IDs but repeated cycle edges',
    (s) => {
      s.loops = [0, 1, 2].map((i) => ({
        ...clone(s.loops[0]),
        id: `repeated-${i}`,
      }));
    },
    'three independent named cycles',
  ],
  [
    'collapsed physical-region transit identity',
    (s) => {
      s.connections.find((l) => l.id === 'gulch-caldera').serviceEndpoints = [
        'sunreach',
        'sunreach',
      ];
    },
    'distinct service endpoints',
  ],
  [
    'missing reciprocal side',
    (s) => {
      s.connections[0].b.side = 'west';
    },
    'reciprocal side',
  ],
  [
    'over-wide passage',
    (s) => {
      s.connections[0].span = [100, 200];
    },
    'clearance',
  ],
  [
    'off-grid passage',
    (s) => {
      s.connections[0].span[0] += 1;
    },
    'cell-aligned span',
  ],
  [
    'diagonal zone adjacency',
    (s) => {
      s.zones.find((z) => z.id === 'woodland').row = -1;
    },
    'cardinal adjacency',
  ],
  [
    'unintended castle back door',
    (s) => {
      s.connections.push({
        id: 'bad-castle-shortcut',
        kind: 'walk',
        a: { zone: 'castle', side: 'north' },
        b: { zone: 'springs', side: 'south' },
        span: [144, 200],
        grade: 1,
        gradeChange: 'ramp',
        corridor: 'Invalid extra castle approach.',
        frame: 'A broken escarpment that must not be accepted.',
      });
    },
    'castle sole approach',
  ],
  [
    'north branch over lava',
    (s) => {
      s.connections.find((l) => l.id === 'lava-bridge-caldera').span = [136, 192];
    },
    'east abutment',
  ],
  [
    'copied reward rule',
    (s) => {
      s.bindings.find((b) => b.id === 'book').reward = 999;
    },
    'no copied rules',
  ],
  [
    'missing valley loop',
    (s) => {
      s.connections = s.connections.filter((l) => l.id !== 'headland-park');
    },
    'three valley cycles',
  ],
  [
    'disconnected moon',
    (s) => {
      s.connections = s.connections.filter((l) => l.id !== 'halcyon-lumen');
    },
    'whole graph reachable',
  ],
  [
    'runtime activation',
    (s) => {
      s.policies.runtimeImported = true;
    },
    'not runtime imported',
  ],
  [
    'new travel fee',
    (s) => {
      s.policies.addsTravelCosts = true;
    },
    'policy addsTravelCosts',
  ],
  [
    'moved maglev station',
    (s) => {
      s.connections.find((l) => l.id === 'cogsworth-neon').b.zone = 'neon';
    },
    'exact existing transit',
  ],
];
for (const [name, change, expected] of negatives) {
  const broken = clone(spec);
  change(broken);
  check(
    validate(broken).some((error) => error.includes(expected)),
    `negative control rejected: ${String(name)}`,
  );
}

console.log(`Connected-world DESIGN proposal: ${checks} assertions passed.`);
console.log(
  `Coverage: ${spec.zones.length} zones; ${spec.regions.length} regions; ${walks.length} reciprocal walk links; ${crossingSamples} directional samples; ${maskEndpoints} synthetic endpoints; 3 valley cycles; ${negatives.length} rejected negative controls.`,
);
console.log(
  'Also checked: source-derived transit stops/vehicles, stop-ID routing inside one physical region, declared width range, independent named cycles, retained actions, blocked castle back door, east-abutment branch, diagonal rejection, stale one-shot intents and idempotent position-only migration fixtures preserving player/unknown fields.',
);
console.log(
  'NOT tested: actual generated terrain/collisions, real bridge supports, app routing or saves, visuals, browser, phone, native lifecycle or multiplayer. No game files or player saves were changed.',
);

// Shared only with the adjacent design-extension checks, never imported by the app.
module.exports = {
  graph,
  reachable,
  crossing,
  attemptCross,
  origin,
  proposedLayouts,
};
