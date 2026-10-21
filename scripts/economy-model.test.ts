import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import {
  economyInputs,
  type EconomyInputs,
  type PlayerPolicy,
  type Scenario,
} from './economy-inputs';
import {
  cappedPay,
  incomingRaidOutcome,
  periodAt,
  qualifiesAsNight,
  realNapCredits,
  simulate,
  total,
} from './economy-model';
import { restRecognitionRules } from '../lib/rest-recognition';
import { renderEconomyReport } from './economy-report';

function fixtureInput(): EconomyInputs {
  const input = structuredClone(economyInputs);
  input.weeks = 1;
  input.initial.dust = 0;
  return input;
}
function fixturePlayer(patch: Partial<PlayerPolicy> = {}): PlayerPolicy {
  return {
    id: 'fixture',
    name: 'Fixture',
    sessions: [],
    visitDays: [],
    visitAt: 19 * 60,
    activeSeconds: 0,
    feedsPerVisit: 0,
    sparWins: [0, 0, 0, 0, 0, 0, 0],
    targetLevel: 1,
    ...patch,
  };
}
function scenario(id: Scenario['id']): Scenario {
  const found = economyInputs.scenarios.find((item) => item.id === id);
  assert.ok(found, `${id}: fixture scenario exists`);
  return found;
}
const today = scenario('today');
const l2 = scenario('l2');
const g10 = scenario('g10');
const tier0 = scenario('tier0');

// Hand-calculated examples, independent of the eight-week report's totals.
const night = fixturePlayer({ sessions: [{ days: [0], at: 23 * 60, minutes: 480 }] });
assert.equal(
  simulate(night, today, fixtureInput()).earned.naps,
  28_800,
  'today pays one per real second',
);
assert.equal(
  simulate(night, l2, fixtureInput()).earned.naps,
  960,
  'L2 pays 480 minutes at Rest 2x',
);
const g10Night = simulate(night, g10, fixtureInput());
assert.equal(g10Night.earned.nights, 60, 'G10 replaces an eight-hour night with one gift');
assert.equal(g10Night.earned.naps, 0, 'the G10 gift has no per-minute pay on top');
assert.equal(g10Night.creditedMinutes, 480, 'a flat gift preserves the night duration');
assert.equal(g10Night.cards, 32, 'a flat gift preserves time-based card progress');

for (const [gross, paid] of [
  [239, 239],
  [240, 240],
  [244, 241],
  [720, 360],
]) {
  assert.equal(
    cappedPay(gross, g10),
    paid,
    `${gross}: G10 full-rate boundary and quarter-rate excess`,
  );
}
const noRhythm = fixtureInput();
noRhythm.rhythm.enabled = false;
const split = simulate(
  fixturePlayer({
    sessions: [
      { days: [0], at: 3 * 60, minutes: 120 },
      { days: [0], at: 10 * 60, minutes: 180 },
    ],
  }),
  g10,
  noRhythm,
);
const unsplit = simulate(
  fixturePlayer({ sessions: [{ days: [0], at: 3 * 60, minutes: 300 }] }),
  g10,
  noRhythm,
);
assert.equal(split.earned.naps, 255, 'sessions share a civil day ceiling');
assert.equal(
  split.earned.naps,
  unsplit.earned.naps,
  'splitting a daytime rest cannot reset its ceiling',
);
const outsideCap = simulate(
  fixturePlayer({
    sessions: [
      { days: [0], at: 3 * 60, minutes: 720 },
      { days: [0], at: 20 * 60, minutes: 480 },
    ],
  }),
  g10,
  noRhythm,
);
assert.equal(outsideCap.earned.naps, 360, '720 daytime minutes pay 240 plus a quarter of 480');
assert.equal(outsideCap.earned.nights, 60, 'night gifts sit outside the daytime ceiling');
assert.equal(
  total(outsideCap.earned),
  420,
  'night and daytime awards combine without replacing each other',
);
const acrossMidnight = simulate(
  fixturePlayer({ sessions: [{ days: [0], at: 23 * 60, minutes: 180 }] }),
  g10,
  fixtureInput(),
);
assert.equal(acrossMidnight.days[0].earned.naps, 60, 'short rest credits its first civil day');
assert.equal(
  acrossMidnight.days[1].earned.naps,
  120,
  'short rest credits the minutes after midnight separately',
);

const partialFocus = fixturePlayer({ sessions: [{ days: [0], at: 8 * 60 + 30, minutes: 90 }] });
assert.equal(
  simulate(partialFocus, l2, fixtureInput()).earned.naps,
  120,
  '30 own minutes plus 60 Focus minutes at 1.5x',
);
assert.equal(
  simulate(partialFocus, g10, fixtureInput()).earned.naps,
  120,
  'G10 retains the approved Focus multiplier',
);
assert.equal(
  periodAt(9 * 60 - 1, fixtureInput()),
  'own',
  'Focus excludes the minute before its start',
);
assert.equal(periodAt(9 * 60, fixtureInput()), 'focus', 'Focus includes its start');
assert.equal(periodAt(17 * 60, fixtureInput()), 'own', 'Focus excludes its end');
const partialRest = fixturePlayer({ sessions: [{ days: [0], at: 22 * 60 + 30, minutes: 120 }] });
assert.equal(
  simulate(partialRest, l2, fixtureInput()).earned.naps,
  210,
  '30 own minutes plus 90 overnight Rest minutes at 2x',
);

assert.equal(
  qualifiesAsNight(23 * 60, 239, fixtureInput()),
  false,
  'a 239-minute rest is below the night threshold',
);
assert.equal(
  qualifiesAsNight(23 * 60, 240, fixtureInput()),
  true,
  'a 240-minute rest meets the night threshold',
);
assert.equal(
  simulate(
    fixturePlayer({ sessions: [{ days: [0], at: 23 * 60, minutes: 239 }] }),
    g10,
    fixtureInput(),
  ).earned.nights,
  0,
);
assert.equal(
  simulate(
    fixturePlayer({ sessions: [{ days: [0], at: 23 * 60, minutes: 240 }] }),
    g10,
    fixtureInput(),
  ).earned.nights,
  60,
);
for (const [start, qualifies] of [
  [19 * 60 + 59, false],
  [20 * 60, true],
  [119, true],
  [120, false],
] as const) {
  assert.equal(
    qualifiesAsNight(start, 240, noRhythm),
    qualifies,
    `${start}: fallback night start uses [20:00, 02:00)`,
  );
}
const disabledRest = fixtureInput();
disabledRest.rhythm.rest.enabled = false;
assert.equal(
  qualifiesAsNight(23 * 60, 240, disabledRest),
  false,
  'a configured rhythm with Rest disabled does not use the no-rhythm fallback',
);
const repeatedNightInput = fixtureInput();
repeatedNightInput.rhythm.rest.start = 20 * 60;
repeatedNightInput.rhythm.rest.end = 8 * 60;
const repeatedNights = simulate(
  fixturePlayer({
    sessions: [
      { days: [0], at: 20 * 60, minutes: 240 },
      { days: [1], at: 4 * 60, minutes: 240 },
    ],
  }),
  g10,
  repeatedNightInput,
);
assert.equal(
  repeatedNights.earned.nights,
  60,
  'the stated one-gift-per-wake-day convention prevents split-night gifts',
);

const book = fixturePlayer({
  sessions: [{ days: [0], at: 18 * 60, minutes: 30, mission: 'book' }],
});
const bookResult = simulate(book, l2, fixtureInput());
assert.equal(bookResult.earned.outings, 60, 'Book Club awards its fixed reward');
assert.equal(bookResult.earned.naps, 0, 'outings replace passive nap earnings');
assert.equal(bookResult.completedOutings, 1, 'a completed outing settles exactly once');
assert.equal(bookResult.cards, 3, 'Book Club earns two time cards and one completion card');
const demoBook = simulate(book, today, fixtureInput());
assert.equal(demoBook.earned.outings, 60, 'the demo clock does not multiply a fixed outing reward');
assert.equal(
  demoBook.creditedMinutes,
  30,
  'a completed demo outing freezes at its deadline despite a longer absence',
);
const earlyBook = simulate(
  fixturePlayer({ sessions: [{ days: [0], at: 18 * 60, minutes: 29, mission: 'book' }] }),
  l2,
  fixtureInput(),
);
assert.equal(total(earlyBook.earned), 0, 'an early outing return awards no Dream Dust');
assert.equal(earlyBook.creditedMinutes, 29, 'early return retains time progress');
assert.equal(earlyBook.earlyOutings, 1);
assert.equal(earlyBook.completedOutings, 0);
const focusedBook = simulate(
  fixturePlayer({ sessions: [{ days: [0], at: 8 * 60 + 45, minutes: 30, mission: 'book' }] }),
  l2,
  fixtureInput(),
);
assert.equal(
  focusedBook.earned.outings,
  75,
  'stated outing convention weights fifteen own and fifteen Focus minutes',
);

const mountain = fixturePlayer({
  sessions: [{ days: [0], at: 18 * 60, minutes: 60, mission: 'mountain' }],
});
const lockedMountain = simulate(mountain, l2, fixtureInput());
assert.equal(lockedMountain.gatedOutings, 1, 'level one retains the Mountain gate');
assert.equal(lockedMountain.completedOutings, 0);
assert.equal(
  lockedMountain.earned.naps,
  60,
  'the stated player policy substitutes a nap for a locked outing',
);
assert.deepEqual(lockedMountain.freeHats, []);
const mountainInput = fixtureInput();
mountainInput.initial.level = 2;
const mountainRun = simulate(
  fixturePlayer({
    sessions: [{ days: [0, 1, 2, 3, 4], at: 18 * 60, minutes: 60, mission: 'mountain' }],
  }),
  l2,
  mountainInput,
);
assert.deepEqual(
  mountainRun.freeHats,
  ['CROWN', 'CAP', 'SHADES', 'TOP HAT'],
  'fixed seed samples unowned hats instead of always taking catalogue order',
);
assert.deepEqual(mountainRun.boughtHats, []);
assert.equal(mountainRun.allHatsDay, 4);
assert.equal(
  mountainRun.earned.outings,
  800,
  'four Mountain rewards at 150, then 150 plus 50 when all hats are owned',
);

const poorInput = fixtureInput();
poorInput.initial.dust = 4;
const spender = fixturePlayer({
  visitDays: [0],
  activeSeconds: 60,
  feedsPerVisit: 1,
  targetLevel: 2,
});
const poor = simulate(spender, l2, poorInput);
assert.equal(poor.balance, 4, 'unaffordable purchases leave the wallet unchanged');
assert.equal(total(poor.spent), 0);
assert.equal(poor.feeds, 0);
assert.equal(poor.level, 1);
const fundedInput = fixtureInput();
fundedInput.initial.dust = 80;
const funded = simulate(spender, l2, fundedInput);
assert.equal(funded.spent.feeding, 5);
assert.equal(funded.spent.levels, 50, 'first level costs 50 times current level one');
assert.equal(funded.spent.hats, 0, 'remaining 25 cannot buy the first 30-cost hat');
assert.equal(funded.balance, 25);
assert.equal(funded.level, 2);
const touchingVisit = simulate(
  fixturePlayer({
    sessions: [{ days: [0], at: 18 * 60, minutes: 60 }],
    visitDays: [0],
    visitAt: 19 * 60,
    targetLevel: 2,
  }),
  l2,
  fixtureInput(),
);
assert.equal(
  touchingVisit.level,
  2,
  'a return settles before a spending visit at exactly the same time',
);
assert.equal(touchingVisit.spent.levels, 50);
assert.equal(touchingVisit.balance, 10);
const levelCardInput = fixtureInput();
levelCardInput.initial.level = 2;
levelCardInput.initial.dust = 250;
levelCardInput.hats = [];
const levelCard = simulate(
  fixturePlayer({ visitDays: [0, 1], targetLevel: 4 }),
  l2,
  levelCardInput,
);
assert.equal(levelCard.level, 4);
assert.equal(
  levelCard.cards,
  1,
  'crossing level three grants Digital Sunset once; the next level grants no card',
);
const fullMoodInput = fixtureInput();
fullMoodInput.initial.dust = 20;
fullMoodInput.initial.mood = 100;
const fullMood = simulate(fixturePlayer({ visitDays: [0], feedsPerVisit: 1 }), l2, fullMoodInput);
assert.equal(fullMood.feeds, 0, 'a full-mood companion cannot consume feed');
assert.equal(fullMood.spent.feeding, 0);
const spars = simulate(
  fixturePlayer({ visitDays: [0], sparWins: [4, 0, 0, 0, 0, 0, 0] }),
  l2,
  fixtureInput(),
);
assert.equal(spars.earned.spars, 15, 'only the first three daily spar wins pay five each');

assert.throws(
  () =>
    simulate(
      fixturePlayer({
        sessions: [
          { days: [6], at: 23 * 60, minutes: 480 },
          { days: [0], at: 6 * 60, minutes: 60 },
        ],
      }),
      l2,
      fixtureInput(),
    ),
  /must not overlap/,
  'schedule validation catches overnight overlap across the Sunday-to-Monday seam',
);
assert.throws(
  () => simulate(fixturePlayer({ visitDays: [0], activeSeconds: 181 }), l2, fixtureInput()),
  /three-minute play budget/,
  'spending policies cannot exceed the existing play allowance',
);

// C40: independently calculated real-minute limits and foreground boundaries.
assert.equal(
  simulate(night, tier0, fixtureInput()).earned.naps,
  480,
  'eight real hours pay 480, not 28,800 demo units or L2 protected-hour pay',
);
const longNap = simulate(
  fixturePlayer({ sessions: [{ days: [0], at: 0, minutes: 900 }] }),
  tier0,
  fixtureInput(),
);
assert.equal(longNap.earned.naps, 720, 'one 15-hour nap stops at 12 credited hours');
assert.equal(longNap.creditedMinutes, 720, 'cards and mood use accepted credit too');
assert.equal(longNap.cards, 48);
assert.equal(longNap.rejectedCapMinutes, 180);
const splitCap = simulate(
  fixturePlayer({
    sessions: [
      { days: [0], at: 0, minutes: 600 },
      { days: [0], at: 720, minutes: 600 },
    ],
  }),
  tier0,
  fixtureInput(),
);
assert.equal(splitCap.earned.naps, 960, 'two ten-hour naps share the sixteen-hour daily cap');
assert.equal(splitCap.rejectedCapMinutes, 240);
const cappedMidnight = simulate(
  fixturePlayer({ sessions: [{ days: [0], at: 23 * 60, minutes: 900 }] }),
  tier0,
  fixtureInput(),
);
assert.equal(cappedMidnight.days[0].earned.naps, 60);
assert.equal(cappedMidnight.days[1].earned.naps, 660);
assert.equal(cappedMidnight.earned.naps, 720, 'midnight does not reset the ongoing nap cap');
const resetDay = simulate(
  fixturePlayer({
    sessions: [
      { days: [0], at: 0, minutes: 600 },
      { days: [0], at: 650, minutes: 600 },
      { days: [1], at: 0, minutes: 180 },
    ],
  }),
  tier0,
  fixtureInput(),
);
assert.equal(resetDay.days[0].earned.naps, 960);
assert.equal(resetDay.days[1].earned.naps, 180, 'a new day restores daily room');
for (const [foregroundMinutes, paid] of [
  [0, 10],
  [0.5, 10],
  [1, 10],
  [1.5, 9.5],
  [10, 1],
]) {
  const r = simulate(
    fixturePlayer({ sessions: [{ days: [0], at: 0, minutes: 10, foregroundMinutes }] }),
    tier0,
    fixtureInput(),
  );
  assert.equal(r.earned.naps, paid, `${foregroundMinutes} foreground minutes, one-minute grace`);
  assert.equal(r.rejectedForegroundMinutes, 10 - paid);
}
const presetDays = [restRecognitionRules.maxDayMinutes - 5];
const clipped = realNapCredits(0, 20, 10, presetDays, 1440);
assert.equal(clipped.minutes, 5, 'foreground exclusion and daily room reconcile together');
assert.equal(clipped.rejectedForeground, 9);
assert.equal(clipped.rejectedCap, 6);
assert.deepEqual(presetDays, [955], 'the real-minute adapter does not mutate prior-day credits');
const tierMission = simulate(
  fixturePlayer({
    sessions: [{ days: [0], at: 0, minutes: 30, foregroundMinutes: 30, mission: 'book' }],
  }),
  tier0,
  fixtureInput(),
);
assert.equal(tierMission.earned.outings, 60, 'tier-0 foreground rule does not change missions');
assert.equal(tierMission.creditedMinutes, 30);
assert.equal(tierMission.rejectedForegroundMinutes, 0);

// Actual current local-button settlement: gains and losses are never shopping spend.
for (const [balance, loss] of [
  [0, 0],
  [4, 4],
  [10, 10],
  [33, 10],
  [34, 10],
  [100, 30],
  [101, 30],
])
  assert.deepEqual(incomingRaidOutcome(balance, true), { gain: 0, loss });
assert.deepEqual(incomingRaidOutcome(100, false), { gain: 20, loss: 0 });
const raidInput = fixtureInput();
raidInput.initial.dust = 100;
raidInput.hats = [];
raidInput.incomingRaids.enabled = true;
raidInput.incomingRaids.attemptsPerVisit = 10;
raidInput.incomingRaids.attackerWinProbability = 1;
const raided = simulate(fixturePlayer({ visitDays: [0], activeSeconds: 120 }), today, raidInput);
assert.equal(raided.incomingAttempts, 2, 'recovery and active-visit length limit presses');
assert.equal(raided.lostToRaids, 51, '100 loses 30, then 70 loses 21');
assert.equal(raided.balance, 49);
assert.equal(total(raided.spent), 0, 'raid losses are not spending');
assert.equal(raided.days[0].lostToRaids, 51);
raidInput.incomingRaids.attackerWinProbability = 0;
const defended = simulate(fixturePlayer({ visitDays: [0], activeSeconds: 120 }), today, raidInput);
assert.equal(defended.defendedRaids, 2);
assert.equal(defended.earned.incomingDefense, 40);
assert.equal(defended.balance, 140);
raidInput.incomingRaids.enabled = false;
assert.equal(
  simulate(fixturePlayer({ visitDays: [0], activeSeconds: 120 }), today, raidInput)
    .incomingAttempts,
  0,
  'default-off produces no attempts/gains/losses',
);
const moodRaidInput = fixtureInput();
moodRaidInput.initial.dust = 100;
moodRaidInput.initial.mood = 100;
moodRaidInput.hats = [];
moodRaidInput.incomingRaids.enabled = true;
moodRaidInput.incomingRaids.attackerWinProbability = 1;
const raidCare = simulate(
  fixturePlayer({ visitDays: [0], activeSeconds: 1, feedsPerVisit: 1 }),
  today,
  moodRaidInput,
);
assert.equal(raidCare.feeds, 1, 'a lost raid reduces mood before feeding is attempted');
assert.equal(raidCare.balance, 65, '100 less 30 lost and 5 feeding');
moodRaidInput.incomingRaids.attackerWinProbability = 0;
assert.equal(
  simulate(
    fixturePlayer({ visitDays: [0], activeSeconds: 1, feedsPerVisit: 1 }),
    today,
    moodRaidInput,
  ).feeds,
  0,
  'successful defense keeps full mood and avoids unnecessary feeding',
);
const hatsWithRaids = structuredClone(mountainInput);
hatsWithRaids.incomingRaids.enabled = true;
hatsWithRaids.hats = mountainInput.hats.map((hat) => ({ ...hat, cost: 1e9 }));
const hatPolicy = fixturePlayer({
  sessions: [{ days: [0, 1, 2, 3, 4], at: 18 * 60, minutes: 60, mission: 'mountain' }],
  visitDays: [0, 1, 2, 3, 4],
  activeSeconds: 60,
});
assert.deepEqual(
  simulate(hatPolicy, tier0, hatsWithRaids).freeHats,
  mountainRun.freeHats,
  'independent raid stream does not consume Mountain hat draws',
);
const differentSeed = structuredClone(mountainInput);
differentSeed.seeds.mountainHats++;
assert.notDeepEqual(
  simulate(
    fixturePlayer({
      sessions: [{ days: [0, 1, 2, 3], at: 18 * 60, minutes: 60, mission: 'mountain' }],
    }),
    l2,
    differentSeed,
  ).freeHats,
  mountainRun.freeHats,
  'a different seed can change hat order',
);
const milestonesInput = fixtureInput();
milestonesInput.initial.dust = 10000;
milestonesInput.weeks = 2;
milestonesInput.hats = [];
const milestones = simulate(
  fixturePlayer({ visitDays: [0, 1, 2, 3, 4, 5, 6], targetLevel: 12 }),
  tier0,
  milestonesInput,
);
assert.deepEqual(milestones.levelDays, { 5: 4, 8: 7, 12: 11 }, 'first purchase day for each level');

// Snapshot contracts read actual declarations without loading the native store.
const source = ts.createSourceFile(
  'game.ts',
  readFileSync(new URL('../lib/game.ts', import.meta.url), 'utf8'),
  ts.ScriptTarget.Latest,
  true,
);
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function productionDeclaration(name: string): Record<string, unknown>[] {
  const declaration = source.statements.find(
    (statement) =>
      ts.isVariableStatement(statement) &&
      statement.declarationList.declarations.some(
        (item) => ts.isIdentifier(item.name) && item.name.text === name,
      ),
  );
  assert.ok(declaration, `${name}: read the current store declaration`);
  const compiled = ts.transpileModule(declaration.getText(source), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const boundary: Record<string, unknown> = {};
  runInNewContext(compiled, { exports: boundary });
  const values: unknown = JSON.parse(JSON.stringify(boundary[name]));
  assert.ok(Array.isArray(values), `${name}: declaration exports an array`);
  return values.map((value: unknown) => {
    assert.ok(isRecord(value), `${name}: each catalogue entry is a record`);
    return value;
  });
}
const productionHats = productionDeclaration('hats');
assert.deepEqual(
  economyInputs.hats,
  productionHats.map(({ id, cost }) => ({ id, cost })),
  'hat snapshot must match the current production catalogue',
);
const productionMissions = productionDeclaration('missions');
assert.deepEqual(
  economyInputs.missions,
  productionMissions.map(({ id, duration, reward, level }) => ({ id, duration, reward, level })),
  'mission snapshot must match current durations, rewards, and level gates',
);

const originalInput = JSON.stringify(economyInputs);
for (const player of economyInputs.players) {
  for (const mode of economyInputs.scenarios) {
    const result = simulate(player, mode);
    assert.deepEqual(
      result,
      simulate(player, mode),
      `${player.id}/${mode.id}: repeated runs are deterministic`,
    );
    assert.equal(result.days.length, 56, 'eight weeks have 56 daily ledger entries');
    assert.equal(
      result.balance,
      economyInputs.initial.dust + total(result.earned) - total(result.spent) - result.lostToRaids,
      'aggregate wallet reconciles with sources and spending',
    );
    assert.equal(
      result.balance,
      result.days.at(-1)?.balance,
      'daily and aggregate closing balances agree',
    );
    for (const day of result.days)
      assert.ok(
        day.balance >= 0,
        `${player.id}/${mode.id}/day ${day.day}: wallet stays nonnegative`,
      );
    assert.equal(
      result.days.reduce((sum, day) => sum + total(day.earned), 0),
      total(result.earned),
      'daily earnings reconcile',
    );
    assert.equal(
      result.days.reduce((sum, day) => sum + total(day.spent), 0),
      total(result.spent),
      'daily spending reconciles',
    );
    const incoming = structuredClone(economyInputs);
    incoming.incomingRaids.enabled = true;
    const sensitivity = simulate(player, mode, incoming);
    assert.deepEqual(sensitivity, simulate(player, mode, incoming), 'seeded raid run repeats');
    assert.equal(
      sensitivity.balance,
      incoming.initial.dust +
        total(sensitivity.earned) -
        total(sensitivity.spent) -
        sensitivity.lostToRaids,
      'raid sensitivity reconciles',
    );
    assert.equal(sensitivity.balance, sensitivity.days.at(-1)?.balance);
    assert.equal(
      sensitivity.days.reduce((sum, day) => sum + day.lostToRaids, 0),
      sensitivity.lostToRaids,
      'daily raid losses reconcile',
    );
    assert.ok(sensitivity.days.every((day) => day.balance >= 0));
    for (const level of [5, 8, 12] as const) {
      const expectedDay = result.days.find((day) => day.level >= level);
      assert.equal(
        result.levelDays[level],
        expectedDay ? expectedDay.day + 1 : null,
        'milestones agree with independently scanned daily levels',
      );
    }
  }
}
assert.equal(
  JSON.stringify(economyInputs),
  originalInput,
  'simulation never mutates the typed inputs',
);
const report = renderEconomyReport(
  economyInputs,
  economyInputs.scenarios.flatMap((mode) =>
    economyInputs.players.map((player) => simulate(player, mode)),
  ),
);
assert.match(report, /OFF by default/);
assert.match(report, /Policy stops at L5/);
assert.match(report, /TIER0 \/ Light/);
console.log(
  'PASS: economy fixtures, production catalogue contracts, deterministic eight-week ledgers, and wallet reconciliation.',
);
