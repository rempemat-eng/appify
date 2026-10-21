import type { RegionId } from './region-walk';

type ImageMap = Readonly<Record<string, unknown>>;

/** Backdrops that are intentional when a camera can see beyond a region's land. */
export const BACKDROP_ALLOWED = [
  { region: 'space', edge: 'all', reason: 'The station is surrounded by open space.' },
  { region: 'moon', edge: 'top', reason: "The moon's sky is visible above its horizon." },
  { region: 'home', edge: 'all', reason: "The hut's room ends at its walls." },
] as const satisfies readonly {
  region: RegionId;
  edge: 'all' | 'top' | 'right' | 'bottom' | 'left';
  reason: string;
}[];

/** Whether cells beyond a region draw continuing land instead of its flat backdrop. */
export function regionOpensOut(region: RegionId, beyondByRegion: ImageMap, scenery: ImageMap) {
  return (
    region === 'valley' ||
    region === 'moon' ||
    Object.hasOwn(beyondByRegion, region) ||
    Object.keys(scenery).some((key) => key.startsWith(`${region}:`))
  );
}

export type LandBox = { x0: number; x1: number; y0: number; y1: number };
export type LandBounds = { width: number; height: number };

/**
 * The walkable-land box plus a margin. `cell`, `bounds` and `pad` use the same unit, so
 * callers can ask for world pixels or already-scaled screen pixels.
 */
export function landBox(
  rows: readonly string[],
  cell: number,
  bounds: LandBounds,
  pad: number,
): LandBox {
  let x0 = Infinity;
  let x1 = -Infinity;
  let y0 = Infinity;
  let y1 = -Infinity;
  rows.forEach((row, r) => {
    const a = row.indexOf('.');
    if (a < 0) return;
    const b = row.lastIndexOf('.');
    x0 = Math.min(x0, a);
    x1 = Math.max(x1, b + 1);
    y0 = Math.min(y0, r);
    y1 = Math.max(y1, r + 1);
  });
  if (!Number.isFinite(x0)) return { x0: 0, x1: bounds.width, y0: 0, y1: bounds.height };
  return {
    x0: Math.max(0, x0 * cell - pad),
    x1: Math.min(bounds.width, x1 * cell + pad),
    y0: Math.max(0, y0 * cell - pad),
    y1: Math.min(bounds.height, y1 * cell + pad),
  };
}
