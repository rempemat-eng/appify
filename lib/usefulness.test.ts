import assert from 'node:assert/strict';
import {
  appendBreak,
  breakReceipt,
  addTogetherReceiptBonus,
  restoreBreakHistory,
} from './break-history';
import {
  bumpDay,
  dailyProgress,
  dayKey,
  freshRules,
  gardenStreak,
  recordOffline,
} from './offline-rules';
import type { WelcomeReward } from './visitors';

const start = new Date(2026, 9, 15, 23, 59, 50).getTime();
const before = dayKey(start);
const after = dayKey(start + 30000);
const rest = recordOffline(freshRules(start), start, 30, 30);
assert.equal(rest.days[before].offline, 10);
assert.equal(rest.days[after].offline, 20);
assert.equal(rest.days[before].grass, 10);
assert.equal(rest.days[after].grass, 20);
// A late return must not extend a mission past its existing end time.
const missionEnd = start + 15000;
const lateReturn = start + 60000;
const elapsed = Math.floor((Math.min(lateReturn, missionEnd) - start) / 1000);
let mission = recordOffline(freshRules(start), start, elapsed, 0);
mission = bumpDay(mission, dayKey(missionEnd), { grass: 20, cards: 1 });
assert.equal(mission.days[before].offline, 10);
assert.equal(mission.days[after].offline, 5);
assert.equal(mission.days[before].grass, 0);
assert.equal(mission.days[after].grass, 20);
const early = recordOffline(freshRules(start), start, 12, 0);
assert.equal(early.days[before].offline, 10);
assert.equal(early.days[after].offline, 2);
assert.equal(early.days[after].grass, 0);
const boundary = new Date(2026, 11, 31, 23, 59, 59).getTime();
const yearSplit = recordOffline(freshRules(boundary), boundary, 2, 2);
assert.equal(yearSplit.days['2026-12-31'].offline, 1);
assert.equal(yearSplit.days['2027-01-01'].offline, 1);
const chunked = recordOffline(recordOffline(freshRules(start), start, 7, 7), start + 7000, 23, 23);
assert.deepEqual(chunked.days, rest.days);
assert.equal(dailyProgress(4138).value, 120);
assert.equal(dailyProgress(4138).percent, 100);
assert.equal(dailyProgress(4138).total, (4138).toLocaleString());
assert.equal(dailyProgress(119).complete, false);
assert.equal(dailyProgress(120).complete, true);
assert.equal(rest.days[after].offline, 20);
let streak = freshRules(start);
streak = bumpDay(streak, '2026-10-12', { offline: 120 });
streak = bumpDay(streak, '2026-10-13', { offline: 120 });
assert.equal(gardenStreak(streak, '2026-10-15').streak, 2);
assert.equal(gardenStreak(streak, '2026-10-15').forgiven, true);
assert.equal(gardenStreak(streak, '2026-10-16').streak, 0);

const recap: WelcomeReward = {
  settlementId: 'garden:nap:123',
  minutes: 4138,
  grass: 4138,
  cards: ['stretch', 'stretch'],
  mission: null,
  early: false,
  visitor: null,
  postcard: null,
  hat: null,
  sessionId: 'together-1',
};
const receipt = breakReceipt(recap.settlementId!, start, recap);
assert.equal(receipt.cards, 2);
assert.equal(receipt.grass, recap.grass);
assert.equal(receipt.minutes, recap.minutes);
const history = appendBreak([], receipt);
assert.equal(appendBreak(history, receipt), history);
const reloaded = restoreBreakHistory(JSON.parse(JSON.stringify(history)));
assert.deepEqual(appendBreak(reloaded, receipt), history);
assert.deepEqual(restoreBreakHistory(undefined), []);
assert.deepEqual(restoreBreakHistory(null), []);
const earlyReceipt = breakReceipt('early', missionEnd, {
  ...recap,
  mission: 'park',
  early: true,
  minutes: 12,
  grass: 0,
  cards: [],
});
assert.equal(earlyReceipt.early, true);
assert.equal(earlyReceipt.mission, 'park');
assert.equal(earlyReceipt.grass, 0);
const bonusHistory = addTogetherReceiptBonus(history, 'together-1', 10);
assert.equal(bonusHistory.length, 1);
assert.equal(bonusHistory[0].grass, 4148);
assert.equal(history[0].grass, 4138);
assert.deepEqual(addTogetherReceiptBonus(history, 'other', 10), history);
let bounded = history;
for (let i = 0; i < 25; i++)
  bounded = appendBreak(bounded, {
    ...receipt,
    id: `nap:${i}`,
    completedAt: start + (i + 1) * 1000,
  });
assert.equal(bounded.length, 20);
assert.equal(bounded[0].id, 'nap:24');
assert.equal(bounded[19].id, 'nap:5');
assert.equal(bounded.slice(0, 5).length, 5);
assert.deepEqual(restoreBreakHistory([...bounded, ...bounded]), bounded);
assert.equal(recap.grass, 4138);
assert.equal(recap.cards.length, 2);
console.log(
  'PASS: usefulness pure checks — local midnight/year boundary, rest/mission intervals, chunking, goal cap/full total, streak forgiveness, receipts, empty legacy history, reload deduplication, early return, Together receipt bonus and max-20 history.',
);
