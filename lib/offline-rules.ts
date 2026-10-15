export const PLAY_LIMIT_MS = 3 * 60 * 1000;
export const PLAY_WINDOW_MS = 30 * 60 * 1000;
export const budgetVoice = "that's enough phone for now. go touch grass. i'll guard the garden.";
export type GardenDay = {
  offline: number;
  cards: number;
  grass: number;
  blocked: number;
  raids: number;
  sparringWins: number;
};
const gardenDayFields: (keyof GardenDay)[] = [
  'offline',
  'cards',
  'grass',
  'blocked',
  'raids',
  'sparringWins',
];
export type PlayBudget = { startedAt: number; usedMs: number };
export type OfflineRules = {
  budget: PlayBudget;
  days: Record<string, GardenDay>;
  recapDay: string;
  checkedDay: string;
  togetherBadges: number;
};
export function dayKey(at = Date.now()) {
  const d = new Date(at);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
export function previousDay(key: string) {
  const d = new Date(`${key}T12:00:00`);
  d.setDate(d.getDate() - 1);
  return dayKey(d.getTime());
}
function weekKey(key: string) {
  const d = new Date(`${key}T12:00:00`);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return dayKey(d.getTime());
}
export function emptyDay(): GardenDay {
  return { offline: 0, cards: 0, grass: 0, blocked: 0, raids: 0, sparringWins: 0 };
}
export function freshRules(now = Date.now()): OfflineRules {
  return {
    budget: { startedAt: 0, usedMs: 0 },
    days: {},
    recapDay: '',
    checkedDay: dayKey(now),
    togetherBadges: 0,
  };
}
export function bumpDay(rules: OfflineRules, key: string, patch: Partial<GardenDay>): OfflineRules {
  const day = { ...emptyDay(), ...rules.days[key] };
  for (const field of gardenDayFields) day[field] += patch[field] ?? 0;
  return { ...rules, days: { ...rules.days, [key]: day } };
}
export function advanceBudget(budget: PlayBudget, now: number, elapsedMs: number): PlayBudget {
  if (budget.startedAt && now - budget.startedAt >= PLAY_WINDOW_MS) {
    elapsedMs = Math.min(elapsedMs, (now - budget.startedAt) % PLAY_WINDOW_MS);
    budget = { startedAt: 0, usedMs: 0 };
  }
  if (elapsedMs <= 0) return budget;
  return {
    startedAt: budget.startedAt || now - elapsedMs,
    usedMs: Math.min(PLAY_LIMIT_MS, budget.usedMs + elapsedMs),
  };
}
export function remainingPlay(budget: PlayBudget, now = Date.now()) {
  return budget.startedAt && now - budget.startedAt >= PLAY_WINDOW_MS
    ? 180
    : Math.max(0, Math.ceil((PLAY_LIMIT_MS - budget.usedMs) / 1000));
}
// Offline MIN are existing demo seconds. Split elapsed time at local midnight.
export function recordOffline(
  rules: OfflineRules,
  start: number,
  minutes: number,
  grass: number,
): OfflineRules {
  let at = start;
  let left = minutes;
  while (left > 0) {
    const d = new Date(at);
    d.setHours(24, 0, 0, 0);
    const chunk = Math.min(left, Math.max(1, Math.ceil((d.getTime() - at) / 1000)));
    rules = bumpDay(rules, dayKey(at), {
      offline: chunk,
      grass: minutes ? (grass * chunk) / minutes : 0,
    });
    at += chunk * 1000;
    left -= chunk;
  }
  return rules;
}
export function gardenStreak(rules: OfflineRules, today = dayKey()) {
  const keys = Object.keys(rules.days).sort();
  let streak = 0;
  let forgiven = false;
  const weeks = new Set<string>();
  if (!keys.length) return { streak, forgiven };
  let key = keys[0];
  while (key <= today) {
    if ((rules.days[key]?.offline ?? 0) >= 120) streak++;
    else if (key < today && streak > 0) {
      const week = weekKey(key);
      if (!weeks.has(week)) {
        weeks.add(week);
        if (key === previousDay(today)) forgiven = true;
      } else streak = 0;
    }
    const d = new Date(`${key}T12:00:00`);
    d.setDate(d.getDate() + 1);
    key = dayKey(d.getTime());
  }
  return { streak, forgiven };
}
export function sparringReward(day: GardenDay, won: boolean) {
  return won && day.sparringWins < 3 ? 5 : 0;
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}
export function isOfflineRules(value: unknown): value is OfflineRules {
  if (!isRecord(value) || !isRecord(value.budget)) return false;
  return (
    typeof value.budget.startedAt === 'number' &&
    typeof value.budget.usedMs === 'number' &&
    typeof value.recapDay === 'string' &&
    typeof value.checkedDay === 'string' &&
    typeof value.togetherBadges === 'number' &&
    isRecord(value.days) &&
    Object.values(value.days).every(
      (day) => isRecord(day) && gardenDayFields.every((field) => typeof day[field] === 'number'),
    )
  );
}
