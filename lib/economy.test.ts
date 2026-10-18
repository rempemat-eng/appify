import assert from 'node:assert/strict';
import {
  attackingRaidReward,
  RAID_TRANSFER_GRASS,
  safeRaidTransport,
  settleAttackingRaid,
  settleDefendingRaid,
} from './economy';

let checks = 0;
function equal(actual: unknown, expected: unknown, label: string) {
  assert.deepEqual(actual, expected, label);
  checks++;
}

equal(RAID_TRANSFER_GRASS, 0, 'Raids transfer no GRASS between players');
for (const [target, reward] of [
  [0, 0],
  [0.5, 0.5],
  [5, 5],
  [20, 10],
  [100, 30],
  [500, 150],
]) {
  equal(attackingRaidReward(true, target), reward, 'Valid victory payouts retain the old formula');
  equal(attackingRaidReward(false, target), 0, 'A defeat never charges a wallet');
}
for (const target of [-1, NaN, Infinity, -Infinity])
  equal(attackingRaidReward(true, target), 0, 'Invalid rival balances cannot create a payout');

for (const balance of [0, 0.5, 20, 500, -7, Number.MAX_SAFE_INTEGER, Number.MAX_VALUE]) {
  for (const won of [false, true]) {
    const a = settleAttackingRaid(balance, won, 100);
    const d = settleDefendingRaid(balance, won);
    assert.ok(a.balance >= balance && d.balance >= balance, 'No raid settlement lowers a wallet');
    checks++;
    equal(a.transferred, 0, 'An attacking result never debits a rival');
    equal(d.transferred, 0, 'A defending result never transfers a wallet');
    equal(a.earned, a.balance - balance, 'Attacker earnings match the actual wallet change');
    equal(d.earned, d.balance - balance, 'Defender earnings match the actual wallet change');
  }
  equal(
    settleAttackingRaid(balance, false, 100).balance,
    balance,
    'No legacy balance normalisation',
  );
  equal(
    settleDefendingRaid(balance, true).balance,
    balance,
    'Loss preserves the exact saved balance',
  );
}
equal(settleAttackingRaid(17.25, true, 100), { balance: 47.25, earned: 30, transferred: 0 }, 'Win');
equal(settleDefendingRaid(17.25, false), { balance: 37.25, earned: 20, transferred: 0 }, 'Defence');
equal(
  settleAttackingRaid(Number.MAX_VALUE, true, Number.MAX_VALUE),
  { balance: Number.MAX_VALUE, earned: 0, transferred: 0 },
  'Overflow cannot replace an existing wallet with infinity',
);
for (const balance of [NaN, Infinity, -Infinity]) {
  assert.ok(Object.is(settleDefendingRaid(balance, true).balance, balance));
  checks++;
}

const legacy = Object.freeze({
  id: 'old-pending-raid',
  attacker_id: 'a',
  defender_id: 'b',
  created_at: '2026-10-16T12:00:00Z',
  attacker_won: true,
  grass_amount: 300,
  seen_by_defender: false,
  futureMetadata: { preserved: true },
});
equal(safeRaidTransport(legacy), { ...legacy, grass_amount: 0 }, 'Legacy transport has zero debit');
equal(legacy.grass_amount, 300, 'Historical/local legacy record is never rewritten');
equal(
  safeRaidTransport(safeRaidTransport(legacy)),
  safeRaidTransport(legacy),
  'Transport is idempotent',
);

// Deterministic property samples, without changing global Math.random or game state.
for (let i = 0; i < 1000; i++) {
  const balance = i * 17.25;
  const target = (i * 937) % 10001;
  for (const won of [false, true]) {
    const actual = settleAttackingRaid(balance, won, target);
    const priorWin = Math.min(target, Math.max(10, Math.floor(target * 0.3)));
    equal(actual.balance, balance + (won ? priorWin : 0), 'Only the old losing debit changes');
  }
}

console.log(`PASS: ${checks} lossless raid currency and legacy transport assertions.`);
