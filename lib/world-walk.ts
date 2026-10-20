import { makeWalkGrid, type Point } from './garden-path';
import {
  tileRows,
  worldAreas,
  worldChunks,
  worldPortals,
  worldTiles,
  WORLD_FLOW,
  WORLD_TILE,
  type WorldArea,
  type WorldChunk,
  type WorldPlane,
} from './world-canvas';

/**
 * The world canvas, step 2 (docs/vision/region-canvas.md): walking and mounting on the
 * world tiles. A region is still addressed in its own pixels (region px, as saves, stands
 * and the screens hold them); its chunk's origin turns them into world px. Pure, so it can
 * be tested (lib/world-walk.test.ts). Used only when WORLD_CANVAS is on (lib/world-flag.ts).
 */

const S = WORLD_TILE.size;
const CELL = WORLD_TILE.cell;
const N = S / CELL;

/** A rectangle in region pixels. */
export type RegionBox = { x0: number; y0: number; x1: number; y1: number };

const chunks = new Map<string, WorldChunk>(worldChunks.map((c) => [c.id, c]));
/** The chunk a region is drawn in (today one per region). */
export function chunkFor(region: string): WorldChunk {
  const ch = chunks.get(region);
  if (!ch) throw new Error(`no chunk for ${region}`);
  return ch;
}

// ---- reading the tiles ---------------------------------------------------------------

const rowCache = new Map<string, string[]>();
function rowsOf(plane: WorldPlane, key: string): string[] | undefined {
  const id = `${plane}/${key}`;
  const hit = rowCache.get(id);
  if (hit) return hit;
  const t = worldTiles[plane][key];
  if (!t) return undefined;
  const rows = tileRows(t.walk);
  rowCache.set(id, rows);
  return rows;
}

/** A window of a region's walk rows: cells [c0, c1) x [r0, r1) of the region, '#' off its
 *  chunk. Built from the tiles' rows a run at a time. */
export function windowRows(
  region: string,
  c0: number,
  r0: number,
  c1: number,
  r1: number,
): string[] {
  const ch = chunkFor(region);
  const cols = ch.size[0] / CELL;
  const rows = ch.size[1] / CELL;
  const oc = ch.origin[0] / CELL;
  const or = ch.origin[1] / CELL;
  const out: string[] = [];
  for (let r = r0; r < r1; r++) {
    let line = '';
    let c = c0;
    while (c < c1) {
      if (r < 0 || r >= rows || c < 0 || c >= cols) {
        const end = c < 0 ? Math.min(c1, 0) : c1;
        line += '#'.repeat(end - c);
        c = end;
        continue;
      }
      const wc = oc + c;
      const wr = or + r;
      const tc = Math.floor(wc / N);
      const tr = Math.floor(wr / N);
      const lc = wc - tc * N;
      const take = Math.min(N - lc, c1 - c, cols - c);
      const tile = rowsOf(ch.plane, `${tc},${tr}`);
      line += tile ? tile[wr - tr * N].slice(lc, lc + take) : '#'.repeat(take);
      c += take;
    }
    out.push(line);
  }
  return out;
}

/** Whether one walk cell of a region (region cells) is open. */
export function cellOpen(region: string, cx: number, cy: number): boolean {
  const ch = chunkFor(region);
  if (cx < 0 || cy < 0 || cx * CELL >= ch.size[0] || cy * CELL >= ch.size[1]) return false;
  const wc = ch.origin[0] / CELL + cx;
  const wr = ch.origin[1] / CELL + cy;
  const tc = Math.floor(wc / N);
  const tr = Math.floor(wr / N);
  return rowsOf(ch.plane, `${tc},${tr}`)?.[wr - tr * N][wc - tc * N] === '.';
}

const regionRows = new Map<string, string[]>();
/** A region's whole walk, read from the tiles (the zones' walks joined, the seams settled). */
export function worldRegionWalk(region: string): string[] {
  let rows = regionRows.get(region);
  if (!rows) {
    const ch = chunkFor(region);
    rows = windowRows(region, 0, 0, ch.size[0] / CELL, ch.size[1] / CELL);
    regionRows.set(region, rows);
  }
  return rows;
}

// ---- finding a way: search windows, then the route graph -------------------------------

/** How far past the box round the start and the goal a search looks: two tiles, then four. */
export const SEARCH_PADS: readonly number[] = [2 * S, 4 * S];

type Window = { c0: number; r0: number; rows: string[]; grid: ReturnType<typeof makeWalkGrid> };
function windowAround(region: string, a: Point, b: Point, pad: number): Window | null {
  const ch = chunkFor(region);
  const cols = ch.size[0] / CELL;
  const rows = ch.size[1] / CELL;
  const c0 = Math.max(0, Math.floor((Math.min(a.x, b.x) - pad) / CELL));
  const r0 = Math.max(0, Math.floor((Math.min(a.y, b.y) - pad) / CELL));
  const c1 = Math.min(cols, Math.ceil((Math.max(a.x, b.x) + pad) / CELL) + 1);
  const r1 = Math.min(rows, Math.ceil((Math.max(a.y, b.y) + pad) / CELL) + 1);
  if (c1 <= c0 || r1 <= r0) return null;
  const w = windowRows(region, c0, r0, c1, r1);
  const grid = makeWalkGrid(w, {
    cell: CELL,
    width: (c1 - c0) * CELL,
    start: { x: a.x - c0 * CELL, y: a.y - r0 * CELL },
  });
  return { c0, r0, rows: w, grid };
}

/** A walk inside one window round its two ends, or [] when it does not get there. */
export function windowPath(region: string, from: Point, to: Point, pad: number): Point[] {
  const w = windowAround(region, from, to, pad);
  if (!w) return [];
  const ox = w.c0 * CELL;
  const oy = w.r0 * CELL;
  return w.grid
    .findPath({ x: from.x - ox, y: from.y - oy }, { x: to.x - ox, y: to.y - oy })
    .map((p) => ({ x: p.x + ox, y: p.y + oy }));
}

/** Steps (4-way) from a point to every open cell of a window round it, -1 where unreached. */
function reach(w: Window, p: Point): { dist: Int32Array; cols: number } {
  const cols = w.rows[0].length;
  const rows = w.rows.length;
  const dist = new Int32Array(cols * rows).fill(-1);
  const s = w.grid.nearestWalkable({ x: p.x - w.c0 * CELL, y: p.y - w.r0 * CELL });
  if (w.rows[s.cy]?.[s.cx] !== '.') return { dist, cols };
  const queue = [s.cy * cols + s.cx];
  dist[queue[0]] = 0;
  for (let head = 0; head < queue.length; head++) {
    const k = queue[head];
    const x = k % cols;
    const y = (k - x) / cols;
    for (const [nx, ny] of [
      [x + 1, y],
      [x - 1, y],
      [x, y + 1],
      [x, y - 1],
    ]) {
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
      const nk = ny * cols + nx;
      if (dist[nk] >= 0 || w.rows[ny][nx] !== '.') continue;
      dist[nk] = dist[k] + 1;
      queue.push(nk);
    }
  }
  return { dist, cols };
}

type Graph = { nodes: Point[]; adj: [number, number][][] };
const graphs = new Map<string, Graph | null>();
function graphOf(region: string): Graph | null {
  if (graphs.has(region)) return graphs.get(region) ?? null;
  const g = worldPortals[region];
  const ch = chunkFor(region);
  let out: Graph | null = null;
  if (g && g.nodes.length) {
    const nodes = g.nodes.map(([x, y]) => ({ x: x - ch.origin[0], y: y - ch.origin[1] }));
    const adj: [number, number][][] = nodes.map(() => []);
    for (const [a, b, cost] of g.edges) {
      adj[a].push([b, cost]);
      adj[b].push([a, cost]);
    }
    out = { nodes, adj };
  }
  graphs.set(region, out);
  return out;
}

/** The nodes of the route graph a walk from `p` reaches inside a window round it: [node, px]. */
function nodesReached(region: string, g: Graph, p: Point, pad: number): [number, number][] {
  const w = windowAround(region, p, p, pad);
  if (!w) return [];
  const { dist, cols } = reach(w, p);
  const out: [number, number][] = [];
  g.nodes.forEach((n, i) => {
    const cx = Math.floor(n.x / CELL) - w.c0;
    const cy = Math.floor(n.y / CELL) - w.r0;
    if (cx < 0 || cy < 0 || cx >= cols || cy >= w.rows.length) return;
    const d = dist[cy * cols + cx];
    if (d >= 0) out.push([i, d * CELL]);
  });
  return out;
}

/** The cheapest chain of route-graph nodes from `from` to `to` (Dijkstra), or null. */
export function routeVia(region: string, from: Point, to: Point, pad: number = SEARCH_PADS[0]) {
  const g = graphOf(region);
  if (!g) return null;
  const starts = nodesReached(region, g, from, pad);
  const ends = new Map(nodesReached(region, g, to, pad));
  if (!starts.length || !ends.size) return null;
  const n = g.nodes.length;
  const cost = new Float64Array(n).fill(Infinity);
  const prev = new Int32Array(n).fill(-1);
  const done = new Uint8Array(n);
  for (const [i, d] of starts) cost[i] = Math.min(cost[i], d);
  for (;;) {
    let best = -1;
    for (let i = 0; i < n; i++)
      if (!done[i] && cost[i] < Infinity && (best < 0 || cost[i] < cost[best])) best = i;
    if (best < 0) break;
    done[best] = 1;
    for (const [j, c] of g.adj[best])
      if (cost[best] + c < cost[j]) {
        cost[j] = cost[best] + c;
        prev[j] = best;
      }
  }
  let end = -1;
  let total = Infinity;
  for (const [i, d] of ends)
    if (cost[i] + d < total) {
      total = cost[i] + d;
      end = i;
    }
  if (end < 0) return null;
  const chain: Point[] = [];
  for (let i = end; i >= 0; i = prev[i]) chain.unshift(g.nodes[i]);
  return { chain, cost: total };
}

/**
 * The way from one point of a region to another: searched in a window round the two
 * ends plus two tiles, then four; failing that, planned on the route graph and walked a
 * leg at a time, each leg in its own window. [] when there is no way there.
 */
export function findWorldPath(
  region: string,
  from: Point,
  to: Point,
  pads: readonly number[] = SEARCH_PADS,
): Point[] {
  for (const pad of pads) {
    const path = windowPath(region, from, to, pad);
    if (path.length) return path;
  }
  const route = routeVia(region, from, to, pads[0]);
  if (!route) return [];
  const out: Point[] = [];
  let at = from;
  // (a leg joins two nodes of one area: its walk can wander the area, so its window may
  // grow to the full search's)
  const legPads = [...new Set([...pads, ...SEARCH_PADS])].sort((x, y) => x - y);
  const same = (p: Point, q: Point) =>
    Math.floor(p.x / CELL) === Math.floor(q.x / CELL) &&
    Math.floor(p.y / CELL) === Math.floor(q.y / CELL);
  for (const stop of [...route.chain, to]) {
    if (same(at, stop)) continue; // (a node in the cell the walk is already in)
    let leg: Point[] = [];
    for (const pad of legPads) {
      leg = windowPath(region, at, stop, pad);
      if (leg.length) break;
    }
    if (!leg.length) break; // as far as it gets
    out.push(...leg);
    at = leg[leg.length - 1];
  }
  return out;
}

/** The same interface as makeWalkGrid (lib/garden-path.ts), over a region's world tiles,
 *  its paths found by findWorldPath. */
export function makeWorldWalk(region: string, start: Point) {
  const ch = chunkFor(region);
  const cols = ch.size[0] / CELL;
  const rows = ch.size[1] / CELL;
  const walkable = (cx: number, cy: number) =>
    cx >= 0 && cy >= 0 && cx < cols && cy < rows && cellOpen(region, cx, cy);
  const toCell = (p: Point) => ({
    cx: Math.max(0, Math.min(cols - 1, Math.floor(p.x / CELL))),
    cy: Math.max(0, Math.min(rows - 1, Math.floor(p.y / CELL))),
  });
  const toPoint = (cx: number, cy: number): Point => ({
    x: cx * CELL + CELL / 2,
    y: cy * CELL + CELL / 2,
  });
  function nearestWalkable(p: Point) {
    const { cx, cy } = toCell(p);
    for (let r = 0; r < 24; r++)
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++)
          if (Math.max(Math.abs(dx), Math.abs(dy)) === r && walkable(cx + dx, cy + dy))
            return { cx: cx + dx, cy: cy + dy };
    return toCell(start);
  }
  const findPath = (from: Point, to: Point): Point[] =>
    [from.x, from.y, to.x, to.y].every(Number.isFinite) ? findWorldPath(region, from, to) : [];
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

// ---- areas -------------------------------------------------------------------------------

const areasOf = new Map<string, WorldArea[]>();
function regionAreas(region: string): WorldArea[] {
  let a = areasOf.get(region);
  if (!a) areasOf.set(region, (a = worldAreas.filter((x) => x.chunk === region)));
  return a;
}
const inArea = (a: WorldArea, wx: number, wy: number, margin = 0) => {
  const [x, y, w, h] = a.rect;
  if (wx < x - margin || wx >= x + w + margin || wy < y - margin || wy >= y + h + margin)
    return false;
  if (!a.cells || margin) return true;
  return a.cells[Math.floor((wy - y) / CELL)]?.[Math.floor((wx - x) / CELL)] === '.';
};
/** The area under a region point, if any. */
export function areaAt(region: string, x: number, y: number): WorldArea | undefined {
  const ch = chunkFor(region);
  return regionAreas(region).find((a) => inArea(a, x + ch.origin[0], y + ch.origin[1]));
}
/** The area under a point, keeping the previous one while the point is within `margin` px
 *  of it (no flicker of the name along an edge; lib/region-walk.ts ZONE_HYSTERESIS). */
export function areaWithHysteresis(
  region: string,
  prev: string | undefined,
  x: number,
  y: number,
  margin: number,
): WorldArea | undefined {
  const here = areaAt(region, x, y);
  if (!prev || here?.id === prev) return here;
  const ch = chunkFor(region);
  const old = regionAreas(region).find((a) => a.id === prev);
  return old && inArea(old, x + ch.origin[0], y + ch.origin[1], margin) ? old : here;
}
/** The areas a region box (grown by `margin`) touches, with their rects in region px. */
export function areasNear(region: string, view: RegionBox, margin: number) {
  const ch = chunkFor(region);
  return regionAreas(region)
    .map((a) => ({
      area: a,
      x: a.rect[0] - ch.origin[0],
      y: a.rect[1] - ch.origin[1],
      w: a.rect[2],
      h: a.rect[3],
    }))
    .filter(
      (a) =>
        a.x < view.x1 + margin &&
        a.x + a.w > view.x0 - margin &&
        a.y < view.y1 + margin &&
        a.y + a.h > view.y0 - margin,
    );
}

// ---- mounting tiles ------------------------------------------------------------------------

/** How far past the camera's view a tile is mounted; it is let go at twice this. */
export const TILE_MOUNT_MARGIN = 24;

/** The world tiles of a region's plane (with a picture or something on them) that a region
 *  box grown by `margin` touches, as 'col,row'. */
export function tileKeysNear(region: string, view: RegionBox, margin: number): string[] {
  const ch = chunkFor(region);
  const [ox, oy] = ch.origin;
  const c0 = Math.floor((view.x0 - margin + ox) / S);
  const c1 = Math.floor((view.x1 + margin - 1 + ox) / S);
  const r0 = Math.floor((view.y0 - margin + oy) / S);
  const r1 = Math.floor((view.y1 + margin - 1 + oy) / S);
  const out: string[] = [];
  for (let r = r0; r <= r1; r++)
    for (let c = c0; c <= c1; c++) if (worldTiles[ch.plane][`${c},${r}`]) out.push(`${c},${r}`);
  return out;
}

/** The tiles to mount for a view: those within the margin, and any already mounted still
 *  within twice it (so a tile at the edge does not mount and unmount as the camera turns). */
export function tilesToMount(
  region: string,
  view: RegionBox,
  mounted: readonly string[] = [],
  margin = TILE_MOUNT_MARGIN,
): string[] {
  const close = new Set(tileKeysNear(region, view, margin));
  const kept = new Set(tileKeysNear(region, view, margin * 2));
  for (const k of mounted) if (kept.has(k)) close.add(k);
  return [...close].sort();
}

/** A tile's top-left in region px. */
export function tileOriginOf(region: string, key: string): Point {
  const ch = chunkFor(region);
  const [c, r] = key.split(',').map(Number);
  return { x: c * S - ch.origin[0], y: r * S - ch.origin[1] };
}

/** The props drawn with a set of mounted tiles: every prop whose picture reaches one of
 *  them (a tall tower whose foot stands in a tile off screen still draws), in region px. */
type RegionProp = { id: string; sprite: string; x: number; y: number; w: number; h: number };
const reachIndex = new Map<string, Map<string, RegionProp[]>>();
function reachOf(region: string): Map<string, RegionProp[]> {
  let idx = reachIndex.get(region);
  if (idx) return idx;
  idx = new Map();
  const ch = chunkFor(region);
  const [ox, oy] = ch.origin;
  for (const t of Object.values(worldTiles[ch.plane]))
    for (const [id, sprite, x, y, w, h] of t.objects) {
      if (x + w <= ox || y + h <= oy || x >= ox + ch.size[0] + S || y >= oy + ch.size[1] + S)
        continue;
      const prop = { id, sprite, x: x - ox, y: y - oy, w, h };
      for (let r = Math.floor(y / S); r <= Math.floor((y + h - 1) / S); r++)
        for (let c = Math.floor(x / S); c <= Math.floor((x + w - 1) / S); c++) {
          const k = `${c},${r}`;
          const list = idx.get(k) ?? [];
          list.push(prop);
          idx.set(k, list);
        }
    }
  reachIndex.set(region, idx);
  return idx;
}
export function propsFor(region: string, keys: readonly string[]): RegionProp[] {
  const idx = reachOf(region);
  const seen = new Set<string>();
  const out: RegionProp[] = [];
  for (const k of keys)
    for (const p of idx.get(k) ?? [])
      if (!seen.has(p.id)) {
        seen.add(p.id);
        out.push(p);
      }
  return out;
}

/** Decoded picture memory of a set of mounted tiles (bytes): each ground picture at its
 *  scale (a one-colour tile is drawn as a colour, no picture) and each moving-water sheet. */
export function mountedBytes(region: string, keys: readonly string[]): number {
  const ch = chunkFor(region);
  let bytes = 0;
  for (const k of keys) {
    const t = worldTiles[ch.plane][k];
    if (!t) continue;
    if (t.art && !t.fill) bytes += (S * WORLD_TILE.scale) ** 2 * 4;
    if (t.flow) bytes += t.flow[2] * t.flow[3] * WORLD_FLOW.frames * 4;
  }
  return bytes;
}
