/**
 * A deterministic walk through the progression spine (art/story/progression.json) for
 * the C33 economy sim's three resters. Like scripts/economy-model.ts it is a solo
 * ledger, never imported by the game: rests come from each player's explicit schedule in
 * scripts/economy-inputs.ts, Dream Dust from that sim's own day-by-day result (after its
 * feeding, levels and hats), and the ways, chapters, folk and home steps follow the
 * spine's proposed rules. Time is fixed civil minutes from Monday 00:00 of week 1.
 */
import { economyInputs, type PlayerPolicy, type Scenario } from './economy-inputs';
import { simulate } from './economy-model';
import { progression, road, type RegionId, type RestTask, type WayLabel } from '../lib/progression';

export type Policy = 'home' | 'chip';
/** 'linked' honours each way's storyLink (a proposal); 'free' is #95's road as approved. */
export type Road = 'linked' | 'free';
export type Rest = { start: number; end: number; minutes: number };
export type WayOpening = { day: number; by: 'task' | 'dust' };
export type ProgressionRun = {
  player: string;
  scenario: string;
  policy: Policy;
  road: Road;
  weeks: number;
  /** day (1-based) each way opened, and how */
  ways: Partial<Record<WayLabel, WayOpening>>;
  /** day each region's chapters 1 to 3 arrived */
  chapters: Partial<Record<RegionId, number[]>>;
  /** day each folk joined (starters on day 1) */
  folk: Record<string, number>;
  /** day each home step finished (policy 'home') */
  home: Record<string, number>;
  dustEarned: number;
  dustChipped: number;
  dustRefunded: number;
  dustToHome: number;
};

const DAY = 1440;
const dayOf = (at: number) => Math.floor(at / DAY);

/** Every explicit rest in the schedule, in order, over `weeks` weeks. */
export function restsOf(player: PlayerPolicy, weeks: number): Rest[] {
  const rests: Rest[] = [];
  for (let day = 0; day < weeks * 7; day++)
    for (const s of player.sessions)
      if (s.days.includes(day % 7)) {
        const start = day * DAY + s.at;
        rests.push({ start, end: start + s.minutes, minutes: s.minutes });
      }
  return rests.sort((a, b) => a.start - b.start);
}

type WayState = {
  reach: number | null;
  inAll: number;
  best: number;
  evening: number;
  days: Map<number, number>;
  longs: Set<number>;
  paid: number;
};

function minutesAfter(rest: Rest, from: number) {
  return Math.max(0, rest.end - Math.max(rest.start, from));
}

function taskMet(task: RestTask, s: WayState): boolean {
  if (task.kind === 'one-rest') return s.best >= task.minutes;
  if (task.kind === 'in-all') return s.inAll >= task.minutes;
  if (task.kind === 'evening') return s.evening >= task.minutes;
  if (task.kind === 'days')
    return [...s.days.values()].filter((m) => m >= task.minutesEachDay).length >= task.days;
  return s.longs.size >= task.rests;
}

/** Plays one player through the spine under one economy scenario and one Dust policy. */
export function playProgression(
  player: PlayerPolicy,
  scenario: Scenario,
  policy: Policy,
  weeks: number,
  variant: Road = 'linked',
): ProgressionRun {
  const input = { ...economyInputs, weeks };
  const economy = simulate(player, scenario, input);
  const { rules, regions, folk, home } = progression;
  const run: ProgressionRun = {
    player: player.name,
    scenario: scenario.name,
    policy,
    road: variant,
    weeks,
    ways: {},
    chapters: {},
    folk: {},
    home: {},
    dustEarned: economy.days.reduce(
      (sum, d) => sum + Object.values(d.earned).reduce((a, b) => a + b, 0),
      0,
    ),
    dustChipped: 0,
    dustRefunded: 0,
    dustToHome: 0,
  };
  // The first starter is chosen at the first launch; the other two come with the circle.
  const [chosen, ...others] = progression.start.folkChoice;
  run.folk[chosen] = 1;

  const ways = new Map<WayLabel, WayState>(
    road.map((w) => [
      w.id,
      {
        reach: w.after.length || (variant === 'linked' && w.storyLink) ? null : 0,
        inAll: 0,
        best: 0,
        evening: 0,
        days: new Map(),
        longs: new Set(),
        paid: 0,
      },
    ]),
  );
  const open = new Map<WayLabel, number>();
  let lastOpenDay = -1;
  const found = new Map<RegionId, number>();
  for (const r of regions) if (r.opensWith === null) found.set(r.id, 0);
  const pendingFind: { region: RegionId; after: number }[] = [];
  const chapters = new Map<RegionId, number[]>();
  // Dust outside the economy sim's own purchases: what this policy spent, and refunds.
  let spent = 0;
  let homeJob: { id: string; need: number; done: number } | null = null;

  const visits = new Set(player.visitDays);
  const visitTimes: number[] = [];
  for (let day = 0; day < weeks * 7; day++)
    if (visits.has(day % 7)) visitTimes.push(day * DAY + player.visitAt);

  const freeDust = (day: number) =>
    (day === 0 ? economyInputs.initial.dust : economy.days[day - 1].balance) - spent;

  /** Puts every way whose prerequisites (and, linked, story chapter) are met in reach. */
  const bringInReach = (at: number) => {
    for (const way of road) {
      const s = ways.get(way.id)!;
      if (s.reach !== null || !way.after.every((a) => open.has(a))) continue;
      const link = variant === 'linked' ? way.storyLink : undefined;
      if (link) {
        const region = regions.find((r) => r.story === link.story)!.id;
        if ((chapters.get(region)?.length ?? 0) < link.chapter) continue;
      }
      s.reach = at;
    }
  };

  const settle = (rest: Rest) => {
    const endDay = dayOf(rest.end);
    for (const [label, s] of ways) {
      if (s.reach === null || open.has(label) || rest.end <= s.reach) continue;
      const counted = minutesAfter(rest, s.reach);
      s.inAll += counted;
      s.best = Math.max(s.best, counted);
      const startHour = (rest.start % DAY) / 60;
      if (
        rest.start >= s.reach &&
        startHour >= rules.way.eveningFromHour &&
        startHour < rules.way.eveningToHour
      )
        s.evening = Math.max(s.evening, rest.minutes);
      // split at midnight: each calendar day keeps its own minutes
      for (let at = Math.max(rest.start, s.reach); at < rest.end; ) {
        const next = Math.min(rest.end, (dayOf(at) + 1) * DAY);
        s.days.set(dayOf(at), (s.days.get(dayOf(at)) ?? 0) + (next - at));
        at = next;
      }
      const task = road.find((w) => w.id === label)!.task;
      if (task.kind === 'long' && counted >= task.minutesEach) s.longs.add(endDay);
    }
    if (endDay === lastOpenDay) return;
    for (const way of road) {
      const s = ways.get(way.id)!;
      if (s.reach === null || open.has(way.id)) continue;
      const met = taskMet(way.task, s);
      const paid = s.paid >= way.dust && rest.minutes >= rules.way.paidOpensAfterRestMinutes;
      if (!met && !paid) continue;
      open.set(way.id, rest.end);
      lastOpenDay = endDay;
      run.ways[way.id] = { day: endDay + 1, by: met ? 'task' : 'dust' };
      if (met && s.paid > 0) {
        run.dustRefunded += s.paid;
        spent -= s.paid;
      }
      bringInReach(rest.end);
      for (const region of way.opensRegions) pendingFind.push({ region, after: rest.end });
      break;
    }
  };

  const visit = (at: number) => {
    for (const p of pendingFind.splice(0))
      if (p.after <= at) found.set(p.region, at);
      else pendingFind.push(p);
    const day = dayOf(at);
    if (policy === 'chip') {
      const way = road.find((w) => ways.get(w.id)!.reach !== null && !open.has(w.id));
      if (way) {
        const s = ways.get(way.id)!;
        const amount = Math.max(0, Math.min(freeDust(day), way.dust - s.paid));
        s.paid += amount;
        spent += amount;
        run.dustChipped += amount;
      }
    } else if (!homeJob) {
      const next = home.steps.find(
        (step) => !(step.id in run.home) && (step.after === null || step.after in run.home),
      );
      if (next && freeDust(day) >= next.dust) {
        spent += next.dust;
        run.dustToHome += next.dust;
        homeJob = { id: next.id, need: next.restMinutes, done: 0 };
      }
    }
  };

  const chaptersOnDay = new Map<number, number>();
  const chapter = (rest: Rest) => {
    const endDay = dayOf(rest.end);
    if ((chaptersOnDay.get(endDay) ?? 0) >= rules.chapter.perDay) return;
    const long = rest.minutes >= rules.chapter.longRestMinutes;
    const byFinding = regions
      .filter((r) => found.has(r.id))
      .sort((a, b) => found.get(a.id)! - found.get(b.id)!);
    for (const region of byFinding) {
      const at = found.get(region.id);
      if (at === undefined || at > rest.start) continue;
      const done = chapters.get(region.id) ?? [];
      if (done.length === 3) continue;
      const lastDay = done.length ? done[done.length - 1] - 1 : -1;
      if (done.length > 0 && !long && endDay <= lastDay) continue;
      done.push(endDay + 1);
      chapters.set(region.id, done);
      chaptersOnDay.set(endDay, (chaptersOnDay.get(endDay) ?? 0) + 1);
      bringInReach(rest.end);
      const call = progression.start.othersJoin;
      if (region.story === call.story && done.length === call.chapter)
        for (const id of others) run.folk[id] = endDay + 1;
      if (done.length === 3) {
        const f = folk.find((x) => x.joins.kind === 'story' && x.joins.story === region.story);
        if (f) run.folk[f.id] = endDay + 1;
      }
      return; // one chapter per rest, at the region found first
    }
  };

  const events: { at: number; order: number; run: () => void }[] = [];
  for (const rest of restsOf(player, weeks))
    events.push({
      at: rest.end,
      order: 0,
      run: () => {
        settle(rest);
        chapter(rest);
        if (homeJob && policy === 'home') {
          homeJob.done += rest.minutes;
          if (homeJob.done >= homeJob.need) {
            run.home[homeJob.id] = dayOf(rest.end) + 1;
            homeJob = null;
          }
        }
      },
    });
  for (const at of visitTimes) events.push({ at, order: 1, run: () => visit(at) });
  // A visit on hatch day finds the start regions before the first rest.
  events.sort((a, b) => a.at - b.at || a.order - b.order);
  for (const e of events) e.run();
  for (const [region, days] of chapters) run.chapters[region] = days;
  return run;
}

/** Every player under every policy for the given scenarios. */
export function progressionRuns(
  scenarioIds: readonly Scenario['id'][],
  weeks: number,
  roads: readonly Road[] = ['linked', 'free'],
) {
  const runs: ProgressionRun[] = [];
  for (const variant of roads)
    for (const id of scenarioIds) {
      const scenario = economyInputs.scenarios.find((s) => s.id === id)!;
      for (const policy of ['home', 'chip'] as const)
        for (const player of economyInputs.players)
          runs.push(playProgression(player, scenario, policy, weeks, variant));
    }
  return runs;
}
