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
export const LAYOUT_VERSION = 3;

type Layout = Record<string, Record<string, readonly [number, number]>>;

/** Earlier layouts, by version. (A save with no version was made in layout 1.) */
const history: Record<number, Layout> = {
  // before the Frostline Highlands grew the valley north (18 Oct)
  2: {
    valley: {
      ridge: [0, -1],
      woodland: [-1, 0],
      garden: [0, 0],
      riverside: [1, 0],
      town: [0, 1],
      park: [1, 1],
      harbour: [0, 2],
      headland: [1, 2],
      halt: [-1, 1],
    },
    steam: { junction: [0, 0], canal: [0, 1] },
    west: {
      gulch: [0, 0],
      oasis: [-1, 0],
      scorch: [1, 0],
      hearthold: [1, -1],
      caldera: [1, -2],
      springs: [2, -2],
    },
    neon: { neon: [0, 0], skyport: [1, 0] },
    space: { station: [0, 0] },
    moon: { lumen: [0, 0] },
    home: { home: [0, 0] },
  },
  // before 18 Oct 19:07: the desert and the fire country were two regions
  1: {
    valley: {
      ridge: [0, -1],
      woodland: [-1, 0],
      garden: [0, 0],
      riverside: [1, 0],
      town: [0, 1],
      park: [1, 1],
      harbour: [0, 2],
      headland: [1, 2],
      halt: [-1, 1],
    },
    steam: { junction: [0, 0], canal: [0, 1] },
    west: { gulch: [0, 0], oasis: [-1, 0] },
    lava: { caldera: [0, -1], springs: [1, -1], hearthold: [0, 0], scorch: [0, 1] },
    neon: { neon: [0, 0], skyport: [1, 0] },
    space: { station: [0, 0] },
    moon: { lumen: [0, 0] },
    home: { home: [0, 0] },
  },
};

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
  const regions = Object.keys(regionLayout).filter((r): r is RegionId =>
    Object.hasOwn(regionLayout, r),
  );
  for (const region of regions) {
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
