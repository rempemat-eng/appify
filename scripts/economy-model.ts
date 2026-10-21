import {
  economyInputs,
  type EconomyInputs,
  type Period,
  type PlayerPolicy,
  type Scenario,
} from './economy-inputs';

export type Sources = {
  naps: number;
  outings: number;
  nights: number;
  spars: number;
  wellKept: number;
};
export type Spending = { feeding: number; levels: number; hats: number };
export type DayResult = {
  day: number;
  earned: Sources;
  spent: Spending;
  daytimeGross: number;
  balance: number;
  level: number;
  hats: number;
};
export type Simulation = {
  player: string;
  scenario: string;
  days: DayResult[];
  earned: Sources;
  spent: Spending;
  balance: number;
  level: number;
  boughtHats: string[];
  freeHats: string[];
  allHatsDay: number | null;
  completedOutings: number;
  earlyOutings: number;
  gatedOutings: number;
  creditedMinutes: number;
  cards: number;
  feeds: number;
  visits: number;
};
export const total = (record: Sources | Spending) =>
  Object.values(record).reduce((a, b) => a + b, 0);
const emptySources = (): Sources => ({ naps: 0, outings: 0, nights: 0, spars: 0, wellKept: 0 });
const emptySpending = (): Spending => ({ feeding: 0, levels: 0, hats: 0 });

function inWindow(minute: number, start: number, end: number) {
  return start < end ? minute >= start && minute < end : minute >= start || minute < end;
}

// Slice at actual minute boundaries for midnight and partial protected windows.
function slices(start: number, end: number, run: (at: number, minutes: number) => void) {
  for (let at = start; at < end; ) {
    const next = Math.min(end, Math.floor(at + 1));
    run(at, next - at);
    at = next;
  }
}
export function periodAt(at: number, input: EconomyInputs = economyInputs): Period {
  if (!input.rhythm.enabled) return 'own';
  const day = Math.floor(at / input.minutesPerDay);
  const minute = at - day * input.minutesPerDay;
  for (const period of ['rest', 'focus'] as const) {
    const window = input.rhythm[period];
    // An overnight window belongs to its starting weekday.
    const owner = day - (window.start > window.end && minute < window.end ? 1 : 0);
    if (
      window.enabled &&
      window.days.includes(((owner % 7) + 7) % 7) &&
      inWindow(minute, window.start, window.end)
    )
      return period;
  }
  return 'own';
}
export function qualifiesAsNight(
  start: number,
  minutes: number,
  input: EconomyInputs = economyInputs,
) {
  if (minutes < input.rules.nightMinimumMinutes) return false;
  if (input.rhythm.enabled) return periodAt(start, input) === 'rest';
  return inWindow(
    start % input.minutesPerDay,
    input.rhythm.fallbackNightStart,
    input.rhythm.fallbackNightEnd,
  );
}
export function cappedPay(gross: number, scenario: Scenario) {
  if (scenario.ceiling === null) return gross;
  return (
    Math.min(gross, scenario.ceiling) + Math.max(0, gross - scenario.ceiling) * scenario.excessRate
  );
}

function validateSchedule(player: PlayerPolicy, input: EconomyInputs) {
  if (!Number.isInteger(input.weeks) || input.weeks < 1)
    throw new Error('weeks must be a positive integer');
  if (player.activeSeconds < 0 || player.activeSeconds > 180)
    throw new Error('spending visits must fit the three-minute play budget');
  const intervals: { start: number; end: number }[] = [];
  // Two weeks catch the Sunday to Monday seam, including overnight rests.
  for (let day = 0; day < input.daysPerWeek * 2; day++) {
    for (const session of player.sessions) {
      if (!session.days.includes(day % 7)) continue;
      if (session.minutes <= 0 || session.at < 0 || session.at >= input.minutesPerDay)
        throw new Error('sessions need a valid start and positive duration');
      if (session.mission && !input.missions.some((mission) => mission.id === session.mission))
        throw new Error('unknown outing');
      const start = day * input.minutesPerDay + session.at;
      intervals.push({ start, end: start + session.minutes });
    }
    if (player.visitDays.includes(day % 7)) {
      const start = day * input.minutesPerDay + player.visitAt;
      intervals.push({ start, end: start + player.activeSeconds / 60 });
    }
  }
  intervals.sort((a, b) => a.start - b.start);
  for (let i = 1; i < intervals.length; i++)
    if (intervals[i].start < intervals[i - 1].end)
      throw new Error('rests and spending visits must not overlap');
}

/** A solo ledger, not a store emulator. Rest is explicit; events use fixed civil minutes. */
export function simulate(
  player: PlayerPolicy,
  scenario: Scenario,
  input: EconomyInputs = economyInputs,
): Simulation {
  validateSchedule(player, input);
  const count = input.weeks * input.daysPerWeek;
  const horizon = count * input.minutesPerDay;
  const days: DayResult[] = Array.from({ length: count }, (_, day) => ({
    day,
    earned: emptySources(),
    spent: emptySpending(),
    daytimeGross: 0,
    balance: 0,
    level: input.initial.level,
    hats: 0,
  }));
  const result: Simulation = {
    player: player.name,
    scenario: scenario.name,
    days,
    earned: emptySources(),
    spent: emptySpending(),
    balance: input.initial.dust,
    level: input.initial.level,
    boughtHats: [],
    freeHats: [],
    allHatsDay: null,
    completedOutings: 0,
    earlyOutings: 0,
    gatedOutings: 0,
    creditedMinutes: 0,
    cards: 0,
    feeds: 0,
    visits: 0,
  };
  const owned = new Set<string>();
  let mood = input.initial.mood;
  const nightGifts = new Map<number, number>();
  type Event = { at: number; priority?: number; run: () => void };
  const events: Event[] = [];
  const dayAt = (at: number) => Math.min(count - 1, Math.floor(at / input.minutesPerDay));
  const credit = (day: number, source: keyof Sources, amount: number) => {
    days[day].earned[source] += amount;
    result.earned[source] += amount;
    result.balance += amount;
  };
  const daytime = (day: number, source: 'naps' | 'outings', gross: number) => {
    const before = days[day].daytimeGross;
    days[day].daytimeGross += gross;
    credit(day, source, cappedPay(before + gross, scenario) - cappedPay(before, scenario));
  };
  const spend = (day: number, sink: keyof Spending, cost: number) => {
    if (result.balance < cost) return false;
    result.balance -= cost;
    result.spent[sink] += cost;
    days[day].spent[sink] += cost;
    return true;
  };
  const checkHats = (day: number) => {
    if (owned.size === input.hats.length && result.allHatsDay === null) result.allHatsDay = day + 1;
  };
  const multiplier = (at: number) => {
    const period = periodAt(at, input);
    return period === 'rest'
      ? scenario.restMultiplier
      : period === 'focus'
        ? scenario.focusMultiplier
        : 1;
  };
  for (let day = 0; day < count; day++) {
    for (const session of player.sessions) {
      if (!session.days.includes(day % 7)) continue;
      const start = day * input.minutesPerDay + session.at;
      const returnAt = Math.min(horizon, start + session.minutes);
      events.push({
        at: start,
        run: () => {
          const mission = input.missions.find((item) => item.id === session.mission);
          const gated = mission && result.level < mission.level;
          if (gated) result.gatedOutings++;
          // A locked outing becomes a plain nap of the offered duration (player policy).
          const outing = gated ? undefined : mission;
          const deadline = outing
            ? start + outing.duration / scenario.creditedMinutesPerRealMinute
            : returnAt;
          const end = Math.min(returnAt, deadline);
          events.push({
            at: end,
            priority: 0, // settle before a spending visit at the exact return time
            run: () => {
              const elapsed = (end - start) * scenario.creditedMinutesPerRealMinute;
              const before = result.creditedMinutes;
              result.creditedMinutes += elapsed;
              result.cards +=
                Math.floor((result.creditedMinutes + 1e-7) / input.rules.cardEveryMinutes) -
                Math.floor((before + 1e-7) / input.rules.cardEveryMinutes);
              mood = Math.min(input.rules.maxMood, mood + elapsed);
              const endDay = dayAt(end);
              if (outing) {
                if (deadline > returnAt) {
                  result.earlyOutings++;
                  return;
                }
                result.completedOutings++;
                result.cards++;
                let reward = outing.reward;
                if (outing.id === 'mountain') {
                  const hat = input.hats.find((item) => !owned.has(item.id));
                  if (hat) {
                    owned.add(hat.id);
                    result.freeHats.push(hat.id);
                    checkHats(endDay);
                  } else reward += input.rules.mountainHatBonus;
                }
                let weighted = 0;
                slices(start, end, (at, minutes) => {
                  weighted += minutes * (input.rules.multiplyOutings ? multiplier(at) : 1);
                });
                daytime(endDay, 'outings', (reward * weighted) / (end - start));
              } else if (
                scenario.nightGift !== null &&
                qualifiesAsNight(start, end - start, input)
              ) {
                const gifts = nightGifts.get(endDay) ?? 0;
                if (gifts < input.rules.nightGiftLimitPerDay) {
                  credit(endDay, 'nights', scenario.nightGift);
                  nightGifts.set(endDay, gifts + 1);
                }
              } else {
                slices(start, end, (at, minutes) =>
                  daytime(
                    dayAt(at),
                    'naps',
                    minutes *
                      scenario.creditedMinutesPerRealMinute *
                      input.rules.napPerMinute *
                      multiplier(at),
                  ),
                );
              }
            },
          });
        },
      });
    }
    if (player.visitDays.includes(day % 7))
      events.push({
        at: day * input.minutesPerDay + player.visitAt,
        run: () => {
          result.visits++;
          mood = Math.max(
            0,
            mood - Math.floor(player.activeSeconds / input.rules.awakeSecondsPerMood),
          );
          credit(
            day,
            'spars',
            Math.min(player.sparWins[day % 7] ?? 0, input.rules.paidSparWinsPerDay) *
              input.rules.sparReward,
          );
          // Eligibility is an external assumption; L2 has no health thresholds yet.
          credit(day, 'wellKept', scenario.wellKeptGift);
          for (let n = 0; n < player.feedsPerVisit; n++) {
            if (mood < input.rules.maxMood && spend(day, 'feeding', input.rules.feedCost)) {
              mood = Math.min(input.rules.maxMood, mood + input.rules.feedMood);
              result.feeds++;
            }
          }
          // Player preference: at most one level and one unowned hat each visit.
          if (
            result.level < player.targetLevel &&
            spend(day, 'levels', input.rules.levelCostFactor * result.level)
          ) {
            result.level++;
            if (result.level === 3) result.cards++;
          }
          const hat = input.hats.find((item) => !owned.has(item.id));
          if (hat && spend(day, 'hats', hat.cost)) {
            owned.add(hat.id);
            result.boughtHats.push(hat.id);
            checkHats(day);
          }
        },
      });
    events.push({
      at: (day + 1) * input.minutesPerDay - 1e-5,
      run: () => {
        days[day].level = result.level;
        days[day].hats = owned.size;
      },
    });
  }
  while (events.length) {
    events.sort((a, b) => a.at - b.at || (a.priority ?? 1) - (b.priority ?? 1));
    events.shift()!.run();
  }
  let balance = input.initial.dust;
  for (const day of days) {
    balance += total(day.earned) - total(day.spent);
    day.balance = balance;
  }
  return result;
}
