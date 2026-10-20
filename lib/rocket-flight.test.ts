/**
 * The rocket and lander journeys (lib/rocket-flight.ts, components/rocket-journey.tsx,
 * scripts/art/rocket.py). Pure checks of the beats and the pictures' data: not the browser's
 * drawing, Reanimated's scheduling or any device.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  ASCENT,
  LANDING,
  LAUNCH,
  LAYOUT,
  PUFF_GONE,
  altitude,
  armFrames,
  boosterAt,
  camera,
  climb,
  docked,
  dustFor,
  flames,
  flightOf,
  grainAt,
  legFrame,
  puffAt,
  puffsFor,
  rcsFrame,
  shake,
  vehicleTop,
  type Flight,
} from './rocket-flight';
import { ROCKET, rocketSizes } from './rocket-sizes';
import { rocketPad, travelBy, travelLinks, travelRoute, travelVehicle } from './world-places';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
let checks = 0;
const ok = (v: unknown, m: string) => {
  assert.ok(v, m);
  checks++;
};
const eq = (a: unknown, b: unknown, m: string) => {
  assert.deepEqual(a, b, m);
  checks++;
};
const flights: Flight[] = ['launch', 'return', 'descent', 'ascent'];
const steps = Array.from({ length: 401 }, (_, i) => i / 400);

// ---- the lines: the rocket replaces the elevator, the rules stay ------------------------
eq(travelVehicle('neon', 'space'), 'rocket', 'the rocket flies from the pad to Halcyon');
eq(travelVehicle('space', 'neon'), 'rocket', 'and back down');
eq(travelVehicle('space', 'moon'), 'shuttle', 'the lander flies on to Lumen');
eq(travelVehicle('moon', 'space'), 'shuttle', 'and back up');
eq(travelBy.space, 'THE ROCKET', 'the travel card names the rocket');
ok(
  travelLinks.some(([a, b]) => a === rocketPad && b === 'space'),
  'the pad is data: the line runs from rocketPad',
);
eq(travelRoute('neon', 'moon'), ['space', 'moon'], 'the route to the moon is unchanged');
eq(flightOf('rocket', 'space'), 'launch', 'up to Halcyon is a launch');
eq(flightOf('rocket', 'neon'), 'return', 'down is the return');
eq(flightOf('shuttle', 'moon'), 'descent', 'to Lumen is a descent');
eq(flightOf('shuttle', 'space'), 'ascent', 'from Lumen is an ascent');
eq(flightOf('train', 'steam'), null, 'every other line keeps its journey');
// a leg lasts what it always did: the journey's times are untouched
const journey = readFileSync(resolve(root, 'components/journey.tsx'), 'utf8');
ok(/const TRIP_MS = 3200;/.test(journey), 'a journey leg still lasts 3.2 s');
ok(/const STILL_MS = 700;/.test(journey), 'reduced motion still lasts 0.7 s');
const world = readFileSync(resolve(root, 'app/(tabs)/world.tsx'), 'utf8');
ok(
  /ms=\{trip\.legs\.length > 1 \? 2200 : undefined\}/.test(world),
  'a leg of a longer trip still 2.2 s',
);
// arriving: never after the journey has left the screen, once only
ok(
  /if \(done\.current \|\| !alive\.current\) return;/.test(journey),
  'no stale arrival after unmount',
);
ok(
  /if \(!active\) \{\s*cancelAnimation\(t\);/.test(journey),
  'an inactive screen stops the flight',
);

// ---- the beats ---------------------------------------------------------------------------
for (const f of flights) {
  const up = f === 'launch' || f === 'ascent';
  const moon = f === 'descent' || f === 'ascent';
  const dock = moon ? LAYOUT.moon.dock : LAYOUT.earth.dock;
  // the climb: from the ground to the port (or back), never past either
  let last = up ? -1 : Infinity;
  for (const p of steps) {
    const a = altitude(f, p);
    ok(a >= -1e-9 && a <= climb(f) + 1e-9, `${f}: altitude within the climb at ${p}`);
    ok(up ? a >= last - 1e-9 : a <= last + 1e-9, `${f}: one way only at ${p}`);
    last = a;
  }
  const top0 = vehicleTop(f, 0);
  const top1 = vehicleTop(f, 1);
  eq(up ? top1 : top0, -dock, `${f}: docked against the port at the ${up ? 'end' : 'start'}`);
  eq(docked(f, up ? 1 : 0), true, `${f}: the port's lamp green while docked`);
  eq(docked(f, up ? 0.5 : 0.5), false, `${f}: and not in flight`);
  // the engines: off at the start of a landing's coast and at the end of every flight
  const fl = flames(f, 1, 3200);
  eq([fl.booster, fl.upper, fl.lander], [-1, -1, -1], `${f}: every engine off on arrival`);
  // the camera: whole px, between the ground and the station framings, the vehicle in view
  for (const h of [380, 450, 560, 655, 700, 900]) {
    const top = Math.ceil(110 / (4 / 3));
    const bottom = Math.ceil(184 / (4 / 3));
    for (const p of steps) {
      const c = camera(f, p, h, top, bottom);
      ok(Number.isInteger(c), `${f}: the camera on whole px`);
      const y = vehicleTop(f, p) - c;
      ok(y >= top - 2 && y <= h - bottom, `${f} (${h} px): the vehicle in view at ${p} (${y})`);
    }
  }
  // thrusters: short puffs, a few frames each
  const rcs = steps.map((p) => rcsFrame(f, p, 3200));
  ok(rcs.some((r) => r >= 0) && rcs.every((r) => r <= 2), `${f}: thruster puffs, finite`);
}

// the launch's own beats, in order: arms, ignition, lift-off, separation, coast, contact
eq(armFrames('launch', 0), [0, 0], 'the arms attached on the pad');
eq(armFrames('launch', 0.21), [3, 3], 'and swung back before ignition');
ok(LAUNCH.armCrew[1] <= LAUNCH.ignite, 'the arms clear before ignition');
eq(flames('launch', LAUNCH.ignite - 0.01, 3200).booster, -1, 'no flame before ignition');
ok(flames('launch', LAUNCH.ignite + 0.05, 3200).booster >= 2, 'a full plume after ignition');
eq(altitude('launch', LAUNCH.liftoff), 0, 'held down on the pad until lift-off');
ok(
  altitude('launch', LAUNCH.liftoff + 0.05) < altitude('launch', 0.6) / 10,
  'lift-off slow, then accelerating',
);
ok(shake('launch', 0.25) !== 0 && shake('launch', 0.8) === 0, 'the ground shakes only at ignition');
ok(boosterAt('launch', LAUNCH.separation - 0.01) !== null, 'the booster carries the stack up');
const b1 = boosterAt('launch', LAUNCH.separation + 0.1);
ok(
  b1 !== null && b1.y - vehicleTop('launch', LAUNCH.separation + 0.1) > 200,
  'after separation the booster falls away below',
);
eq(flames('launch', LAUNCH.separation + 0.01, 3200).booster, -1, 'the booster burns out');
ok(flames('launch', LAUNCH.upperIgnite + 0.05, 3200).upper >= 2, 'the upper stage lights');
eq(flames('launch', LAUNCH.coast + 0.01, 3200).upper, -1, 'and coasts up to the port');
eq(legFrame('launch', 0.5), 0, 'the upper stage flies with its legs folded');
// the landings: legs out, touchdown, compress and settle
eq(legFrame('return', LANDING.legsOut[0] - 0.01), 0, 'legs folded in the fall');
eq(legFrame('return', 1), 3, 'the upper stage stands on compressed legs');
eq(vehicleTop('return', 1), LAYOUT.earth.upperLandDip, 'on the pad');
eq(legFrame('descent', LANDING.touchdown - 0.01), 0, 'the lander flies with its legs out');
eq(legFrame('descent', LANDING.compress), 2, 'they compress at touchdown');
eq(legFrame('descent', 1), 3, 'and settle');
ok(
  vehicleTop('descent', LANDING.compress) > vehicleTop('descent', LANDING.touchdown),
  'the body dips onto its legs',
);
eq(legFrame('ascent', 0), 3, 'the lander starts on its pad');
eq(legFrame('ascent', ASCENT.liftoff + 0.05), 0, 'and unloads its legs as it lifts');

// ---- smoke, steam and dust ------------------------------------------------------------------
for (const f of flights) {
  const puffs = puffsFor(f);
  const moon = f === 'descent' || f === 'ascent';
  eq(puffs.length === 0, moon, `${f}: smoke only where there is air`);
  for (const q of puffs) {
    ok(q.life > 0 && q.life < 0.6, `${f}: a puff lives a short while`);
    eq(puffAt(q, q.at - 0.001).frame, PUFF_GONE, `${f}: nothing before it is born`);
    eq(puffAt(q, q.at + q.life + 1e-9).frame, PUFF_GONE, `${f}: gone when it has rolled out`);
  }
  const dust = dustFor(f);
  eq(dust.length > 0, moon, `${f}: dust only on the moon`);
  for (const g of dust) {
    // ballistic: up and straight back down to the ground, no billowing (one size throughout)
    const path = steps.map((p) => grainAt(g, p)).filter((s) => s !== null);
    ok(path.length > 0, `${f}: each grain flies`);
    ok(
      path.every((s) => s.y <= 0),
      `${f}: never below the ground`,
    );
    ok(grainAt(g, g.at + g.life + 1e-9) === null, `${f}: gone once it lands`);
    const mid = grainAt(g, g.at + g.life / 2);
    ok(mid !== null && mid.y <= -g.h + 1, `${f}: its arc peaks at its height`);
  }
}

// ---- the pictures: sizes by the size guide, memory -----------------------------------------
const STOREY = 32;
const ADULT = 25;
const stack = -LAYOUT.earth.upperOnBooster;
ok(stack >= 4 * STOREY, `the rocket stands at least four storeys (${stack} px)`);
ok(ROCKET.gantry >= stack, 'its gantry stands over it');
ok(ROCKET.diameter >= ADULT, 'it is wider than an adult is tall');
let bytes = 0;
for (const [k, a] of Object.entries(rocketSizes)) {
  const scale = k === 'sky' ? ROCKET.skyScale : ROCKET.scale;
  bytes += a.w * a.h * scale * scale * 4;
}
ok(
  bytes < 12 * 1024 * 1024,
  `all the flights' pictures decode to under 12 MiB (${(bytes / 1048576).toFixed(1)})`,
);

console.log(
  `Rocket journeys: ${checks} checks (beats, camera at 6 screen heights, smoke, dust, sizes; ` +
    `pictures ${(bytes / 1048576).toFixed(1)} MiB decoded). Source-level: not a browser or device test.`,
);
