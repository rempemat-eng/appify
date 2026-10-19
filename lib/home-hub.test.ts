import assert from 'node:assert/strict';
import { GARDEN } from './garden-map';
import { GARDEN_START, HUT_DOOR, findPath } from './garden-path';
import {
  GATE_OUT,
  YARD_MARGIN,
  gardenOrigin,
  homeSide,
  hubCardAt,
  hubOpening,
  hubWalk,
  toGarden,
  toRegion,
  type HubSide,
} from './home-hub';
import {
  MOUNT_MARGIN,
  TILE,
  ZONE_HYSTERESIS,
  regionTiles,
  tileAt,
  tileOrigin,
  tileWithHysteresis,
  zonesToMount,
} from './region-walk';
import { GARDEN_YARD, exits, missionPlaces, regionPoint, travelPoints } from './world-places';
import { zoneMaps } from './zone-maps';

// The home hub (docs/vision/home-hub.md): the garden is a place in the valley on one
// screen. These check the pure handoff logic: the moved walk, home or out with
// hysteresis, which ways into the world the hub takes over, and the zones mounted.
let checks = 0;
const ok = (condition: boolean, message: string) => {
  assert.ok(condition, message);
  checks++;
};
const close = (a: { x: number; y: number }, b: { x: number; y: number }, d = 12) =>
  Math.hypot(a.x - b.x, a.y - b.y) <= d;

// ---- the garden's pixels run on into the valley's
ok(
  gardenOrigin.x % TILE.cell === 0 && gardenOrigin.y % TILE.cell === 0,
  'the garden lies on whole cells of the valley',
);
const p = { x: 123, y: -45 };
ok(close(toGarden(toRegion(p)), p, 0), 'garden and valley pixels convert both ways');

// ---- the valley's walk in garden pixels
const walk = hubWalk();
const inside = [HUT_DOOR, { x: 250, y: 400 }, { x: 60, y: 300 }];
for (const target of inside) {
  const hub = walk.findPath(GARDEN_START, target);
  const garden = findPath(GARDEN_START, target);
  ok(
    close(hub[hub.length - 1], garden[garden.length - 1], 6),
    `inside the garden the hub's walk ends where the garden's own does (${target.x},${target.y})`,
  );
}
// out through every way out of the yard, and on to a stand in each neighbouring zone
const ways = {
  gate: exits.gate,
  trail: exits.trail,
  west: exits.west,
  east: exits.east,
};
for (const [way, place] of Object.entries(ways)) {
  const target = toGarden(regionPoint(place));
  const path = walk.findPath(GARDEN_START, target);
  ok(path.length > 0, `${way}: the companion walks out of the garden on foot`);
  const end = path[path.length - 1];
  ok(close(end, target), `${way}: and arrives where the world screen used to open`);
  ok(homeSide('home', end) === 'out', `${way}: which is out of the yard`);
  const back = walk.findPath(end, GARDEN_START);
  ok(close(back[back.length - 1], GARDEN_START), `${way}: and walks back in`);
}
for (const tile of regionTiles('valley')) {
  if (tile.id === 'garden') continue;
  const o = tileOrigin('valley', tile);
  const [name, [x, y]] = Object.entries(zoneMaps[tile.id].stands)[0];
  const target = toGarden({ x: o.x + x, y: o.y + y });
  const path = walk.findPath(GARDEN_START, target);
  ok(
    path.length > 0 && close(path[path.length - 1], target),
    `${tile.id}/${name}: reachable from home without a screen change`,
  );
}
ok(close(GATE_OUT, toGarden(regionPoint(exits.gate)), 60), 'the gate leads into the town lane');
const cell = walk.toCell(GATE_OUT);
ok(walk.walkable(cell.cx, cell.cy), 'just past the gate is open ground');
ok(close(walk.toPoint(cell.cx, cell.cy), GATE_OUT, 4), 'cells convert in garden pixels');

// ---- home or out, with hysteresis at the yard's edge
const y = GARDEN_YARD;
ok(homeSide('home', GARDEN_START) === 'home', 'the start is home');
ok(homeSide('out', GARDEN_START) === 'home', 'deep in the yard is home from either side');
const justOut = { x: 160, y: y.maxY + YARD_MARGIN / 2 };
const justIn = { x: 160, y: y.maxY - YARD_MARGIN / 2 };
ok(homeSide('home', justOut) === 'home', 'a step over the edge is still home');
ok(homeSide('out', justIn) === 'out', 'a step back in from outside is still out');
ok(homeSide('home', { x: 160, y: y.maxY + YARD_MARGIN + 2 }) === 'out', 'well past it is out');
ok(homeSide('out', { x: 160, y: y.maxY - YARD_MARGIN - 2 }) === 'home', 'well inside is home');
// walking along the edge, wobbling a few pixels either side, never flips it
let side: HubSide = 'home';
let flips = 0;
for (let i = 0; i < 200; i++) {
  const next = homeSide(side, { x: y.minX + (i % 7) - 3, y: 100 + i });
  if (next !== side) flips++;
  side = next;
}
ok(flips === 0, 'wobbling along the west edge never flips home and out');
side = 'out';
flips = 0;
for (let i = 0; i < 200; i++) {
  const next = homeSide(side, { x: y.minX + (i % 7) - 3, y: 100 + i });
  if (next !== side) flips++;
  side = next;
}
ok(flips === 0, 'nor from outside');

// ---- the zone's name and the mounted zones, with hysteresis at a border
const garden = regionTiles('valley').find((t) => t.id === 'garden')!;
const g0 = tileOrigin('valley', garden);
const border = g0.x; // the woodland lies west of the garden
ok(tileAt('valley', border - 2, g0.y + 300)?.id === 'woodland', 'west of the garden is woodland');
ok(
  tileWithHysteresis('valley', 'garden', border - ZONE_HYSTERESIS / 2, g0.y + 300)?.id === 'garden',
  'a few steps over a border keep the zone',
);
ok(
  tileWithHysteresis('valley', 'garden', border - ZONE_HYSTERESIS - 2, g0.y + 300)?.id ===
    'woodland',
  'further over, the zone changes',
);
ok(
  tileWithHysteresis('valley', 'woodland', border + ZONE_HYSTERESIS / 2, g0.y + 300)?.id ===
    'woodland',
  'and back over the border keeps the new zone for a few steps',
);
const view = (x: number, yy: number) => ({ x0: x - 130, y0: yy - 230, x1: x + 130, y1: yy + 190 });
const mid = zonesToMount('valley', view(g0.x + 160, g0.y + 300));
ok(mid.length === 1 && mid[0] === 'garden', 'in the middle of the garden only the garden mounts');
const nearEdge = zonesToMount('valley', view(g0.x + 140, g0.y + 300));
ok(
  nearEdge.includes('garden') && nearEdge.includes('woodland'),
  'near the west edge the woodland mounts before it is seen',
);
ok(
  zonesToMount('valley', view(g0.x + 160 + MOUNT_MARGIN / 2, g0.y + 300), nearEdge).includes(
    'woodland',
  ),
  'stepping back from the margin keeps it mounted (no mount and unmount at the margin)',
);
ok(
  !zonesToMount('valley', view(g0.x + 290, g0.y + 300), nearEdge).includes('woodland'),
  'far away it is let go',
);
for (let x = g0.x + 20; x < g0.x + 300; x += 40) {
  const n = zonesToMount('valley', view(x, g0.y + 300)).length;
  ok(n <= 4, `a phone's view mounts at most a few zones (${n} at x ${x})`);
}

// ---- which ways into the world the hub takes over
const stall = toGarden(regionPoint(missionPlaces.shop));
ok(close(hubOpening({ place: 'shop' }, null)!, stall, 0), "the stall's link opens in the hub");
ok(hubOpening({ from: 'hut' }, null) === null, 'the hut keeps its door (the world screen)');
ok(
  hubOpening({ trip: { from: 'valley', to: 'steam' } }, null) === null,
  'a journey plays on the world screen',
);
ok(
  close(hubOpening({ station: 'valley' }, null)!, toGarden(regionPoint(travelPoints.valley)), 0),
  "the valley's own station opens in the hub",
);
ok(hubOpening({ station: 'moon' }, null) === null, 'another region opens on the world screen');
ok(
  close(hubOpening({}, { region: 'valley', x: 100, y: 200 })!, toGarden({ x: 100, y: 200 }), 0),
  'a saved spot in the valley resumes in the hub',
);
ok(hubOpening({}, { region: 'isles', x: 100, y: 200 }) === null, 'one on the isles does not');
ok(hubOpening({ from: 'gate' }, null) !== null, 'an old exit link lands in the hub');

// ---- the cards the hub shows
ok(hubCardAt(GARDEN_START) === null, 'at home there is no card (the garden is home already)');
ok(hubCardAt(HUT_DOOR) === null, 'nor at the hut door (the hut is tapped)');
ok(hubCardAt(stall)?.kind === 'shop', "at the stall, the stall's card");
ok(
  hubCardAt(toGarden(regionPoint(travelPoints.valley)))?.kind === 'travel',
  "at the halt, the station's card",
);
ok(GARDEN.height === TILE.height && GARDEN.width === TILE.width, 'the garden is one zone in size');

console.log(`${checks} home-hub checks passed`);
