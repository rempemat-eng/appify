'use strict';

// Proposal-only contract. Reuses the baseline's checks, not production pathfinding.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  graph,
  reachable,
  crossing,
  attemptCross,
  origin,
  proposedLayouts,
} = require('./check-topology.cjs');
const read = (name) => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
const base = read('topology.json');
const extension = read('biome-extensions.json');
const join = (extra) => ({
  ...base,
  regions: [...base.regions, ...extra.regions],
  zones: [...base.zones, ...extra.zones],
  connections: [...base.connections, ...extra.connections],
  loops: [...base.loops, ...extra.loops],
});
const opposite = { north: 'south', south: 'north', east: 'west', west: 'east' };
const delta = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };
const pair = (a, b) => [a, b].sort((left, right) => left.localeCompare(right)).join('|');
const { zoneWidth: W, zoneHeight: H, cell: CELL } = base.coordinates;
let assertions = 0;
const check = (value, label) => {
  assert.ok(value, label);
  assertions += 1;
};

function validate(extra) {
  const errors = [];
  const demand = (value, label) => {
    if (!value) errors.push(label);
  };
  const all = join(extra);
  const zones = new Map(all.zones.map((zone) => [zone.id, zone]));
  const regions = new Set(all.regions.map((region) => region.id));
  demand(extra.status === 'proposal-not-runtime', 'proposal only');
  for (const [key, value] of Object.entries(extra.policies))
    demand(value === false, `policy ${key}`);
  demand(zones.size === all.zones.length, 'unique zone ids');
  demand(regions.size === all.regions.length, 'unique region ids');
  const cells = new Set();
  for (const zone of all.zones) {
    const key = `${zone.region}:${zone.col},${zone.row}`;
    demand(!cells.has(key), `no overlapping segments ${zone.id}`);
    cells.add(key);
    demand(regions.has(zone.region), `known region ${zone.id}`);
    demand(Number.isInteger(zone.col) && Number.isInteger(zone.row), `integer segment ${zone.id}`);
  }
  const ids = new Set();
  const seams = new Set();
  for (const link of all.connections) {
    demand(!ids.has(link.id), `unique connection ${link.id}`);
    ids.add(link.id);
    const a = zones.get(link.a.zone),
      b = zones.get(link.b.zone);
    demand(a && b && a !== b, `existing distinct endpoints ${link.id}`);
    if (!a || !b) continue;
    if (link.kind !== 'walk') continue;
    const d = delta[link.a.side];
    demand(a.region === b.region, `no ocean walking ${link.id}`);
    demand(d && opposite[link.a.side] === link.b.side, `reciprocal ports ${link.id}`);
    demand(d && b.col === a.col + d[0] && b.row === a.row + d[1], `adjacent segments ${link.id}`);
    const limit = ['north', 'south'].includes(link.a.side) ? W : H;
    const span = link.span;
    demand(
      Array.isArray(span) && span.length === 2 && span.every(Number.isFinite),
      `span shape ${link.id}`,
    );
    if (Array.isArray(span) && span.length === 2) {
      demand(
        span.every((n) => Number.isInteger(n) && n % CELL === 0),
        `aligned ports ${link.id}`,
      );
      demand(
        span[0] >= 0 && span[1] <= limit && span[1] - span[0] >= 48 && span[1] - span[0] <= 64,
        `port bounds ${link.id}`,
      );
    }
    demand(
      a.tier === b.tier
        ? link.gradeChange === 'level'
        : ['ramp', 'stairs'].includes(link.gradeChange),
      `visible slope ${link.id}`,
    );
    demand(typeof link.frame === 'string' && link.frame.length > 20, `visible boundary ${link.id}`);
    demand(!seams.has(pair(a.id, b.id)), `single seam ${link.id}`);
    seams.add(pair(a.id, b.id));
  }
  const walking = graph(all, ['walk']);
  for (const district of extra.districts) {
    demand(
      zones.get(district.anchor)?.region === district.physicalRegion,
      `district anchor ${district.id}`,
    );
    demand(
      district.zones.every((id) => zones.get(id)?.region === district.physicalRegion),
      `district membership ${district.id}`,
    );
    demand(
      district.zones.every((id) => reachable(walking, district.anchor).has(id)),
      `district walkable ${district.id}`,
    );
  }
  for (const loop of extra.loops) {
    demand(loop.zones.length >= 4 && loop.zones[0] === loop.zones.at(-1), `closed loop ${loop.id}`);
    demand(
      new Set(loop.zones.slice(0, -1)).size === loop.zones.length - 1,
      `simple loop ${loop.id}`,
    );
    demand(
      loop.zones.slice(1).every((id, i) => walking.get(loop.zones[i])?.has(id)),
      `loop edges ${loop.id}`,
    );
  }
  for (const blocked of extra.blockedAdjacencies) {
    demand(zones.has(blocked.a) && zones.has(blocked.b), `blocked endpoints ${blocked.a}`);
    demand(!seams.has(pair(blocked.a, blocked.b)), `blocked seam ${blocked.a}`);
  }
  demand(walking.get('high_lookout')?.size === 1, 'lookout remains optional terminus');
  demand(
    !reachable(walking, 'garden').has('lagoon_landing'),
    'sea separates island from mainland walking',
  );
  const sea = extra.connections.filter((link) => link.kind !== 'walk');
  demand(sea.length === 1, 'one proposed sea link only');
  const link = sea[0];
  demand(
    link?.kind === 'proposed-sea-link' && link.runtimeEnabled === false,
    'sea not existing service',
  );
  demand(link?.activation === 'explicit-interaction-only', 'deliberate sea departure');
  demand(
    link?.a.zone === 'harbour' && link?.b.zone === 'lagoon_landing',
    'sea endpoints retain return anchor',
  );
  for (const endpoint of [link?.a, link?.b])
    demand(
      Array.isArray(endpoint?.at) &&
        endpoint.at.every(Number.isFinite) &&
        endpoint.at[0] > 16 &&
        endpoint.at[0] < W - 16 &&
        endpoint.at[1] > 16 &&
        endpoint.at[1] < H - 16,
      'inland landing point',
    );
  demand(
    reachable(graph(all, ['walk', 'door', 'transit', 'proposed-sea-link']), 'garden').size ===
      zones.size,
    'concept graph connected including proposed link',
  );
  demand(
    base.bindings.filter((binding) => binding.missionId === 'mountain').length === 1 &&
      base.bindings.find((binding) => binding.missionId === 'mountain')?.zone === 'ridge',
    'existing mountain mission retained',
  );
  return errors;
}

check(validate(extension).length === 0, validate(extension).join('; '));
const all = join(extension);
check(all.zones.length === 31 && all.regions.length === 8, '31 segments / eight physical regions');
const walks = extension.connections.filter((link) => link.kind === 'walk');
check(walks.length === 9, 'five snow and four island links');
for (const link of walks) {
  for (const [a, b] of [
    [link.a, link.b],
    [link.b, link.a],
  ]) {
    for (let lateral = link.span[0] + CELL / 2; lateral < link.span[1]; lateral += CELL) {
      const next = crossing(all, a.zone, a.side, lateral);
      check(next?.zone === b.zone, `${link.id} every open cell reaches opposite segment`);
      check(
        next.at[['north', 'south'].includes(b.side) ? 0 : 1] === lateral,
        `${link.id} preserves lateral offset`,
      );
    }
    check(crossing(all, a.zone, a.side, link.span[0] - 2) === null, `${link.id} below span closed`);
    check(crossing(all, a.zone, a.side, link.span[1]) === null, `${link.id} half-open end closed`);
  }
}
check(crossing(all, 'fir_hollow', 'south', 160) === null, 'no snow-to-woodland cliff shortcut');
check(
  attemptCross(all, 'lagoon_landing', [318, 574], [322, 578]) === null,
  'no island diagonal corner escape',
);
for (const district of extension.districts) {
  const set = new Set(district.zones);
  const edges = all.connections.filter(
    (link) => link.kind === 'walk' && set.has(link.a.zone) && set.has(link.b.zone),
  );
  check(edges.length - set.size + 1 === 1, `${district.id} exactly one independent circuit`);
}
const oldLayout = proposedLayouts(base).valley;
const newLayout = proposedLayouts(all).valley;
for (const zone of Object.keys(oldLayout)) {
  const before = origin(oldLayout, zone),
    after = origin(newLayout, zone);
  check(
    after[0] - before[0] === 0 && after[1] - before[1] === 1152,
    `${zone} snow expansion shifts origin, not local position`,
  );
}
check(
  JSON.stringify(extension.saveIntegration.snowOriginShiftArtPixels) === '[0,1152]',
  'documented origin shift matches coordinates',
);

const negatives = [
  [
    'ocean footpath',
    (s) => {
      s.connections.at(-1).kind = 'walk';
    },
    'no ocean walking',
  ],
  [
    'active boat',
    (s) => {
      s.connections.at(-1).runtimeEnabled = true;
    },
    'sea not existing service',
  ],
  [
    'automatic boat',
    (s) => {
      s.connections.at(-1).activation = 'on-arrival';
    },
    'deliberate sea departure',
  ],
  [
    'lost return point',
    (s) => {
      s.connections.at(-1).a.zone = 'garden';
    },
    'sea endpoints',
  ],
  [
    'tide gate',
    (s) => {
      s.policies.tidesAffectAccess = true;
    },
    'policy tides',
  ],
  [
    'broken island loop',
    (s) => {
      s.connections = s.connections.filter((l) => l.id !== 'black-sand-landing');
    },
    'loop edges',
  ],
  [
    'snow tile overlap',
    (s) => {
      s.zones[0].col = 0;
    },
    'no overlapping',
  ],
  [
    'mismatched port',
    (s) => {
      s.connections[0].b.side = 'south';
    },
    'reciprocal ports',
  ],
  [
    'diagonal ascent',
    (s) => {
      s.zones.find((z) => z.id === 'snow_saddle').col = 1;
    },
    'adjacent segments',
  ],
  [
    'missing ramp',
    (s) => {
      s.connections.find((l) => l.id === 'headwaters-black-sand').gradeChange = 'level';
    },
    'visible slope',
  ],
  [
    'island reset',
    (s) => {
      s.policies.resetsPlayerData = true;
    },
    'policy resets',
  ],
];
for (const [name, mutate, reason] of negatives) {
  const broken = structuredClone(extension);
  mutate(broken);
  check(
    validate(broken).some((error) => error.includes(reason)),
    `reject ${String(name)}`,
  );
}
console.log(
  `Biome extension DESIGN: ${assertions} assertions passed; ${negatives.length} rejected negative controls.`,
);
console.log(
  'Combined concept: 31 segments, 8 physical regions, 28 walk seams, 5 circuits, 6 retained transit services and 1 separately proposed sea link.',
);
console.log(
  'Not runtime: no boat service, actual slopes/bridges/collision grids, save migration, device or browser integration tested.',
);

const transport = read('transport-contract.json');
function validateTransport(contract) {
  const errors = [];
  const demand = (value, label) => {
    if (!value) errors.push(label);
  };
  const services = new Map(
    base.connections.filter((l) => l.kind === 'transit').map((l) => [l.id, l]),
  );
  const covered = [];
  const gauges = {
    train: 'standard-rail',
    carts: 'narrow-mine-rail',
    maglev: 'separate-elevated-guideway',
    capsule: 'not-a-railway',
    shuttle: 'not-a-railway',
  };
  const terminals = {
    train: 'buffer-stop',
    carts: 'buffer-stop',
    maglev: 'guideway-buffer',
    capsule: 'sealed-dock',
    shuttle: 'landing-pad',
  };
  const modesAt = new Map();
  demand(
    new Set(contract.networks.map((n) => n.id)).size === contract.networks.length,
    'unique network IDs',
  );
  for (const network of contract.networks) {
    demand(network.gauge === gauges[network.mode], `mode/gauge never changes ${network.id}`);
    demand(
      network.connectionIds.length === network.orderedStops.length - 1,
      `continuous station chain ${network.id}`,
    );
    demand(
      new Set(network.orderedStops).size === network.orderedStops.length,
      `no phantom station loop ${network.id}`,
    );
    for (const [index, id] of network.connectionIds.entries()) {
      const service = services.get(id);
      covered.push(id);
      demand(service?.vehicle === network.mode, `existing vehicle retained ${id}`);
      demand(
        service &&
          pair(...service.serviceEndpoints) ===
            pair(network.orderedStops[index], network.orderedStops[index + 1]),
        `consecutive segment endpoints ${id}`,
      );
    }
    demand(network.terminals.length === 2, `two explicit terminals ${network.id}`);
    demand(
      network.terminals[0]?.stop === network.orderedStops[0] &&
        network.terminals[1]?.stop === network.orderedStops.at(-1),
      `terminal matches chain ${network.id}`,
    );
    demand(
      network.terminals.every((t) => t.end === terminals[network.mode]),
      `supported terminal type ${network.id}`,
    );
    demand(
      JSON.stringify(network.throughStops) === JSON.stringify(network.orderedStops.slice(1, -1)),
      `all internal stations are through stations ${network.id}`,
    );
    for (const stop of network.orderedStops) {
      if (!modesAt.has(stop)) modesAt.set(stop, []);
      modesAt.get(stop).push(network.id);
    }
  }
  demand(
    covered.length === services.size &&
      new Set(covered).size === services.size &&
      covered.every((id) => services.has(id)),
    'all existing services covered exactly once',
  );
  for (const [stop, networks] of modesAt) {
    const interchanges = contract.interchanges.filter((i) => i.stop === stop);
    demand(interchanges.length === (networks.length > 1 ? 1 : 0), `exact interchange at ${stop}`);
    if (networks.length < 2) continue;
    const interchange = interchanges[0];
    demand(
      interchange?.trackJoin === false && interchange?.connection === 'pedestrian-forecourt',
      `no mode-changing rail join ${stop}`,
    );
    demand(
      JSON.stringify([...(interchange?.networks ?? [])].sort((a, b) => a.localeCompare(b))) ===
        JSON.stringify([...networks].sort((a, b) => a.localeCompare(b))),
      `interchange networks ${stop}`,
    );
  }
  demand(contract.sea.status === 'proposed-only-not-existing-service', 'sea remains proposed');
  demand(
    JSON.stringify(contract.sea.endpoints) === '["harbour","lagoon_landing"]',
    'sea touches named piers only',
  );
  return errors;
}
check(validateTransport(transport).length === 0, validateTransport(transport).join('; '));
const transportNegatives = [
  [
    'missing track segment',
    (s) => {
      s.networks[0].connectionIds.pop();
    },
    'continuous station chain',
  ],
  [
    'train becomes path',
    (s) => {
      s.networks[0].mode = 'walk';
    },
    'existing vehicle retained',
  ],
  [
    'track fades at end',
    (s) => {
      s.networks[0].terminals[0].end = 'path';
    },
    'supported terminal type',
  ],
  [
    'maglev joins normal rail',
    (s) => {
      s.interchanges[0].trackJoin = true;
    },
    'no mode-changing rail join',
  ],
  [
    'through track vanishes at Cogsworth',
    (s) => {
      s.networks[0].throughStops = [];
    },
    'through stations',
  ],
  [
    'wrong sea landing',
    (s) => {
      s.sea.endpoints[1] = 'black_sand';
    },
    'named piers',
  ],
];
for (const [name, mutate, reason] of transportNegatives) {
  const broken = structuredClone(transport);
  mutate(broken);
  check(
    validateTransport(broken).some((error) => error.includes(reason)),
    `transport rejects ${String(name)}`,
  );
}
console.log(
  `Combined extension + transport checks: ${assertions} assertions; ${negatives.length + transportNegatives.length} rejected negative controls. Track continuity is a graph/design guarantee, not proof of pixels in the concept render.`,
);
