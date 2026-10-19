import { deckAt, regionBounds, tileAt, type RegionId } from '@/lib/region-walk';
import { regionLayout } from '@/lib/zone-maps';
import { LAYOUT_VERSION, carryForward } from '@/lib/world-layouts';

/**
 * Where the companion is in the walkable world, and which zones it has seen (living-
 * world plan W1; this takes over Codex's C19). Saved with the game; walking only moves
 * it and grants nothing. Pure, so it can be tested (lib/world-save.test.ts).
 */
export type WorldSpot = {
  region: RegionId;
  x: number;
  y: number;
  visited: string[];
  /** on a deck above x/y (docs/vision/two-level-walk.md); absent on the ground, as every
   *  spot saved before decks is */
  level?: 1;
  /** the shape of the world it was saved in (lib/world-layouts.ts) */
  layout?: number;
};

const isRegion = (value: unknown): value is RegionId =>
  typeof value === 'string' && Object.hasOwn(regionLayout, value);
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

/** Zone ids retired from the world, and the place that took each one's ground. */
const LEGACY_ZONES: Record<string, string> = { castle: 'headland' };

/** A saved spot if it is whole and inside its region; otherwise none (start fresh). */
export function restoreWorld(value: unknown): WorldSpot | null {
  if (!isRecord(value)) return null;
  const v = value;
  if (typeof v.region !== 'string') return null;
  if (
    typeof v.x !== 'number' ||
    typeof v.y !== 'number' ||
    !Number.isFinite(v.x) ||
    !Number.isFinite(v.y)
  )
    return null;
  // a spot saved in an earlier shape of the world: the same place in its zone, today
  const version = typeof v.layout === 'number' ? v.layout : 1;
  const here =
    version === LAYOUT_VERSION
      ? isRegion(v.region)
        ? { region: v.region, x: v.x, y: v.y }
        : null
      : carryForward(version, v.region, v.x, v.y);
  if (!here) return null;
  const { region, x, y } = here;
  const b = regionBounds(region);
  if (x < 0 || y < 0 || x >= b.width || y >= b.height || !tileAt(region, x, y)) return null;
  const known = new Set<string>(Object.values(regionLayout).flatMap((r) => Object.keys(r)));
  // (18 Oct: the valley's castle corner became the Headland and the castle moved to the
  // Ember Lands as 'hearthold'; a saved visit to the old corner is a visit to the
  // Headland, never to the new castle. A spot there keeps its valley x/y, which now
  // falls in the Headland.)
  const renamed = (z: string) => LEGACY_ZONES[z] ?? z;
  const visited = Array.isArray(v.visited)
    ? [
        ...new Set(
          v.visited
            .filter((z): z is string => typeof z === 'string')
            .map(renamed)
            .filter((z) => known.has(z)),
        ),
      ]
    : [];
  // (on a deck only while that deck is still there; otherwise on the ground below it)
  const level = v.level === 1 && version === LAYOUT_VERSION && deckAt(region, x, y) ? 1 : undefined;
  return { region, x, y, visited, layout: LAYOUT_VERSION, ...(level ? { level } : {}) };
}

/** The spot after a step: the new position, and the zone underfoot added to the visited. */
export function moveTo(
  spot: WorldSpot | null,
  region: RegionId,
  x: number,
  y: number,
  level?: 1,
): WorldSpot {
  const zone = tileAt(region, x, y)?.id;
  const visited = spot?.visited ?? [];
  return {
    region,
    x: Math.round(x),
    y: Math.round(y),
    visited: zone && !visited.includes(zone) ? [...visited, zone] : visited,
    layout: LAYOUT_VERSION,
    ...(level ? { level } : {}),
  };
}
