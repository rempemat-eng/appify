import { regionBounds, tileAt, type RegionId } from '@/lib/region-walk';
import { regionLayout } from '@/lib/zone-maps';

/**
 * Where the companion is in the walkable world, and which zones it has seen (living-
 * world plan W1; this takes over Codex's C19). Saved with the game; walking only moves
 * it and grants nothing. Pure, so it can be tested (lib/world-save.test.ts).
 */
export type WorldSpot = { region: RegionId; x: number; y: number; visited: string[] };

const isRegion = (value: unknown): value is RegionId =>
  typeof value === 'string' && Object.hasOwn(regionLayout, value);
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

/** Zone ids retired from the world, and the place that took each one's ground. */
const LEGACY_ZONES: Record<string, string> = { castle: 'headland' };

/** Shared by position and map acknowledgement migrations; unknown future IDs survive. */
export const restoreWorldZoneId = (id: string): string =>
  Object.hasOwn(LEGACY_ZONES, id) ? LEGACY_ZONES[id] : id;

/** A saved spot if it is whole and inside its region; otherwise none (start fresh). */
export function restoreWorld(value: unknown): WorldSpot | null {
  if (!isRecord(value)) return null;
  const v = value;
  if (!isRegion(v.region)) return null;
  const { x, y } = v;
  if (typeof x !== 'number' || typeof y !== 'number' || !Number.isFinite(x) || !Number.isFinite(y))
    return null;
  const b = regionBounds(v.region);
  if (x < 0 || y < 0 || x >= b.width || y >= b.height || !tileAt(v.region, x, y)) return null;
  const known = new Set<string>(Object.values(regionLayout).flatMap((r) => Object.keys(r)));
  // (18 Oct: the valley's castle corner became the Headland and the castle moved to the
  // Ember Lands as 'hearthold'; a saved visit to the old corner is a visit to the
  // Headland, never to the new castle. A spot there keeps its valley x/y, which now
  // falls in the Headland.)
  const visited = Array.isArray(v.visited)
    ? [
        ...new Set(
          v.visited
            .filter((z): z is string => typeof z === 'string')
            .map(restoreWorldZoneId)
            .filter((z) => known.has(z)),
        ),
      ]
    : [];
  return { region: v.region, x, y, visited };
}

/** The spot after a step: the new position, and the zone underfoot added to the visited. */
export function moveTo(spot: WorldSpot | null, region: RegionId, x: number, y: number): WorldSpot {
  const zone = tileAt(region, x, y)?.id;
  const visited = spot?.visited ?? [];
  return {
    region,
    x: Math.round(x),
    y: Math.round(y),
    visited: zone && !visited.includes(zone) ? [...visited, zone] : visited,
  };
}
