/**
 * The light of the hour over the world (Matt, 21 Oct 13:37: night "a touch darker", with
 * transitions from day to night). Four states, dawn, day, dusk and night, each a tint laid
 * over the world, blended over real time between keyframes: cool and pale at dawn, clear by
 * day, warm and low at dusk, deep blue at night. Lanterns fade in through dusk and out at
 * dawn (`lamps`, 0 to 1, the strength of each zone's night light).
 *
 * With reduced motion there is no blend: the light steps from one state to the next at the
 * state's hour (docs/vision/interface.md). Nothing animates by itself: the value follows the
 * clock the caller reads, so it is finite and still while the screen is.
 *
 * Pure, so it can be tested (lib/daylight.test.ts).
 */
export type DayPhase = 'night' | 'dawn' | 'day' | 'dusk';

export type Daylight = {
  /** an rgba() colour to lay over the world, or null by day */
  tint: string | null;
  /** how lit the lanterns are, 0 (out) to 1 (lit) */
  lamps: number;
  phase: DayPhase;
};

type Key = { at: number; rgb: readonly [number, number, number]; a: number; lamps: number };

const NIGHT: Key['rgb'] = [20, 24, 62];
const DAWN: Key['rgb'] = [150, 176, 236];
const DAY: Key['rgb'] = [255, 240, 214];
const DUSK: Key['rgb'] = [240, 120, 64];
const LATE: Key['rgb'] = [92, 58, 104];

/** Keyframes over the day (hours, local time). Between two keys every value is blended. */
export const DAYLIGHT_KEYS: readonly Key[] = [
  { at: 0, rgb: NIGHT, a: 0.5, lamps: 1 },
  { at: 5, rgb: NIGHT, a: 0.5, lamps: 1 },
  { at: 6.5, rgb: DAWN, a: 0.2, lamps: 0.5 },
  { at: 7.5, rgb: DAWN, a: 0.12, lamps: 0 },
  { at: 9, rgb: DAY, a: 0, lamps: 0 },
  { at: 16.5, rgb: DAY, a: 0, lamps: 0 },
  { at: 18.5, rgb: DUSK, a: 0.2, lamps: 0.25 },
  { at: 20, rgb: LATE, a: 0.34, lamps: 0.85 },
  { at: 21, rgb: NIGHT, a: 0.5, lamps: 1 },
  { at: 24, rgb: NIGHT, a: 0.5, lamps: 1 },
];

/** The state an hour belongs to (the steps reduced motion shows). */
export function dayPhase(hour: number): DayPhase {
  if (hour < 6 || hour >= 21) return 'night';
  if (hour < 9) return 'dawn';
  if (hour >= 17) return 'dusk';
  return 'day';
}

/** Each state's own light, used without blending under reduced motion. */
const STEPS: Record<DayPhase, { rgb: Key['rgb']; a: number; lamps: number }> = {
  night: { rgb: NIGHT, a: 0.5, lamps: 1 },
  dawn: { rgb: DAWN, a: 0.16, lamps: 0 },
  day: { rgb: DAY, a: 0, lamps: 0 },
  dusk: { rgb: DUSK, a: 0.2, lamps: 0.5 },
};

const rgba = (rgb: readonly number[], a: number) =>
  a <= 0.004
    ? null
    : `rgba(${rgb.map((v) => Math.round(v)).join(',')},${Math.round(a * 1000) / 1000})`;

/** The light at a time of day (`hour` 0 to 24, fractional). */
export function daylight(hour: number, reduced = false): Daylight {
  const h = ((hour % 24) + 24) % 24;
  const phase = dayPhase(h);
  if (reduced) {
    const st = STEPS[phase];
    return { tint: rgba(st.rgb, st.a), lamps: st.lamps, phase };
  }
  let i = 0;
  while (i < DAYLIGHT_KEYS.length - 2 && DAYLIGHT_KEYS[i + 1].at <= h) i++;
  const k0 = DAYLIGHT_KEYS[i];
  const k1 = DAYLIGHT_KEYS[i + 1];
  const t = k1.at === k0.at ? 0 : Math.min(1, Math.max(0, (h - k0.at) / (k1.at - k0.at)));
  const mix = (a: number, b: number) => a + (b - a) * t;
  const rgb = [mix(k0.rgb[0], k1.rgb[0]), mix(k0.rgb[1], k1.rgb[1]), mix(k0.rgb[2], k1.rgb[2])];
  return {
    tint: rgba(rgb, mix(k0.a, k1.a)),
    lamps: Math.round(mix(k0.lamps, k1.lamps) * 100) / 100,
    phase,
  };
}

/** The fractional hour of a time stamp (local time). */
export function hourOf(now: number): number {
  const d = new Date(now);
  return d.getHours() + d.getMinutes() / 60;
}
