import { GARDEN_START, makeWalkGrid, type Point } from '@/lib/garden-path';
import { TILE, regionBounds, regionWalk } from '@/lib/region-walk';
import { cardAt, placeIds, type Card } from '@/lib/world-cards';
import {
  GARDEN_YARD,
  exitWalk,
  exits,
  missionPlaces,
  regionPoint,
  stopIds,
  travelPoints,
  type MissionPlaceId,
  type StopId,
} from '@/lib/world-places';

const placeIdOf = (id: string | undefined): MissionPlaceId | undefined =>
  placeIds.find((p) => p === id);
const stopIdOf = (id: string | undefined): StopId | undefined => stopIds.find((s) => s === id);

/**
 * The home hub (docs/vision/home-hub.md): the garden is a place in the valley, walked
 * and drawn on one screen. The garden's code keeps working in garden pixels; in the hub
 * those pixels simply run on past the garden's edges into the valley around it. This
 * module converts between the two, moves the valley's walk into garden pixels, and
 * decides which ways into the world the hub takes over. Pure, so it can be tested
 * (lib/home-hub.test.ts). Presentation only: nothing here grants, costs or saves.
 */
export const HUB_REGION = 'valley' as const;

/** The garden tile's top-left in the valley's pixels. */
export const gardenOrigin: Point = regionPoint({ region: HUB_REGION, zone: 'garden', at: [0, 0] });

/** A garden point in the valley's pixels. */
export const toRegion = (p: Point): Point => ({ x: p.x + gardenOrigin.x, y: p.y + gardenOrigin.y });
/** A valley point in the garden's pixels (outside the garden it runs on past its edges). */
export const toGarden = (p: Point): Point => ({ x: p.x - gardenOrigin.x, y: p.y - gardenOrigin.y });

/** The same interface as the garden's own walk (lib/garden-path.ts), over a grid. */
export type HomeWalk = {
  walkable: (cx: number, cy: number) => boolean;
  toCell: (p: Point) => { cx: number; cy: number };
  toPoint: (cx: number, cy: number) => Point;
  nearestWalkable: (p: Point) => { cx: number; cy: number };
  findPath: (from: Point, to: Point) => Point[];
  randomSpot: (near: Point, radius: number, random?: () => number) => Point;
};

/**
 * The whole valley's walk, in garden pixels and garden cells: inside the garden it is the
 * garden's own grid (lib/region-walk.ts lays it into the valley with the gate and the
 * trail open), and past its edges the companion walks on into the town, the ridge, the
 * woodland and the riverside. `rows` is the valley's walk with any keepsakes in it.
 */
export function hubWalk(rows: readonly string[] = regionWalk(HUB_REGION)): HomeWalk {
  const b = regionBounds(HUB_REGION);
  const grid = makeWalkGrid(rows, {
    cell: TILE.cell,
    width: b.width,
    start: toRegion(GARDEN_START),
  });
  // the garden's origin lies on whole cells (a zone is a whole number of cells)
  const ox = gardenOrigin.x / TILE.cell;
  const oy = gardenOrigin.y / TILE.cell;
  const local = (c: { cx: number; cy: number }) => ({ cx: c.cx - ox, cy: c.cy - oy });
  return {
    walkable: (cx, cy) => grid.walkable(cx + ox, cy + oy),
    toCell: (p) => local(grid.toCell(toRegion(p))),
    toPoint: (cx, cy) => toGarden(grid.toPoint(cx + ox, cy + oy)),
    nearestWalkable: (p) => local(grid.nearestWalkable(toRegion(p))),
    findPath: (from, to) => grid.findPath(toRegion(from), toRegion(to)).map(toGarden),
    randomSpot: (near, radius, random) => toGarden(grid.randomSpot(toRegion(near), radius, random)),
  };
}

/** Whether the companion is at home (in the garden's yard) or out in the valley. */
export type HubSide = 'home' | 'out';
/** How far past the yard's edge (garden pixels) the companion must go before it counts as
 *  out, and how far back in before it counts as home again. */
export const YARD_MARGIN = 12;

/**
 * Home or out, with hysteresis: it changes only once the companion is YARD_MARGIN past
 * the yard's edge, so walking along the edge (or a tap just over it) never flicks it.
 * Only presentation follows it (the idle stroll, the garden's pin); nothing navigates.
 */
export function homeSide(prev: HubSide, at: Point): HubSide {
  const y = GARDEN_YARD;
  const within = (m: number) =>
    at.x >= y.minX + m && at.x <= y.maxX - m && at.y >= y.minY + m && at.y <= y.maxY - m;
  return prev === 'home'
    ? within(-YARD_MARGIN)
      ? 'home'
      : 'out'
    : within(YARD_MARGIN)
      ? 'home'
      : 'out';
}

/** The card for where the companion stands in the hub (garden pixels): the valley's
 *  places, not the garden's own (its hut is tapped, and it is already home). */
export function hubCardAt(at: Point): Card | null {
  const card = cardAt(HUB_REGION, toRegion(at));
  return card && card.kind !== 'garden' && card.kind !== 'hut' ? card : null;
}

/** Walking on out through the gate (the ring's hotspot): just past it, in the town lane. */
export const GATE_OUT: Point = toGarden(exitWalk('gate', 162, 520).goal);

/** How the game asks to open the world (lib/ui.ts WorldLink), as far as the hub cares. */
export type HubLink = {
  from?: string;
  place?: string;
  station?: string;
  trip?: unknown;
};

/**
 * Where in the hub (garden pixels) a way into the world opens, when it opens in the
 * valley; null when it belongs to the world screen (the hut's inside, a journey, another
 * region). `saved` is where the companion last stood (lib/world-save.ts).
 */
export function hubOpening(
  link: HubLink,
  saved: { region: string; x: number; y: number } | null,
): Point | null {
  if (link.trip) return null;
  const place = placeIdOf(link.place);
  if (place) return toGarden(regionPoint(missionPlaces[place]));
  const station = stopIdOf(link.station);
  if (station) {
    const stop = travelPoints[station];
    return stop.region === HUB_REGION ? toGarden(regionPoint(stop)) : null;
  }
  if (link.from === 'hut') return null;
  const exit = (['gate', 'trail', 'west', 'east'] as const).find((e) => e === link.from);
  if (exit) return toGarden(regionPoint(exits[exit]));
  if (saved) return saved.region === HUB_REGION ? toGarden(saved) : null;
  return toGarden(regionPoint(exits.gate));
}
