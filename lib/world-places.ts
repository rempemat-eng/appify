import { tileOrigin, regionTiles, type RegionId, type TileId } from '@/lib/region-walk';
import { zoneMaps, type ZoneId } from '@/lib/zone-maps';
import { HUT_DOOR, type Point } from '@/lib/garden-path';

/**
 * The places in the walkable world where something happens (living-world plan W1/W2):
 * where each mission sets out from, the stall and the ring, the station in each region
 * the journeys leave from, and the doors between the garden and the hut. Places are
 * given in their zone's own pixels and converted to region pixels here. Pure data, so
 * it can be tested (lib/world-places.test.ts): every place is open, reachable ground.
 */

/** The mission places keep their ids from lib/mission-places.ts and missions. */
export type MissionPlaceId = 'book' | 'park' | 'mountain' | 'shop' | 'arena' | 'garden';

type PlaceDef = { region: RegionId; zone: TileId; at: readonly [number, number] };

const stand = (zone: ZoneId, name: string): readonly [number, number] => {
  const s = zoneMaps[zone].stands[name];
  if (!s) throw new Error(`no stand ${name} in ${zone}`);
  return s;
};

export const missionPlaces: Record<MissionPlaceId, PlaceDef> = {
  book: { region: 'valley', zone: 'town', at: stand('town', 'library') },
  park: { region: 'valley', zone: 'park', at: stand('park', 'bandstand') },
  mountain: { region: 'valley', zone: 'ridge', at: stand('ridge', 'cabin') },
  shop: { region: 'valley', zone: 'town', at: stand('town', 'stall') },
  arena: { region: 'valley', zone: 'town', at: stand('town', 'ring') },
  // in front of the hut, where the garden screen's companion lives
  garden: { region: 'valley', zone: 'garden', at: [160, 196] },
};

/** Where each region's journeys leave from and arrive (its station, platform or hatch). */
export const travelPoints: Partial<Record<RegionId, PlaceDef>> = {
  valley: { region: 'valley', zone: 'halt', at: stand('halt', 'platform') },
  steam: { region: 'steam', zone: 'junction', at: stand('junction', 'platform') },
  west: { region: 'west', zone: 'gulch', at: stand('gulch', 'platform') },
  lava: { region: 'lava', zone: 'caldera', at: stand('caldera', 'tunnel') },
  neon: { region: 'neon', zone: 'skyport', at: stand('skyport', 'platform') },
  space: { region: 'space', zone: 'station', at: stand('station', 'lift') },
  moon: { region: 'moon', zone: 'lumen', at: stand('lumen', 'shuttle') },
};

/** Sparring rings out in the regions: each opens the same ring screen as the town's. */
export const rings: PlaceDef[] = [
  { region: 'steam', zone: 'junction', at: stand('junction', 'ring') },
  { region: 'neon', zone: 'neon', at: stand('neon', 'court') },
  { region: 'lava', zone: 'caldera', at: stand('caldera', 'ring') },
  { region: 'moon', zone: 'lumen', at: stand('lumen', 'sparring') },
];

/**
 * The lines between regions (world-atlas.md, "How you reach it"): the valley train to
 * Cogsworth; from there the line west to Dust Gulch and the maglev to Neon Harbour; the
 * mine cart from the gulch to the caldera; the space elevator from Neon Harbour to
 * Halcyon, and Halcyon's shuttle to Lumen. A tree rooted at the valley.
 */
export const travelLinks: readonly (readonly [RegionId, RegionId])[] = [
  ['valley', 'steam'],
  ['steam', 'west'],
  ['west', 'lava'],
  ['steam', 'neon'],
  ['neon', 'space'],
  ['space', 'moon'],
];

/** What runs on each line: the steam train in the valley and out west, the maglev to the
 * city, the mine carts to the caldera, the elevator capsule up to Halcyon, the shuttle on
 * to Lumen. */
export function travelVehicle(
  a: RegionId,
  b: RegionId,
): 'train' | 'maglev' | 'carts' | 'capsule' | 'shuttle' {
  const pair = new Set([a, b]);
  if (pair.has('lava')) return 'carts';
  if (pair.has('moon')) return 'shuttle';
  if (pair.has('space')) return 'capsule';
  if (pair.has('neon')) return 'maglev';
  return 'train';
}

/** The stations a trip stops at from one region to another, the destination last
 * (the start left out); empty when there is no line. */
export function travelRoute(from: RegionId, to: RegionId): RegionId[] {
  if (from === to) return [];
  const prev = new Map<RegionId, RegionId>([[from, from]]);
  const queue: RegionId[] = [from];
  while (queue.length) {
    const here = queue.shift()!;
    for (const [a, b] of travelLinks) {
      const next = a === here ? b : b === here ? a : undefined;
      if (next && !prev.has(next)) {
        prev.set(next, here);
        queue.push(next);
      }
    }
  }
  if (!prev.has(to)) return [];
  const route: RegionId[] = [];
  for (let r = to; r !== from; r = prev.get(r)!) route.unshift(r);
  return route;
}

/** How each journey is made, for its name on the travel card. */
export const travelBy: Partial<Record<RegionId, string>> = {
  valley: 'THE VALLEY TRAIN',
  steam: 'THE COGSWORTH LINE',
  west: 'THE DESERT LINE',
  lava: 'THE MINE CART',
  neon: 'THE MAGLEV',
  space: 'THE SPACE ELEVATOR',
  moon: 'THE SHUTTLE',
};

/** The doors between the garden and the inside of the hut. */
export const doors = {
  hut: { region: 'valley', zone: 'garden', at: [HUT_DOOR.x, HUT_DOOR.y] },
  inside: { region: 'home', zone: 'home', at: stand('home', 'door') },
} as const satisfies Record<string, PlaceDef>;

/** The keepsake chest in the hut's bedroom, where decorating starts (lib/decor.ts). */
export const keepsakeChest: PlaceDef = { region: 'home', zone: 'home', at: stand('home', 'chest') };

/** Where the walk out of the garden screen leads: past the gate, up the ridge trail, or
 *  over the meadow's sides into the woodland and the riverside. */
export const exits = {
  gate: { region: 'valley', zone: 'town', at: stand('town', 'garden') },
  trail: { region: 'valley', zone: 'ridge', at: stand('ridge', 'garden') },
  west: { region: 'valley', zone: 'woodland', at: stand('woodland', 'garden') },
  east: { region: 'valley', zone: 'riverside', at: stand('riverside', 'garden-north') },
} as const satisfies Record<string, PlaceDef>;
export type ExitId = keyof typeof exits;

/** The home garden's walkable yard (its feet bounds in lib/garden-path.ts), in garden pixels. */
export const GARDEN_YARD = { minX: 16, maxX: 304, minY: 48, maxY: 524 } as const;

/** A point of the valley in the garden's own pixels when it is inside the garden's yard. */
export function inGardenYard(region: string, at: Point): Point | null {
  if (region !== 'valley') return null;
  const o = regionPoint({ region: 'valley', zone: 'garden', at: [0, 0] });
  const g = { x: at.x - o.x, y: at.y - o.y };
  const y = GARDEN_YARD;
  return g.x >= y.minX && g.x <= y.maxX && g.y >= y.minY && g.y <= y.maxY ? g : null;
}

const mid = (x: number, centre: number) => centre + Math.max(-6, Math.min(6, x - centre));

/** Walking out of the garden screen: start at the same spot in the valley's garden and
 *  walk on through the gap, a little past the border. */
export function exitWalk(exit: ExitId, gx: number, gy: number): { start: Point; goal: Point } {
  const at = (x: number, y: number) =>
    regionPoint({ region: 'valley', zone: 'garden', at: [x, y] });
  // through the gate and up the trail, keep to the middle of the gap
  const sx = exit === 'gate' ? mid(gx, 162) : exit === 'trail' ? mid(gx, 200) : gx;
  const goal =
    exit === 'gate'
      ? at(162, 576 + 30)
      : exit === 'trail'
        ? at(200, -40)
        : exit === 'west'
          ? at(-40, gy)
          : at(320 + 40, gy);
  return { start: at(sx, gy), goal };
}

/**
 * Where one region's edge walks on into another's (Matt, 18 Oct: from the desert on foot
 * into the fire country): Dust Gulch's track east leaves its east edge at the pass and
 * comes in at the Scorched Pass's west edge. Crossing is a walk, not a journey: the
 * scene fades and the companion walks on (app/world.tsx).
 */
export const regionPasses = [
  {
    a: { region: 'west', zone: 'gulch', at: stand('gulch', 'pass'), side: 'east' },
    b: { region: 'lava', zone: 'scorch', at: stand('scorch', 'gulch'), side: 'west' },
  },
] as const satisfies readonly {
  a: PlaceDef & { side: 'east' | 'west' };
  b: PlaceDef & { side: 'east' | 'west' };
}[];

/** The pass a point stands at the end of, if any: where it leads and which way to walk on. */
export function passAt(
  region: RegionId,
  at: Point,
): { region: RegionId; at: Point; goal: Point } | null {
  for (const { a, b } of regionPasses) {
    for (const [here, there] of [
      [a, b],
      [b, a],
    ] as const) {
      if (here.region !== region) continue;
      const p = regionPoint(here);
      // within a few steps of the edge, on the track
      if (Math.abs(at.x - p.x) <= 10 && Math.abs(at.y - p.y) <= 22) {
        const q = regionPoint(there);
        const inward = there.side === 'west' ? 36 : -36;
        return { region: there.region, at: q, goal: { x: q.x + inward, y: q.y } };
      }
    }
  }
  return null;
}

/** A place's position in its region's pixels. */
export function regionPoint(place: PlaceDef): Point {
  const tile = regionTiles(place.region).find((t) => t.id === place.zone);
  if (!tile) throw new Error(`${place.zone} is not in ${place.region}`);
  const o = tileOrigin(place.region, tile);
  return { x: o.x + place.at[0], y: o.y + place.at[1] };
}

/** How close (art pixels) the companion must stand for a place's card to show. */
export const PLACE_RADIUS = 20;
