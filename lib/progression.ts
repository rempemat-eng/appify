import spine from '../art/story/progression.json';
import tales from '../art/story/stories.json';

/**
 * The progression spine and the resident stories as typed data (Claude K, 21 Oct):
 * what unlocks when, from the first launch to the moon Lumen. The data lives in
 * art/story/progression.json and art/story/stories.json; this module only types it and
 * offers lookups. It keeps no state, reads no clock, changes no rule and is not read by
 * the game: everything here is a proposal until Matt decides
 * (docs/story/choices-for-matt.md). The rules that will act on it (way progress, chip-in,
 * refunds, one opening a day, chapters) belong to the store and Codex's modules.
 * Checked by lib/progression.test.ts (`npm run check:progression`); played through by
 * scripts/sim-progression.ts, which writes docs/story/pacing.md.
 */

export type RegionId =
  | 'valley'
  | 'brackens'
  | 'lull'
  | 'frostline'
  | 'cogsworth'
  | 'isles'
  | 'sunstone'
  | 'fire'
  | 'neon'
  | 'halcyon'
  | 'lumen';
export type WayLabel = 'W1' | 'W2' | 'W3' | 'W4' | 'W5' | 'W6' | 'W7' | 'W8' | 'W9';

/** A task of time away, in real minutes (world-unlocks.md 2.3; the same kinds as
 *  lib/world-ways.ts). An evening rest starts between rules.way.eveningFromHour and
 *  eveningToHour. */
export type RestTask =
  | { kind: 'one-rest'; minutes: number }
  | { kind: 'in-all'; minutes: number }
  | { kind: 'days'; days: number; minutesEachDay: number }
  | { kind: 'evening'; minutes: number }
  | { kind: 'long'; rests: number; minutesEach: number };

export type Way = {
  id: WayLabel;
  /** the id in lib/world-ways.ts's catalogue */
  catalogueId: string;
  name: string;
  kind: 'line' | 'area';
  /** a threshold id in lib/world-routes.ts, or null for a journey off the land */
  threshold: string | null;
  /** ways that must be open before this one comes in reach */
  after: WayLabel[];
  task: RestTask;
  /** the Dream Dust price of the other route */
  dust: number;
  /** route stops (lib/world-routes.ts) this way adds to the walkable world */
  opensStops: string[];
  opensRegions: RegionId[];
  resident: string;
  /** PROPOSAL: the way comes in reach only once this story reaches this chapter */
  storyLink?: { story: string; chapter: 1 | 2 | 3; why: string };
};

export type RestSpot = {
  id: string;
  name: string;
  /** a good place for a night's rest */
  night: boolean;
  default?: boolean;
  /** a way that must be open before the spot can be found */
  after?: WayLabel;
};

export type Region = {
  id: RegionId;
  name: string;
  /** the way that opens it, or null when it is open from the start */
  opensWith: WayLabel | null;
  places: string;
  /** the region plan (art/regions/*.json) the map lanes build from; `pr` while it is in review */
  plan: { file: string | null; owner: string; pr: number | null };
  story: string;
  ring: { place: string; rival: string } | null;
  spots: RestSpot[];
};

export type Folk = {
  id: string;
  name: string;
  /** its stone in the woodland circle and its night of Lumen's moon (cast.md) */
  night: number;
  home: RegionId;
  joins: { kind: 'start' } | { kind: 'story'; story: string };
};

export type Outing = {
  id: string;
  name: string;
  region: RegionId;
  spot: string;
  minutes: number;
  dust: number;
  status: 'live' | 'proposal';
  after?: WayLabel;
};

export type HomeStep = {
  id: string;
  name: string;
  dust: number;
  restMinutes: number;
  after: string | null;
};

export type Comfort = {
  id: string;
  catalogueId?: string;
  name: string;
  kind: 'comfort' | 'shortcut';
  region: RegionId;
  /** null while the price is still open */
  dust: number | null;
  after: WayLabel | null;
  afterStory?: string;
};

export type Line = { who: string; text: string };
export type Chapter = {
  n: 1 | 2 | 3;
  title: string;
  /** the rest spot (in its region) where the chapter is set */
  spot: string;
  /** the welcome-back text: what happened while the player was away */
  beat: string;
  lines: Line[];
  /** what stays changed in the world afterwards (presentation only), or null */
  change: string | null;
};
export type Story = {
  id: string;
  region: RegionId;
  resident: string;
  /** the folk who joins when chapter 3 ends */
  apprentice: string;
  title: string;
  theme: string;
  chapters: Chapter[];
  join: { ask: string; joins: string };
  rival: { who: string; invite: string } | null;
  artNeeds: string[];
};

export type Spine = {
  status: 'proposal';
  decided: string[];
  rules: {
    way: {
      oneOpeningPerDay: boolean;
      paidOpensAfterRestMinutes: number;
      eveningFromHour: number;
      eveningToHour: number;
      restsSplitAtMidnight: boolean;
      refundIfTaskWins: boolean;
      storyLinks: { about: string; default: 'linked' | 'free' };
    };
    chapter: {
      about: string;
      minRestMinutes: number;
      longRestMinutes: number;
      perRest: number;
      /** at most this many new chapters in all on one calendar day (a proposal) */
      perDay: number;
    };
    spots: { about: string };
    /** where the app opens: after a rest, and when opened without one */
    reopen: { afterRest: 'spot' | 'home'; otherwise: 'left-off' | 'home'; about: string };
  };
  start: {
    dust: number;
    familiar: string;
    folkChoice: string[];
    /** the two starters not chosen join when this story reaches this chapter */
    othersJoin: { story: string; chapter: 1 | 2 | 3; about: string };
    regionsOpen: RegionId[];
    stopsOpen: string[];
  };
  firstLaunch: { id: string; what: string; line: string }[];
  ways: Way[];
  regions: Region[];
  folk: Folk[];
  outings: Outing[];
  home: { about: string; steps: HomeStep[] };
  comforts: Comfort[];
  journeyEnd: { story: string; folk: string; what: string };
};

const regionIds: readonly string[] = [
  'valley',
  'brackens',
  'lull',
  'frostline',
  'cogsworth',
  'isles',
  'sunstone',
  'fire',
  'neon',
  'halcyon',
  'lumen',
];
const wayLabels: readonly string[] = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9'];
const taskKinds: readonly string[] = ['one-rest', 'in-all', 'days', 'evening', 'long'];

/** The JSON's string fields hold the ids the types promise: checked once on load, so a
 *  typo in the data fails loudly here rather than as an undefined lookup later. */
function isSpine(data: typeof spine): data is typeof spine & Spine {
  return (
    data.status === 'proposal' &&
    data.ways.every(
      (w) =>
        wayLabels.includes(w.id) &&
        taskKinds.includes(w.task.kind) &&
        w.after.every((a) => wayLabels.includes(a)) &&
        w.opensRegions.every((r) => regionIds.includes(r)),
    ) &&
    data.regions.every(
      (r) => regionIds.includes(r.id) && (r.opensWith === null || wayLabels.includes(r.opensWith)),
    ) &&
    data.start.regionsOpen.every((r) => regionIds.includes(r)) &&
    data.folk.every((f) => regionIds.includes(f.home)) &&
    data.outings.every((o) => regionIds.includes(o.region)) &&
    data.comforts.every((c) => regionIds.includes(c.region))
  );
}
function isStories(data: typeof tales): data is typeof tales & { stories: Story[] } {
  return data.stories.every(
    (s) =>
      regionIds.includes(s.region) &&
      s.chapters.length === 3 &&
      s.chapters.every((c, i) => c.n === i + 1),
  );
}
if (!isSpine(spine)) throw new Error('art/story/progression.json does not match its types');
if (!isStories(tales)) throw new Error('art/story/stories.json does not match its types');

export const progression: Spine = spine;
export const stories: readonly Story[] = tales.stories;

/** The road in order (W1 to W9): the order in which ready ways open, one a day. */
export const road: readonly Way[] = progression.ways;
export const wayByLabel = (id: string): Way | undefined => road.find((w) => w.id === id);
export const regionById = (id: string): Region | undefined =>
  progression.regions.find((r) => r.id === id);
export const storyById = (id: string): Story | undefined => stories.find((s) => s.id === id);
export const folkById = (id: string): Folk | undefined => progression.folk.find((f) => f.id === id);

/** Every way before `id` on its chain of prerequisites, nearest last. */
export function waysBefore(id: WayLabel): WayLabel[] {
  const seen: WayLabel[] = [];
  const visit = (label: WayLabel) => {
    for (const before of wayByLabel(label)?.after ?? []) {
      visit(before);
      if (!seen.includes(before)) seen.push(before);
    }
  };
  visit(id);
  return seen;
}

/** The regions open once every way in `open` is open. */
export function openRegions(open: ReadonlySet<string>): RegionId[] {
  return progression.regions
    .filter((r) => r.opensWith === null || open.has(r.opensWith))
    .map((r) => r.id);
}

/** The route stops reachable on foot once every way in `open` is open. */
export function openStops(open: ReadonlySet<string>): string[] {
  const stops = new Set(progression.start.stopsOpen);
  for (const way of road) if (open.has(way.id)) for (const stop of way.opensStops) stops.add(stop);
  return [...stops].sort();
}

/** The task in the words the game shows on a way's card. */
const h = (m: number) => (m % 60 === 0 && m >= 60 ? `${m / 60} h` : `${m} min`);
export function taskWords(task: RestTask): string {
  if (task.kind === 'one-rest') return `one rest of ${h(task.minutes)}`;
  if (task.kind === 'in-all') return `${h(task.minutes)} of rest in all`;
  if (task.kind === 'days')
    return `${task.minutesEachDay === 60 ? 'an hour' : h(task.minutesEachDay)} of rest on ${task.days} different days`;
  if (task.kind === 'evening') return `an evening rest of ${h(task.minutes)}`;
  return `a long rest of ${h(task.minutesEach)}, on ${task.rests} different days`;
}
