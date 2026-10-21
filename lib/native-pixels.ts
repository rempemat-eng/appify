/** Geometry for the default-off C34 device probe. All input positions are art pixels. */
import { WORLD_TILE } from './world-canvas';

export const TILE_SIZE = WORLD_TILE.size;
export const TILE_SCALE = WORLD_TILE.scale;
export const PROBE_COLS = 3;
export const PROBE_ROWS = 4;
const MOUNT_MARGIN = 24;

export type Point = { x: number; y: number };
export type ProbeTile = Point & { id: string; source: number };

/** Keep the probe on its fixture surface and put its origin on a physical pixel. */
export function clampCamera(
  point: Point,
  viewWidth: number,
  viewHeight: number,
  pixel: number,
  dpr: number,
): Point {
  const devicePerArt = pixel * dpr;
  const axis = (value: number, extent: number, viewport: number) => {
    // Floor the far bound before clamping: rounding it up can expose a strip
    // outside the surface when the viewport has a fractional art-pixel width.
    const maxDevice = Math.max(0, Math.floor((extent - viewport / pixel) * devicePerArt));
    return Math.min(maxDevice, Math.max(0, Math.round(value * devicePerArt))) / devicePerArt;
  };
  return {
    x: axis(point.x, PROBE_COLS * TILE_SIZE, viewWidth),
    y: axis(point.y, PROBE_ROWS * TILE_SIZE, viewHeight),
  };
}

/** Snap shared edges, rather than independent widths, to avoid cracks between tiles. */
export function tileLayout(tile: Point, camera: Point, pixel: number, dpr: number) {
  const edge = (value: number) => Math.round(value * pixel * dpr) / dpr;
  const left = edge(tile.x - camera.x);
  const top = edge(tile.y - camera.y);
  const right = edge(tile.x + TILE_SIZE - camera.x);
  const bottom = edge(tile.y + TILE_SIZE - camera.y);
  return { left, top, width: right - left, height: bottom - top };
}

/** One visible set for both renderers, including the planned 24-art-pixel mount margin. */
export function visibleTiles<T extends Point>(
  tiles: readonly T[],
  camera: Point,
  viewWidth: number,
  viewHeight: number,
  pixel: number,
): T[] {
  const left = camera.x - MOUNT_MARGIN;
  const top = camera.y - MOUNT_MARGIN;
  const right = camera.x + viewWidth / pixel + MOUNT_MARGIN;
  const bottom = camera.y + viewHeight / pixel + MOUNT_MARGIN;
  return tiles.filter(
    (tile) =>
      tile.x < right && tile.y < bottom && tile.x + TILE_SIZE > left && tile.y + TILE_SIZE > top,
  );
}

/** JS animation callback intervals only; this does not measure render time or GPU work. */
export function summarizeCadence(samples: readonly number[], budgetMs: number) {
  const ordered = samples
    .filter((sample) => Number.isFinite(sample) && sample > 0)
    .sort((a, b) => a - b);
  const percentile = (fraction: number) => ordered[Math.ceil(ordered.length * fraction) - 1] ?? 0;
  return {
    count: ordered.length,
    p50: percentile(0.5),
    p95: percentile(0.95),
    overBudget: ordered.filter((sample) => sample > budgetMs).length,
  };
}
