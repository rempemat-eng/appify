// Reproduce: node game/test/combat/build_flight_oracle.mjs /path/to/original-modules.json
// Expose only original F; the source is hash-verified before adding that test-only export.
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import vm from 'node:vm';
const reference = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const hash = s => createHash('sha256').update(s).digest('hex');
if (hash(reference.engine) !== '21aa782577f3d2fc51389efdd80c4c61a1a7ddd48d128e01eb318daa75d6bc10' ||
    hash(reference.catalogue) !== '8b2dc37132bc29f9e9f184b42abc209933a2ba98f35ef46e9c1061838492ad6f') throw Error('Wrong oracle');
const modules = new Map();
for (const [key, id, deps] of [['catalogue', 3501, []], ['engine', 3500, [3501]]]) {
  let source = reference[key];
  if (key === 'engine') {
    const ending = '},3500,[3501]);';
    if (!source.endsWith(ending)) throw Error('Boundary changed');
    source = source.slice(0, -ending.length) + '_e.oracleFlight=F;' + ending;
    source = source.replace('function T(i,e,a){', 'function T(i,e,a){i.oracleImpacts.push({target_id:a?.id??null,position:[e.x,e.y],damage:e.damage,pierce:e.pierce,hit_ids:[...e.hitIds]});');
  }
  let factory, moduleId, dependencies;
  vm.runInNewContext(source, { __d: (f, i, d) => { factory = f; moduleId = i; dependencies = d; } }, { timeout: 1000 });
  if (moduleId !== id || JSON.stringify(dependencies) !== JSON.stringify(deps)) throw Error('Dependencies changed');
  const exports = {};
  factory({}, i => modules.get(i), null, null, { exports }, exports, dependencies);
  modules.set(id, exports);
}
const engine = modules.get(3500);
const launches = JSON.parse(readFileSync(new URL('./projectile-oracle.json', import.meta.url))).cases;
const cases = [];
for (const sample of launches) for (const initial of sample.expected) for (const ticks of [1, 7, 120]) {
  const state = engine.createCombatState(sample.id);
  state.enemies = []; state.oracleImpacts = [];
  const shot = { ...initial, x: initial.position[0], y: initial.position[1],
    vx: initial.velocity[0], vy: initial.velocity[1], hitIds: [...initial.hit_ids],
    blastRadius: initial.blast_radius, launchHeight: initial.launch_height, flightDuration: initial.flight_duration };
  state.projectiles = [shot];
  for (let t = 0; t < ticks && state.projectiles.length; t++) engine.oracleFlight(state);
  cases.push({ initial, ticks, alive: state.projectiles.length > 0,
    position: [shot.x, shot.y], age: shot.age, remaining: shot.remaining });
}
const contacts = [];
for (const id of ['bramble', 'morel', 'mirra', 'clack', 'rook', 'brine', 'pendle']) for (const powered of [false, true]) {
  const initial = launches.find(c => c.id === id && c.powered === powered && c.angle === 0 && c.action === 'primary').expected[0];
  const state = engine.createCombatState(id); state.oracleImpacts = [];
  state.enemies = state.enemies.slice(0, 2).map((e, n) => ({ ...e, id: n + 1, x: 130 + n * 25, y: 98, hp: 500, radius: 1 }));
  const targets = state.enemies.map(e => ({ id: e.id, position: [e.x, e.y], hp: e.hp, radius: e.radius }));
  state.fields = [{id: 999, kind: 'seal', x: 110, y: 98, radius: 1, remaining: 1}];
  const shot = { ...initial, x: initial.position[0], y: initial.position[1], vx: 6000, vy: 0,
    hitIds: [], blastRadius: initial.blast_radius, launchHeight: initial.launch_height, flightDuration: initial.flight_duration };
  state.projectiles = [shot]; engine.oracleFlight(state);
  contacts.push({ initial: {...initial, velocity: [6000, 0]}, targets,
    seals: [{position: [110,98],radius:1,remaining:1}], alive: state.projectiles.length > 0,
    impacts: state.oracleImpacts, position: [shot.x, shot.y], pierce: shot.pierce, hit_ids: shot.hitIds });
}
writeFileSync(new URL('./flight-contacts-oracle.json', import.meta.url), JSON.stringify({contacts}, null, 2)+'\n');
writeFileSync(new URL('./flight-oracle.json', import.meta.url), JSON.stringify({ engine_sha256: hash(reference.engine), cases }, null, 2) + '\n');
console.log(`${cases.length} original F flight samples`);
