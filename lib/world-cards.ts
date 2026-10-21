import { regionTiles, tileOrigin, type RegionId } from '@/lib/region-walk';
import { residentRoutes } from '@/lib/resident-routes';
import {
  PLACE_RADIUS,
  doors,
  keepsakeChest,
  missionPlaces,
  regionPoint,
  rings,
  stopsIn,
  travelBy,
  travelPoints,
  type MissionPlaceId,
  type StopId,
} from '@/lib/world-places';
import type { Point } from '@/lib/garden-path';

/**
 * What happens where the companion stands out in the world: a place's card (a mission's
 * start, the stall, the ring, a station, a resident's hello, the hut's doors). Shared by
 * the world screen (app/(tabs)/world.tsx) and the home hub (components/garden-world.tsx). Pure,
 * so it can be tested (lib/home-hub.test.ts).
 */
export type Card =
  | { kind: 'mission'; id: 'book' | 'park' | 'mountain' }
  | { kind: 'shop' | 'arena' | 'garden' }
  | { kind: 'travel'; stop: StopId }
  | { kind: 'hut' | 'inside' | 'chest' }
  | { kind: 'ring'; backdrop: string }
  | { kind: 'chat'; who: string };

export const placeIds: MissionPlaceId[] = ['book', 'park', 'mountain', 'shop', 'arena', 'garden'];

const placeNames: Record<MissionPlaceId, string> = {
  book: 'LIBRARY',
  park: 'PARK',
  mountain: 'MOUNTAIN CABIN',
  shop: "MOSS'S STALL",
  arena: 'SPARRING RING',
  garden: 'HOME GARDEN',
};

/** A place's pin in the world. */
export type PlaceMarker = { id: string; x: number; y: number; label: string; selected?: boolean };

/** The places to show by name in a region, so you can see where things are and walk there. */
export function placeMarkers(region: RegionId, card: Card | null): PlaceMarker[] {
  const out: PlaceMarker[] = [];
  const add = (id: string, at: Point, label: string, selected = false) =>
    out.push({ id, x: at.x, y: at.y, label, selected });
  for (const stop of stopsIn(region))
    add(
      `travel-${stop}`,
      regionPoint(travelPoints[stop]),
      travelBy[stop],
      card?.kind === 'travel' && card.stop === stop,
    );
  rings
    .filter((r) => r.region === region)
    .forEach((r, i) => add(`ring-${i}`, regionPoint(r), 'SPARRING RING', card?.kind === 'ring'));
  if (region === 'home') {
    add('inside', regionPoint(doors.inside), 'FRONT DOOR', card?.kind === 'inside');
    add('chest', regionPoint(keepsakeChest), 'KEEPSAKE CHEST', card?.kind === 'chest');
  }
  if (region === 'valley') {
    for (const id of placeIds) {
      const selected = card?.kind === 'mission' ? card.id === id : card?.kind === id;
      add(id, regionPoint(missionPlaces[id]), placeNames[id], selected);
    }
  }
  return out;
}

const near = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y) <= PLACE_RADIUS * 1.6;

/** What, if anything, happens where the companion stands (region pixels). */
export function cardAt(region: RegionId, at: Point): Card | null {
  if (region === 'home')
    return near(at, regionPoint(doors.inside))
      ? { kind: 'inside' }
      : near(at, regionPoint(keepsakeChest))
        ? { kind: 'chest' }
        : null;
  const stop = stopsIn(region).find((id) => near(at, regionPoint(travelPoints[id])));
  if (stop) return { kind: 'travel', stop };
  const ring = rings.find((r) => r.region === region && near(at, regionPoint(r)));
  if (ring) return { kind: 'ring', backdrop: ring.backdrop };
  // a resident on their route beside the companion says hello
  for (const [who, route] of Object.entries(residentRoutes)) {
    const tile = regionTiles(region).find((t) => t.id === route.zone);
    if (!tile) continue;
    const o = tileOrigin(region, tile);
    const ax = o.x + route.from[0];
    const ay = o.y + route.from[1];
    const bx = o.x + route.to[0];
    const by = o.y + route.to[1];
    const t = Math.max(
      0,
      Math.min(
        1,
        ((at.x - ax) * (bx - ax) + (at.y - ay) * (by - ay)) /
          Math.max(1, (bx - ax) ** 2 + (by - ay) ** 2),
      ),
    );
    if (Math.hypot(at.x - (ax + (bx - ax) * t), at.y - (ay + (by - ay) * t)) <= 18)
      return { kind: 'chat', who };
  }
  if (region !== 'valley') return null;
  if (near(at, regionPoint(doors.hut))) return { kind: 'hut' };
  for (const id of placeIds) {
    if (!near(at, regionPoint(missionPlaces[id]))) continue;
    if (id === 'shop' || id === 'arena' || id === 'garden') return { kind: id };
    return { kind: 'mission', id };
  }
  return null;
}
