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
import { cappedPay, periodAt, qualifiesAsNight, simulate, total } from './economy-model';

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
  ['CAP', 'SHADES', 'TOP HAT', 'CROWN'],
  'deterministic unowned-hat order makes four free grants reproducible',
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
      economyInputs.initial.dust + total(result.earned) - total(result.spent),
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
  }
}
assert.equal(
  JSON.stringify(economyInputs),
  originalInput,
  'simulation never mutates the typed inputs',
);
console.log(
  'PASS: economy fixtures, production catalogue contracts, deterministic eight-week ledgers, and wallet reconciliation.',
);
