/** Source-backed probes against the hash-checked original pure engine. */
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { loadCanonicalCombat } from './reference/adapter.mjs';

const data = JSON.parse(readFileSync(new URL('./abilities-v1.json', import.meta.url)));
const constants = JSON.parse(readFileSync(new URL('./reference/runtime-constants.json', import.meta.url)));
const catalogue = JSON.parse(readFileSync(new URL('./reference/catalogue.json', import.meta.url)));
const engine = loadCanonicalCombat({ referenceHelpers: true });
const h = engine.__reference;
const checks = [];
const plain = value => JSON.parse(JSON.stringify(value));
const check = (name, fn) => { fn(); checks.push(name); };
const fresh = id => engine.createCombatState(id, 1, 'practice');
const snapshot = s => plain({ projectiles: s.projectiles, fields: s.fields, effects: s.effects, reload: s.player.reload, heat: s.player.heat, ammo: s.player.ammo, vaultRemaining: s.player.vaultRemaining });
const input = s => ({ active: true, primary: false, secondary: false, special: false, block: false, moveX: 0, moveY: 0, aimX: s.player.x + 120, aimY: s.player.y });
function advance(s, seconds, patch = {}) {
  for (let remaining = seconds; remaining > 1e-10;) {
    const dt = Math.min(.1, remaining);
    s = engine.stepCombat(s, { ...input(s), ...patch }, dt);
    remaining -= dt;
  }
  return s;
}
function isolateTarget(s, distance = 20, kind = 'dummy') {
  s.enemies[0].x = s.player.x + distance;
  s.enemies[0].y = s.player.y;
  s.enemies[0].kind = kind;
  s.enemies[0].hp = 500;
  for (const enemy of s.enemies.slice(1)) { enemy.x = 300; enemy.y = 160; }
  return s.enemies[0];
}

check('exact14-character catalogue/order preserved', () => assert.deepEqual(data.characters.map(c => c.id), catalogue.CHARACTER_IDS));
for (const c of data.characters) for (const form of ['base', 'powered']) {
  const powered = form === 'powered';
  for (const action of ['primary', 'secondary', 'special']) check(`${c.id}/${form}/${action}: original helper and saved timing agree`, () => {
    const s = fresh(c.id);
    s.player.specialRemaining = powered ? c.powered.duration_seconds : 0;
    s.player.action = action;
    s.player.actionDuration = h.duration(s.player, action);
    assert.equal(c[form].actions[action].duration_seconds, s.player.actionDuration);
    assert.equal(c[form].actions[action].release_seconds, h.releaseTime(s.player));
    assert.equal(c[form].actions[action].duration_seconds, constants.characters[c.id][form].actions[action].duration);
    assert.equal(c[form].actions[action].release_seconds, constants.characters[c.id][form].actions[action].releaseTime);
  });
  for (const action of ['primary', 'secondary']) check(`${c.id}/${form}/${action}: direct release snapshot matches recovered reference`, () => {
    const s = fresh(c.id);
    // Recovered release snapshots were captured without targets. Target-hit
    // consequences are checked separately below, not mixed into spawn data.
    s.enemies = [];
    s.player.specialRemaining = powered ? c.powered.duration_seconds : 0;
    if (action === 'primary') h.primary(s, 'primary'); else h.secondary(s);
    assert.deepEqual(snapshot(s), constants.characters[c.id][form][action + 'Release']);
  });
}

check('Nix Q preserves heat; special alone caps existing heat at45', () => {
  for (const powered of [false, true]) {
    const s = fresh('nix'); s.player.heat = 73; s.player.specialRemaining = powered ? 7 : 0;
    s.player.actionOriginX = 80; s.player.actionOriginY = 90;
    s.player.x = 105; s.player.y = 110;
    h.secondary(s);
    assert.equal(s.player.heat, 73);
    assert.equal(s.fields[0].kind, 'hologram'); assert.equal(s.fields[0].x, 80); assert.equal(s.fields[0].y, 90);
    assert.equal(s.fields[0].remaining, 3); assert.equal(s.fields[0].damage, 0);
    h.activateForm(s); assert.equal(s.player.heat, 45);
  }
});

check('Mote powered primary has3 glass plus2 orbit-shard projectiles', () => {
  const s = fresh('mote'); h.activateForm(s); h.primary(s, 'primary');
  assert.equal(s.projectiles.filter(p => p.kind === 'glass').length, 3);
  assert.equal(s.projectiles.filter(p => p.kind === 'orbit-shard').length, 2);
  assert.equal(s.projectiles.length, 5);
});
check('Mote powered idle causes no autonomous orbit damage or projectile spawning', () => {
  let s = fresh('mote'); isolateTarget(s, 17); h.activateForm(s);
  s = advance(s, 2);
  assert.ok(s.player.specialRemaining > 5.9); assert.equal(s.statistics.damageDealt, 0);
  assert.equal(s.enemies[0].hp, 500); assert.equal(s.projectiles.length, 0); assert.equal(s.fields.length, 0);
});

check('Velvet powered guard primes a counter that survives form expiry until consumed', () => {
  let s = fresh('velvet'); isolateTarget(s, 20);
  s.player.specialRemaining = .05; s.player.blocking = true;
  s = engine.applyCombatDamage(s, 10, s.player.x + 20, s.player.y);
  assert.equal(s.player.counterRemaining, 2); assert.equal(s.player.guard, 85);
  s = advance(s, .1);
  assert.equal(s.player.specialRemaining, 0); assert.ok(s.player.counterRemaining > 1.89);
  h.primary(s, 'primary'); assert.equal(s.enemies[0].hp, 465); assert.equal(s.player.counterRemaining, 0);
});
check('Velvet own counter timer expires and returns next primary to21 damage', () => {
  let s = fresh('velvet'); isolateTarget(s, 20); s.player.counterRemaining = 2;
  s = advance(s, 2.1); assert.equal(s.player.counterRemaining, 0);
  h.primary(s, 'primary'); assert.equal(s.enemies[0].hp, 479);
});
check('Velvet flare applies vulnerability before its raw9 damage, yielding12.15', () => {
  const s = fresh('velvet'); isolateTarget(s, 20); h.secondary(s);
  assert.ok(Math.abs((500 - s.enemies[0].hp) - 12.15) < 1e-9);
  assert.equal(s.enemies[0].vulnerableRemaining, 2.2);
});

check('Brine out-of-range tether uses21-damage gun-butt fallback', () => {
  const s = fresh('brine'); isolateTarget(s, 20);
  s.enemies[1].x = 300; s.enemies[1].y = s.player.y;
  s.player.tetherId = s.enemies[1].id; s.player.tetherRemaining = 3;
  h.secondary(s); assert.equal(s.enemies[0].hp, 479); assert.equal(s.projectiles.length, 0);
});
check('Brine heavy reel moves operator42 units and deals15 damage', () => {
  const s = fresh('brine'); const target = isolateTarget(s, 100, 'dummy');
  s.player.tetherId = target.id; s.player.tetherRemaining = 3;
  h.secondary(s); assert.equal(s.player.x, 128); assert.equal(target.x, 186); assert.equal(target.hp, 485);
});
check('Powered harpoon retains launch-captured four-second tether after form expiry', () => {
  let s = fresh('brine'); isolateTarget(s, 44); s.player.specialRemaining = 8;
  h.primary(s, 'primary'); assert.equal(s.projectiles[0].powered, true);
  s.player.specialRemaining = 0; s = advance(s, .2);
  assert.equal(s.player.tetherId, s.enemies[0].id); assert.ok(s.player.tetherRemaining > 3.9);
});
check('Brine/Clack special refills and cancels reload, Pendle special does neither', () => {
  for (const id of ['brine', 'clack', 'pendle']) {
    const s = fresh(id); s.player.ammo = 0; s.player.reload = 1.2; h.activateForm(s);
    assert.equal(s.player.ammo, id === 'pendle' ? 0 : 1);
    assert.equal(s.player.reload, id === 'pendle' ? 1.2 : 0);
  }
});
check('Pendle fan uses only remaining rounds and powered Q is22-damage melee', () => {
  const base = fresh('pendle'); base.player.ammo = 2; h.secondary(base);
  assert.equal(base.projectiles.length, 2); assert.equal(base.player.ammo, 0); assert.equal(base.player.reload, 1.4);
  const powered = fresh('pendle'); isolateTarget(powered, 20); powered.player.specialRemaining = 8;
  h.secondary(powered); assert.equal(powered.projectiles.length, 0); assert.equal(powered.enemies[0].hp, 478);
});
check('Pendle powered primary starts during ordinary empty-ammo reload', () => {
  let s = fresh('pendle'); s.player.ammo = 0; s.player.reload = 1.2; s.player.specialRemaining = 8;
  s = advance(s, .05, { primary: true }); assert.equal(s.player.action, 'primary');
  assert.equal(s.player.actionDuration, .9);
});

check('Morel powered chain is finite and reaches one neighbouring patch outside initial155 search', () => {
  const s = fresh('morel'); s.player.specialRemaining = 8;
  s.fields = [110, 150, 190].map((offset, i) => ({ id: 20 + i, kind: 'reagent', x: s.player.x + offset, y: s.player.y, radius: 18, remaining: 5, damage: 3, tickIn: .2, color: '#d9b570', source: 'morel' }));
  h.secondary(s); assert.equal(s.fields.length, 0); assert.equal(s.effects.filter(e => e.kind === 'reaction').length, 3);
});
check('Mirra seal behind the first target does not amplify its incoming water bolt', () => {
  let s = fresh('mirra'); isolateTarget(s, 34); h.primary(s, 'primary');
  s.fields = [{ id: 20, kind: 'seal', x: 144, y: 98, radius: 18, remaining: 6, damage: 0, tickIn: .2, color: '#77bdd1', source: 'mirra' }];
  s = advance(s, .15); assert.equal(s.enemies[0].hp, 479);
});
check('Mirra seal crossed before the target amplifies to28 damage', () => {
  let s = fresh('mirra'); isolateTarget(s, 34); h.primary(s, 'primary');
  s.fields = [{ id: 20, kind: 'seal', x: 110, y: 98, radius: 18, remaining: 6, damage: 0, tickIn: .2, color: '#77bdd1', source: 'mirra' }];
  s = advance(s, .15); assert.equal(s.enemies[0].hp, 472);
});
check('Mirra replacement threshold does not truncate five powered seals at expiry or next base insertion', () => {
  const s = fresh('mirra'); s.player.specialRemaining = 8;
  s.fields = [0, 1, 2, 3, 4].map(i => ({ id: 20 + i, kind: 'seal', x: 100 + i * 10, y: 50, radius: 18, remaining: 8, damage: 0, tickIn: .2, color: '#77bdd1', source: 'mirra' }));
  h.endForm(s, false); assert.equal(s.fields.length, 5);
  h.secondary(s); assert.equal(s.fields.length, 5); assert.ok(!s.fields.some(f => f.id === 20));
});

check('Ashe natural expiry uses current aim and deals immediate34-damage finisher', () => {
  const s = fresh('ashe'); const target = isolateTarget(s, 20);
  target.x = s.player.x; target.y = s.player.y + 28;
  s.player.specialRemaining = 8; s.player.dirX = 0; s.player.dirY = 1;
  h.endForm(s, false); assert.equal(target.hp, 466); assert.equal(s.player.specialRemaining, 0);
  assert.equal(s.fields[0].x, s.player.x); assert.equal(s.fields[0].y, s.player.y + 52);
});
check('Ashe interruption suppresses expiry finisher', () => {
  const s = fresh('ashe'); isolateTarget(s, 20); s.player.specialRemaining = 8;
  h.endForm(s, true); assert.equal(s.enemies[0].hp, 500); assert.equal(s.fields.length, 0);
});
check('Rook activation creates exactly2 finite turrets and expiry removes designation/turrets', () => {
  const s = fresh('rook'); s.player.designatedId = s.enemies[0].id; s.player.designationRemaining = 1.2; h.activateForm(s);
  assert.equal(s.turrets.length, 2); assert.ok(s.turrets.every(t => t.remaining === 10 && t.cooldown === .18));
  assert.equal(s.player.designatedId, s.enemies[0].id);
  s.player.designatedId = s.enemies[0].id; h.endForm(s, false);
  assert.equal(s.turrets.length, 0); assert.equal(s.player.designatedId, null);
});
check('Queue is one latest-eligible-edge slot; special wins only simultaneous rising edges', () => {
  let s = fresh('bramble'); s.player.action = 'hit'; s.player.actionDuration = .5;
  s = advance(s, 1 / 60, { secondary: true }); assert.equal(s.queuedAction, 'secondary');
  s = advance(s, 1 / 60); s = advance(s, 1 / 60, { special: true }); assert.equal(s.queuedAction, 'special');
  s = advance(s, 1 / 60); s = advance(s, 1 / 60, { secondary: true }); assert.equal(s.queuedAction, 'secondary');
  let both = fresh('bramble'); both.player.action = 'hit'; both.player.actionDuration = .5;
  both = advance(both, 1 / 60, { special: true, secondary: true }); assert.equal(both.queuedAction, 'special');
});
check('Rook turret cooldowns emit two real pulses once designated', () => {
  let s = fresh('rook'); isolateTarget(s, 100); h.activateForm(s);
  s.player.designatedId = s.enemies[0].id; s.player.designationRemaining = 1.2;
  s = advance(s, .2);
  assert.equal(s.projectiles.filter(p => p.kind === 'turret-pulse').length, 2);
  assert.ok(s.turrets.every(t => t.cooldown > .4));
});
check('Rook airborne policy avoids melee/field but allows projectile/explosion damage', () => {
  for (const kind of ['melee', 'field', 'projectile', 'explosion']) {
    let s = fresh('rook'); s.player.airborne = true;
    s = engine.applyCombatDamage(s, 10, s.player.x + 20, s.player.y, kind);
    assert.equal(s.player.hp, ['melee', 'field'].includes(kind) ? 160 : 150);
  }
});
check('Guard recovers22 per second during an attack when recovery gates permit', () => {
  let s = fresh('bramble'); s.player.guard = 50; s.player.action = 'primary';
  s.player.actionDuration = .42; s.player.actionReleased = true;
  s = advance(s, .1); assert.equal(s.player.action, 'primary'); assert.ok(Math.abs(s.player.guard - 52.2) < 1e-9);
});
check('Rook projectile captures launch height and original aimed flight-duration metadata', () => {
  const s = fresh('rook'); s.player.vaultHeight = 12.4; h.primary(s, 'primary');
  assert.equal(s.projectiles[0].launchHeight, 12.4);
  assert.equal(s.projectiles[0].flightDuration, (134 - 9) / 220);
});
check('Non-practice wave victory clears Ashe form without a natural-expiry finisher', () => {
  let s = engine.createCombatState('ashe', 1, 'live'); s.player.specialRemaining = 8;
  for (const enemy of s.enemies) enemy.hp = 0;
  s = advance(s, 1 / 60); assert.equal(s.status, 'victory'); assert.equal(s.player.specialRemaining, 0);
  assert.equal(s.fields.length, 0); assert.equal(s.projectiles.length, 0);
  assert.ok(!s.effects.some(e => e.kind === 'fire-finisher'));
});

const report = { status: 'passed', source_engine_sha256: data.source.engineSha256, source_catalogue_sha256: data.source.catalogueSha256, data_sha256: createHash('sha256').update(readFileSync(new URL('./abilities-v1.json', import.meta.url))).digest('hex'), checks_passed: checks.length, checks, scope: 'hash-checked original compiled pure engine; this is not Godot4.7.2/runtime or new-art validation' };
writeFileSync(new URL('./validation.json', import.meta.url), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ passed: checks.length, failed: 0, data_sha256: report.data_sha256 }));
