import assert from 'node:assert/strict';
import { makeWalkGrid, type Point } from './garden-path';
import { gardenAnchors } from './garden-map';
import {
  regionBounds,
  regionLevels,
  regionTiles,
  regionWalk,
  tileAt,
  tileOrigin,
  TILE,
  zoneReach,
  zonesToMount,
  type RegionId,
} from './region-walk';
import { regionLayout, zoneMaps, zoneOverhead, zonePorts } from './zone-maps';
import { residentRoutes } from './resident-routes';
import { residentSprites } from './resident-sprites';

// The valley is walkable as one place: from the garden's start the companion can
// reach a stand in every zone of the region without any cut between zones.
const region = 'valley';
const rows = regionWalk(region);
const b = regionBounds(region);
assert.equal(rows.length * TILE.cell, b.height, 'one walk row per cell down the region');
assert.equal(rows[0].length * TILE.cell, b.width, 'one walk column per cell across the region');
const garden = regionTiles(region).find((t) => t.id === 'garden');
assert.ok(garden, 'the garden is part of the valley');
const g0 = tileOrigin(region, garden);
const start = { x: g0.x + gardenAnchors.start.x, y: g0.y + gardenAnchors.start.y };
const grid = makeWalkGrid(rows, { cell: TILE.cell, width: b.width, start });
let checks = 0;
for (const tile of regionTiles(region)) {
  if (tile.id === 'garden') continue;
  const o = tileOrigin(region, tile);
  for (const [name, [x, y]] of Object.entries(zoneMaps[tile.id].stands)) {
    const target = { x: o.x + x, y: o.y + y };
    const path = grid.findPath(start, target);
    assert.ok(path.length > 0, `${tile.id}/${name} is reachable on foot from the garden`);
    const end = path[path.length - 1];
    assert.ok(
      Math.hypot(end.x - target.x, end.y - target.y) < 12,
      `${tile.id}/${name}: the walk ends there`,
    );
    assert.equal(
      tileAt(region, target.x, target.y)?.id,
      tile.id,
      `${tile.id}/${name} lies in its own zone`,
    );
    checks++;
  }
}
console.log(`Region walk: ${checks} stands reachable from the garden across zone borders.`);

// Every other region is one walkable place too: from where its journey arrives (the
// first stand of its first zone, as the atlas places the companion) every stand in
// every zone is reachable without a cut, including across the new borders (the
// oasis, the canal, the springs, the Skyport).
let others = 0;
for (const r of ['steam', 'west', 'neon', 'space', 'moon', 'home'] as const) {
  const tiles = regionTiles(r);
  const bb = regionBounds(r);
  const first = tiles[0];
  assert.ok(first && first.id !== 'garden', `${r} starts in a drawn zone`);
  const fo = tileOrigin(r, first);
  const [sx, sy] = Object.values(zoneMaps[first.id].stands)[0];
  const from = { x: fo.x + sx, y: fo.y + sy };
  const g = makeWalkGrid(regionWalk(r), { cell: TILE.cell, width: bb.width, start: from });
  for (const tile of tiles) {
    if (tile.id === 'garden') continue;
    const o = tileOrigin(r, tile);
    for (const [name, [x, y]] of Object.entries(zoneMaps[tile.id].stands)) {
      const target = { x: o.x + x, y: o.y + y };
      if (Math.hypot(target.x - from.x, target.y - from.y) < TILE.cell) continue; // where it starts
      const path = g.findPath(from, target);
      assert.ok(path.length > 0, `${r}: ${tile.id}/${name} is reachable on foot`);
      const end = path[path.length - 1];
      assert.ok(
        Math.hypot(end.x - target.x, end.y - target.y) < 12,
        `${r}: ${tile.id}/${name}: the walk ends there`,
      );
      others++;
    }
  }
}
console.log(`Region walk: ${others} stands reachable across the other regions.`);

// Residents walk only on open ground and never behind a prop (they are drawn above
// the props), and each has its sprite.
let walked = 0;
for (const [rid, route] of Object.entries(residentRoutes)) {
  assert.ok(residentSprites[rid], `${rid} has a sprite`);
  const { w: RES_W, h: RES_H } = residentSprites[rid];
  assert.equal(residentSprites[rid].zone, route.zone, `${rid} is drawn for the zone it walks`);
  const m = zoneMaps[route.zone];
  const steps = Math.ceil(Math.hypot(route.to[0] - route.from[0], route.to[1] - route.from[1]) / 2);
  for (let i = 0; i <= steps; i++) {
    const x = route.from[0] + ((route.to[0] - route.from[0]) * i) / steps;
    const y = route.from[1] + ((route.to[1] - route.from[1]) * i) / steps;
    assert.equal(
      m.walk[Math.floor(y / TILE.cell)][Math.floor(x / TILE.cell)],
      '.',
      `${rid} walks on open ground at ${x},${y}`,
    );
    for (const [id, key, ox, oy, w, h] of m.objects) {
      if (zoneOverhead.includes(key)) continue;
      // residents are drawn above the props, which is right only where they stand in
      // front: overlapping a prop whose foot is lower would put them in front of it
      const overlaps = x - RES_W / 2 < ox + w && x + RES_W / 2 > ox && y - RES_H < oy + h && y > oy;
      assert.ok(!overlaps || y >= oy + h, `${rid} never walks behind ${id}`);
    }
    walked++;
  }
}
console.log(
  `Residents: ${Object.keys(residentRoutes).length} routes, ${walked} steps on open ground.`,
);

// Places meet only at their ports (Codex's connected-world contract, PR #23;
// scripts/art/frames.py). On every shared edge the walk crosses inside the declared
// span and nowhere else, so the drawn hedge, wall, tree belt or rock shoulder that
// closes the rest is really closed.
{
  let seams = 0;
  for (const [key, { span }] of Object.entries(zonePorts)) {
    const [a, c] = key.split('|');
    const reg = Object.keys(regionLayout)
      .filter((r): r is keyof typeof regionLayout => r in regionLayout)
      .find((r) => a in regionLayout[r] && c in regionLayout[r]);
    assert.ok(reg, `${key}: both zones are in one region`);
    const tiles = regionTiles(reg);
    const ta = tiles.find((t) => t.id === a);
    const tb = tiles.find((t) => t.id === c);
    assert.ok(ta && tb, `${key}: both zones are laid out`);
    const vertical = tb.col === ta.col + 1 && tb.row === ta.row;
    assert.ok(vertical || (tb.col === ta.col && tb.row === ta.row + 1), `${key}: the zones touch`);
    const g = regionWalk(reg);
    const oa = tileOrigin(reg, ta);
    const ob = tileOrigin(reg, tb);
    const n = (vertical ? TILE.height : TILE.width) / TILE.cell;
    let open = 0;
    for (let k = 0; k < n; k++) {
      const p = k * TILE.cell;
      const ra = vertical
        ? g[oa.y / TILE.cell + k][(oa.x + TILE.width) / TILE.cell - 1]
        : g[(oa.y + TILE.height) / TILE.cell - 1][oa.x / TILE.cell + k];
      const rb = vertical
        ? g[ob.y / TILE.cell + k][ob.x / TILE.cell]
        : g[ob.y / TILE.cell][ob.x / TILE.cell + k];
      const crosses = ra === '.' && rb === '.';
      if (crosses) open++;
      const inside = span !== null && p >= span[0] && p < span[1];
      if (!inside) assert.ok(!crosses, `${key}: no way across outside the port (at ${p} px)`);
    }
    if (span !== null) assert.ok(open > 0, `${key}: the port at ${span[0]}-${span[1]} px is open`);
    seams++;
  }
  assert.ok(seams >= 28, 'every shared edge has a port record');
}

// Two walk levels (docs/vision/two-level-walk.md): a deck laid beside the ground and
// joined by a stair link. A walk crosses only by the link, keeps both of its ends, and
// with no link the deck cannot be reached.
const isRegion = (k: string): k is RegionId => k in regionLayout;
{
  const ground = '.....#.....';
  const twoLevels = Array.from({ length: 5 }, () => ground);
  const stair: [Point, Point] = [
    { x: 4 * 4 + 2, y: 2 * 4 + 2 },
    { x: 6 * 4 + 2, y: 2 * 4 + 2 },
  ];
  const linked = makeWalkGrid(twoLevels, {
    cell: 4,
    width: 44,
    start: { x: 2, y: 2 },
    links: [stair],
  });
  const across = linked.findPath({ x: 2, y: 2 }, { x: 40, y: 18 });
  assert.ok(across.length > 0, 'the deck is reached by the stair');
  assert.ok(
    across.some((p) => p.x === stair[0].x && p.y === stair[0].y) &&
      across.some((p) => p.x === stair[1].x && p.y === stair[1].y),
    'both ends of the stair are kept in the path',
  );
  const unlinked = makeWalkGrid(twoLevels, { cell: 4, width: 44, start: { x: 2, y: 2 } });
  const end = unlinked.findPath({ x: 2, y: 2 }, { x: 40, y: 18 });
  const last = end[end.length - 1];
  assert.ok(!last || last.x < 20, 'without a stair the walk stays on its own level');
  for (const key of Object.keys(regionLayout)) {
    if (!isRegion(key)) continue;
    const levels = regionLevels(key);
    if (!levels) continue;
    assert.equal(
      levels.rows[0].length,
      regionWalk(key)[0].length * 2 + 1,
      `${key}: two levels side by side, a blocked column between them`,
    );
    // the levels meet only at their connectors: nothing walks across the seam beside them
    const seam = levels.offset / 4 - 1;
    assert.ok(
      levels.rows.every((row) => row[seam] === '#'),
      `${key}: the column between the levels is blocked`,
    );
    for (const [bottom, top] of [...levels.links, ...levels.lifts]) {
      assert.ok(
        bottom.x < levels.offset && top.x >= levels.offset,
        `${key}: connectors join the two levels`,
      );
    }
  }
  console.log(
    'Two levels: a deck is reached only by its stairs, and both ends of a stair are kept.',
  );
}

// A zone whose art reaches out of its rectangle (a tower whose body rises into the zone
// above) is mounted while that art is in view, even with its own rectangle out of view.
{
  let towers = 0;
  for (const key of Object.keys(regionLayout)) {
    if (!isRegion(key)) continue;
    for (const t of regionTiles(key)) {
      const r = zoneReach(t.id);
      if (!r || r.y0 > -80) continue;
      const o = tileOrigin(key, t);
      // a thin view across the top of the overhang only, well above the zone itself
      const view = { x0: o.x, x1: o.x + TILE.width, y0: o.y + r.y0, y1: o.y + r.y0 + 20 };
      assert.ok(
        zonesToMount(key, view).includes(t.id),
        `${key}: ${t.id} is mounted while its art reaching ${-r.y0} px above it is in view`,
      );
      towers++;
    }
  }
  console.log(`Mounting: ${towers} zones with art reaching far above them mount while it is seen.`);
}
