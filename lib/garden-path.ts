import { GARDEN, gardenWalk } from './garden-map';

// Pure pathfinding for the garden world (no React), so it can be unit tested.
export type Point = { x: number; y: number };
export const GARDEN_START: Point = { x: 96, y: 112 };

// ---- walk grid (4px cells, '#' = blocked) -----------------------------------
const rows = gardenWalk.length;
const cols = gardenWalk[0].length;
// The map describes feet, but the guardian can be nearly 40 native pixels wide.
// Keep its centre/head inside the scene even when wandering or following an edge tap.
export const walkable = (cx: number, cy: number) => {
  const x = cx * GARDEN.cell + GARDEN.cell / 2;
  const y = cy * GARDEN.cell + GARDEN.cell / 2;
  return (
    cy >= 0 &&
    cy < rows &&
    cx >= 0 &&
    cx < cols &&
    x >= 20 &&
    x <= GARDEN.width - 20 &&
    y >= 40 &&
    y <= 158 &&
    gardenWalk[cy][cx] === '.'
  );
};
export const toCell = (p: Point) => ({
  cx: Math.max(0, Math.min(cols - 1, Math.floor(p.x / GARDEN.cell))),
  cy: Math.max(0, Math.min(rows - 1, Math.floor(p.y / GARDEN.cell))),
});
export const toPoint = (cx: number, cy: number): Point => ({
  x: cx * GARDEN.cell + GARDEN.cell / 2,
  y: cy * GARDEN.cell + GARDEN.cell / 2,
});

// Nearest walkable cell to a point (the pet stops at the edge of the pond, etc.).
export function nearestWalkable(p: Point) {
  const { cx, cy } = toCell(p);
  for (let r = 0; r < 12; r++)
    for (let dy = -r; dy <= r; dy++)
      for (let dx = -r; dx <= r; dx++)
        if (Math.max(Math.abs(dx), Math.abs(dy)) === r && walkable(cx + dx, cy + dy))
          return { cx: cx + dx, cy: cy + dy };
  return toCell(GARDEN_START);
}

// Breadth-first search on the walk grid (8 directions), then thin to turning points.
export function findPath(from: Point, to: Point): Point[] {
  if (![from.x, from.y, to.x, to.y].every(Number.isFinite)) return [];
  const a = nearestWalkable(from);
  const b = nearestWalkable(to);
  const key = (x: number, y: number) => y * cols + x;
  const prev = new Map<number, number>();
  const queue: [number, number][] = [[a.cx, a.cy]];
  prev.set(key(a.cx, a.cy), -1);
  while (queue.length) {
    const [x, y] = queue.shift()!;
    if (x === b.cx && y === b.cy) break;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
      [1, 1],
      [1, -1],
      [-1, 1],
      [-1, -1],
    ]) {
      const nx = x + dx;
      const ny = y + dy;
      if (!walkable(nx, ny) || prev.has(key(nx, ny))) continue;
      if (dx && dy && (!walkable(x + dx, y) || !walkable(x, y + dy))) continue; // no corner cutting
      prev.set(key(nx, ny), key(x, y));
      queue.push([nx, ny]);
    }
  }
  if (!prev.has(key(b.cx, b.cy))) return [];
  const cells: [number, number][] = [];
  for (let k = key(b.cx, b.cy); k !== -1; k = prev.get(k)!)
    cells.unshift([k % cols, Math.floor(k / cols)]);
  // keep only cells where the direction changes, so the stroll looks smooth
  const out: Point[] = [];
  for (let i = 1; i < cells.length; i++) {
    const last = i === cells.length - 1;
    const turn =
      !last &&
      (cells[i + 1][0] - cells[i][0] !== cells[i][0] - cells[i - 1][0] ||
        cells[i + 1][1] - cells[i][1] !== cells[i][1] - cells[i - 1][1]);
    if (last || turn) out.push(toPoint(cells[i][0], cells[i][1]));
  }
  return out;
}

export function randomSpot(near: Point, radius: number, random = Math.random): Point {
  for (let i = 0; i < 30; i++) {
    const p = {
      x: near.x + (random() * 2 - 1) * radius,
      y: near.y + (random() * 2 - 1) * radius * 0.7,
    };
    const { cx, cy } = toCell(p);
    if (walkable(cx, cy)) return p;
  }
  return near;
}
