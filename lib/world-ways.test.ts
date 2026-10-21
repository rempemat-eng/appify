import assert from 'node:assert/strict';
import { regionLayout, zoneIds, zoneMaps, zonePorts } from './zone-maps';
import { regionTiles, type RegionId } from './region-walk';
import { stopIds, travelLinks, travelPoints } from './world-places';
import {
  alwaysOpen,
  isAlwaysOpen,
  isWayId,
  onOpenStrip,
  openLines,
  openZones,
  plannedZones,
  prerequisites,
  roadWays,
  taskWords,
  wayById,
  wayForLine,
  wayForZone,
  wayIds,
  waysInReach,
  waysToReach,
  worldWays,
  zonesBehind,
  type WorldWay,
} from './world-ways';

/**
 * The catalogue of ways (lib/world-ways.ts) against the world as drawn and against the
 * two design docs: docs/vision/world-unlocks.md (2.1, 2.4, 2.5) and
 * docs/vision/world-plan.md (section 4). Data only: the rules are Codex's
 * lib/way-progress.ts, and the walk-grid flood fills come with the barriers (P11).
 */

const regions = Object.keys(regionLayout).filter((id): id is RegionId =>
  Object.hasOwn(regionLayout, id),
);
const zonesOf = (region: RegionId) => regionTiles(region).map((t) => t.id as string);
const allZones = regions.flatMap(zonesOf);

// --- ids are unique and the order is the doc's ---
assert.equal(new Set(wayIds).size, wayIds.length, 'way ids are unique');
assert.deepEqual(
  worldWays.map((w) => w.label),
  ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'S1', 'S2', 'S3', 'S4'],
  'the road W1 to W9, then the shortcuts and comforts S1 to S4',
);
assert.deepEqual(
  roadWays.map((w) => w.id),
  [
    'headland',
    'ridge-col',
    'valley-train',
    'ferry',
    'desert-line',
    'chasm-bridge',
    'maglev',
    'elevator',
    'shuttle',
  ],
  'the road keeps the save sketch ids (world-unlocks.md 4)',
);
for (const w of worldWays) {
  assert.ok(isWayId(w.id) && wayById(w.id) === w, `${w.id} looks itself up`);
}
assert.equal(wayById('not-a-way'), undefined, 'an unknown id is undefined, not an error');
assert.equal(isWayId('not-a-way'), false);
console.log('Ways: thirteen, ids unique, in road order.');

// --- prices, tasks and kinds as world-unlocks.md 2.4 and world-plan.md 4 give them ---
const doc: Record<
  string,
  { kind: WorldWay['kind']; after: string | null; task: string | null; grass: number | null }
> = {
  headland: { kind: 'area', after: null, task: 'one rest of 10 min', grass: 25 },
  'ridge-col': { kind: 'area', after: null, task: '45 min of rest in all', grass: 60 },
  'valley-train': { kind: 'line', after: null, task: 'one rest of 30 min', grass: 120 },
  ferry: { kind: 'line', after: null, task: 'an evening rest of 45 min', grass: 150 },
  'desert-line': {
    kind: 'line',
    after: 'valley-train',
    task: 'an hour of rest on 3 different days',
    grass: 250,
  },
  'chasm-bridge': {
    kind: 'area',
    after: 'desert-line',
    task: '6 hours of rest in all',
    grass: 350,
  },
  maglev: { kind: 'line', after: 'valley-train', task: 'an evening rest of 2 h', grass: 450 },
  elevator: {
    kind: 'line',
    after: 'maglev',
    task: 'an hour of rest on 7 different days',
    grass: 700,
  },
  shuttle: {
    kind: 'line',
    after: 'elevator',
    task: 'a long rest of 5 h, on 3 different days',
    grass: 900,
  },
  'mine-cart': { kind: 'shortcut', after: 'chasm-bridge', task: null, grass: 100 },
  'millpond-boat': { kind: 'comfort', after: null, task: null, grass: 60 },
  'coastal-steamer': { kind: 'shortcut', after: 'maglev', task: null, grass: null },
  'ridge-lanterns': { kind: 'comfort', after: null, task: null, grass: 40 },
};
assert.deepEqual(Object.keys(doc).sort(), [...wayIds].sort(), 'every way is in the doc table');
for (const w of worldWays) {
  const d = doc[w.id];
  assert.equal(w.kind, d.kind, `${w.id}'s kind`);
  assert.equal(w.after, d.after, `${w.id} comes in reach after ${d.after}`);
  assert.equal(w.task ? taskWords(w.task) : null, d.task, `${w.id}'s task`);
  assert.equal(w.grass, d.grass, `${w.id}'s price`);
}
assert.equal(
  roadWays.reduce((sum, w) => sum + (w.grass ?? 0), 0),
  3005,
  'the whole road costs 3,005 Dream Dust by the side road (world-unlocks.md 2.4)',
);
for (const w of roadWays) {
  assert.ok(w.task && w.grass !== null && w.grass > 0, `${w.id} opens by either route`);
}
for (const w of worldWays.filter((x) => x.kind === 'shortcut' || x.kind === 'comfort')) {
  assert.equal(w.task, null, `${w.id} is Dream Dust only`);
  assert.equal(w.opens.zones.length + w.opens.plannedZones.length, 0, `${w.id} opens no place`);
  assert.ok(w.grass !== null || w.proposal, `${w.id} has a price unless it is a proposal`);
}
for (const w of worldWays) {
  if (w.task?.kind === 'evening') {
    assert.deepEqual([w.task.fromHour, w.task.toHour], [18, 24], 'evening is 18:00 to midnight');
  }
  if (w.task?.kind === 'long') assert.equal(w.task.minutesEach, 300, 'a long rest is 5 h');
  if (w.task?.kind === 'days') assert.equal(w.task.minutesEachDay, 60, 'a day counts at an hour');
}
console.log('Ways: kinds, tasks and prices match the docs; the road costs 3,005 Dream Dust.');

// --- prerequisites form a DAG in the doc's order ---
const index = new Map(wayIds.map((id, i) => [id as string, i]));
for (const w of worldWays) {
  if (w.after === null) continue;
  assert.ok(isWayId(w.after), `${w.id}'s way before exists`);
  assert.ok(index.get(w.after)! < index.get(w.id)!, `${w.after} comes before ${w.id}`);
}
assert.deepEqual(prerequisites('shuttle'), ['valley-train', 'maglev', 'elevator']);
assert.deepEqual(prerequisites('chasm-bridge'), ['valley-train', 'desert-line']);
assert.deepEqual(prerequisites('mine-cart'), ['valley-train', 'desert-line', 'chasm-bridge']);
assert.deepEqual(prerequisites('headland'), []);
assert.deepEqual(prerequisites('nope'), []);
assert.deepEqual(
  waysInReach([]),
  ['headland', 'ridge-col', 'valley-train', 'ferry', 'millpond-boat', 'ridge-lanterns'],
  'W1 to W4 (and the valley comforts) are in reach from the start',
);
assert.deepEqual(
  waysInReach(['valley-train']).filter((id) => wayById(id)!.kind !== 'comfort'),
  ['headland', 'ridge-col', 'ferry', 'desert-line', 'maglev'],
  'the train brings the desert line and the maglev in reach',
);
console.log('Ways: prerequisites are a DAG in the order W1-W4, W3 > W5 > W6, W3 > W7 > W8 > W9.');

// --- every id the catalogue names exists in today's world ---
for (const w of worldWays) {
  assert.ok(w.barriers.length > 0, `${w.id} stands somewhere`);
  for (const b of w.barriers) {
    assert.ok(regions.includes(b.region), `${w.id}: region ${b.region}`);
    assert.ok(zonesOf(b.region).includes(b.zone), `${w.id}: ${b.zone} is in ${b.region}`);
    if (b.stand !== undefined) {
      const zone = b.zone;
      assert.ok(zone !== 'garden', `${w.id}: the garden has no zone stands`);
      assert.ok(Object.hasOwn(zoneMaps[zone].stands, b.stand), `${w.id}: stand ${zone}.${b.stand}`);
    }
    if (b.at) {
      assert.ok(b.at[0] >= 0 && b.at[0] <= 320 && b.at[1] >= 0 && b.at[1] <= 576, `${w.id}: at`);
    }
    for (const port of b.ports ?? []) {
      assert.ok(Object.hasOwn(zonePorts, port), `${w.id}: port ${port}`);
      assert.ok(port.split('|').includes(b.zone), `${w.id}: ${port} meets ${b.zone}`);
    }
    if (b.stop !== undefined) {
      assert.ok(stopIds.includes(b.stop), `${w.id}: stop ${b.stop}`);
      assert.equal(travelPoints[b.stop].region, b.region, `${w.id}: ${b.stop} is in ${b.region}`);
    }
    if (b.plannedZone) assert.ok(b.plannedZone in plannedZones, `${w.id}: ${b.plannedZone}`);
  }
  for (const z of w.opens.zones) assert.ok(allZones.includes(z), `${w.id} opens ${z}`);
  for (const [a, b] of w.opens.lines) {
    assert.ok(
      travelLinks.some(([x, y]) => (x === a && y === b) || (x === b && y === a)),
      `${w.id}'s line ${a}-${b} is a travelLinks pair`,
    );
  }
  if (w.opens.plannedLine) {
    assert.ok(allZones.includes(w.opens.plannedLine.from), `${w.id}: planned line's start`);
    assert.ok(allZones.includes(w.opens.plannedLine.to), `${w.id}: planned line's end`);
    assert.ok(w.proposal, `${w.id}: a line with no stops is a proposal`);
  }
}
for (const [id, p] of Object.entries(plannedZones)) {
  assert.ok(
    !(zoneIds as readonly string[]).includes(id),
    `${id} is now drawn: move it from plannedZones into its way's zones`,
  );
  assert.ok(regions.includes(p.region), `planned ${id}'s region`);
  const taken = regionTiles(p.region).some((t) => t.col === p.col && t.row === p.row);
  assert.ok(!taken, `planned ${id}'s cell (${p.col}, ${p.row}) is free in ${p.region}`);
}
console.log('Ways: every region, zone, stand, port, stop and line named exists.');

// --- every gated zone and every journey line is guarded by exactly one way ---
for (const zone of allZones) {
  const guards = worldWays.filter((w) => (w.opens.zones as readonly string[]).includes(zone));
  if (isAlwaysOpen(zone)) {
    assert.equal(guards.length, 0, `${zone} is always open and never gated`);
    assert.equal(wayForZone(zone), null);
  } else {
    assert.equal(guards.length, 1, `${zone} lies behind exactly one way`);
    assert.equal(wayForZone(zone), guards[0]);
  }
}
for (const id of Object.keys(plannedZones)) {
  const guards = worldWays.filter((w) => (w.opens.plannedZones as readonly string[]).includes(id));
  assert.equal(guards.length, 1, `planned ${id} lies behind exactly one way`);
}
for (const zone of alwaysOpen.zones) assert.ok(allZones.includes(zone), `always-open ${zone}`);
for (const s of alwaysOpen.strips) {
  assert.ok(
    allZones.includes(s.zone) && !isAlwaysOpen(s.zone),
    `${s.zone}'s strip is in gated ground`,
  );
  assert.ok(onOpenStrip(s.zone, [s.rect[0], s.rect[1]]) && !onOpenStrip(s.zone, [160, 300]));
}
for (const [a, b] of travelLinks) {
  const guards = worldWays.filter((w) =>
    w.opens.lines.some(([x, y]) => (x === a && y === b) || (x === b && y === a)),
  );
  assert.equal(guards.length, 1, `the line ${a}-${b} is run by exactly one way`);
  assert.equal(wayForLine(a, b), guards[0]);
  assert.equal(wayForLine(b, a), guards[0], 'either direction');
}
for (const w of worldWays.filter((x) => x.kind === 'line')) {
  assert.equal(w.opens.lines.length, 1, `${w.id} runs one line`);
}
for (const w of worldWays.filter((x) => x.kind === 'area')) {
  assert.equal(w.opens.lines.length, 0, `${w.id} is walked, not ridden`);
  assert.ok(w.opens.zones.length > 0, `${w.id} opens ground`);
}
for (const stop of alwaysOpen.stops) {
  assert.ok(isAlwaysOpen(travelPoints[stop].zone), `${stop} stands in the heart`);
}
console.log(
  'Ways: every gated zone and every journey line has exactly one way; the heart has none.',
);

// --- each way stands on the near side, and its line reaches what it opens ---
/** Zones walkable once a way's prerequisites are open (before the way itself). */
const nearSide = (w: WorldWay) => new Set<string>(openZones(prerequisites(w.id)));
for (const w of worldWays) {
  const near = nearSide(w);
  for (const b of w.barriers) {
    assert.ok(
      near.has(b.zone) || (b.at !== undefined && onOpenStrip(b.zone, b.at)),
      `${w.id} stands in ${b.zone}, reachable before it opens`,
    );
    if (b.stop) assert.ok(near.has(travelPoints[b.stop].zone), `${w.id}'s stop is reachable`);
    for (const port of b.ports ?? []) {
      const [a, c] = port.split('|');
      const behind = zonesBehind(w.id);
      assert.ok(
        (near.has(a) && behind.includes(c)) || (near.has(c) && behind.includes(a)),
        `${w.id}'s port ${port} joins its near side to what it opens`,
      );
    }
  }
  for (const [a, b] of w.opens.lines) {
    const za = travelPoints[a].zone,
      zb = travelPoints[b].zone;
    if (w.kind === 'line') {
      // one end on the near side, the other in what it opens
      assert.ok(
        (near.has(za) && w.opens.zones.includes(zb)) ||
          (near.has(zb) && w.opens.zones.includes(za)),
        `${w.id}'s line ${a}-${b} runs from the near side into what it opens`,
      );
    } else {
      // a shortcut joins places already reached on foot
      assert.ok(near.has(za) && near.has(zb), `${w.id} joins places already reached`);
    }
  }
}
// with the road closed, a seam open today between the heart and a gated zone (or between
// two ways' ground) is either one of that way's ports or crossed by a barrier drawn in
// the gated zone itself (the Headland's wall with the stile)
const guardOf = (zone: string) => wayForZone(zone)?.id ?? null;
for (const [key, port] of Object.entries(zonePorts)) {
  if (!port.span || port.span[1] <= port.span[0]) continue;
  const [a, b] = key.split('|');
  const ga = guardOf(a),
    gb = guardOf(b);
  if (ga === gb) continue;
  // the far side is the way that is not the other's prerequisite
  const far = ga === null ? gb! : gb === null ? ga : prerequisites(gb).includes(ga) ? gb : ga;
  const w = wayById(far)!;
  const behind = zonesBehind(far);
  assert.ok(
    w.barriers.some(
      (x) =>
        (x.ports ?? []).includes(key) ||
        (behind.includes(x.zone) && x.at !== undefined && onOpenStrip(x.zone, x.at)),
    ),
    `the open seam ${key} into ${far}'s ground is closed by its barrier`,
  );
}
console.log('Ways: each stands on its near side; each seam into gated ground has its barrier.');

// --- the helpers ---
assert.deepEqual(new Set(openZones([])), new Set(alwaysOpen.zones), 'nothing open: the heart');
assert.deepEqual(
  new Set(openZones(wayIds)),
  new Set(allZones),
  'every way open: the whole world as today',
);
assert.ok(openZones(['ferry', 'future-way']).includes('cove'), 'unknown ids are ignored');
assert.deepEqual(openLines([]), [], 'no line runs with every way closed');
assert.equal(openLines(wayIds).length, travelLinks.length, 'every line runs with all open');
assert.deepEqual(openLines(['valley-train']), [['valley', 'steam']]);
assert.deepEqual(waysToReach(['garden', 'harbour', 'ridge']), [], 'the heart needs nothing');
assert.deepEqual(waysToReach(['skyport']), ['valley-train', 'maglev'], 'the route to Neon');
assert.deepEqual(waysToReach(['caldera', 'cove']), [
  'valley-train',
  'ferry',
  'desert-line',
  'chasm-bridge',
]);
assert.deepEqual(waysToReach(['lumen']), ['valley-train', 'maglev', 'elevator', 'shuttle']);
assert.deepEqual(waysToReach(['retired-zone']), [], 'unknown zones are ignored');
assert.deepEqual(zonesBehind('valley-train'), ['junction', 'canal', 'hill', 'terminus']);
assert.deepEqual(zonesBehind('nope'), []);
console.log('Ways: openZones, openLines, waysToReach and zonesBehind agree with the catalogue.');

// --- the words: the companion is cosy and never shaming ---
const never = /\b(missed|miss|lost|lose|hurry|failed|only|left|streak|late|must)\b/i;
for (const w of worldWays) {
  for (const line of [w.companion.closed, w.companion.opened]) {
    assert.equal(line, line.toLowerCase(), `${w.id}: the companion speaks lowercase`);
    assert.ok(!never.test(line), `${w.id}: "${line}" never nags`);
    assert.ok(line.length <= 100, `${w.id}: "${line}" is short`);
  }
  assert.equal(w.welcome, w.welcome.toUpperCase(), `${w.id}: the welcome row is uppercase`);
  assert.ok(w.name && w.closed && w.open && w.pictogram, `${w.id} is described`);
}
for (const w of roadWays) assert.ok(w.resident, `${w.id} has a resident who explains it`);
console.log('Ways: the companion lines are lowercase, short and never nag.');
