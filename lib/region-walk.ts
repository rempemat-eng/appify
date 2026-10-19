import { GARDEN, gardenWalk } from '@/lib/garden-map';
import {
  ZONE,
  regionLayout,
  zoneDecks,
  zoneIds,
  zoneMaps,
  zonePorts,
  type ZoneId,
} from '@/lib/zone-maps';
import type { Point } from '@/lib/garden-path';

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

/**
 * A region's two walk levels (docs/vision/two-level-walk.md), or null when it has no
 * decks. The deck level is laid beside the ground level, `offset` region pixels to the
 * right, so one walk grid covers both and a point's level is which half it is in. The
 * stairs and ramps are `links` between a ground cell and a deck cell; lifts are links a
 * walk takes only when asked to (`lifts`), so an interrupted walk never rides one.
 * `heightAt` is how high the deck under a deck point is drawn.
 */
export function regionLevels(region: RegionId) {
  const b = regionBounds(region);
  const decked = regionTiles(region).flatMap((t) => {
    const deck = t.id === 'garden' ? undefined : zoneDecks[t.id];
    return deck ? [{ tile: t, deck }] : [];
  });
  if (decked.length === 0) return null;
  const ground = regionWalk(region);
  const upper = Array.from({ length: b.tileRows * ROWS }, () => Array(b.tileCols * COLS).fill('#'));
  const links: [Point, Point][] = [];
  const lifts: [Point, Point][] = [];
  const heights: { x: number; y: number; height: number }[] = [];
  for (const { tile, deck } of decked) {
    const o = tileOrigin(region, tile);
    const oc = o.x / TILE.cell;
    const or = o.y / TILE.cell;
    deck.walk.forEach((row, r) => {
      for (let c = 0; c < row.length && c < COLS; c++)
        if (row[c] === '.') upper[or + r][oc + c] = '.';
    });
    for (const c of deck.connectors) {
      const pair: [Point, Point] = [
        { x: o.x + c.bottom[0], y: o.y + c.bottom[1] },
        { x: b.width + o.x + c.top[0], y: o.y + c.top[1] },
      ];
      (c.kind === 'lift' ? lifts : links).push(pair);
    }
    heights.push({ x: o.x, y: o.y, height: deck.height });
  }
  const rows = ground.map((row, r) => row + upper[r].join(''));
  const heightAt = (p: Point) => {
    if (p.x < b.width) return 0;
    const x = p.x - b.width;
    const h = heights.find(
      (t) => x >= t.x && x < t.x + TILE.width && p.y >= t.y && p.y < t.y + TILE.height,
    );
    return h ? h.height : 0;
  };
  return { rows, offset: b.width, links, lifts, heightAt };
}

/** The tile under a point in region pixels, if any. */
export function tileAt(region: RegionId, x: number, y: number): RegionTile | undefined {
  const b = regionBounds(region);
  const col = Math.floor(x / TILE.width) + b.minCol;
  const row = Math.floor(y / TILE.height) + b.minRow;
  return regionTiles(region).find((t) => t.col === col && t.row === row);
}

/** How far (region pixels) the companion must be over a zone's edge before it counts as in
 *  the next zone, so walking along a border does not flick the name or the sound. */
export const ZONE_HYSTERESIS = 12;

/**
 * The zone a point is in, keeping the previous zone while the point is still within
 * `margin` pixels of it (docs/vision/home-hub.md: no ping-pong at an edge).
 */
export function tileWithHysteresis(
  region: RegionId,
  prev: TileId | undefined,
  x: number,
  y: number,
  margin = ZONE_HYSTERESIS,
): RegionTile | undefined {
  const tile = tileAt(region, x, y);
  if (!prev || tile?.id === prev) return tile;
  const old = regionTiles(region).find((t) => t.id === prev);
  if (!old) return tile;
  const o = tileOrigin(region, old);
  const inside =
    x >= o.x - margin &&
    x < o.x + TILE.width + margin &&
    y >= o.y - margin &&
    y < o.y + TILE.height + margin;
  return inside ? old : tile;
}

/** A rectangle in region pixels (the part of the region the camera shows). */
export type RegionRect = { x0: number; y0: number; x1: number; y1: number };

/** Every grid cell (zone-sized, inside the region or past its edge) that a rectangle
 *  grown by `margin` touches. */
export function cellsNear(region: RegionId, view: RegionRect, margin: number) {
  const b = regionBounds(region);
  const c0 = Math.floor((view.x0 - margin) / TILE.width) + b.minCol;
  const c1 = Math.floor((view.x1 + margin - 1) / TILE.width) + b.minCol;
  const r0 = Math.floor((view.y0 - margin) / TILE.height) + b.minRow;
  const r1 = Math.floor((view.y1 + margin - 1) / TILE.height) + b.minRow;
  const out: { col: number; row: number }[] = [];
  for (let col = c0; col <= c1; col++) for (let row = r0; row <= r1; row++) out.push({ col, row });
  return out;
}

/** How far past the camera's view a zone is mounted, and how far it may drift before it
 *  is let go (twice this). Small, because a phone sees most of one zone: the region's
 *  pictures are fetched ahead (zone-prefetch.ts) so a zone mounting at the margin draws at
 *  once, and the doubled margin stops a zone at the edge mounting and unmounting as the
 *  companion turns. */
export const MOUNT_MARGIN = 24;

/**
 * The zones to mount for a view: those within MOUNT_MARGIN of it, plus any already
 * mounted that are still within twice that. Mounting what the camera can see (not every
 * neighbour of the zone the companion stands in) keeps a phone's memory to a few zones
 * and stops a border from changing the mounted set as the companion steps over it.
 */
export function zonesToMount(
  region: RegionId,
  view: RegionRect,
  mounted: readonly TileId[] = [],
  margin = MOUNT_MARGIN,
): TileId[] {
  const tiles = regionTiles(region);
  const near = (m: number) =>
    new Set(cellsNear(region, view, m).map(({ col, row }) => `${col},${row}`));
  const close = near(margin);
  const kept = near(margin * 2);
  return tiles
    .filter(
      (t) =>
        close.has(`${t.col},${t.row}`) || (mounted.includes(t.id) && kept.has(`${t.col},${t.row}`)),
    )
    .map((t) => t.id);
}
