import { TILE, regionTiles, tileOrigin, type RegionId } from '@/lib/region-walk';
import { regionLayout } from '@/lib/zone-maps';

/**
 * Where the zones stood in each earlier shape of the world, so a saved spot survives a
 * change to the map (Matt, 18 Oct 19:07: the connected world Codex drew, which joins
 * the desert to the fire country and grows the valley north into the Frostline). A
 * saved spot is read in the layout it was saved in: which zone, and where in that zone;
 * then placed at that zone's place in today's world. Pure, tested in
 * lib/world-save.test.ts.
 *
 * To change the layout: copy today's `regionLayout` here under the current version,
 * then raise LAYOUT_VERSION.
 */
export const LAYOUT_VERSION = 1;

type Layout = Record<string, Record<string, readonly [number, number]>>;

/** Earlier layouts, by version. (A save with no version was made in layout 1.) */
const history: Record<number, Layout> = {};

const layoutOf = (version: number): Layout | undefined =>
  version === LAYOUT_VERSION ? regionLayout : history[version];

/** The zone under a point of a region in a given layout, and the point in the zone. */
function zoneUnder(layout: Layout, region: string, x: number, y: number) {
  const cells = layout[region];
  if (!cells) return null;
  const all = Object.values(cells);
  const minCol = Math.min(...all.map(([c]) => c));
  const minRow = Math.min(...all.map(([, r]) => r));
  const col = Math.floor(x / TILE.width) + minCol;
  const row = Math.floor(y / TILE.height) + minRow;
  const zone = Object.keys(cells).find((z) => cells[z][0] === col && cells[z][1] === row);
  if (!zone) return null;
  return { zone, lx: x - (col - minCol) * TILE.width, ly: y - (row - minRow) * TILE.height };
}

/** Today's region and region pixels for a point in a zone, if the zone still exists. */
export function placeInZone(zone: string, lx: number, ly: number) {
  for (const region of Object.keys(regionLayout) as RegionId[]) {
    const tile = regionTiles(region).find((t) => t.id === zone);
    if (!tile) continue;
    const o = tileOrigin(region, tile);
    return { region, x: o.x + lx, y: o.y + ly };
  }
  return null;
}

/**
 * A spot saved in layout `version` (region, region pixels), in today's world; null when
 * that layout is unknown or the spot's zone is gone.
 */
export function carryForward(
  version: number,
  region: string,
  x: number,
  y: number,
): { region: RegionId; x: number; y: number } | null {
  const old = layoutOf(version);
  if (!old) return null;
  const at = zoneUnder(old, region, x, y);
  return at ? placeInZone(at.zone, at.lx, at.ly) : null;
}
