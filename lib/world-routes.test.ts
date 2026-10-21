import assert from 'node:assert/strict';
import {
  ROUTE_CANVAS,
  ROUTE_GRID,
  ROUTE_VERTEX_EVERY,
  ROUTE_WIDTH,
  ROUTES_BETWEEN,
  ROUTES_HOME,
  TIER_CHANGE_RUN,
  routeFootprints,
  routeGates,
  routeLinks,
  routeStops,
  worldRouteMeets,
  worldRoutes,
  worldThresholds,
  type WorldRoute,
} from './world-routes';
import { worldWays } from './world-ways';

/**
 * The routes between the regions (lib/world-routes.ts, from scripts/art/world_routes.py,
 * lane G), checked against the world plan v5.3 (docs/vision/world-plan.md 5.2, 5.6, 6.1,
 * 10) and the brief (docs/vision/regions/routes-thresholds-edges.md). Data only: nothing
 * in the game reads it yet. Every rule is measured again here from the exported points,
 * not taken from the generator's own report.
 */

type Pt = readonly [number, number];
const dist = (a: Pt, b: Pt) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const heading = (a: Pt, b: Pt) => (Math.atan2(b[1] - a[1], b[0] - a[0]) * 180) / Math.PI;
const turn = (h0: number, h1: number) => ((((h1 - h0 + 180) % 360) + 360) % 360) - 180;
const pts = (r: WorldRoute): Pt[] => r.points.map((p) => [p[0], p[1]] as const);

function arclen(line: Pt[]): number[] {
  const s = [0];
  for (let i = 1; i < line.length; i++) s.push(s[i - 1] + dist(line[i - 1], line[i]));
  return s;
}

function resample(line: Pt[], step: number): Pt[] {
  const out: Pt[] = [line[0]];
  let carry = 0;
  for (let i = 1; i < line.length; i++) {
    const a = line[i - 1];
    const b = line[i];
    const seg = dist(a, b);
    let t = step - carry;
    while (t <= seg) {
      out.push([a[0] + ((b[0] - a[0]) * t) / seg, a[1] + ((b[1] - a[1]) * t) / seg]);
      t += step;
    }
    carry = seg - (t - step);
  }
  return out;
}

function nearest(line: Pt[], p: Pt): number {
  let best = Infinity;
  for (let i = 1; i < line.length; i++) {
    const a = line[i - 1];
    const b = line[i];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const l2 = dx * dx + dy * dy;
    const t = l2 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2)) : 0;
    best = Math.min(best, dist([a[0] + dx * t, a[1] + dy * t], p));
  }
  return best;
}

function ownerAt(x: number, y: number): string {
  for (const f of routeFootprints) {
    const [x0, y0, x1, y1] = f.box;
    if (x >= x0 && x < x1 && y >= y0 && y < y1) return f.owner;
  }
  return ROUTES_BETWEEN;
}

// --- the twenty routes of the brief, once each ---
const briefRoutes = [
  'Col Path',
  'High Fells',
  'Foothill Road',
  'Towpath',
  'Lull Road',
  'Coast Path',
  'Headland Lane',
  'Shell Bar',
  "Drover's Road",
  'Lode Track',
  'Canyon Road',
  'Forge Stair',
  'Ember Way',
  'Ash Coast',
  'Delta Road',
  'Harbour Bridge',
  'Old Bridges',
  'Quay Street',
  'Beacon Causeway',
  'Cape Road',
];
assert.deepEqual(
  worldRoutes.map((r) => r.name),
  briefRoutes,
  'the routes are the brief table, in order',
);
assert.equal(new Set(worldRoutes.map((r) => r.id)).size, worldRoutes.length, 'route ids unique');

for (const r of worldRoutes) {
  const line = pts(r);
  assert.ok(routeStops[r.from] && routeStops[r.to], `${r.name}: its ends are stops`);

  // --- on the grid, on the canvas, vertices close enough to follow the bends ---
  for (const [x, y, w, t] of r.points) {
    assert.ok(x % ROUTE_GRID === 0 && y % ROUTE_GRID === 0, `${r.name}: (${x}, ${y}) on the grid`);
    assert.ok(
      x >= 0 && y >= 0 && x <= ROUTE_CANVAS[0] && y <= ROUTE_CANVAS[1],
      `${r.name}: on the canvas`,
    );
    assert.ok(
      w >= ROUTE_WIDTH.min && w <= ROUTE_WIDTH.max && w % ROUTE_GRID === 0,
      `${r.name}: width ${w}`,
    );
    assert.ok(Number.isInteger(t) && t >= 0, `${r.name}: tier ${t}`);
  }
  for (let i = 1; i < line.length; i++) {
    assert.ok(dist(line[i - 1], line[i]) > 0, `${r.name}: no repeated vertex`);
    assert.ok(
      dist(line[i - 1], line[i]) <= ROUTE_VERTEX_EVERY + ROUTE_GRID,
      `${r.name}: vertices at most ${ROUTE_VERTEX_EVERY} px apart`,
    );
  }
  const s = arclen(line);
  const length = s[s.length - 1];
  assert.ok(Math.abs(length - r.length) <= 1, `${r.name}: length ${r.length} is the line's`);

  // --- the ends lie at their places ---
  assert.ok(dist(line[0], routeStops[r.from].at) <= 300, `${r.name}: starts at ${r.from}`);
  assert.ok(dist(line[line.length - 1], routeStops[r.to].at) <= 300, `${r.name}: ends at ${r.to}`);
  assert.ok(r.blockout.tierChanges >= 0, `${r.name}: the brief's tier count is kept`);

  // --- tiers: one step at a time, each at a declared change with room for its kind ---
  let prevEnd = -Infinity;
  for (const c of r.changes) {
    assert.equal(Math.abs(c.to - c.from), 1, `${r.name}: a change is one tier`);
    assert.equal(
      c.run,
      TIER_CHANGE_RUN[c.kind],
      `${r.name}: a ${c.kind} takes ${TIER_CHANGE_RUN[c.kind]} px`,
    );
    assert.ok(c.s - c.run / 2 >= prevEnd - 0.5, `${r.name}: changes do not overlap (s ${c.s})`);
    assert.ok(
      c.s - c.run / 2 >= -0.5 && c.s + c.run / 2 <= r.length + 0.5,
      `${r.name}: a ${c.kind} fits on the route`,
    );
    prevEnd = c.s + c.run / 2;
    for (const x of r.crossings.filter((k) => k.kind !== 'step'))
      assert.ok(
        Math.abs(c.s - x.s) >= (x.span + c.run) / 2 - 1,
        `${r.name}: no ${c.kind} on ${x.name}`,
      );
  }
  for (let i = 1; i < r.points.length; i++) {
    const a = r.points[i - 1][3];
    const b = r.points[i][3];
    assert.ok(Math.abs(a - b) <= 1, `${r.name}: tier steps one at a time`);
    if (a !== b) {
      const between = r.changes.filter((c) => c.s > s[i - 1] - 1 && c.s <= s[i] + 1);
      assert.ok(between.length > 0, `${r.name}: tier ${a} to ${b} at a declared change`);
    }
  }
  const first = r.changes[0];
  if (first)
    assert.equal(r.points[0][3], first.from, `${r.name}: starts at its first change's tier`);
  const last = r.changes[r.changes.length - 1];
  if (last)
    assert.equal(
      r.points[r.points.length - 1][3],
      last.to,
      `${r.name}: ends at its last change's tier`,
    );
  if (!first)
    assert.ok(
      r.points.every((p) => p[3] === r.points[0][3]),
      `${r.name}: level all along`,
    );

  // --- crossings lie on the line ---
  for (const x of r.crossings) {
    assert.ok(nearest(line, x.at) <= ROUTE_GRID, `${r.name}: ${x.name} on the line`);
    assert.ok(x.s >= 0 && x.s <= r.length, `${r.name}: ${x.name} within the route`);
  }

  // --- check 16: no straight run over 240 px (built straight things aside) ---
  if (r.kind !== 'bridge' && r.kind !== 'causeway' && r.length > 300) {
    const built = r.crossings.map((x) => [x.s - x.span / 2 - 64, x.s + x.span / 2 + 64]);
    const rs = resample(line, 8);
    const hs: (number | null)[] = [];
    for (let i = 0; i + 4 < rs.length; i++) {
      const si = i * 8 + 16;
      hs.push(built.some(([lo, hi]) => si >= lo && si <= hi) ? null : heading(rs[i], rs[i + 4]));
    }
    let best = 0;
    for (let i = 0; i < hs.length; ) {
      const h0 = hs[i];
      if (h0 === null) {
        i++;
        continue;
      }
      let j = i;
      for (;;) {
        const next = j + 1 < hs.length ? hs[j + 1] : null;
        if (next === null || Math.abs(turn(h0, next)) > 6) break;
        j++;
      }
      best = Math.max(best, (j - i + 4) * 8);
      i = j + 1;
    }
    assert.ok(best <= 240, `${r.name}: straight run of ${best} px (check 16: 240 at most)`);
  }

  // --- side paths leave and rejoin the road at a Y, and go round the far side ---
  for (const p of r.sidePaths) {
    assert.ok(nearest(line, p.leaves) <= ROUTE_GRID, `${r.name}: side path leaves the road`);
    assert.ok(nearest(line, p.rejoins) <= ROUTE_GRID, `${r.name}: side path rejoins the road`);
    assert.ok(
      dist(p.leaves, p.rejoins) >= 300,
      `${r.name}: side path round ${p.obstacle} is a real loop`,
    );
    const far = Math.max(...p.points.map((q) => nearest(line, q)));
    assert.ok(far > nearest(line, p.at), `${r.name}: side path passes beyond ${p.obstacle}`);
  }
  // --- secret pockets: dead-end paths of 80 px or more ---
  for (const p of r.pockets) {
    assert.ok(nearest(line, p.leaves) <= ROUTE_GRID, `${r.name}: pocket path leaves the route`);
    assert.ok(
      dist(p.points[p.points.length - 1], p.clearing) <= ROUTE_GRID,
      `${r.name}: reaches ${p.holds}`,
    );
    assert.ok(p.length >= 80, `${r.name}: the path to ${p.holds} is 80 px or more`);
  }
}

// --- every way on the road that stands on a route is on one, and each is a catalogue way ---
const labels = new Set(worldWays.map((w) => w.label));
const waysOnRoutes = new Set(
  worldRoutes.flatMap((r) => r.crossings.map((x) => x.way)).filter(Boolean),
);
for (const w of ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7']) {
  assert.ok(labels.has(w), `${w} is in the ways catalogue`);
  assert.ok(waysOnRoutes.has(w) || routeLinks.some((l) => l.way === w), `${w} stands on a route`);
}
const wayAt = (route: string, way: string) =>
  worldRoutes.find((r) => r.id === route)?.crossings.some((x) => x.way === way);
// plan 10: where each way stands
assert.ok(wayAt('headland-lane', 'W1'), 'W1 at the Headland stile');
assert.ok(wayAt('col-path', 'W2') && wayAt('high-fells', 'W2'), 'W2 at the lip and the east col');
assert.ok(
  wayAt('foothill-road', 'W3') && wayAt('towpath', 'W3') && wayAt('high-fells', 'W3'),
  'W3 on the three routes over the Cog',
);
assert.ok(wayAt('shell-bar', 'W4'), 'W4 on the Shell Bar');
assert.ok(
  wayAt('drovers-road', 'W5') && wayAt('ash-coast', 'W5'),
  "W5 at Drover's bridge and the Rift ferry",
);
assert.ok(
  wayAt('canyon-road', 'W6') && wayAt('ash-coast', 'W6'),
  'W6 at the chasm bridge and the crust causeway',
);
assert.ok(wayAt('lull-road', 'W7'), "W7 at Lullford's swing bridge");

// --- the fifteen thresholds, each on its route, its sides the owners of the land there ---
assert.equal(worldThresholds.length, 15, 'fifteen thresholds');
for (const t of worldThresholds) {
  const r = worldRoutes.find((x) => x.id === t.route);
  assert.ok(r, `${t.name}: on a route`);
  if (!r) continue;
  assert.ok(nearest(pts(r), t.at) <= ROUTE_GRID, `${t.name}: on its route`);
  assert.ok(dist(t.at, t.brief) <= 48, `${t.name}: within 48 px of the brief`);
  assert.equal(t.objectBy, ROUTES_BETWEEN, `${t.name}: the object is lane G's`);
  assert.equal(t.bandFade, 160, `${t.name}: the ambience fades over 160 px`);
}

// --- meeting cells: on an owner's line, and every change of owner along a route listed ---
for (const r of worldRoutes) {
  const line = pts(r);
  const rs = resample(line, 1);
  let changes = 0;
  for (let i = 1; i < rs.length; i++)
    if (ownerAt(rs[i - 1][0], rs[i - 1][1]) !== ownerAt(rs[i][0], rs[i][1])) changes++;
  const own = worldRouteMeets.filter((m) => m.route === r.id);
  assert.ok(own.length >= changes, `${r.name}: every change of owner has a meeting cell`);
  for (const m of own) {
    assert.deepEqual(
      m.cell,
      [m.at[0] / ROUTE_GRID, m.at[1] / ROUTE_GRID],
      `${r.name}: cell is at / 8`,
    );
    assert.ok(nearest(line, m.at) <= ROUTE_GRID, `${r.name}: meeting cell on the line`);
    const onEdge = routeFootprints.some((f) => {
      const [x0, y0, x1, y1] = f.box;
      const inside =
        m.at[0] >= x0 - 8 && m.at[0] <= x1 + 8 && m.at[1] >= y0 - 8 && m.at[1] <= y1 + 8;
      const near =
        Math.min(
          Math.abs(m.at[0] - x0),
          Math.abs(m.at[0] - x1),
          Math.abs(m.at[1] - y0),
          Math.abs(m.at[1] - y1),
        ) <= ROUTE_GRID;
      return inside && near;
    });
    assert.ok(onEdge, `${r.name}: meeting cell (${m.at[0]}, ${m.at[1]}) on a footprint's edge`);
    assert.ok(m.width >= ROUTE_WIDTH.min && m.width <= ROUTE_WIDTH.max, `${r.name}: meeting width`);
  }
}

// --- the gate check (plan 10): ways opened in order, nothing reached early ---
const steps = new Map(routeGates.map((g) => [g.open, new Set(g.reached)]));
const reachedAt = (stop: string) => routeGates.find((g) => g.reached.includes(stop))?.open;
assert.ok(steps.get('start')?.has(ROUTES_HOME), 'the valley at the start');
for (const stop of ['driftwood', 'fernhollow', 'lullford', 'gullwick', 'valley-halt'])
  assert.equal(reachedAt(stop), 'start', `${stop} from the start (plan 10)`);
assert.equal(reachedAt('headland-tip'), 'W1', 'the Headland behind W1');
assert.equal(reachedAt('frostline'), 'W2', 'the Frostline behind W2');
assert.equal(reachedAt('cogsworth'), 'W3', 'Cogsworth behind W3');
assert.equal(reachedAt('lagoon-landing'), 'W4', 'the isles behind W4');
for (const stop of ['dust-gulch', 'palm-spring', 'the-lode'])
  assert.equal(reachedAt(stop), 'W5', `${stop} behind W5`);
for (const stop of ['hearthold', 'cinderwick', 'ember-forge'])
  assert.equal(reachedAt(stop), 'W6', `${stop} behind W6`);
for (const stop of ['neon-market', 'launch-cape', 'beacon-isle'])
  assert.equal(reachedAt(stop), 'W7', `${stop} behind W7`);
for (let i = 1; i < routeGates.length; i++)
  for (const stop of routeGates[i - 1].reached)
    assert.ok(routeGates[i].reached.includes(stop), 'opening a way never closes a place');
assert.equal(
  routeGates[routeGates.length - 1].reached.length,
  Object.keys(routeStops).length,
  'with every way open, every stop is reached',
);

console.log(
  `world-routes: ${worldRoutes.length} routes, ${worldRoutes.reduce((a, r) => a + r.length, 0)} px, ` +
    `${worldThresholds.length} thresholds, ${worldRouteMeets.length} meeting cells, gate check in ${routeGates.length} steps: ok`,
);
