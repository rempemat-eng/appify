/**
 * Animals that live (art-faults.md A9): how each placed animal spends the world's shared
 * 36 s clock. Pure planning, no drawing (components/atlas-animals.tsx draws it). An animal
 * stands at the spot its zone gave it (its home) most of the time, showing its idle
 * accents now and then (a sheep lifts its head and chews, a heron preens and strikes, the
 * cat washes and flicks its tail), and, if it moves, walks or swims to a few spots near
 * home (scripts/art/animal_frames.py chose them clear of props, water, walls and cliffs)
 * and back. Every walk eases in and settles; each animal runs on its own phase.
 * Decorative only: nothing here touches the walk grid, taps or the game.
 */
import { type AnimalKind, type ZoneId, zoneAnimalSpots } from '@/lib/zone-maps';

/** The world's shared clock loop (atlas-walk.tsx FLOAT_LOOP); every period divides it. */
export const ANIMAL_LOOP = 36000;

/** Which drawn set: 0 the still facing east, 1 facing west. */
export type AnimalSide = 0 | 1;

/**
 * One stretch of an animal's loop: from `start` to `end` ms it goes from (x0, y0) to
 * (x1, y1) (px from home; the same point while it stands), drawn from `side`, showing
 * frame `frame` of that side, or its walk frames in turn when `frame` is -1.
 */
export type AnimalEvent = readonly [
  start: number,
  end: number,
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  side: AnimalSide,
  frame: number,
];

export type AnimalPlan = { period: number; phase: number; events: AnimalEvent[] };

const MIN_WALK_MS = 700;
const STILL_REST_MS = 6000; // a standing animal's accents come about every 3 s

/** A stable 0..1 from a name, so each animal keeps its own phase. */
export function phaseOf(name: string) {
  let h = 2166136261;
  for (let i = 0; i < name.length; i++) h = Math.imul(h ^ name.charCodeAt(i), 16777619);
  return ((h >>> 0) % 10007) / 10007;
}

/** The accents shown while standing still for `ms` at a point, as events from `t0`. */
function rest(
  kind: AnimalKind,
  t0: number,
  ms: number,
  at: readonly [number, number],
  side: AnimalSide,
  j: number,
): AnimalEvent[] {
  const [x, y] = at;
  const out: AnimalEvent[] = [];
  const n = kind.idle.length;
  const picks =
    n === 0 ? [] : n === 1 ? [kind.idle[0]] : [kind.idle[(2 * j) % n], kind.idle[(2 * j + 1) % n]];
  let t = t0;
  picks.forEach(([frame, hold, times], i) => {
    const length = Math.min(hold * (2 * times - 1), ms * 0.3);
    const at0 = Math.max(t, t0 + ms * (i === 0 ? 0.3 : 0.68) - length / 2);
    if (at0 > t) out.push([t, at0, x, y, x, y, side, 0]);
    const beat = length / (2 * times - 1);
    for (let k = 0; k < 2 * times - 1; k++)
      out.push([at0 + k * beat, at0 + (k + 1) * beat, x, y, x, y, side, k % 2 === 0 ? frame : 0]);
    t = at0 + length;
  });
  if (t < t0 + ms) out.push([t, t0 + ms, x, y, x, y, side, 0]);
  return out;
}

/** The loop of one placed animal: `oid` its object id in `zone`. */
export function animalPlan(zone: ZoneId, oid: string, kind: AnimalKind): AnimalPlan {
  const placed: AnimalSide = kind.faces === 'east' ? 0 : 1;
  const spots = kind.moves === 'still' ? [] : (zoneAnimalSpots[zone]?.[oid] ?? []);
  const name = `${zone}:${oid}`;
  if (spots.length === 0 || kind.walk.length < 2 || kind.speed <= 0) {
    // it stays put: its accents in turn, two to a rest
    const rests = Math.min(3, Math.max(1, Math.ceil(kind.idle.length / 2)));
    const period = STILL_REST_MS * rests;
    const events = Array.from({ length: rests }, (_, j) =>
      rest(kind, j * STILL_REST_MS, STILL_REST_MS, [0, 0], placed, j),
    ).flat();
    return { period, phase: phaseOf(name) * period, events };
  }
  const points: (readonly [number, number])[] = [[0, 0], ...spots, [0, 0]];
  const walks = points.slice(1).map((p, i) => {
    const q = points[i];
    return Math.max(MIN_WALK_MS, (Math.hypot(p[0] - q[0], p[1] - q[1]) / kind.speed) * 1000);
  });
  const walking = walks.reduce((a, b) => a + b, 0);
  const rests = spots.length + 1; // at home, then at each spot
  const restMs = (ANIMAL_LOOP - walking) / rests;
  // the way each walk faces (a walk straight up or down keeps the way it faced)
  const sides: AnimalSide[] = [];
  let side: AnimalSide = placed;
  for (let i = 1; i < points.length; i++) {
    const dx = points[i][0] - points[i - 1][0];
    if (dx > 0) side = 0;
    else if (dx < 0) side = 1;
    sides.push(side);
  }
  // standing at home it faces the way it last walked in (the loop runs on without a turn)
  let facing = sides[sides.length - 1];
  const events: AnimalEvent[] = [];
  let t = 0;
  for (let i = 0; i < rests; i++) {
    events.push(...rest(kind, t, restMs, points[i], facing, i));
    t += restMs;
    const [x0, y0] = points[i];
    const [x1, y1] = points[i + 1];
    events.push([t, t + walks[i], x0, y0, x1, y1, sides[i], -1]);
    t += walks[i];
    facing = sides[i];
  }
  return { period: ANIMAL_LOOP, phase: phaseOf(name) * ANIMAL_LOOP, events };
}

/** Flat numbers (eight to an event) for the UI thread. */
export function flatEvents(plan: AnimalPlan): number[] {
  return plan.events.flatMap((e) => [...e]);
}

/**
 * Where the animal is at clock `ms`: its offset from home (whole px), the side drawn and
 * the frame shown. Runs on the UI thread (a worklet) and in tests.
 */
export function animalAt(
  flat: readonly number[],
  period: number,
  phase: number,
  walk: readonly number[],
  stepMs: number,
  ms: number,
): { x: number; y: number; side: number; frame: number } {
  'worklet';
  const t = (((ms + phase) % period) + period) % period;
  for (let i = 0; i < flat.length; i += 8) {
    if (t < flat[i + 1] || i + 8 >= flat.length) {
      const span = flat[i + 1] - flat[i];
      const k0 = span > 0 ? Math.min(1, Math.max(0, (t - flat[i]) / span)) : 0;
      const k = k0 * k0 * (3 - 2 * k0); // eases in and settles
      const frame =
        flat[i + 7] >= 0
          ? flat[i + 7]
          : walk.length
            ? walk[Math.floor(ms / stepMs) % walk.length]
            : 0;
      return {
        x: Math.round(flat[i + 2] + (flat[i + 4] - flat[i + 2]) * k),
        y: Math.round(flat[i + 3] + (flat[i + 5] - flat[i + 3]) * k),
        side: flat[i + 6],
        frame,
      };
    }
  }
  return { x: 0, y: 0, side: 0, frame: 0 };
}
