import type { RegionId, TileId } from '@/lib/region-walk';
import { travelLinks, type StopId } from '@/lib/world-places';

/**
 * The ways that open the world (Matt, 20 Oct: "progressively unlock more of the world
 * through tasks that ask the user to not use their phone or via in game currency").
 * The mechanism is `docs/vision/world-unlocks.md`; where each way stands is section 4
 * of `docs/vision/world-plan.md`. This file is the catalogue only: what each way is,
 * where it stands, what it opens, what comes before it, its rest task and its Dream Dust
 * price, who stands by it and what the companion says. Pure data and lookups: it keeps
 * no state, reads no clock, changes no rule and is not read by the game yet. The
 * rules (progress, chip-in, refunds, one way a day, migration) are Codex's
 * `lib/way-progress.ts` (C29 to C32); the walk and travel honour it in a later step.
 * Tested by lib/world-ways.test.ts (`npm run check:world-ways`).
 *
 * Numbers are real minutes (Matt, 20 Oct: rests run in real time when ways ship; demo
 * speed stays a developer switch, applied by the rules, not here).
 */

/** The nine ways on the road (W1 to W9), then the shortcuts and comforts (S1 to S4). */
export type WayId =
  | 'headland'
  | 'ridge-col'
  | 'valley-train'
  | 'ferry'
  | 'desert-line'
  | 'chasm-bridge'
  | 'maglev'
  | 'elevator'
  | 'shuttle'
  | 'mine-cart'
  | 'millpond-boat'
  | 'coastal-steamer'
  | 'ridge-lanterns';

/**
 * A line is a journey service to a region; an area is zones behind a drawn barrier;
 * lines and areas make up the road. A shortcut is a quicker way between places already
 * reached on foot; a comfort is presentation in a place already reached. Shortcuts and
 * comforts are Dream Dust only and never stand between the player and a place.
 */
export type WayKind = 'line' | 'area' | 'shortcut' | 'comfort';

/**
 * A task of time away (world-unlocks.md 2.3). Every task is measured in rest: a nap or
 * an outing, from START to WAKE UP or the outing's end.
 * - `one-rest`: a single rest of at least `minutes`.
 * - `in-all`: rest since the way came in reach adds up to `minutes`.
 * - `days`: `days` calendar days, not necessarily in a row, each with at least
 *   `minutesEachDay` of rest.
 * - `evening`: a single rest of at least `minutes` that starts between `fromHour` and
 *   `toHour` (local time; 24 is midnight).
 * - `long`: `rests` rests of at least `minutesEach`, ending on different days.
 */
export type RestTask =
  | { kind: 'one-rest'; minutes: number }
  | { kind: 'in-all'; minutes: number }
  | { kind: 'days'; days: number; minutesEachDay: number }
  | { kind: 'evening'; minutes: number; fromHour: number; toHour: number }
  | { kind: 'long'; rests: number; minutesEach: number };

/** Zones `world-plan.md` 3.4 adds to Cogsworth (`LAYOUT`: `hill` at (1, 0), `terminus` at
 *  (1, 1)). Not drawn yet: they are named here only so the way that will open them is
 *  known. When one is drawn, move it into that way's `zones` (the test says so). */
export type PlannedZoneId = 'hill' | 'terminus';
export const plannedZones: Readonly<
  Record<PlannedZoneId, { region: RegionId; col: number; row: number }>
> = {
  hill: { region: 'steam', col: 1, row: 0 },
  terminus: { region: 'steam', col: 1, row: 1 },
};

/**
 * Where a way's barrier stands. `zone` and `stand` are today's ids in lib/zone-maps.ts
 * (the stand nearest the barrier, where its card will sit until the redrawn art gives
 * it its own); `at` is the spot `world-plan.md` gives, in zone pixels, approximate until
 * drawn; `ports` are the `zonePorts` seams the barrier closes; `stop` is the journey
 * stop the vehicle waits at. `planned` is true while the barrier exists only in the
 * plan, not yet in the zone art and the walk grid.
 */
export type WayBarrier = {
  region: RegionId;
  zone: TileId;
  /** What stands there while the way is closed. */
  what: string;
  stand?: string;
  at?: readonly [number, number];
  ports?: readonly string[];
  stop?: StopId;
  /** The zone the barrier moves into once `world-plan.md` adds it. */
  plannedZone?: PlannedZoneId;
  planned: boolean;
};

export type WorldWay = {
  id: WayId;
  /** 'W1'..'W9' on the road, 'S1'..'S4' for shortcuts and comforts. */
  label: string;
  kind: WayKind;
  /** The world feature being mended, as the card names it (shown uppercase). */
  name: string;
  /** How it looks closed (being mended) and open (world-unlocks.md 2.5). */
  closed: string;
  open: string;
  /** The map's pictogram on a closed line or border (world-unlocks.md 2.5). */
  pictogram: string;
  barriers: readonly WayBarrier[];
  opens: {
    /** Zones that lie behind this way (closed until it opens). */
    zones: readonly TileId[];
    /** Zones the world plan adds behind this way, not drawn yet. */
    plannedZones: readonly PlannedZoneId[];
    /** Journey lines (`travelLinks` pairs) this way runs. */
    lines: readonly (readonly [StopId, StopId])[];
    /** A line the plan proposes between two zones with no stops yet (S3). */
    plannedLine?: { from: TileId; to: TileId };
  };
  /** The way that must be open before this one comes in reach; null from the start. */
  after: WayId | null;
  /** The rest task that opens it; null for shortcuts and comforts (Dream Dust only). */
  task: RestTask | null;
  /**
   * Its Dream Dust price (the currency was GRASS until 20 Oct; the field keeps the name
   * `grass`, as the balance `player.grass` does); null only for a proposal with no price yet.
   */
  grass: number | null;
  /** The resident who stands by it and explains it; null where the plan names none. */
  resident: string | null;
  /** The companion's lines: first seeing it closed, and at welcome back once it opened.
   *  Lowercase, short, never nagging (world-unlocks.md 2.5). */
  companion: { closed: string; opened: string };
  /** The welcome-back row (uppercase in the pixel font). */
  welcome: string;
  /** True for a proposal in the plan still waiting for Matt (S3, world-plan.md 6.3). */
  proposal?: boolean;
};

const ONE_HOUR = 60;
const EVENING = { fromHour: 18, toHour: 24 } as const;
const LONG_REST = 5 * ONE_HOUR;

/** The catalogue: the road in order (W1 to W9), then the shortcuts and comforts. */
export const worldWays: readonly WorldWay[] = [
  {
    id: 'headland',
    label: 'W1',
    kind: 'area',
    name: 'the Headland stile',
    closed: "the stile's step broken, a hurdle across it",
    open: 'a new stile, the old hurdle against the wall',
    pictogram: 'stile',
    barriers: [
      {
        region: 'valley',
        zone: 'headland',
        what: 'the stile in the drystone wall from the estuary to the cliff',
        at: [168, 96],
        planned: true,
      },
    ],
    // The lane along the zone's top strip (y 0 to 96) and the estuary footbridge stay
    // open with W1 closed; the wall south of the lane closes the promontory.
    opens: { zones: ['headland'], plannedZones: [], lines: [] },
    after: null,
    task: { kind: 'one-rest', minutes: 10 },
    grass: 25,
    resident: 'the shepherd',
    companion: {
      closed: "the stile's step is broken. if we rest a while, i bet the shepherd mends it.",
      opened: "while you were away, the shepherd mended the stile. let's see the tower?",
    },
    welcome: 'THE HEADLAND STILE IS MENDED',
  },
  {
    id: 'ridge-col',
    label: 'W2',
    kind: 'area',
    name: 'the ridge col',
    closed: 'a snowy pine across the col, and one across the gully trail',
    open: 'sawn into rounds stacked beside each trail, an axe in a block',
    pictogram: 'log',
    barriers: [
      {
        region: 'valley',
        zone: 'ridge',
        what: 'a fallen pine across the col in the rock shoulders',
        stand: 'saddle',
        ports: ['saddle|ridge'],
        planned: true,
      },
      {
        // the hollow/ridge seam is open land today; the plan closes it with a rock rib
        // cut only by the gully trail (about y 360 to 408)
        region: 'valley',
        zone: 'ridge',
        what: 'a fallen pine across the gully trail through the rock rib',
        stand: 'hollow',
        ports: ['hollow|ridge'],
        planned: true,
      },
    ],
    opens: { zones: ['hollow', 'snowmelt', 'saddle', 'summit'], plannedZones: [], lines: [] },
    after: null,
    task: { kind: 'in-all', minutes: 45 },
    grass: 60,
    resident: 'the forester',
    companion: {
      closed: 'a pine came down across the col. if we rest a while, the forester will clear it.',
      opened: 'while you were away, the forester sawed up the pines. the high path is clear.',
    },
    welcome: 'THE RIDGE COL IS CLEAR',
  },
  {
    id: 'valley-train',
    label: 'W3',
    kind: 'line',
    name: 'the valley train',
    closed: 'the engine in its shed, boiler cold, the signal at danger',
    open: 'steam up at the platform, the signal off',
    pictogram: 'cold engine',
    barriers: [
      {
        region: 'valley',
        zone: 'halt',
        what: 'the engine shed beside the platform',
        stand: 'platform',
        stop: 'valley',
        planned: true,
      },
    ],
    opens: {
      zones: ['junction', 'canal'],
      plannedZones: ['hill', 'terminus'],
      lines: [['valley', 'steam']],
    },
    after: null,
    task: { kind: 'one-rest', minutes: 30 },
    grass: 120,
    resident: 'the porter',
    companion: {
      closed: "the engine's boiler is cold. if we rest a while, i bet the porter gets it going.",
      opened: 'while you were away, the train got its steam back. want to ride?',
    },
    welcome: 'THE VALLEY TRAIN IS RUNNING',
  },
  {
    id: 'ferry',
    label: 'W4',
    kind: 'line',
    name: 'the Driftwood ferry',
    closed: 'the ferry on the slip, a patched hull, a tar pot',
    open: 'afloat at the pier, its flag up',
    pictogram: 'anchor',
    barriers: [
      {
        region: 'valley',
        zone: 'harbour',
        what: "the slipway at Driftwood's west quay",
        stand: 'jetty',
        stop: 'pier',
        planned: true,
      },
    ],
    opens: {
      zones: ['landing', 'rainforest', 'headwaters', 'cove'],
      plannedZones: [],
      lines: [['pier', 'isles']],
    },
    after: null,
    task: { kind: 'evening', minutes: 45, ...EVENING },
    grass: 150,
    resident: 'the boatwoman',
    companion: {
      closed: "the ferry's being mended. if we rest a while, i bet it's ready.",
      opened: 'while you were away, the boatwoman patched the ferry. want to sail?',
    },
    welcome: 'THE FERRY IS AFLOAT',
  },
  {
    id: 'desert-line',
    label: 'W5',
    kind: 'line',
    name: 'the desert line',
    closed: 'a goods wagon caked in sand at the platform, the departure board showing a dune',
    open: 'the wagon unloaded, the board showing a cactus',
    pictogram: 'dune',
    barriers: [
      {
        region: 'steam',
        zone: 'junction',
        what: "the sand-caked wagon at Cogsworth's platform",
        stand: 'platform',
        stop: 'steam',
        planned: true,
      },
    ],
    opens: { zones: ['gulch', 'oasis', 'scorch'], plannedZones: [], lines: [['steam', 'west']] },
    after: 'valley-train',
    task: { kind: 'days', days: 3, minutesEachDay: ONE_HOUR },
    grass: 250,
    resident: 'a tinkerer',
    companion: {
      closed: 'the desert wagon is full of sand. if we rest a while, the tinkerer will dig it out.',
      opened: 'while you were away, the tinkerer emptied the wagon. the desert line runs.',
    },
    welcome: 'THE DESERT LINE IS RUNNING',
  },
  {
    id: 'chasm-bridge',
    label: 'W6',
    kind: 'area',
    name: 'the chasm bridge',
    closed: "the middle span missing, a mason's crane and stacked blocks",
    open: 'the span closed, banners on the posts',
    pictogram: 'broken arch',
    barriers: [
      {
        region: 'west',
        zone: 'scorch',
        what: 'the long bridge at the north edge of the Scorched Pass',
        stand: 'bridge',
        ports: ['hearthold|scorch'],
        planned: true,
      },
    ],
    opens: { zones: ['hearthold', 'caldera', 'springs'], plannedZones: [], lines: [] },
    after: 'desert-line',
    task: { kind: 'in-all', minutes: 6 * ONE_HOUR },
    grass: 350,
    resident: 'the masons',
    companion: {
      closed: 'the bridge is missing its middle. if we rest a while, the masons will close it.',
      opened: 'while you were away, the masons closed the bridge. the castle is across.',
    },
    welcome: 'THE CHASM BRIDGE IS WHOLE',
  },
  {
    id: 'maglev',
    label: 'W7',
    kind: 'line',
    name: 'the maglev',
    closed: "the terminus dark, the car's glass dusty, the pump house cold",
    open: "lit and humming, the pump house's stack smoking",
    pictogram: 'dark car',
    barriers: [
      {
        // today the terminus stands on the canal and the maglev leaves from the
        // junction's platform (travelPoints.steam); the plan gives it its own zone
        region: 'steam',
        zone: 'canal',
        what: 'the dark terminus and its cold pump house',
        stand: 'terminus',
        stop: 'steam',
        plannedZone: 'terminus',
        planned: true,
      },
    ],
    opens: {
      zones: [
        'skyport',
        'neon',
        'point',
        'market',
        'downtown',
        'docks',
        'heights',
        'plaza',
        'waterfront',
      ],
      plannedZones: [],
      lines: [['steam', 'neon']],
    },
    after: 'valley-train',
    // "an evening without the phone"
    task: { kind: 'evening', minutes: 2 * ONE_HOUR, ...EVENING },
    grass: 450,
    resident: 'the clerk',
    companion: {
      closed: "the maglev's dark. if we rest a while, i bet the clerk lights it up.",
      opened: "while you were away, the maglev lit up. it's humming.",
    },
    welcome: 'THE MAGLEV IS HUMMING',
  },
  {
    id: 'elevator',
    label: 'W8',
    kind: 'line',
    name: 'the space elevator',
    closed: 'the capsule parked, the ribbon unlit',
    open: 'the ribbon lit, the capsule cycling',
    pictogram: 'ribbon',
    barriers: [
      {
        region: 'neon',
        zone: 'skyport',
        what: "the anchor at the end of the Skyport's pier",
        stand: 'anchor',
        stop: 'neon',
        planned: true,
      },
    ],
    opens: { zones: ['station'], plannedZones: [], lines: [['neon', 'space']] },
    after: 'maglev',
    task: { kind: 'days', days: 7, minutesEachDay: ONE_HOUR },
    grass: 700,
    resident: 'a porter',
    companion: {
      closed: "the capsule's parked. if we rest a while, i bet the ribbon lights up.",
      opened: "while you were away, the ribbon lit up. the capsule's climbing.",
    },
    welcome: 'THE SPACE ELEVATOR IS CLIMBING',
  },
  {
    id: 'shuttle',
    label: 'W9',
    kind: 'line',
    name: 'the shuttle',
    closed: 'the shuttle under a cover, a star chart with a gap',
    open: 'the hatch lit, the chart complete',
    pictogram: 'covered shuttle',
    barriers: [
      {
        region: 'space',
        zone: 'station',
        what: 'the hatch at the top of Halcyon',
        stand: 'shuttle',
        stop: 'space',
        planned: true,
      },
    ],
    opens: { zones: ['lumen'], plannedZones: [], lines: [['space', 'moon']] },
    after: 'elevator',
    task: { kind: 'long', rests: 3, minutesEach: LONG_REST },
    grass: 900,
    resident: 'the station botanist',
    companion: {
      closed:
        "the shuttle's under its cover. if we rest a while, the botanist will finish the chart.",
      opened: "while you were away, the star chart got its last star. the shuttle's ready.",
    },
    welcome: 'THE SHUTTLE IS READY',
  },
  {
    id: 'mine-cart',
    label: 'S1',
    kind: 'shortcut',
    name: 'the mine cart',
    closed: 'the cart line quiet, the tubs standing in the bay',
    open: 'the carts rolling through the mesa',
    pictogram: 'ore tub',
    barriers: [
      {
        region: 'west',
        zone: 'gulch',
        what: "the cart bay at the mine mouth, through the mesa to the caldera's",
        stand: 'mine',
        stop: 'west',
        planned: true,
      },
    ],
    // until it opens: walk over the chasm bridge and through the castle
    opens: { zones: [], plannedZones: [], lines: [['west', 'lava']] },
    after: 'chasm-bridge',
    task: null,
    grass: 100,
    resident: null,
    companion: {
      closed: "the cart line's quiet. we can walk over the bridge.",
      opened: 'while you were away, the mine carts got rolling again.',
    },
    welcome: 'THE MINE CARTS ARE ROLLING',
  },
  {
    // world-plan.md lists it among the shortcuts (S2: "you walk round the pond");
    // world-unlocks.md 2.1 names "a boat on the millpond" as a comfort
    id: 'millpond-boat',
    label: 'S2',
    kind: 'comfort',
    name: 'a rowing boat on the millpond',
    closed: 'no boat on the pond',
    open: 'a rowing boat tied at the bank',
    pictogram: 'rowing boat',
    barriers: [
      {
        region: 'valley',
        zone: 'riverside',
        what: 'the millpond above the mill',
        stand: 'mill',
        planned: true,
      },
    ],
    opens: { zones: [], plannedZones: [], lines: [] },
    after: null,
    task: null,
    grass: 60,
    resident: 'the miller',
    companion: {
      closed: 'a boat would be nice on the millpond.',
      opened: "while you were away, a little boat turned up on the millpond. let's row.",
    },
    welcome: 'A ROWING BOAT ON THE MILLPOND',
  },
  {
    id: 'coastal-steamer',
    label: 'S3',
    kind: 'shortcut',
    name: 'the coastal steamer',
    closed: 'no steamer calls at the waterfront',
    open: 'the steamer at the waterfront, smoke up',
    pictogram: 'steamer',
    barriers: [
      {
        region: 'neon',
        zone: 'waterfront',
        what: "a steamer stop on Neon's waterfront",
        stand: 'promenade',
        planned: true,
      },
    ],
    // until it opens: ride back by maglev and train
    opens: {
      zones: [],
      plannedZones: [],
      lines: [],
      plannedLine: { from: 'waterfront', to: 'harbour' },
    },
    after: 'maglev',
    task: null,
    grass: null,
    resident: null,
    companion: {
      closed: 'a boat home by sea would be nice one day.',
      opened: 'while you were away, a steamer started calling. we can sail home.',
    },
    welcome: 'THE STEAMER CALLS AT DRIFTWOOD',
    proposal: true,
  },
  {
    id: 'ridge-lanterns',
    label: 'S4',
    kind: 'comfort',
    name: 'lanterns on the ridge trail',
    closed: 'the trail dark at night',
    open: 'lanterns lit along the trail at night',
    pictogram: 'lantern',
    barriers: [
      {
        region: 'valley',
        zone: 'ridge',
        what: 'the ridge trail',
        planned: true,
      },
    ],
    opens: { zones: [], plannedZones: [], lines: [] },
    after: null,
    task: null,
    grass: 40,
    resident: null,
    companion: {
      closed: 'the trail gets dark at night. lanterns would be cosy.',
      opened: 'while you were away, someone hung lanterns on the ridge trail.',
    },
    welcome: 'LANTERNS ON THE RIDGE TRAIL',
  },
];

/** The places open from the first minute: the valley's heart (world-unlocks.md 2.1,
 *  world-plan.md 4). Driftwood's lane and footbridge lie in the top strip of the
 *  `headland` zone (`strips`); the rest of that zone is behind W1. */
export const alwaysOpen = {
  zones: [
    'garden',
    'home',
    'woodland',
    'riverside',
    'town',
    'park',
    'halt',
    'ridge',
    'harbour',
  ] as readonly TileId[],
  stops: ['valley', 'pier'] as readonly StopId[],
  /** Open ground inside a zone that otherwise lies behind a way, in zone pixels
   *  (x0, y0, x1, y1): the coast loop's lane along the Headland's top strip, from the
   *  estuary footbridge to the park, north of the wall with W1's stile (planned). */
  strips: [
    {
      zone: 'headland',
      rect: [0, 0, 320, 96],
      what: 'the lane from the estuary footbridge to the park',
    },
  ] as readonly { zone: TileId; rect: readonly [number, number, number, number]; what: string }[],
} as const;

/** True when a point of a zone lies on an always-open strip of it (edges included). */
export function onOpenStrip(zone: string, at: readonly [number, number]): boolean {
  return alwaysOpen.strips.some(
    (s) =>
      s.zone === zone &&
      at[0] >= s.rect[0] &&
      at[0] <= s.rect[2] &&
      at[1] >= s.rect[1] &&
      at[1] <= s.rect[3],
  );
}

export const wayIds: readonly WayId[] = worldWays.map((w) => w.id);

const byId = new Map<string, WorldWay>(worldWays.map((w) => [w.id, w]));

export const isWayId = (id: string): id is WayId => byId.has(id);

/** A way by id; undefined for an unknown id (a save may keep ids from a later build). */
export const wayById = (id: string): WorldWay | undefined => byId.get(id);

/** The ways on the road (lines and areas), W1 to W9. */
export const roadWays: readonly WorldWay[] = worldWays.filter(
  (w) => w.kind === 'line' || w.kind === 'area',
);

/** Every way that must open before `id` comes in reach, earliest first. */
export function prerequisites(id: string): WayId[] {
  const out: WayId[] = [];
  const seen = new Set<string>([id]);
  for (let w = byId.get(id); w?.after && !seen.has(w.after); w = byId.get(w.after)) {
    seen.add(w.after);
    out.unshift(w.after);
  }
  return out;
}

/** True when the zone is open from the start. */
export const isAlwaysOpen = (zone: string): boolean =>
  (alwaysOpen.zones as readonly string[]).includes(zone);

/** The way a zone lies behind (planned zones too); null when it is always open or
 *  unknown. */
export function wayForZone(zone: string): WorldWay | null {
  return (
    worldWays.find(
      (w) =>
        (w.opens.zones as readonly string[]).includes(zone) ||
        (w.opens.plannedZones as readonly string[]).includes(zone),
    ) ?? null
  );
}

const samePair = (line: readonly [string, string], a: string, b: string) =>
  (line[0] === a && line[1] === b) || (line[0] === b && line[1] === a);

/** The way that runs the journey line between two stops, in either direction. */
export function wayForLine(a: string, b: string): WorldWay | null {
  return worldWays.find((w) => w.opens.lines.some((l) => samePair(l, a, b))) ?? null;
}

/** The zones behind a way, drawn and planned. */
export function zonesBehind(id: string): string[] {
  const w = byId.get(id);
  return w ? [...w.opens.zones, ...w.opens.plannedZones] : [];
}

/** The drawn zones walkable with these ways open (unknown ids ignored). */
export function openZones(open: Iterable<string>): TileId[] {
  const out = new Set<TileId>(alwaysOpen.zones);
  for (const id of open) for (const z of byId.get(id)?.opens.zones ?? []) out.add(z);
  return [...out];
}

/** The journey lines that run with these ways open. */
export function openLines(open: Iterable<string>): (readonly [StopId, StopId])[] {
  const set = new Set(open);
  return travelLinks.filter(([a, b]) => {
    const w = wayForLine(a, b);
    return !w || set.has(w.id);
  });
}

/** The closed ways whose way before is open (or that need none), in catalogue order. */
export function waysInReach(open: Iterable<string>): WayId[] {
  const set = new Set(open);
  return worldWays
    .filter((w) => !set.has(w.id) && (w.after === null || set.has(w.after)))
    .map((w) => w.id);
}

/**
 * The ways a player must have had open to stand in these zones: the way each zone lies
 * behind and every way before it (a player who walked in Neon Harbour had the valley
 * train and the maglev). Geometry for the legacy migration in world-unlocks.md 4; the
 * migration itself is Codex's.
 */
export function waysToReach(zones: Iterable<string>): WayId[] {
  const need = new Set<string>();
  for (const zone of zones) {
    const w = wayForZone(zone);
    if (!w) continue;
    need.add(w.id);
    for (const p of prerequisites(w.id)) need.add(p);
  }
  return wayIds.filter((id) => need.has(id));
}

const duration = (minutes: number, long: boolean) =>
  minutes % ONE_HOUR === 0
    ? long
      ? `${minutes / ONE_HOUR} hours`
      : `${minutes / ONE_HOUR} h`
    : `${minutes} min`;

/** The task as the game words it (world-unlocks.md 2.3 and 2.4); the card shows it
 *  uppercase. */
export function taskWords(task: RestTask): string {
  switch (task.kind) {
    case 'one-rest':
      return `one rest of ${duration(task.minutes, false)}`;
    case 'in-all':
      return `${duration(task.minutes, true)} of rest in all`;
    case 'days':
      return `${task.minutesEachDay === ONE_HOUR ? 'an hour' : duration(task.minutesEachDay, false)} of rest on ${task.days} different days`;
    case 'evening':
      return `an evening rest of ${duration(task.minutes, false)}`;
    default:
      // 'long'
      return `a long rest of ${duration(task.minutesEach, false)}, on ${task.rests} different days`;
  }
}
