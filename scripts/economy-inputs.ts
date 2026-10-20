/** C33 only. These snapshots/assumptions are never imported by the game. */
export type MissionId = 'park' | 'book' | 'mountain';
export type Period = 'rest' | 'focus' | 'own';
export type Session = { days: readonly number[]; at: number; minutes: number; mission?: MissionId };
export type PlayerPolicy = {
  id: string;
  name: string;
  sessions: readonly Session[];
  visitDays: readonly number[];
  visitAt: number;
  activeSeconds: number;
  feedsPerVisit: number;
  sparWins: readonly number[];
  targetLevel: number;
};
export type Scenario = {
  id: 'today' | 'l2' | 'g10';
  name: string;
  creditedMinutesPerRealMinute: number;
  restMultiplier: number;
  focusMultiplier: number;
  nightGift: number | null;
  ceiling: number | null;
  excessRate: number;
  wellKeptGift: number;
};

const weekdays = [0, 1, 2, 3, 4]; // Monday = 0. Fixed civil days, no host clock/DST.
const daily = [0, 1, 2, 3, 4, 5, 6];
export const economyInputs = {
  weeks: 8,
  daysPerWeek: 7,
  minutesPerDay: 1440,
  source: {
    main: '81070e190846f51930ead7f99cb955b14d5f5600',
    proposal: '0aa6661319a204d997fcb0ef558966521377422f',
  },
  initial: { dust: 20, level: 1, mood: 80 },
  rules: {
    napPerMinute: 1,
    levelCostFactor: 50,
    feedCost: 5,
    feedMood: 20,
    maxMood: 100,
    awakeSecondsPerMood: 3,
    sparReward: 5,
    paidSparWinsPerDay: 3,
    mountainHatBonus: 50,
    cardEveryMinutes: 15,
    nightMinimumMinutes: 240,
    // G10 ambiguity: one gift per wake day, never twice for split nights.
    nightGiftLimitPerDay: 1,
    // Assumption: weight fixed outing rewards by time in each window; no passive pay on top.
    multiplyOutings: true,
  },
  hats: [
    { id: 'CAP', cost: 30 },
    { id: 'SHADES', cost: 40 },
    { id: 'TOP HAT', cost: 60 },
    { id: 'CROWN', cost: 150 },
  ],
  missions: [
    { id: 'park', duration: 15, reward: 20, level: 1 },
    { id: 'book', duration: 30, reward: 60, level: 1 },
    { id: 'mountain', duration: 60, reward: 150, level: 2 },
  ],
  rhythm: {
    enabled: true,
    rest: { enabled: true, days: daily, start: 23 * 60, end: 7 * 60 },
    focus: { enabled: true, days: weekdays, start: 9 * 60, end: 17 * 60 },
    fallbackNightStart: 20 * 60,
    fallbackNightEnd: 2 * 60,
  },
  scenarios: [
    {
      id: 'today',
      name: 'Today (demo clock)',
      creditedMinutesPerRealMinute: 60,
      restMultiplier: 1,
      focusMultiplier: 1,
      nightGift: null,
      ceiling: null,
      excessRate: 1,
      wellKeptGift: 0,
    },
    {
      id: 'l2',
      name: 'L2 (real time)',
      creditedMinutesPerRealMinute: 1,
      restMultiplier: 2,
      focusMultiplier: 1.5,
      nightGift: null,
      ceiling: null,
      excessRate: 1,
      wellKeptGift: 0,
    },
    {
      id: 'g10',
      name: 'G10 (proposal)',
      creditedMinutesPerRealMinute: 1,
      restMultiplier: 1,
      focusMultiplier: 1.5,
      nightGift: 60,
      ceiling: 240,
      excessRate: 0.25,
      wellKeptGift: 0,
    },
  ] satisfies Scenario[],
  players: [
    {
      id: 'light',
      name: 'Light',
      sessions: [
        { days: [0, 2, 4], at: 18 * 60, minutes: 30 },
        { days: [1, 3], at: 12 * 60, minutes: 30, mission: 'book' },
        { days: [6], at: 14 * 60, minutes: 60, mission: 'mountain' },
      ],
      visitDays: [0, 1, 2, 3, 4, 6],
      visitAt: 19 * 60,
      activeSeconds: 60,
      feedsPerVisit: 1,
      sparWins: [0, 0, 0, 0, 0, 0, 1],
      targetLevel: 5,
    },
    {
      id: 'regular',
      name: 'Regular',
      sessions: [
        { days: weekdays, at: 10 * 60, minutes: 45 },
        { days: daily, at: 18 * 60, minutes: 30 },
        { days: [5], at: 14 * 60, minutes: 30, mission: 'book' },
        { days: [6], at: 14 * 60, minutes: 60, mission: 'mountain' },
        { days: [0, 2, 4], at: 23 * 60, minutes: 480 },
      ],
      visitDays: daily,
      visitAt: 19 * 60,
      activeSeconds: 90,
      feedsPerVisit: 1,
      sparWins: [1, 0, 1, 0, 1, 0, 1],
      targetLevel: 10,
    },
    {
      id: 'committed',
      name: 'Committed',
      sessions: [
        { days: daily, at: 14 * 60, minutes: 60, mission: 'mountain' },
        { days: daily, at: 18 * 60, minutes: 45 },
        { days: weekdays, at: 23 * 60, minutes: 480 },
      ],
      visitDays: daily,
      visitAt: 19 * 60,
      activeSeconds: 120,
      feedsPerVisit: 1,
      sparWins: [3, 3, 3, 3, 3, 3, 3],
      targetLevel: 20,
    },
  ] satisfies PlayerPolicy[],
};
export type EconomyInputs = typeof economyInputs;
