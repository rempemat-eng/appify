// Planning only: this module never reads device activity or awards game rewards.
export const RHYTHM_STORAGE_KEY = 'napattack-rhythm-v1';
export const rhythmGroups = ['weekdays', 'weekends'] as const;
export const rhythmPeriods = ['rest', 'focus'] as const;
export type RhythmGroup = (typeof rhythmGroups)[number];
export type PlannedPeriod = (typeof rhythmPeriods)[number];
export type RhythmPeriod = PlannedPeriod | 'own';
export type RhythmWindow = { enabled: boolean; start: string; end: string };
export type RhythmDay = Record<PlannedPeriod, RhythmWindow>;
export type DailyRhythm = {
  version: 1;
  enabled: boolean;
  timezone: 'device';
  weekdays: RhythmDay;
  weekends: RhythmDay;
};

export const periodLabels: Record<RhythmPeriod, string> = {
  rest: 'Rest',
  focus: 'Focus',
  own: 'Own time',
};
export const groupLabels: Record<RhythmGroup, string> = {
  weekdays: 'Weekdays',
  weekends: 'Weekends',
};

export function freshRhythm(): DailyRhythm {
  return {
    version: 1,
    enabled: false,
    timezone: 'device',
    weekdays: {
      rest: { enabled: true, start: '23:00', end: '07:00' },
      focus: { enabled: true, start: '09:00', end: '17:00' },
    },
    weekends: {
      rest: { enabled: true, start: '23:30', end: '08:00' },
      focus: { enabled: false, start: '10:00', end: '12:00' },
    },
  };
}

export function parseRhythmTime(value: string): number | null {
  if (!/^\d{2}:\d{2}$/.test(value)) return null;
  const [hours, minutes] = value.split(':').map(Number);
  return hours < 24 && minutes < 60 ? hours * 60 + minutes : null;
}

export function plannedMinutes(window: RhythmWindow): number {
  if (!window.enabled) return 0;
  const start = parseRhythmTime(window.start);
  const end = parseRhythmTime(window.end);
  return start === null || end === null ? 0 : (end - start + 1440) % 1440;
}

export function ownTimeMinutes(day: RhythmDay): number {
  return Math.max(0, 1440 - plannedMinutes(day.rest) - plannedMinutes(day.focus));
}

export function durationLabel(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `${hours}h${rest ? ` ${rest}m` : ''}`;
}

function groupForDay(day: number): RhythmGroup {
  return day === 0 || day === 6 ? 'weekends' : 'weekdays';
}

export function validateRhythm(plan: DailyRhythm): string[] {
  const issues: string[] = [];
  for (const group of rhythmGroups) {
    for (const period of rhythmPeriods) {
      const window = plan[group][period];
      if (!window.enabled) continue;
      const start = parseRhythmTime(window.start);
      const end = parseRhythmTime(window.end);
      const name = `${groupLabels[group]} ${periodLabels[period]}`;
      if (start === null || end === null)
        issues.push(`${name}: use 24-hour HH:MM times, such as 23:00 and 07:00.`);
      else if (start === end)
        issues.push(
          `${name}: choose different start and end times. A window must be under 24 hours.`,
        );
    }
  }
  if (issues.length) return issues;

  // Validate the repeating week, including Sunday→Monday and Friday→Saturday.
  // Each overnight window belongs to the day on which it starts.
  const week = 7 * 1440;
  const intervals: { start: number; end: number; name: string }[] = [];
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  for (let day = 0; day < 7; day++) {
    const group = day < 5 ? 'weekdays' : 'weekends';
    for (const period of rhythmPeriods) {
      const window = plan[group][period];
      if (!window.enabled) continue;
      const start = day * 1440 + parseRhythmTime(window.start)!;
      const interval = {
        start,
        end: start + plannedMinutes(window),
        name: `${days[day]} ${periodLabels[period]}`,
      };
      intervals.push(interval, { ...interval, start: start + week, end: interval.end + week });
    }
  }
  intervals.sort((a, b) => a.start - b.start);
  for (let i = 1; i < intervals.length; i++) {
    const previous = intervals[i - 1];
    const current = intervals[i];
    if (current.start < previous.end && previous.start < week)
      return [`${previous.name} overlaps ${current.name}. Move a window or switch it off.`];
  }
  return issues;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

// Invalid planner data is kept separate from the player's garden save.
export function restoreRhythm(value: unknown): DailyRhythm | null {
  if (
    !isRecord(value) ||
    value.version !== 1 ||
    typeof value.enabled !== 'boolean' ||
    value.timezone !== 'device'
  )
    return null;
  const weekdays = restoreRhythmDay(value.weekdays);
  const weekends = restoreRhythmDay(value.weekends);
  if (!weekdays || !weekends) return null;
  const plan: DailyRhythm = {
    version: 1,
    enabled: value.enabled,
    timezone: 'device',
    weekdays,
    weekends,
  };
  return validateRhythm(plan).length ? null : plan;
}

function restoreRhythmDay(value: unknown): RhythmDay | null {
  if (!isRecord(value)) return null;
  const rest = restoreRhythmWindow(value.rest);
  const focus = restoreRhythmWindow(value.focus);
  return rest && focus ? { rest, focus } : null;
}

function restoreRhythmWindow(value: unknown): RhythmWindow | null {
  if (
    !isRecord(value) ||
    typeof value.enabled !== 'boolean' ||
    typeof value.start !== 'string' ||
    typeof value.end !== 'string'
  )
    return null;
  return { enabled: value.enabled, start: value.start, end: value.end };
}

type LocalInterval = { start: number; end: number; period: PlannedPeriod };

function localIntervals(plan: DailyRhythm, now: number): LocalInterval[] {
  const today = new Date(now);
  const intervals: LocalInterval[] = [];
  for (let offset = -1; offset <= 8; offset++) {
    const day = new Date(today.getFullYear(), today.getMonth(), today.getDate() + offset);
    for (const period of rhythmPeriods) {
      const window = plan[groupForDay(day.getDay())][period];
      if (!window.enabled) continue;
      const from = parseRhythmTime(window.start)!;
      const to = parseRhythmTime(window.end)!;
      const start = new Date(
        day.getFullYear(),
        day.getMonth(),
        day.getDate(),
        Math.floor(from / 60),
        from % 60,
      ).getTime();
      // Calendar construction follows local daylight-saving changes. No rewards
      // are calculated from the resulting seven- or nine-hour night.
      const end = new Date(
        day.getFullYear(),
        day.getMonth(),
        day.getDate() + (to <= from ? 1 : 0),
        Math.floor(to / 60),
        to % 60,
      ).getTime();
      intervals.push({ start, end, period });
    }
  }
  return intervals;
}

function periodAt(intervals: LocalInterval[], at: number): RhythmPeriod {
  return intervals.find((interval) => at >= interval.start && at < interval.end)?.period ?? 'own';
}

export function rhythmStatus(
  plan: DailyRhythm,
  now = Date.now(),
): {
  current: RhythmPeriod | null;
  next: { period: RhythmPeriod; at: number } | null;
} {
  if (!plan.enabled || !Number.isFinite(now) || validateRhythm(plan).length)
    return { current: null, next: null };
  const intervals = localIntervals(plan, now);
  const current = periodAt(intervals, now);
  const boundaries = [...new Set(intervals.flatMap((interval) => [interval.start, interval.end]))]
    .filter((at) => at > now)
    .sort((a, b) => a - b);
  for (const at of boundaries) {
    const period = periodAt(intervals, at);
    if (period !== current) return { current, next: { period, at } };
  }
  return { current, next: null };
}

export function deviceTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'device local time';
  } catch {
    return 'device local time';
  }
}

function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export function nextTimeLabel(at: number, now = Date.now()): string {
  const date = new Date(at);
  const today = new Date(now);
  const tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
  const day = sameDay(date, today)
    ? ''
    : sameDay(date, tomorrow)
      ? 'tomorrow '
      : `${date.toLocaleDateString(undefined, { weekday: 'short' })} `;
  return `${day}${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}
