import assert from 'node:assert/strict';
import { DAYLIGHT_KEYS, dayPhase, daylight } from './daylight';

// the states by the hour
assert.equal(dayPhase(3), 'night');
assert.equal(dayPhase(7), 'dawn');
assert.equal(dayPhase(12), 'day');
assert.equal(dayPhase(19), 'dusk');
assert.equal(dayPhase(22), 'night');

// by day there is no tint and the lanterns are out
assert.equal(daylight(12).tint, null);
assert.equal(daylight(12).lamps, 0);

// night is a touch darker than the old 0.42 (Matt, 21 Oct 13:37) and the lanterns are lit
const night = daylight(23);
assert.ok(night.tint && Number(/,([0-9.]+)\)$/.exec(night.tint)![1]) > 0.42, night.tint ?? 'none');
assert.equal(night.lamps, 1);

// dusk is warm (more red than blue), dawn is cool (more blue than red)
const ch = (tint: string | null) => tint!.match(/[0-9.]+/g)!.map(Number);
const [dr, , db] = ch(daylight(18.5).tint);
assert.ok(dr > db, 'dusk is warm');
const [ar, , ab] = ch(daylight(6.5).tint);
assert.ok(ab > ar, 'dawn is cool');

// blended: the tint changes a little at a time across a transition, never in a jump
let prev = daylight(16.5);
for (let m = 1; m <= 270; m++) {
  const cur = daylight(16.5 + m / 60);
  const a0 = prev.tint ? ch(prev.tint)[3] : 0;
  const a1 = cur.tint ? ch(cur.tint)[3] : 0;
  assert.ok(Math.abs(a1 - a0) < 0.02, `a smooth dusk at ${16.5 + m / 60}`);
  assert.ok(cur.lamps >= prev.lamps, 'the lanterns only fade in through dusk');
  prev = cur;
}

// reduced motion: no blend, one value per state
assert.equal(daylight(18.2, true).tint, daylight(20.7, true).tint);
assert.notEqual(daylight(16.9, true).tint, daylight(17.1, true).tint);

// the keys cover the day
assert.equal(DAYLIGHT_KEYS[0].at, 0);
assert.equal(DAYLIGHT_KEYS[DAYLIGHT_KEYS.length - 1].at, 24);

console.log('daylight: ok');
