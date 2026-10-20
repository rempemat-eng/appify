import assert from 'node:assert/strict';
import { ANIMAL_LOOP, animalAt, animalPlan, flatEvents } from './animal-life';
import {
  ZONE,
  zoneAnimalSpots,
  zoneAnimals,
  zoneIds,
  zoneMaps,
  zoneTerrain,
  type ZoneId,
} from './zone-maps';
import { existsSync } from 'node:fs';

// Animals that live (art-faults.md A9): every placed animal has a loop that fits the shared
// clock, ends where it began, faces the way it walks, and only wanders where its feet may go.
const CELL = ZONE.cell;
/** The walk cells under an animal's feet (scripts/art/animal_frames.foot_cells). */
const feet = (x: number, y: number, w: number, h: number) => {
  const out = new Set<string>();
  for (let yy = y + h - 6; yy < y + h; yy++)
    for (let xx = x + 3; xx < x + w - 3; xx++)
      out.add(`${Math.floor(xx / CELL)},${Math.floor(yy / CELL)}`);
  return out;
};

let animals = 0;
let movers = 0;
const kinds = new Set<string>();
for (const zone of zoneIds as readonly ZoneId[]) {
  const map = zoneMaps[zone];
  for (const [oid, sprite, x, y, w, h] of map.objects) {
    const kind = zoneAnimals[sprite];
    if (!kind) continue;
    animals++;
    kinds.add(sprite);
    // every frame is a picture the app bundles, and the still is frame 0 of its side
    for (const f of [...kind.east, ...kind.west, ...(kind.shade ? [kind.shade] : [])])
      assert.ok(
        existsSync(new URL(`../assets/zones/props/${f[0]}.png`, import.meta.url)),
        `${sprite}: frame ${f[0]} has no picture`,
      );
    assert.equal(
      (kind.faces === 'east' ? kind.east : kind.west)[0][0],
      sprite,
      `${sprite}: the still is not its own side's first frame`,
    );
    assert.equal(kind.east.length, kind.west.length, `${sprite}: its sides differ in frames`);
    assert.ok(kind.idle.length >= 1, `${sprite}: no idle accents`);
    for (const [i] of kind.idle) assert.ok(i > 0 && i < kind.east.length, `${sprite}: idle ${i}`);

    const plan = animalPlan(zone, oid, kind);
    assert.equal(
      ANIMAL_LOOP % plan.period,
      0,
      `${zone}/${oid}: its loop does not divide the clock`,
    );
    const ev = plan.events;
    assert.equal(ev[0][0], 0);
    assert.ok(Math.abs(ev[ev.length - 1][1] - plan.period) < 1e-6, `${zone}/${oid}: loop length`);
    for (let i = 1; i < ev.length; i++) {
      assert.ok(Math.abs(ev[i][0] - ev[i - 1][1]) < 1e-6, `${zone}/${oid}: a gap in its loop`);
      assert.deepEqual([ev[i][2], ev[i][3]], [ev[i - 1][4], ev[i - 1][5]], `${zone}/${oid}: jumps`);
    }
    // it starts and ends at home, facing the same way (no jump or turn as the clock wraps)
    assert.deepEqual([ev[0][2], ev[0][3]], [0, 0]);
    assert.deepEqual([ev[ev.length - 1][4], ev[ev.length - 1][5]], [0, 0]);
    assert.equal(ev[0][6], ev[ev.length - 1][6], `${zone}/${oid}: turns as the loop wraps`);
    // most of the time it stands
    const walking = ev.filter((e) => e[7] < 0).reduce((a, e) => a + e[1] - e[0], 0);
    assert.ok(
      walking <= plan.period * 0.35,
      `${zone}/${oid}: walks ${walking} ms of ${plan.period}`,
    );
    for (const e of ev) {
      if (e[7] >= 0) continue;
      const dx = e[4] - e[2];
      if (dx) assert.equal(e[6], dx > 0 ? 0 : 1, `${zone}/${oid}: walks backwards`);
    }

    const spots = zoneAnimalSpots[zone]?.[oid] ?? [];
    if (kind.moves === 'still') assert.equal(spots.length, 0, `${zone}/${oid} should stay put`);
    if (spots.length) movers++;
    // where it goes: on the straight way to each spot and back, its feet stay on ground it
    // may stand on (open walk cells or its own home's, or water for a swimmer or a wader)
    const home = feet(x, y, w, h);
    // (a wader keeps to what it stands in at home: the shallows, or the shallows and the bank)
    const wades = new Set(
      [...home].map((cell) => {
        const [c, r] = cell.split(',').map(Number);
        return zoneTerrain[zone][r]?.[c];
      }),
    );
    const ok = (dx: number, dy: number) => {
      if (dx === 0 && dy === 0) return true; // home is where the zone put it
      for (const cell of feet(x + dx, y + dy, w, h)) {
        const [c, r] = cell.split(',').map(Number);
        const t = zoneTerrain[zone][r]?.[c];
        if (t === undefined) return false;
        if (kind.moves === 'ground') {
          if (!'.='.includes(t)) return false;
          if (map.walk[r][c] !== '.' && !home.has(cell)) return false;
        } else if (kind.moves === 'wade') {
          if (!wades.has(t) || t === '^' || t === '!') return false;
          if (t !== '~' && map.walk[r][c] !== '.' && !home.has(cell)) return false;
        } else if (t !== '~') return false;
      }
      return true;
    };
    const points = [[0, 0], ...spots, [0, 0]];
    for (let i = 1; i < points.length; i++) {
      const [ax, ay] = points[i - 1];
      const [bx, by] = points[i];
      const n = Math.max(Math.abs(bx - ax), Math.abs(by - ay));
      for (let k = 0; k <= n; k++)
        assert.ok(
          ok(Math.round(ax + ((bx - ax) * k) / n), Math.round(ay + ((by - ay) * k) / n)),
          `${zone}/${oid}: its way to (${bx}, ${by}) crosses ground it may not stand on`,
        );
    }
    // the worklet: whole pixels, always a frame of its own, home when the clock is at rest
    const flat = flatEvents(plan);
    for (let ms = 0; ms < plan.period; ms += 97) {
      const at = animalAt(flat, plan.period, plan.phase, kind.walk, kind.stepMs, ms);
      assert.ok(Number.isInteger(at.x) && Number.isInteger(at.y));
      assert.ok(at.frame >= 0 && at.frame < kind.east.length, `${zone}/${oid}: frame ${at.frame}`);
      assert.ok(Math.hypot(at.x, at.y) <= 16, `${zone}/${oid}: wanders ${at.x}, ${at.y}`);
    }
  }
}
for (const sprite of ['sheep', 'sheep_left', 'heron', 'duck', 'cat', 'ibex'])
  assert.ok(kinds.has(sprite), `${sprite} no longer lives anywhere`);
assert.ok(movers >= 8, `only ${movers} animals move`);
console.log(
  `PASS: animal life — ${animals} animals of ${kinds.size} kinds, ${movers} wandering; loops fit the shared clock, end at home facing as placed, mostly stand, face the way they walk and keep their feet on ground they may stand on.`,
);
