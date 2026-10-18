import { decorSizes } from '@/lib/decor-sizes';
import { zoneMaps } from '@/lib/zone-maps';
import { regionWalk } from '@/lib/region-walk';

/**
 * Keepsakes and where they stand in the nap hut (C12, living-world plan W4; research:
 * "collect once, place freely"). Every place the companion walks leaves one keepsake; it
 * waits in the keepsake chest and can be set anywhere on the hut's floor, moved or put
 * away again, free and instant. Nothing is bought or scored, and nothing here touches
 * the game's rules: a keepsake only changes how the room looks and where the companion
 * can walk, and a placement is refused if it would cut off any part of the room.
 * Pure, so it is tested (lib/world-save.test.ts).
 */
export type DecorPlacement = { item: string; x: number; y: number };

type Keepsake = {
  id: string;
  name: string;
  /** where it comes from, as the chest names it */
  from: string;
  /** the zones that leave it (any one); none for the things the hut starts with */
  zones: readonly string[] | null;
};

export const keepsakes: readonly Keepsake[] = [
  { id: 'fern_pot', name: 'Potted fern', from: 'the hut', zones: null },
  { id: 'stool', name: 'Three-legged stool', from: 'the hut', zones: null },
  { id: 'rag_rug', name: 'Rag rug', from: 'the hut', zones: null },
  { id: 'town_lantern', name: 'Brass lantern', from: 'Crossroads Town', zones: ['town'] },
  { id: 'reed_vase', name: 'Vase of reeds', from: 'the Riverside', zones: ['riverside'] },
  { id: 'pinecone_jar', name: 'Jar of pine cones', from: 'the Woodland', zones: ['woodland'] },
  { id: 'cairn', name: 'Little cairn', from: 'the Snowy Ridge', zones: ['ridge'] },
  {
    id: 'shell_bowl',
    name: 'Bowl of shells',
    from: 'Driftwood Harbour',
    zones: ['harbour', 'headland'],
  },
  { id: 'cog_clock', name: 'Cog clock', from: 'Cogsworth', zones: ['junction', 'canal'] },
  { id: 'cactus_pot', name: 'Potted cactus', from: 'Dust Gulch', zones: ['gulch', 'oasis'] },
  {
    id: 'ember_lamp',
    name: 'Ember lamp',
    from: 'the Ember Lands',
    zones: ['caldera', 'springs', 'scorch'],
  },
  { id: 'dragon_plush', name: 'Dragon plush', from: 'Hearthold Castle', zones: ['hearthold'] },
  { id: 'neon_sign', name: 'Little neon sign', from: 'Neon Harbour', zones: ['neon', 'skyport'] },
  { id: 'star_globe', name: 'Star globe', from: 'Halcyon Station', zones: ['station'] },
  { id: 'moon_crystal', name: 'Moon crystal', from: 'Lumen', zones: ['lumen'] },
];
const byId = new Map(keepsakes.map((k) => [k.id, k]));
export const keepsake = (id: string) => byId.get(id);

/** The keepsakes found so far: the hut's own, and one for each place walked. */
export function foundKeepsakes(visited: readonly string[]): string[] {
  return keepsakes
    .filter((k) => !k.zones || k.zones.some((z) => visited.includes(z)))
    .map((k) => k.id);
}

/** The keepsakes a walk into `zone` leaves that were not found before it. */
export function newKeepsakes(before: readonly string[], zone: string): string[] {
  if (before.includes(zone)) return [];
  const had = new Set(foundKeepsakes(before));
  return foundKeepsakes([...before, zone]).filter((id) => !had.has(id));
}

const CELL = 4;
const home = zoneMaps.home;
/** where the companion must always be able to reach: the door first, then the bed, the
 *  hearth, the table, the sunroom and the chest */
const stands: readonly (readonly [number, number])[] = [
  home.stands.door,
  ...Object.entries(home.stands)
    .filter(([k]) => k !== 'door')
    .map(([, v]) => v),
];
let hutRows: string[] | null = null;
/** The hut's own walk rows (the home region is the hut alone, so its pixels are the hut's). */
export const hutWalk = () => (hutRows ??= regionWalk('home'));
/** how near a stand nothing may stand, so the companion has room there */
const STAND_CLEAR = 10;

/** A keepsake's drawing box and the cells its footprint covers, at feet `x, y`. */
export function decorBox(item: string, x: number, y: number) {
  const s = decorSizes[item];
  const left = Math.round(x - s.w / 2);
  const top = y - s.h;
  const cells: [number, number][] = [];
  // a rug covers its whole box (to keep rugs apart and on the floor); the rest stand on
  // their footprint, the bottom `foot` pixels, a pixel in from each side
  const fx0 = s.foot ? left + 1 : left;
  const fx1 = s.foot ? left + s.w - 2 : left + s.w - 1;
  const fy0 = s.foot ? y - s.foot : top;
  for (let cy = Math.floor(fy0 / CELL); cy <= Math.floor((y - 1) / CELL); cy++)
    for (let cx = Math.floor(fx0 / CELL); cx <= Math.floor(fx1 / CELL); cx++) cells.push([cx, cy]);
  return { left, top, w: s.w, h: s.h, flat: !s.foot, cells };
}

/** Where a tap puts a keepsake's feet: on the cell grid. */
export const snapDecor = (p: { x: number; y: number }) => ({
  x: Math.round(p.x / CELL) * CELL,
  y: Math.round(p.y / CELL) * CELL,
});

/** The hut's walk rows with the placed keepsakes standing in the way (rugs are walked over). */
export function walkWithDecor(walk: readonly string[], placed: readonly DecorPlacement[]) {
  const rows = walk.map((r) => r.split(''));
  for (const p of placed) {
    if (!decorSizes[p.item]) continue;
    const b = decorBox(p.item, p.x, p.y);
    if (b.flat) continue;
    for (const [cx, cy] of b.cells) if (rows[cy]?.[cx] !== undefined) rows[cy][cx] = '#';
  }
  return rows.map((r) => r.join(''));
}

export type DecorCheck =
  | { ok: true }
  | { ok: false; why: 'wall' | 'crowded' | 'spot' | 'cut-off' | 'unknown' };

/**
 * Whether `item` can stand with its feet at `x, y` among the `placed` ones (`placed`
 * may include the item itself, which is ignored, so moving is a check like any other).
 * `walk` is the hut's own walk rows, without keepsakes.
 */
export function checkDecor(
  walk: readonly string[],
  placed: readonly DecorPlacement[],
  item: string,
  x: number,
  y: number,
): DecorCheck {
  if (!decorSizes[item] || !Number.isFinite(x) || !Number.isFinite(y))
    return { ok: false, why: 'unknown' };
  const others = placed.filter((p) => p.item !== item && decorSizes[p.item]);
  const box = decorBox(item, x, y);
  // on the floor: every footprint cell is open floor in the room itself
  if (!box.cells.every(([cx, cy]) => walk[cy]?.[cx] === '.')) return { ok: false, why: 'wall' };
  // not on another keepsake (a stool may stand on a rug, a rug not on a rug)
  const taken = new Set<string>();
  for (const p of others) {
    const b = decorBox(p.item, p.x, p.y);
    if (b.flat !== box.flat) continue;
    for (const [cx, cy] of b.cells) taken.add(`${cx},${cy}`);
  }
  if (box.cells.some(([cx, cy]) => taken.has(`${cx},${cy}`))) return { ok: false, why: 'crowded' };
  if (box.flat) return { ok: true };
  // room to stand at the door, the bed, the hearth, the chest...
  for (const [sx, sy] of stands)
    for (const [cx, cy] of box.cells) {
      const nx = Math.max(cx * CELL, Math.min(sx, cx * CELL + CELL));
      const ny = Math.max(cy * CELL, Math.min(sy, cy * CELL + CELL));
      if (Math.hypot(nx - sx, ny - sy) < STAND_CLEAR) return { ok: false, why: 'spot' };
    }
  // and every one of them still reachable from the door
  const rows = walkWithDecor(walk, [...others, { item, x, y }]);
  if (!allReachable(rows)) return { ok: false, why: 'cut-off' };
  return { ok: true };
}

function allReachable(rows: readonly string[]) {
  const cols = rows[0]?.length ?? 0;
  const cell = ([x, y]: readonly [number, number]) => [Math.floor(x / CELL), Math.floor(y / CELL)];
  const [dx, dy] = cell(stands[0]);
  const seen = new Set<number>([dy * cols + dx]);
  const queue: [number, number][] = [[dx, dy]];
  for (let i = 0; i < queue.length; i++) {
    const [x, y] = queue[i];
    for (const [ax, ay] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ]) {
      const nx = x + ax;
      const ny = y + ay;
      if (rows[ny]?.[nx] !== '.' || seen.has(ny * cols + nx)) continue;
      seen.add(ny * cols + nx);
      queue.push([nx, ny]);
    }
  }
  return stands.every((s) => {
    const [x, y] = cell(s);
    return seen.has(y * cols + x);
  });
}

/**
 * Saved keepsakes, made safe: known, found, one of each, and each still standing where
 * it may (a hut redrawn since the save sends one that no longer fits back to the chest).
 */
export function restoreDecor(
  value: unknown,
  visited: readonly string[],
  walk: readonly string[],
): DecorPlacement[] {
  if (!Array.isArray(value)) return [];
  const found = new Set(foundKeepsakes(visited));
  const out: DecorPlacement[] = [];
  for (const v of value as unknown[]) {
    if (typeof v !== 'object' || v === null || Array.isArray(v)) continue;
    const item: unknown = Reflect.get(v, 'item');
    const x: unknown = Reflect.get(v, 'x');
    const y: unknown = Reflect.get(v, 'y');
    if (typeof item !== 'string' || typeof x !== 'number' || typeof y !== 'number') continue;
    if (!found.has(item) || out.some((p) => p.item === item)) continue;
    if (checkDecor(walk, out, item, x, y).ok) out.push({ item, x, y });
  }
  return out;
}
