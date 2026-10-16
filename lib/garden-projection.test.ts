import assert from 'node:assert/strict';
import { billboard, lift, makeProjection, project, unproject } from './garden-projection';

const native = { width: 192, height: 176 };
const near = (a: number, b: number, eps = 1e-6) => Math.abs(a - b) < eps;

// Flat view is the identity mapping the garden already used.
const flat = makeProjection('flat', 384, native);
assert.equal(flat.scale, 2);
assert.equal(flat.height, 352);
for (const [x, y] of [
  [0, 0],
  [96, 112],
  [191, 175],
]) {
  const s = project(flat, x, y);
  assert.ok(near(s.sx, x * 2) && near(s.sy, y * 2) && s.f === 1, 'flat identity');
}

// Tilted view: near edge keeps full scale, the far edge shrinks and rises.
const tilt = makeProjection('tilt', 402, native, 60);
const bottom = project(tilt, 96, 176);
const top = project(tilt, 96, 0);
assert.ok(near(bottom.f, 1) && near(bottom.sy, tilt.height), 'near edge at the bottom');
assert.ok(top.f < 0.9 && top.f > 0.6, `far edge shrinks (${top.f.toFixed(3)})`);
assert.ok(near(top.sy, tilt.horizon, 1e-6), 'far edge meets the horizon');
assert.ok(tilt.height < 176 * (402 / 192), 'tilted world is shorter than flat');

// Depth ordering: higher on the ground plane is always higher on screen and smaller.
let prev = project(tilt, 96, 176);
for (let y = 170; y >= 0; y -= 6) {
  const s = project(tilt, 96, y);
  assert.ok(s.sy < prev.sy && s.f < prev.f, 'monotonic depth');
  prev = s;
}

// Taps round-trip: unproject(project(p)) == p.
for (const [x, y] of [
  [20, 40],
  [96, 112],
  [170, 150],
  [5, 170],
]) {
  const s = project(tilt, x, y);
  const back = unproject(tilt, s.sx, s.sy);
  assert.ok(near(back.x, x, 1e-6) && near(back.y, y, 1e-6), `round trip ${x},${y}`);
}

// Billboards stand on their feet point and shrink with distance.
const farTree = billboard(tilt, 80, -10, 36, 46);
const nearTree = billboard(tilt, 80, 120, 36, 46);
assert.ok(farTree.width < nearTree.width, 'far billboard smaller');
assert.ok(near(farTree.top + farTree.height, project(tilt, 98, 36).sy), 'feet on the ground');

console.log(
  'PASS: 2.5D projection is identity when flat; tilt keeps depth order, taps round-trip, billboards stand on the ground.',
);
for (const [x, y, g] of [
  [52, 29, 76],
  [140, 106, 112],
]) {
  const a = lift(flat, x, y, g);
  assert.ok(near(a.sx, x * 2) && near(a.sy, y * 2), 'lift is identity when flat');
  const b = lift(tilt, x, y, g);
  assert.ok(b.sy < project(tilt, x, g).sy, 'lifted point is above its ground point');
}
console.log('PASS: airborne points lift above their ground point.');
