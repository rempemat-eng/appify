// Reproduce with the pinned #245 canonical/reference/adapter.mjs as the sole argument.
// The original engine is the oracle, not AbilityProjectiles or a restatement of its formulas.
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const adapter = await import(pathToFileURL(resolve(process.argv[2])).href);
if (adapter.canonicalProvenance.engineSha256 !== '21aa782577f3d2fc51389efdd80c4c61a1a7ddd48d128e01eb318daa75d6bc10') throw Error('Wrong oracle');
const engine = adapter.loadCanonicalCombat({ referenceHelpers: true });
const cases = [];
function sample(id, action, powered, rounds = 1, distance = 120, angle = 0, height = 0) {
  const state = engine.createCombatState(id);
  state.enemies = [];
  const p = state.player;
  Object.assign(p, { x: 86, y: 98, actionDirX: Math.cos(angle), actionDirY: Math.sin(angle),
    aimX: 86 + distance, aimY: 98, vaultHeight: height, ammo: rounds });
  if (powered) engine.__reference.activateForm(state);
  engine.__reference.primary(state, action);
  cases.push({ id, action, powered, rounds, distance, angle, height, expected: state.projectiles.map(x => ({
    kind: x.kind, owner: x.owner, source: x.source, position: [x.x, x.y], velocity: [x.vx, x.vy],
    radius: x.radius, remaining: x.remaining, damage: x.damage, pierce: x.pierce,
    blast_radius: x.blastRadius, powered: x.powered, launch_height: x.launchHeight,
    age: x.age, flight_duration: x.flightDuration, hit_ids: x.hitIds,
  })) });
}
for (const id of engine.ROSTER.map(x => x.id)) for (const powered of [false, true]) {
  sample(id, 'primary', powered);
  sample(id, 'primary', powered, 1, 72, 0.63, 13);
}
for (const n of [0, 1, 2, 3]) sample('pendle', 'secondary', false, n);
sample('pendle', 'secondary', true, 0);
for (const powered of [false, true]) sample('cairn', 'secondary', powered);
for (const distance of [0, 28, 70, 135, 300]) sample('morel', 'primary', true, 1, distance);
writeFileSync(new URL('./projectile-oracle.json', import.meta.url), JSON.stringify({
  source_commit: '1820a07c5ae8b745e239aa2aaa25e0c5ef483d42', engine_sha256: adapter.canonicalProvenance.engineSha256, cases,
}, null, 2) + '\n');
console.log(`${cases.length} original-engine launch samples`);
