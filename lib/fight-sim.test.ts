import assert from 'node:assert/strict';
import { families, folk, habitDeckAt, pipsFor, restedCharge, rivals } from '@/lib/fight-content';
import {
  createFight,
  matchup,
  proposedRules,
  rivalSetup,
  runFight,
  signatureCards,
  todayRules,
  type FighterSetup,
} from '@/lib/fight-sim';
import { cards } from '@/lib/cards';

// The content: fourteen folk, four signature cards each, three variant choices at 4, 8, 12.
assert.equal(folk.length, 14, 'fourteen folk (cast.md)');
assert.deepEqual(
  folk.map((f) => f.night),
  Array.from({ length: 14 }, (_, i) => i + 1),
  'one folk a night, in the circle order',
);
const ids = new Set<string>();
for (const f of folk) {
  assert.equal(f.cards.length, 4, `${f.name} has four signature cards`);
  assert.deepEqual(
    f.variants.map((v) => v.level),
    [4, 8, 12],
    `${f.name} has variants at shared levels 4, 8 and 12`,
  );
  for (const c of f.cards) {
    assert.ok(!ids.has(c.id) && !(c.id in cards), `${c.id} is a unique card id`);
    ids.add(c.id);
    assert.ok(c.cost >= 0 && c.cost <= 3, `${c.id} costs 0 to 3 energy`);
  }
  for (const v of f.variants)
    assert.ok(
      f.cards.some((c) => c.id === v.card),
      `${f.name}'s level ${v.level} variant changes one of its own cards`,
    );
}
// Nothing banks past 3, and no passive is a time-of-day or Dream Dust rule.
for (const f of folk) assert.doesNotMatch(f.passive.text, /night bonus|dream dust|o'clock/i);

// Rivals: every ring has a level, its own zen (F4), and only habit cards.
for (const r of rivals) {
  assert.ok(r.level >= 1 && r.level <= 12, `${r.id} has a level`);
  assert.ok(r.zen >= 0 && r.zen <= 0.3, `${r.id} has its own zen`);
  for (const id of r.deck) assert.ok(id in cards, `${r.id} plays habit cards only (${id})`);
}
assert.equal(
  rivals.find((r) => r.id === 'dave')?.family,
  'mirror',
  'Dave mirrors your family (F5)',
);

// The rested special: one pip per 20 minutes of rest since the last spar, at most three.
assert.equal(pipsFor(0), 0);
assert.equal(pipsFor(19), 0);
assert.equal(pipsFor(20), 1);
assert.equal(pipsFor(60), 3);
assert.equal(pipsFor(600), restedCharge.maxPips, 'a longer rest adds nothing');

// Matchup: today's numbers, and the proposal's flat spar.
assert.equal(matchup('REST', 'FOCUS'), 1.5);
assert.equal(matchup('FOCUS', 'REST'), 0.67);
assert.equal(matchup('ROAM', 'ROAM'), 1);
assert.deepEqual(todayRules.matchup, [1.5, 0.67]);
assert.equal(todayRules.drawAtLimit, false, 'today the limit is a loss');
assert.equal(proposedRules.drawAtLimit, true, 'F3: a draw');

// Variants apply only at or above their level.
const bramble = folk[0];
assert.equal(signatureCards(bramble, 3, ['b', 'b', 'b'])[1].name, 'LOOSE');
assert.equal(
  signatureCards(bramble, 4, ['a', 'a', 'a'])[1].cost,
  0,
  'variant A applies its own patch',
);
assert.equal(signatureCards(bramble, 4, ['b', 'a', 'a'])[1].name, 'HEAVY LOOSE');

// Determinism: the same seed gives the same fight.
const me = (fam: (typeof families)[number]): FighterSetup => ({
  name: 'bramble',
  family: fam,
  level: 3,
  zen: 0,
  deck: habitDeckAt(3),
  folk: bramble,
  pips: 3,
  policy: 'smart',
});
const warden = rivals.find((r) => r.id === 'hut_warden');
assert.ok(warden);
const once = () => {
  const fight = createFight(me('ROAM'), rivalSetup(warden, 'ROAM', true), proposedRules, 42);
  const res = runFight(fight);
  return JSON.stringify([res, fight.a.hp, fight.d.hp, fight.a.dealt, fight.d.dealt]);
};
assert.equal(once(), once(), 'a seeded spar is deterministic');

// Every folk finishes a spar against every ring within the round limit, and HP stays sane.
for (const f of folk)
  for (const r of rivals) {
    const fight = createFight(
      { ...me('FOCUS'), folk: f, level: r.level, deck: habitDeckAt(r.level) },
      rivalSetup(r, 'FOCUS', true),
      proposedRules,
      7,
    );
    const res = runFight(fight);
    assert.ok(res.result !== null, `${f.id} against ${r.id} ends`);
    assert.ok(res.turns <= 13, `${f.id} against ${r.id} ends by the round limit`);
    assert.ok(fight.a.hp >= 0 && fight.a.hp <= fight.a.max, `${f.id}'s HP stays in range`);
    assert.ok(fight.a.stack >= 0 && fight.a.stack <= 3, `${f.id}'s stack stays 0 to 3`);
  }

// A raid never dozes: Puffcap's three spores soften instead.
const puffcap = folk.find((f) => f.id === 'puffcap');
assert.ok(puffcap);
const raid = createFight(
  { ...me('REST'), folk: puffcap, policy: 'smart' },
  rivalSetup(warden, 'REST', true),
  { ...todayRules, raid: true },
  3,
);
runFight(raid);
assert.equal(raid.a.dozed, false, 'no doze in a raid against an absent player');

console.log('Fight content and simulation checks passed.');
