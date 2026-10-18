import { residentRoutes } from './resident-routes';
import { zoneIds, ZONE } from './zone-maps';
import type { TileId } from './region-walk';

/** Presentation inputs, supplied explicitly. No clock, location, save or game store. */
export type LifeTime = 'dawn' | 'day' | 'dusk' | 'night';
export type LifeSeason = 'original' | 'spring' | 'summer' | 'autumn' | 'winter';
export type LifeWeather = 'original' | 'clear' | 'rain';
export type LifeKind =
  | 'puff'
  | 'ember'
  | 'spore'
  | 'gull'
  | 'butterfly'
  | 'rain'
  | 'firefly'
  | 'lizard'
  | 'fish'
  | 'leaf';
export type LifeEmitter = Readonly<{ kind: LifeKind; x: number; y: number; seed: number }>;
export type LifeContext = Readonly<{
  zone: TileId;
  /** Local minutes since midnight; the caller chooses the presentation clock. */
  minuteOfDay: number;
  season: LifeSeason;
  weather: LifeWeather;
  /** Aggregate screen focus, app activity and absence of covering sheets/naps. */
  active: boolean;
  quiet: boolean;
  reducedMotion: boolean;
  /** Monotonic elapsed time since this finite batch began; do not reset on a tick. */
  elapsedMs: number;
}>;
export type LifeResident = Readonly<{
  id: string;
  from: Readonly<{ x: number; y: number }>;
  to: Readonly<{ x: number; y: number }>;
}>;
export type LifeBudget = Readonly<{
  emitters: number;
  residents: number;
  framesPerSecond: number;
  batchMs: number;
}>;
export type LifePlan = Readonly<{
  mode: 'off' | 'still' | 'animated';
  time: LifeTime | null;
  budget: LifeBudget;
  framesPerSecond: number;
  remainingMs: number;
  emitters: readonly LifeEmitter[];
  residents: readonly LifeResident[];
}>;

// Engineering ceilings, not measured phone performance or a new game rule.
const NORMAL_BUDGET: LifeBudget = Object.freeze({
  emitters: 24,
  residents: 2,
  framesPerSecond: 12,
  batchMs: 18000,
});
const RAIN_CITY_BUDGET: LifeBudget = Object.freeze({ ...NORMAL_BUDGET, emitters: 32 });

export function lifeBudget(zone: TileId): LifeBudget {
  return zone === 'neon' || zone === 'skyport' ? RAIN_CITY_BUDGET : NORMAL_BUDGET;
}

/** Matches the existing 21:00–06:00 night, subdividing the daylight for routines. */
export function lifeTime(minute: number): LifeTime | null {
  if (!Number.isFinite(minute) || minute < 0 || minute >= 1440) return null;
  if (minute < 360 || minute >= 1260) return 'night';
  if (minute < 540) return 'dawn';
  if (minute < 1080) return 'day';
  return 'dusk';
}

// Presence only: nobody closes a shop, blocks a place or becomes missable.
// All positions and routes continue to belong to resident-routes.ts.
const WORKDAY: readonly LifeTime[] = ['dawn', 'day', 'dusk'];
const RESIDENT_TIMES: Readonly<Record<string, readonly LifeTime[]>> = {
  gardener: WORKDAY,
  baker: ['dawn', 'day'],
  fisher: ['dawn', 'day'],
  keeper: ['dusk', 'night'],
  steward: WORKDAY,
  tinkerer: ['day', 'dusk'],
  boatwoman: WORKDAY,
  cowhand: ['dawn', 'day'],
  saloon: ['day', 'dusk'],
  trader: ['dawn', 'day', 'dusk'],
  smith: ['dawn', 'day'],
  attendant: ['day', 'dusk'],
  vendor: ['dusk', 'night'],
  courier: ['dawn', 'day'],
  porter: WORKDAY,
  farmer: ['dawn', 'day'],
  hiker: ['dawn', 'day'],
  forager: ['dawn', 'day'],
  picnicker: ['day', 'dusk'],
  angler: ['dawn', 'day'],
  botanist: WORKDAY,
};

function inSeason(kind: LifeKind, season: LifeSeason): boolean {
  if (season === 'original') return true;
  if (kind === 'leaf') return season === 'autumn';
  if (kind === 'butterfly' || kind === 'firefly' || kind === 'lizard') return season !== 'winter';
  return true;
}

function selectedKind(e: LifeEmitter, time: LifeTime, weather: LifeWeather): LifeKind | null {
  const dark = time === 'dusk' || time === 'night';
  if (e.kind === 'rain') return weather === 'clear' ? null : 'rain';
  if (e.kind === 'butterfly' || e.kind === 'firefly') {
    if (weather === 'rain') return null;
    return dark ? 'firefly' : 'butterfly';
  }
  if (e.kind === 'lizard' && (dark || weather === 'rain')) return null;
  if ((e.kind === 'gull' || e.kind === 'fish') && time === 'night') return null;
  return e.kind;
}

/**
 * Select from the renderer's EXISTING zoneEmitters(zone, false) catalogue. Requiring
 * candidates avoids duplicating art coordinates or inventing water/shelter spawns.
 * Rain never creates emitters where the catalogue does not already provide them.
 * Returned values are fresh copies; callers cannot mutate the source routes.
 */
export function ambientLife(context: LifeContext, candidates: readonly LifeEmitter[]): LifePlan {
  const budget = lifeBudget(context.zone);
  const time = lifeTime(context.minuteOfDay);
  const off: LifePlan = {
    mode: 'off',
    time,
    budget,
    framesPerSecond: 0,
    remainingMs: 0,
    emitters: [],
    residents: [],
  };
  if (
    !context.active ||
    context.quiet ||
    !time ||
    (context.zone !== 'garden' && !zoneIds.some((id) => id === context.zone)) ||
    !Number.isFinite(context.elapsedMs) ||
    context.elapsedMs < 0 ||
    !['original', 'spring', 'summer', 'autumn', 'winter'].includes(context.season) ||
    !['original', 'clear', 'rain'].includes(context.weather)
  )
    return off;

  const emitters: LifeEmitter[] = [];
  const seen = new Set<string>();
  const perKind = new Map<LifeKind, number>();
  for (const e of candidates) {
    if (
      !Number.isFinite(e.x) ||
      !Number.isFinite(e.y) ||
      !Number.isFinite(e.seed) ||
      e.x < 0 ||
      e.x >= ZONE.width ||
      e.y < 0 ||
      e.y >= ZONE.height
    )
      continue;
    const kind = selectedKind(e, time, context.weather);
    if (!kind || !inSeason(kind, context.season)) continue;
    const key = `${kind}:${e.x}:${e.y}:${e.seed}`;
    // Rain cannot fill every slot and crowd out the animals or a chimney.
    if (seen.has(key) || (perKind.get(kind) ?? 0) >= (kind === 'rain' ? 12 : 4)) continue;
    seen.add(key);
    perKind.set(kind, (perKind.get(kind) ?? 0) + 1);
    emitters.push({ kind, x: e.x, y: e.y, seed: e.seed });
    if (emitters.length === budget.emitters) break;
  }
  const residents: LifeResident[] = [];
  for (const [id, route] of Object.entries(residentRoutes)) {
    // A future resident gets the ordinary workday until its routine is authored.
    if (route.zone !== context.zone || !(RESIDENT_TIMES[id] ?? WORKDAY).includes(time)) continue;
    residents.push({
      id,
      from: { x: route.from[0], y: route.from[1] },
      to: { x: route.to[0], y: route.to[1] },
    });
    if (residents.length === budget.residents) break;
  }
  const moving = !context.reducedMotion && context.elapsedMs < budget.batchMs;
  return {
    mode: moving ? 'animated' : 'still',
    time,
    budget,
    framesPerSecond: moving ? budget.framesPerSecond : 0,
    remainingMs: moving ? budget.batchMs - context.elapsedMs : 0,
    emitters,
    residents,
  };
}
