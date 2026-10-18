import { tileOrigin, regionTiles, type RegionId, type TileId } from '@/lib/region-walk';
import { zoneMaps, type ZoneId } from '@/lib/zone-maps';
import type { Point } from '@/lib/garden-path';

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
  hut: { region: 'valley', zone: 'garden', at: [68, 132] },
  inside: { region: 'home', zone: 'home', at: stand('home', 'door') },
} as const satisfies Record<string, PlaceDef>;

/** Where the walk out of the garden screen begins: past the gate, or up the ridge trail. */
export const exits = {
  gate: { region: 'valley', zone: 'town', at: stand('town', 'garden') },
  trail: { region: 'valley', zone: 'ridge', at: stand('ridge', 'garden') },
} as const satisfies Record<string, PlaceDef>;

/** A place's position in its region's pixels. */
export function regionPoint(place: PlaceDef): Point {
  const tile = regionTiles(place.region).find((t) => t.id === place.zone);
  if (!tile) throw new Error(`${place.zone} is not in ${place.region}`);
  const o = tileOrigin(place.region, tile);
  return { x: o.x + place.at[0], y: o.y + place.at[1] };
}

/** How close (art pixels) the companion must stand for a place's card to show. */
export const PLACE_RADIUS = 20;
