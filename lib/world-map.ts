import { regionTiles, tileAt, type RegionId, type TileId } from './region-walk';
import { regionLayout } from './zone-maps';
import { doors, PLACE_RADIUS, regionPoint, travelLinks, travelPoints } from './world-places';
import { restoreWorld, type WorldSpot } from './world-save';

/** C22: a schematic, not a navigator or an unlock/reward system. */
export type MapState = 'unseen' | 'visited' | 'here';
export type MapLocation = Pick<WorldSpot, 'region' | 'x' | 'y'>;
export type MapNode = {
  id: string;
  kind: 'region' | 'zone' | 'station';
  region: RegionId;
  zone?: TileId;
  /** Zone coordinates in the authored region grid; not screen pixels. */
  col?: number;
  row?: number;
  state: MapState;
  isNew: boolean;
};
export type MapLink = {
  from: TileId;
  to: TileId;
  kind: 'border' | 'line' | 'door';
};

const regions = Object.keys(regionLayout).filter((id): id is RegionId =>
  Object.hasOwn(regionLayout, id),
);
const knownZones = new Set<string>(regions.flatMap((r) => regionTiles(r).map((t) => t.id)));
const strings = (value: unknown): string[] =>
  Array.isArray(value)
    ? [...new Set(value.filter((v): v is string => typeof v === 'string' && v.length > 0))]
    : [];

/** Home is already known; a valid legacy position is known even if its list is missing. */
export function mapVisitedZones(world: WorldSpot | null): TileId[] {
  const spot = restoreWorld(world);
  const underfoot = spot && tileAt(spot.region, spot.x, spot.y)?.id;
  return [
    ...new Set(['garden', ...(spot?.visited ?? []), ...(underfoot ? [underfoot] : [])]),
  ].filter((id): id is TileId => knownZones.has(id));
}

/** Additive v1 migration: don't turn a veteran's old discoveries into a new backlog.
 * Unknown future string IDs survive round trips, but never appear in today's atlas. */
export function restoreMapSeen(value: unknown, world: WorldSpot | null): string[] {
  return Array.isArray(value) ? strings(value) : mapVisitedZones(world);
}

/** Acknowledge only the visited IDs captured when the map opened, not later visits. */
export function acknowledgeMapSeen(
  previous: readonly string[],
  captured: readonly string[],
  world: WorldSpot | null,
): string[] {
  const visited = new Set<string>(mapVisitedZones(world));
  return [...new Set([...previous, ...captured.filter((id) => visited.has(id))])];
}

/** Authored topology only. Border edges do not certify passability; the existing walk
 * grid and travel rules remain authoritative. The hut is joined by its door, not rail. */
function atlasLinks(): MapLink[] {
  const links: MapLink[] = [];
  for (const region of regions) {
    const tiles = regionTiles(region);
    for (let i = 0; i < tiles.length; i++)
      for (let j = i + 1; j < tiles.length; j++) {
        const a = tiles[i],
          b = tiles[j];
        if (Math.abs(a.col - b.col) + Math.abs(a.row - b.row) === 1)
          links.push({ from: a.id, to: b.id, kind: 'border' });
      }
  }
  for (const [a, b] of travelLinks) {
    const from = travelPoints[a],
      to = travelPoints[b];
    if (from && to) links.push({ from: from.zone, to: to.zone, kind: 'line' });
  }
  links.push({ from: doors.hut.zone, to: doors.inside.zone, kind: 'door' });
  return links;
}

/** Pass current='garden' on Home: the saved world spot is a resume location, not the
 * active screen. World can pass its live position before a settled position is saved.
 * An invalid explicit location has no 'here'; it never silently points somewhere else. */
export function buildWorldMap(input: {
  world: WorldSpot | null;
  mapSeen: readonly string[];
  current?: MapLocation | 'garden';
}) {
  const saved = restoreWorld(input.world);
  const current =
    input.current === 'garden'
      ? { region: 'valley' as const, ...regionPoint(doors.hut) }
      : (input.current ?? saved ?? { region: 'valley' as const, ...regionPoint(doors.hut) });
  const location = restoreWorld({ ...current, visited: [] });
  const here = location && tileAt(location.region, location.x, location.y)?.id;
  const visited = new Set<string>(mapVisitedZones(saved));
  // The live position is visible, without recording it in exploration history.
  if (here) visited.add(here);
  const seen = new Set(input.mapSeen);
  const state = (zone: TileId): MapState =>
    here === zone ? 'here' : visited.has(zone) ? 'visited' : 'unseen';
  const fresh = (zone: TileId) => visited.has(zone) && !seen.has(zone);
  const nodes: MapNode[] = [];
  for (const region of regions) {
    const tiles = regionTiles(region);
    nodes.push({
      id: `region:${region}`,
      kind: 'region',
      region,
      state:
        location?.region === region
          ? 'here'
          : tiles.some((t) => visited.has(t.id))
            ? 'visited'
            : 'unseen',
      isNew: tiles.some((t) => fresh(t.id)),
    });
    for (const tile of tiles)
      nodes.push({
        id: `zone:${tile.id}`,
        kind: 'zone',
        region,
        zone: tile.id,
        col: tile.col,
        row: tile.row,
        state: state(tile.id),
        isNew: fresh(tile.id),
      });
    const station = travelPoints[region];
    if (station) {
      const at = regionPoint(station);
      const atStation =
        location?.region === region &&
        Math.hypot(location.x - at.x, location.y - at.y) <= PLACE_RADIUS;
      nodes.push({
        id: `station:${region}`,
        kind: 'station',
        region,
        zone: station.zone,
        state: atStation ? 'here' : visited.has(station.zone) ? 'visited' : 'unseen',
        isNew: fresh(station.zone),
      });
    }
  }
  const links = atlasLinks();
  // One gentle suggestion, by schematic hops and stable authored order. No deadline,
  // completion percentage, automatic trip, new gate or permission to travel.
  let suggestion: TileId | null = null;
  const queue: TileId[] = here ? [here] : [];
  const reached = new Set(queue);
  for (let i = 0; i < queue.length; i++) {
    const zone = queue[i];
    if (!visited.has(zone)) {
      suggestion = zone;
      break;
    }
    for (const link of links) {
      const next = link.from === zone ? link.to : link.to === zone ? link.from : null;
      if (next && !reached.has(next)) {
        reached.add(next);
        queue.push(next);
      }
    }
  }
  return {
    nodes,
    links,
    suggestion,
    // Only saved discoveries can be acknowledged. A transient location does not
    // make an unrecorded visit permanent merely because a map was rendered.
    visitedSnapshot: mapVisitedZones(saved),
  };
}
