import { GARDEN, gardenWalk } from './garden-map';

// Pure pathfinding on a walk grid ('#' = blocked, '.' = walkable), no React, so
// it can be unit tested. One instance per map: the home garden and each world.
export type Point = { x: number; y: number };
export type WalkGrid = ReturnType<typeof makeWalkGrid>;

export function makeWalkGrid(
  walk: readonly string[],
  opts: {
    cell: number;
    width: number;
    start: Point;
    /** keep the companion's body inside the scene (feet-based grid) */
    bounds?: { minX: number; maxX: number; minY: number; maxY: number };
  },
) {
  const rows = walk.length;
  const cols = walk[0].length;
  const { cell, start } = opts;
  const b = opts.bounds ?? { minX: 0, maxX: opts.width, minY: 0, maxY: rows * cell };

  const walkable = (cx: number, cy: number) => {
    const x = cx * cell + cell / 2;
    const y = cy * cell + cell / 2;
    return (
      cy >= 0 &&
      cy < rows &&
      cx >= 0 &&
      cx < cols &&
      x >= b.minX &&
      x <= b.maxX &&
      y >= b.minY &&
      y <= b.maxY &&
      walk[cy][cx] === '.'
    );
  };
  const toCell = (p: Point) => ({
    cx: Math.max(0, Math.min(cols - 1, Math.floor(p.x / cell))),
    cy: Math.max(0, Math.min(rows - 1, Math.floor(p.y / cell))),
  });
  const toPoint = (cx: number, cy: number): Point => ({
    x: cx * cell + cell / 2,
    y: cy * cell + cell / 2,
  });

  // Nearest walkable cell to a point (the pet stops at the edge of the pond, etc.).
  function nearestWalkable(p: Point) {
    const { cx, cy } = toCell(p);
    for (let r = 0; r < 12; r++)
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++)
          if (Math.max(Math.abs(dx), Math.abs(dy)) === r && walkable(cx + dx, cy + dy))
            return { cx: cx + dx, cy: cy + dy };
    return toCell(start);
  }

  // Breadth-first search (8 directions, no corner cutting), thinned to turning points.
  function findPath(from: Point, to: Point): Point[] {
    if (![from.x, from.y, to.x, to.y].every(Number.isFinite)) return [];
    const a = nearestWalkable(from);
    const z = nearestWalkable(to);
    const key = (x: number, y: number) => y * cols + x;
    const prev = new Map<number, number>();
    const queue: [number, number][] = [[a.cx, a.cy]];
    prev.set(key(a.cx, a.cy), -1);
    for (let head = 0; head < queue.length; head++) {
      const [x, y] = queue[head];
      if (x === z.cx && y === z.cy) break;
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
        if (dx && dy && (!walkable(x + dx, y) || !walkable(x, y + dy))) continue;
        prev.set(key(nx, ny), key(x, y));
        queue.push([nx, ny]);
      }
    }
    if (!prev.has(key(z.cx, z.cy))) return [];
    const cells: [number, number][] = [];
    for (let k = key(z.cx, z.cy); k !== -1; k = prev.get(k)!)
      cells.unshift([k % cols, Math.floor(k / cols)]);
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

  function randomSpot(near: Point, radius: number, random = Math.random): Point {
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

  return { walkable, toCell, toPoint, nearestWalkable, findPath, randomSpot };
}

// ---- the home garden -------------------------------------------------------
export const GARDEN_START: Point = { x: 96, y: 112 };
// The map describes feet, but the guardian can be nearly 40 native pixels wide.
// Keep its centre/head inside the scene even when wandering or following an edge tap.
const garden = makeWalkGrid(gardenWalk, {
  cell: GARDEN.cell,
  width: GARDEN.width,
  start: GARDEN_START,
  bounds: { minX: 20, maxX: GARDEN.width - 20, minY: 40, maxY: GARDEN.fenceY - 4 },
});
export const { walkable, toCell, toPoint, nearestWalkable, findPath, randomSpot } = garden;
