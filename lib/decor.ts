import { decorSizes } from '@/lib/decor-sizes';
import { zoneMaps } from '@/lib/zone-maps';
import { regionWalk } from '@/lib/region-walk';
import { GARDEN, gardenAnchors, gardenFlat, gardenHotspots, gardenWalk } from '@/lib/garden-map';
import { HUT_DOOR, TRAIL_X } from '@/lib/garden-path';

/**
 * Keepsakes and where they stand in the nap hut (C12, living-world plan W4; research:
 * "collect once, place freely"). Every place the companion walks leaves one keepsake; it
 * waits in the keepsake chest and can be set anywhere on the hut's floor, moved or put
 * away again, free and instant. Nothing is bought or scored, and nothing here touches
 * the game's rules: a keepsake only changes how the room looks and where the companion
 * can walk, and a placement is refused if it would cut off any part of the room.
 * Pure, so it is tested (lib/world-save.test.ts).
 */
/** Where a keepsake can stand: inside the hut, or out in the garden. */
export type DecorArea = 'hut' | 'garden';
/** A keepsake set out; `area` is left out inside the hut (saves from before the garden);
 *  `flip` turns it to face the other way. */
export type DecorPlacement = { item: string; x: number; y: number; area?: 'garden'; flip?: true };
export const areaOf = (p: DecorPlacement): DecorArea => p.area ?? 'hut';

/**
 * The hut's outside (C12's second half, coherence plan B1): its door's paint, what grows
 * under its windows and the path up to its step. Every choice is open from the start,
 * free and instant, and only a look: the hut's footprint, its door and the garden's
 * hotspots never move. Each look is drawn by scripts/art/garden.py.
 */
export const hutDoors = ['oak', 'red', 'violet', 'green'] as const;
export const hutBoxes = ['none', 'flowers', 'herbs'] as const;
export const hutPaths = ['earth', 'flagstones'] as const;
export type HutLook = {
  door: (typeof hutDoors)[number];
  boxes: (typeof hutBoxes)[number];
  path: (typeof hutPaths)[number];
};
export const DEFAULT_HUT_LOOK: HutLook = { door: 'oak', boxes: 'flowers', path: 'earth' };
/** The drawn hut for a look (lib/garden-hut-assets.ts, hutImages). */
export const hutImageKey = (look: HutLook) => `${look.door}-${look.boxes}`;

function oneOf<T extends string>(options: readonly T[], value: unknown, fallback: T): T {
  return options.find((o) => o === value) ?? fallback;
}
/** A saved hut look, made safe: each part known, or the hut as it first stood. */
export function restoreHutLook(value: unknown): HutLook {
  if (typeof value !== 'object' || value === null || Array.isArray(value))
    return { ...DEFAULT_HUT_LOOK };
  return {
    door: oneOf(hutDoors, Reflect.get(value, 'door'), DEFAULT_HUT_LOOK.door),
    boxes: oneOf(hutBoxes, Reflect.get(value, 'boxes'), DEFAULT_HUT_LOOK.boxes),
    path: oneOf(hutPaths, Reflect.get(value, 'path'), DEFAULT_HUT_LOOK.path),
  };
}

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
    id: 'brass_telescope',
    name: 'Brass telescope',
    from: 'the Frostline',
    zones: ['hollow', 'snowmelt', 'saddle', 'summit'],
  },
  {
    id: 'shell_bowl',
    name: 'Bowl of shells',
    from: 'Driftwood Harbour',
    zones: ['harbour', 'headland'],
  },
  {
    id: 'orchid_pot',
    name: 'Potted orchid',
    from: 'the Tidebloom Isles',
    zones: ['landing', 'rainforest', 'headwaters', 'cove'],
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
  {
    id: 'neon_sign',
    name: 'Little neon sign',
    from: 'Neon Harbour',
    zones: [
      'neon',
      'skyport',
      'market',
      'downtown',
      'heights',
      'plaza',
      'waterfront',
      'docks',
      'point',
    ],
  },
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
type Spot = readonly [number, number];
const home = zoneMaps.home;

/**
 * Where a keepsake belongs (coherence plan H1, Matt: "nothing placed at random"). Every
 * keepsake can stand on the floor; the small ones (a bowl, a vase, a jar, a lamp, a globe,
 * the mantel clock, the little sign) can also stand on a surface in the hut: the mantel,
 * the top of the bookcase, the kitchen counter, the table, the bedroom window's sill.
 * Set on a surface, a keepsake takes no floor and never blocks a way through.
 */
export type DecorPlace = 'floor' | 'surface';
const SURFACE_ITEMS = new Set([
  'shell_bowl',
  'reed_vase',
  'pinecone_jar',
  'town_lantern',
  'ember_lamp',
  'star_globe',
  'moon_crystal',
  'orchid_pot',
  'cactus_pot',
  'cog_clock',
  'neon_sign',
]);
export const placeOf = (item: string): DecorPlace =>
  SURFACE_ITEMS.has(item) ? 'surface' : 'floor';

type Surface = { x: number; y: number; on: string; depth: number };
let surfaces: Surface[] | null = null;
/**
 * The surfaces in the hut a small keepsake can stand on, each the point its feet rest at
 * (scripts/art/home_zones.py): read from the furniture where it stands, so they move with
 * it, and the bedroom's west window sill, which is part of the wall.
 */
export function hutSurfaces(): readonly Surface[] {
  if (surfaces) return surfaces;
  const at = (id: string, dx: number, dy: number, on: string): Surface[] => {
    const o = home.objects.find(([oid]) => oid === id);
    return o ? [{ x: o[2] + dx, y: o[3] + dy, on, depth: o[3] + o[5] + 1 }] : [];
  };
  surfaces = [
    ...at('hearth', 23, 19, 'the mantel'), // between the candle and the mantel clock's place
    ...at('hearth', 37, 19, 'the mantel'),
    ...at('books', 11, 3, 'the bookcase'), // beside the plant on its top
    ...at('kitchen', 29, 25, 'the counter'), // between the herbs and the sink
    ...at('table', 14, 21, 'the table'), // in front of the cups
    ...at('table', 35, 21, 'the table'),
    { x: 68, y: 50, on: 'the window sill', depth: 65 }, // the bedroom's west window (x 52, sill at 48)
    { x: 82, y: 50, on: 'the window sill', depth: 65 },
  ];
  return surfaces;
}
const surfaceAt = (x: number, y: number) => hutSurfaces().find((s) => s.x === x && s.y === y);
/** The depth to draw a keepsake at: its feet, or, on a surface, just in front of the
 *  furniture it stands on (so the mantel never hides what is set on it). */
export function decorDepth(p: DecorPlacement): number {
  const s = areaOf(p) === 'hut' && placeOf(p.item) === 'surface' ? surfaceAt(p.x, p.y) : undefined;
  return s ? Math.max(p.y, s.depth) : p.y;
}
/** Whether a keepsake stands on a surface in the hut, off the floor. */
export function raised(p: DecorPlacement): boolean {
  return areaOf(p) === 'hut' && placeOf(p.item) === 'surface' && surfaceAt(p.x, p.y) !== undefined;
}
let hutRows: string[] | null = null;
/** The hut's own walk rows (the home region is the hut alone, so its pixels are the hut's). */
export const hutWalk = () => (hutRows ??= regionWalk('home'));
let gardenRows: string[] | null = null;
/** The garden's walk rows, kept inside the scene the way the companion is (garden-path.ts). */
export const gardenFloor = () =>
  (gardenRows ??= gardenWalk.map((row, cy) =>
    row
      .split('')
      .map((c, cx) => {
        const x = cx * CELL + CELL / 2;
        const y = cy * CELL + CELL / 2;
        const inside = x >= 16 && x <= GARDEN.width - 16 && y >= 48 && y <= GARDEN.fenceY - 4;
        return inside ? c : '#';
      })
      .join(''),
  ));
/** The nearest open cell to a point, as the point of its centre. */
function onFloor(rows: readonly string[], [x, y]: Spot): Spot {
  const cx = Math.floor(x / CELL);
  const cy = Math.floor(y / CELL);
  for (let r = 0; r < 12; r++)
    for (let dy = -r; dy <= r; dy++)
      for (let dx = -r; dx <= r; dx++)
        if (Math.max(Math.abs(dx), Math.abs(dy)) === r && rows[cy + dy]?.[cx + dx] === '.')
          return [(cx + dx) * CELL + CELL / 2, (cy + dy) * CELL + CELL / 2];
  return [x, y];
}
/**
 * Each area's floor and the places the companion must always be able to reach there
 * (the first is where the reach is measured from): in the hut the front door, the bed,
 * the hearth, the table, the sunroom and the chest; in the garden where it wakes, every
 * hotspot, the hut's door and the four ways out. Garden flats (the bridge) stay bare.
 */
const areas: Record<
  DecorArea,
  {
    floor: () => readonly string[];
    keep: () => readonly Spot[];
    bare: readonly { x: number; y: number; w: number; h: number }[];
  }
> = {
  hut: {
    floor: hutWalk,
    keep: () => [
      home.stands.door,
      ...Object.entries(home.stands)
        .filter(([k]) => k !== 'door')
        .map(([, v]) => v),
    ],
    bare: [],
  },
  garden: {
    floor: gardenFloor,
    keep: () =>
      (
        [
          [gardenAnchors.start.x, gardenAnchors.start.y],
          [HUT_DOOR.x, HUT_DOOR.y],
          ...Object.values(gardenHotspots).map((h) => [h.x, h.y] as const),
          [TRAIL_X, 52],
          [20, 456],
          [GARDEN.width - 20, 220],
        ] as Spot[]
      ).map((p) => onFloor(gardenFloor(), p)),
    bare: gardenFlat,
  },
};
export const decorFloor = (area: DecorArea) => areas[area].floor();
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

/** Where a tap puts a keepsake's feet: on the cell grid, or, for a small keepsake tapped
 *  near a surface in the hut, on that surface. */
export function snapDecorFor(item: string, area: DecorArea, p: { x: number; y: number }) {
  if (area === 'hut' && placeOf(item) === 'surface') {
    let best: Surface | null = null;
    let near = 20;
    for (const s of hutSurfaces()) {
      const d = Math.hypot(s.x - p.x, s.y - p.y);
      if (d < near) {
        near = d;
        best = s;
      }
    }
    if (best) return { x: best.x, y: best.y };
  }
  return snapDecor(p);
}

/** The hut's walk rows with the placed keepsakes standing in the way (rugs are walked
 *  over, and those on a surface take no floor). */
export function walkWithDecor(walk: readonly string[], placed: readonly DecorPlacement[]) {
  const rows = walk.map((r) => r.split(''));
  for (const p of placed) {
    if (!decorSizes[p.item] || raised(p)) continue;
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
 * Whether `item` can stand with its feet at `x, y` in `area` among the `placed` ones
 * (any area; `placed` may include the item itself, which is ignored, so moving is a
 * check like any other).
 */
export function checkDecor(
  area: DecorArea,
  placed: readonly DecorPlacement[],
  item: string,
  x: number,
  y: number,
): DecorCheck {
  if (!decorSizes[item] || !Number.isFinite(x) || !Number.isFinite(y))
    return { ok: false, why: 'unknown' };
  const box = decorBox(item, x, y);
  if (raised({ item, x, y, ...(area === 'garden' ? { area } : {}) })) {
    // on a surface: it takes no floor; only another keepsake on a surface can be in its way
    const clash = placed.some((p) => {
      if (p.item === item || !decorSizes[p.item] || !raised(p)) return false;
      const b = decorBox(p.item, p.x, p.y);
      return (
        box.left < b.left + b.w && box.left + box.w > b.left && box.top < b.top + b.h && y > b.top
      );
    });
    return clash ? { ok: false, why: 'crowded' } : { ok: true };
  }
  const { floor, keep, bare } = areas[area];
  const walk = floor();
  const stands = keep();
  const others = placed.filter(
    (p) => p.item !== item && decorSizes[p.item] && areaOf(p) === area && !raised(p),
  );
  // on the floor: every footprint cell is open floor in the room itself
  if (!box.cells.every(([cx, cy]) => walk[cy]?.[cx] === '.')) return { ok: false, why: 'wall' };
  if (
    bare.some(
      (f) => box.left < f.x + f.w && box.left + box.w > f.x && box.top < f.y + f.h && y > f.y,
    )
  )
    return { ok: false, why: 'wall' };
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
  if (!allReachable(rows, stands)) return { ok: false, why: 'cut-off' };
  return { ok: true };
}

function allReachable(rows: readonly string[], stands: readonly Spot[]) {
  const cols = rows[0]?.length ?? 0;
  const cell = ([x, y]: Spot) => [Math.floor(x / CELL), Math.floor(y / CELL)];
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
export function restoreDecor(value: unknown, visited: readonly string[]): DecorPlacement[] {
  if (!Array.isArray(value)) return [];
  const found = new Set(foundKeepsakes(visited));
  const out: DecorPlacement[] = [];
  for (const v of value as unknown[]) {
    if (typeof v !== 'object' || v === null || Array.isArray(v)) continue;
    const item: unknown = Reflect.get(v, 'item');
    const x: unknown = Reflect.get(v, 'x');
    const y: unknown = Reflect.get(v, 'y');
    const area: DecorArea = Reflect.get(v, 'area') === 'garden' ? 'garden' : 'hut';
    const flip = Reflect.get(v, 'flip') === true ? { flip: true as const } : {};
    if (typeof item !== 'string' || typeof x !== 'number' || typeof y !== 'number') continue;
    if (!found.has(item) || out.some((p) => p.item === item)) continue;
    if (checkDecor(area, out, item, x, y).ok)
      out.push(area === 'garden' ? { item, x, y, area, ...flip } : { item, x, y, ...flip });
  }
  return out;
}

/** The keepsake in hand while decorating, where it was last tapped, and whether it is
 *  turned to face the other way. */
export type DecorHand = { item: string; at: { x: number; y: number } | null; flip?: boolean };

/**
 * What a tap does while decorating `area`: a keepsake standing there under the tap is
 * taken in hand (to move or put away; a rug only when nothing is in hand, so things can
 * be set on it); with one in hand, the tap is where it would go, and the companion walks
 * to just in front of it. `walk` is true for no walk, or the point to walk to.
 */
export function tapToDecorate(
  placed: readonly DecorPlacement[],
  area: DecorArea,
  hand: DecorHand | null,
  at: { x: number; y: number },
): { hand: DecorHand | null; walk: true | { x: number; y: number } | null } {
  const under = placed.filter((p) => {
    if (areaOf(p) !== area || !decorSizes[p.item]) return false;
    const b = decorBox(p.item, p.x, p.y);
    return at.x >= b.left && at.x < b.left + b.w && at.y >= b.top && at.y < b.top + b.h;
  });
  const solid = under.filter((p) => !decorBox(p.item, p.x, p.y).flat).sort((a, b) => b.y - a.y)[0];
  const hit = solid ?? (hand ? undefined : under[0]);
  if (hit && hit.item !== hand?.item)
    return { hand: { item: hit.item, at: null, ...(hit.flip ? { flip: true } : {}) }, walk: true };
  if (!hand) return { hand: null, walk: null };
  const spot = snapDecorFor(hand.item, area, at);
  const kept = { item: hand.item, at: spot, ...(hand.flip ? { flip: true } : {}) };
  if (area === 'hut' && surfaceAt(spot.x, spot.y) && placeOf(hand.item) === 'surface') {
    // set on a surface: the companion walks to the floor in front of it
    const [fx, fy] = onFloor(decorFloor(area), [spot.x, spot.y + 24]);
    return { hand: kept, walk: { x: fx, y: fy } };
  }
  return { hand: kept, walk: { x: spot.x, y: spot.y + 12 } };
}

/** A keepsake in hand turned to face the other way (decorating's TURN). */
export const turnHand = (hand: DecorHand): DecorHand =>
  hand.flip ? { item: hand.item, at: hand.at } : { ...hand, flip: true };

/** The footprint to light up under a keepsake about to be set down (area pixels). */
export function decorFootprint(item: string, x: number, y: number) {
  const b = decorBox(item, x, y);
  const xs = b.cells.map(([cx]) => cx * CELL);
  const ys = b.cells.map(([, cy]) => cy * CELL);
  const x0 = Math.min(...xs);
  const y0 = Math.min(...ys);
  return { x: x0, y: y0, w: Math.max(...xs) + CELL - x0, h: Math.max(...ys) + CELL - y0 };
}
