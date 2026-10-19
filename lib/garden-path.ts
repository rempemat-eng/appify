import { GARDEN, gardenAnchors, gardenWalk } from './garden-map';

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
    /** pairs of points a walk may step between directly, both ways: the stairs and
     *  ramps joining two walk levels laid side by side (docs/vision/two-level-walk.md) */
    links?: readonly (readonly [Point, Point])[];
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
    for (let r = 0; r < 24; r++)
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++)
          if (Math.max(Math.abs(dx), Math.abs(dy)) === r && walkable(cx + dx, cy + dy))
            return { cx: cx + dx, cy: cy + dy };
    return toCell(start);
  }

  const linkTo = new Map<number, number[]>();
  for (const [p, q] of opts.links ?? []) {
    const ca = toCell(p);
    const cb = toCell(q);
    const ka = ca.cy * cols + ca.cx;
    const kb = cb.cy * cols + cb.cx;
    linkTo.set(ka, [...(linkTo.get(ka) ?? []), kb]);
    linkTo.set(kb, [...(linkTo.get(kb) ?? []), ka]);
  }

  // Breadth-first search (8 directions, no corner cutting, and across any links),
  // thinned to turning points; both ends of a link are always kept.
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
      for (const k of linkTo.get(key(x, y)) ?? []) {
        const nx = k % cols;
        const ny = Math.floor(k / cols);
        if (!walkable(nx, ny) || prev.has(k)) continue;
        prev.set(k, key(x, y));
        queue.push([nx, ny]);
      }
    }
    if (!prev.has(key(z.cx, z.cy))) return [];
    const cells: [number, number][] = [];
    for (let k = key(z.cx, z.cy); k !== -1; k = prev.get(k)!)
      cells.unshift([k % cols, Math.floor(k / cols)]);
    const out: Point[] = [];
    const jump = (i: number) =>
      i > 0 &&
      i < cells.length &&
      (Math.abs(cells[i][0] - cells[i - 1][0]) > 1 || Math.abs(cells[i][1] - cells[i - 1][1]) > 1);
    for (let i = 1; i < cells.length; i++) {
      const last = i === cells.length - 1;
      const turn =
        !last &&
        (cells[i + 1][0] - cells[i][0] !== cells[i][0] - cells[i - 1][0] ||
          cells[i + 1][1] - cells[i][1] !== cells[i][1] - cells[i - 1][1]);
      if (last || turn || jump(i) || jump(i + 1)) out.push(toPoint(cells[i][0], cells[i][1]));
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
export const GARDEN_START: Point = gardenAnchors.start;
// The map describes feet, but the companion is 32 art pixels wide. Keep its
// centre and head inside the scene even when wandering or following an edge tap.
const gardenGrid = (rows: readonly string[]) =>
  makeWalkGrid(rows, {
    cell: GARDEN.cell,
    width: GARDEN.width,
    start: GARDEN_START,
    bounds: { minX: 16, maxX: GARDEN.width - 16, minY: 48, maxY: GARDEN.fenceY - 4 },
  });
let garden = gardenGrid(gardenWalk);
/** The garden's walk with keepsakes standing in it (lib/decor.ts); the garden's own rows
 *  when none do. Paths found after this go round them. */
export function setGardenWalk(rows: readonly string[]) {
  garden = gardenGrid(rows);
}
export const walkable = (cx: number, cy: number) => garden.walkable(cx, cy);
export const toCell = (p: Point) => garden.toCell(p);
export const toPoint = (cx: number, cy: number) => garden.toPoint(cx, cy);
export const nearestWalkable = (p: Point) => garden.nearestWalkable(p);
export const findPath = (from: Point, to: Point) => garden.findPath(from, to);
export const randomSpot = (near: Point, radius: number, random?: () => number) =>
  garden.randomSpot(near, radius, random);

// ---- ways out of the home garden ---------------------------------------------
// Every exit is a break in the garden's frame with a way through it
// (docs/vision/world-rules.md, check 7): the gate in the south fence, the ridge trail
// leaving the clearing's top edge, and the open meadow edges east and west.
export type GardenExit = 'gate' | 'trail' | 'west' | 'east';
/** Where the companion stands to go in at the hut's door (garden pixels). */
export const HUT_DOOR: Point = { x: 68, y: 132 };
/** Where the ridge trail leaves the top of the clearing, and the gate's opening. */
export const TRAIL_X = 204;
export const GATE_SPAN = { x0: 140, x1: 180 } as const;

/** The exit a tap (or a held key) asks for when it points past the garden's edge, if any. */
export function gardenExitToward(p: Point): GardenExit | null {
  if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) return null;
  if (p.y >= GARDEN.fenceY - 2 && p.x >= GATE_SPAN.x0 && p.x <= GATE_SPAN.x1) return 'gate';
  if (p.y <= 44 && Math.abs(p.x - TRAIL_X) <= 24) return 'trail';
  if (p.y > 48 && p.y < GARDEN.fenceY - 4) {
    if (p.x <= 14) return 'west';
    if (p.x >= GARDEN.width - 14) return 'east';
  }
  return null;
}

/** Whether the companion stands at that exit, ready to walk on out. */
export function atGardenExit(exit: GardenExit, p: Point): boolean {
  if (exit === 'gate')
    return p.y >= GARDEN.fenceY - 18 && p.x >= GATE_SPAN.x0 - 8 && p.x <= GATE_SPAN.x1 + 8;
  if (exit === 'trail') return p.y <= 60 && Math.abs(p.x - TRAIL_X) <= 28;
  if (exit === 'west') return p.x <= 24;
  return p.x >= GARDEN.width - 24;
}
