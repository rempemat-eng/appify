import { GARDEN, gardenWalk } from '@/lib/garden-map';
import { ZONE, regionLayout, zoneIds, zoneMaps, zonePorts, type ZoneId } from '@/lib/zone-maps';

/**
 * One walk grid for a whole region (world-atlas.md, "Seamless travel"): each zone's
 * grid laid at its place on the region's grid, so a walk can cross from one zone into
 * the next with no cut. Presentation only: nothing here is saved. Pure, so it can be
 * tested.
 */
export type RegionId = keyof typeof regionLayout;
export type TileId = ZoneId | 'garden';
export type RegionTile = { id: TileId; col: number; row: number };

export const TILE = { width: ZONE.width, height: ZONE.height, cell: ZONE.cell } as const;
const COLS = TILE.width / TILE.cell;
const ROWS = TILE.height / TILE.cell;

// The garden's grid keeps the companion inside the fence and below the trees; for a
// walk on into the town the gate stands open, and into the ridge the trail does (cells in garden pixels: x from, x to, y from, y to).
const GARDEN_OPENINGS = [
  { x0: 144, x1: 176, y0: GARDEN.fenceY - 20, y1: GARDEN.height },
  // and the ridge trail runs on up through the treeline
  { x0: 198, x1: 214, y0: 0, y1: 48 },
];

// The garden meets its neighbours only at their ports (Codex's connected-world
// contract, scripts/art/frames.py): along its west and east edges the meadow is closed
// two cells deep except where the woodland lane and the riverside bank come through.
const GARDEN_EDGE = 2;
function gardenSpan(side: 'west' | 'east'): readonly [number, number] | null {
  const key = side === 'west' ? 'woodland|garden' : 'garden|riverside';
  return zonePorts[key]?.span ?? null;
}

function tileWalk(id: TileId): readonly string[] {
  if (id !== 'garden') return zoneMaps[id].walk;
  const west = gardenSpan('west');
  const east = gardenSpan('east');
  return gardenWalk.map((row, r) =>
    row
      .split('')
      .map((ch, c) => {
        const x = c * TILE.cell + TILE.cell / 2;
        const y = r * TILE.cell + TILE.cell / 2;
        const open = GARDEN_OPENINGS.some((o) => x >= o.x0 && x < o.x1 && y >= o.y0 && y < o.y1);
        if (open) return '.';
        const inSpan = (s: readonly [number, number] | null) => s !== null && y >= s[0] && y < s[1];
        if (c < GARDEN_EDGE && !inSpan(west)) return '#';
        if (c >= COLS - GARDEN_EDGE && !inSpan(east)) return '#';
        return ch;
      })
      .join(''),
  );
}

const isTileId = (id: string): id is TileId =>
  id === 'garden' || (zoneIds as readonly string[]).includes(id);

export function regionTiles(region: RegionId): RegionTile[] {
  const out: RegionTile[] = [];
  for (const [id, [col, row]] of Object.entries(regionLayout[region])) {
    if (isTileId(id)) out.push({ id, col, row });
  }
  return out;
}

/** The region's extent in tiles, so tile (minCol, minRow) sits at region pixel (0, 0). */
export function regionBounds(region: RegionId) {
  const tiles = regionTiles(region);
  const cols = tiles.map((t) => t.col);
  const rows = tiles.map((t) => t.row);
  const minCol = Math.min(...cols);
  const minRow = Math.min(...rows);
  const tileCols = Math.max(...cols) - minCol + 1;
  const tileRows = Math.max(...rows) - minRow + 1;
  return {
    minCol,
    minRow,
    tileCols,
    tileRows,
    width: tileCols * TILE.width,
    height: tileRows * TILE.height,
  };
}

/** Where a tile's top-left lies in region pixels. */
export function tileOrigin(region: RegionId, tile: RegionTile) {
  const b = regionBounds(region);
  return { x: (tile.col - b.minCol) * TILE.width, y: (tile.row - b.minRow) * TILE.height };
}

/** The region's combined walk rows: '#' wherever no zone lies. */
export function regionWalk(region: RegionId): string[] {
  const b = regionBounds(region);
  const grid = Array.from({ length: b.tileRows * ROWS }, () => Array(b.tileCols * COLS).fill('#'));
  for (const tile of regionTiles(region)) {
    const walk = tileWalk(tile.id);
    const oc = (tile.col - b.minCol) * COLS;
    const or = (tile.row - b.minRow) * ROWS;
    walk.forEach((row, r) => {
      for (let c = 0; c < row.length && c < COLS; c++) grid[or + r][oc + c] = row[c];
    });
  }
  return grid.map((row) => row.join(''));
}

/** The tile under a point in region pixels, if any. */
export function tileAt(region: RegionId, x: number, y: number): RegionTile | undefined {
  const b = regionBounds(region);
  const col = Math.floor(x / TILE.width) + b.minCol;
  const row = Math.floor(y / TILE.height) + b.minRow;
  return regionTiles(region).find((t) => t.col === col && t.row === row);
}
