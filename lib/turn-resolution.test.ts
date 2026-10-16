import assert from 'node:assert/strict';
import { beginTurn, createCombat, resolveMove } from './battle';
import type { Player } from './game';
import { combatTurnId, createTurnResolutionGate } from './turn-resolution';

const player = (id: string): Player => ({
  id,
  code: id,
  name: id,
  pet_name: id,
  species: 'BLOB',
  level: 1,
  grass: 20,
  mood: 80,
  hat: null,
  owned_hats: [],
  mode: 'awake',
  care_until: 0,
  recovery_until: 0,
  mission_id: null,
  mission_ends_at: 0,
  offline_seconds: 0,
  last_seen: 0,
  deck: ['short_walk', 'short_walk', 'stretch'],
  collection: [],
  guardian: null,
  postcards: [],
});
const players = { a: player('a'), d: player('d') };
let current = createCombat(players.a, players.d, () => 0);
current.a = {
  ...current.a,
  hand: ['short_walk', 'short_walk'],
  energy: 3,
  discard: [],
};
const initialHp = current.d.hp;
const gate = createTurnResolutionGate<ReturnType<typeof resolveMove>>();
let resolutions = 0;
const play = () => {
  const result = gate.resolve(combatTurnId(current), () => {
    resolutions++;
    return resolveMove(current, 'short_walk', players, 1, false, () => 0);
  });
  current = result.value.state;
  return result;
};
const first = play();
assert.equal(first.first, true);
assert.equal(current.a.energy, 2);
assert.equal(current.a.hand.filter((id) => id === 'short_walk').length, 1);
assert.deepEqual(current.a.discard, ['short_walk']);
assert.ok(current.d.hp < initialHp);

// Re-enter resolution after committing the model but before animations finish,
// as the old motion-preference dependency did. A duplicate copy of the card is
// still affordable, so replaying resolveMove would otherwise deal damage twice.
for (let replay = 0; replay < 3; replay++) {
  const again = play();
  assert.equal(again.first, false);
  assert.equal(again.value, first.value);
  assert.equal(resolutions, 1);
  assert.equal(current.a.energy, 2);
  assert.deepEqual(current.a.discard, ['short_walk']);
  assert.equal(current.d.hp, first.value.state.d.hp);
}

// The guard belongs to a turn, not the whole battle or a particular card.
current = beginTurn(current, 'd', () => 0).state;
const defender = gate.resolve(combatTurnId(current), () =>
  resolveMove(current, 'pass', players, 1, false, () => 0),
);
assert.equal(defender.first, true);
current = beginTurn(defender.value.state, 'a', () => 0).state;
const next = play();
assert.equal(next.first, true);
assert.equal(resolutions, 2);
assert.ok(current.d.hp < first.value.state.d.hp);

console.log(
  'PASS: turn resolution replays spend one card and roll damage once; later turns still resolve.',
);
