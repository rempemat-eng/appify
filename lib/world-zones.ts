import { gardenAnchors } from './garden-map';
import { regionTiles, regionWalk, tileOrigin, TILE, type TileId } from './region-walk';
import { regionLayout, zoneMaps } from './zone-maps';

export type WorldZoneId = TileId;
export type WorldEdge = 'north' | 'east' | 'south' | 'west';
export type WorldPoint = Readonly<{ x: number; y: number }>;
export type WorldAccess = Readonly<{ level: number; mountainLevel: number }>;
export type WorldExit = Readonly<{
  id: string;
  from: WorldZoneId;
  to: WorldZoneId;
  edge: WorldEdge;
  departure: WorldPoint;
  entry: WorldPoint;
}>;
// Strings deliberately retain unknown future zone ids in the save. Only the
// known, accessible projection below can become a renderer destination.
export type WorldProgress = { currentZone: string; visitedZones: string[] };
export const worldRegionIds = Object.keys(regionLayout).filter(
  (id): id is keyof typeof regionLayout => Object.hasOwn(regionLayout, id),
);
export const worldZoneIds: readonly WorldZoneId[] = [
  ...new Set(worldRegionIds.flatMap((region) => regionTiles(region).map((t) => t.id))),
];
export function isWorldZoneId(value: unknown): value is WorldZoneId {
  return typeof value === 'string' && (worldZoneIds as readonly string[]).includes(value);
}
export function freshWorldProgress(): WorldProgress {
  return { currentZone: 'garden', visitedZones: ['garden'] };
}
const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
export function restoreWorldProgress(value: unknown): WorldProgress {
  if (!isRecord(value)) return freshWorldProgress();
  const v = value;
  const currentZone = typeof v.currentZone === 'string' && v.currentZone ? v.currentZone : 'garden';
  const visited = Array.isArray(v.visitedZones)
    ? v.visitedZones.filter((id): id is string => typeof id === 'string' && id.length > 0)
    : [];
  return { currentZone, visitedZones: [...new Set(['garden', ...visited, currentZone])] };
}
export function canEnterWorldZone(id: unknown, access: WorldAccess): id is WorldZoneId {
  return (
    isWorldZoneId(id) &&
    (id !== 'ridge' ||
      (Number.isFinite(access.level) &&
        Number.isFinite(access.mountainLevel) &&
        access.mountainLevel > 0 &&
        access.level >= access.mountainLevel))
  );
}
export function currentWorldZone(progress: WorldProgress, access: WorldAccess): WorldZoneId {
  return canEnterWorldZone(progress.currentZone, access) ? progress.currentZone : 'garden';
}

const reverse: Record<WorldEdge, WorldEdge> = {
  north: 'south',
  east: 'west',
  south: 'north',
  west: 'east',
};
const standPoints = (from: WorldZoneId, to: WorldZoneId): WorldPoint[] =>
  from === 'garden'
    ? []
    : Object.entries(zoneMaps[from].stands)
        .filter(([name]) => name === to || name.startsWith(`${to}-`))
        .map(([, [x, y]]) => ({ x, y }));

/** Read explicit connection markers, layout and BOTH walk grids. Mere adjacency
 * is not an exit: e.g. station -> Lumen needs a shuttle, not a walk off the edge.
 * Entry coordinates are cell centres on the actual shared open boundary. */
function makeExits(): readonly WorldExit[] {
  const result: WorldExit[] = [];
  for (const region of worldRegionIds) {
    const tiles = regionTiles(region);
    const rows = regionWalk(region);
    for (const from of tiles)
      for (const to of tiles) {
        const dc = to.col - from.col,
          dr = to.row - from.row;
        if (Math.abs(dc) + Math.abs(dr) !== 1 || from.id >= to.id) continue;
        const markers = [...standPoints(from.id, to.id), ...standPoints(to.id, from.id)];
        if (!markers.length) continue;
        const edge: WorldEdge =
          dc === 1 ? 'east' : dc === -1 ? 'west' : dr === 1 ? 'south' : 'north';
        const horizontal = dc !== 0;
        const origin = tileOrigin(region, from),
          target = tileOrigin(region, to);
        const candidates: { departure: WorldPoint; entry: WorldPoint; tangent: number }[] = [];
        for (let t = TILE.cell / 2; t < (horizontal ? TILE.height : TILE.width); t += TILE.cell) {
          const departure = {
            x: horizontal ? (dc > 0 ? TILE.width - TILE.cell / 2 : TILE.cell / 2) : t,
            y: horizontal ? t : dr > 0 ? TILE.height - TILE.cell / 2 : TILE.cell / 2,
          };
          const entry = {
            x: horizontal ? (dc > 0 ? TILE.cell / 2 : TILE.width - TILE.cell / 2) : t,
            y: horizontal ? t : dr > 0 ? TILE.cell / 2 : TILE.height - TILE.cell / 2,
          };
          const open = (o: WorldPoint, p: WorldPoint) =>
            rows[Math.floor((o.y + p.y) / TILE.cell)]?.[Math.floor((o.x + p.x) / TILE.cell)] ===
            '.';
          if (open(origin, departure) && open(target, entry))
            candidates.push({ departure, entry, tangent: t });
        }
        const selected = new Set<number>();
        for (const marker of markers) {
          const tangent = horizontal ? marker.y : marker.x;
          const best = candidates.reduce<(typeof candidates)[number] | undefined>(
            (a, b) => (!a || Math.abs(b.tangent - tangent) < Math.abs(a.tangent - tangent) ? b : a),
            undefined,
          );
          if (!best || selected.has(best.tangent)) continue;
          selected.add(best.tangent);
          const id = `${from.id}:${to.id}:${best.tangent}`;
          result.push(
            {
              id: `${id}:out`,
              from: from.id,
              to: to.id,
              edge,
              departure: best.departure,
              entry: best.entry,
            },
            {
              id: `${id}:back`,
              from: to.id,
              to: from.id,
              edge: reverse[edge],
              departure: best.entry,
              entry: best.departure,
            },
          );
        }
      }
  }
  return result;
}
export const worldExits = makeExits();
export function exitsFromWorldZone(zone: WorldZoneId, access: WorldAccess): readonly WorldExit[] {
  return worldExits.filter((exit) => exit.from === zone && canEnterWorldZone(exit.to, access));
}
export function worldZoneStart(zone: WorldZoneId): WorldPoint {
  if (zone === 'garden') return { ...gardenAnchors.start };
  const [x, y] = Object.values(zoneMaps[zone].stands)[0];
  return { x, y };
}
export function enterWorldZone(progress: WorldProgress, to: WorldZoneId): WorldProgress {
  return { currentZone: to, visitedZones: [...new Set([...progress.visitedZones, to])] };
}

export type WorldWalk = Readonly<{ exit: WorldExit; owner: string }>;
/** Opaque object identity, not a reusable counter or client-supplied zone id.
 * Pending walks are never saved; reload, cancellation or supersession invalidates
 * the old callback. This controller never navigates, starts a nap or grants loot. */
export function createWorldWalkGuard() {
  let pending: WorldWalk | null = null;
  return {
    begin(from: WorldZoneId, exitId: string, owner: string, access: WorldAccess): WorldWalk | null {
      pending = null;
      const exit = exitsFromWorldZone(from, access).find((e) => e.id === exitId);
      if (!exit) return null;
      pending = Object.freeze({ exit, owner });
      return pending;
    },
    cancel() {
      pending = null;
    },
    finish(
      walk: WorldWalk,
      from: WorldZoneId,
      owner: string,
      access: WorldAccess,
    ): WorldZoneId | null {
      if (!pending || walk !== pending) return null;
      pending = null;
      return walk.owner === owner &&
        walk.exit.from === from &&
        canEnterWorldZone(walk.exit.to, access)
        ? walk.exit.to
        : null;
    },
  };
}
