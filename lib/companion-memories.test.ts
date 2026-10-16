import assert from 'node:assert/strict';
import type { RecentBreak } from './break-history';
import type { Player } from './game';
import {
  breakCompanion,
  isBreakIntention,
  memoryLimit,
  memoryResolutionLimit,
  offerCompanionMemory,
  pendingMemoryLimit,
  restoreActiveBreakContext,
  restoreCompanionMemories,
  restoreMemoryResolutions,
  restorePendingMemories,
  type ActiveBreakContext,
  type CompanionMemory,
} from './companion-memories';

const player: Player = {
  id: 'gardener',
  code: 'ABCD',
  name: 'GARDENER',
  pet_name: 'ORIGINAL',
  species: 'BLOB',
  level: 3,
  grass: 50,
  mood: 80,
  hat: null,
  owned_hats: [],
  mode: 'screen_off',
  care_until: 0,
  recovery_until: 0,
  mission_id: null,
  mission_ends_at: 0,
  offline_seconds: 12,
  last_seen: 0,
  deck: ['stretch'],
  collection: [{ id: 'inkling', metAt: 0, minutes: 15, befriendedAt: 0 }],
  guardian: null,
  postcards: [],
};
const context: ActiveBreakContext = {
  breakId: 'settlement',
  playerId: player.id,
  intention: 'read',
  companion: breakCompanion(player),
  startedAt: 1000,
};
const receipt: RecentBreak = {
  id: context.breakId,
  completedAt: 5000,
  minutes: 4,
  grass: 4,
  cards: 0,
  mission: null,
  early: false,
  sessionId: null,
};
const offers = offerCompanionMemory(context, receipt, [], []);
assert.equal(offers.length, 1);
assert.equal(offers[0].id, receipt.id);
assert.deepEqual(offers[0].companion, { key: 'starter', name: 'ORIGINAL', species: 'BLOB' });
assert.deepEqual(breakCompanion({ ...player, guardian: 'inkling' }), {
  key: 'inkling',
  name: 'INKLING',
  species: 'CUBE',
});
assert.equal(breakCompanion({ ...player, guardian: 'skyfern' }).key, 'starter');
assert.equal(breakCompanion({ ...player, guardian: 'inkling', collection: [] }).key, 'starter');
assert.equal(offers[0].companion.key, 'starter', 'Later selection cannot rewrite the snapshot');
context.companion.name = 'CHANGED AFTER SETTLEMENT';
assert.equal(offers[0].companion.name, 'ORIGINAL', 'Pending memory owns its companion snapshot');
context.companion.name = 'ORIGINAL';
for (const intention of ['rest', 'read', 'move', 'create']) assert.ok(isBreakIntention(intention));
for (const intention of [null, undefined, '', 'sleep', {}, 0])
  assert.equal(isBreakIntention(intention), false);

assert.equal(offerCompanionMemory(null, receipt, [], []).length, 0);
assert.equal(offerCompanionMemory(context, { ...receipt, id: 'other' }, [], []).length, 0);
assert.equal(offerCompanionMemory(context, { ...receipt, minutes: 0 }, [], []).length, 0);
assert.equal(offerCompanionMemory(context, { ...receipt, completedAt: 0 }, [], []).length, 0);
assert.equal(offerCompanionMemory(context, receipt, [], [receipt.id]).length, 0);
assert.equal(offerCompanionMemory(context, receipt, offers, []).length, 1);
const early = offerCompanionMemory(context, { ...receipt, mission: 'book', early: true }, [], []);
assert.equal(
  early[0].early,
  true,
  'An optional early-return reflection does not complete a mission',
);
assert.equal(early[0].mission, 'book');
assert.deepEqual(restoreActiveBreakContext(context, receipt.id, player), context);
for (const bad of [
  undefined,
  [],
  { ...context, playerId: 'another-account' },
  { ...context, breakId: 'stale' },
  { ...context, intention: 'unknown' },
  { ...context, startedAt: -1 },
  { ...context, startedAt: Infinity },
  { ...context, companion: { ...context.companion, key: 'unknown' } },
  { ...context, companion: { ...context.companion, name: '' } },
  { ...context, companion: { key: 'inkling', name: 'INKLING', species: 'RAT' } },
])
  assert.equal(restoreActiveBreakContext(bad, receipt.id, player), null);
assert.equal(restoreActiveBreakContext(context, receipt.id, { ...player, mode: 'awake' }), null);
assert.equal(restoreActiveBreakContext(context, receipt.id, null), null);

const memory: CompanionMemory = { ...offers[0], recordedAt: 6000, source: 'self-reported' };
assert.deepEqual(restoreCompanionMemories([memory]), [memory]);
assert.deepEqual(restoreCompanionMemories([null, {}, [], memory, memory]), [memory]);
assert.deepEqual(restoreCompanionMemories(null), []);
for (const patch of [
  { source: 'automatic' },
  { recordedAt: 4999 },
  { recordedAt: NaN },
  { minutes: 1.5 },
  { minutes: -2 },
  { minutes: Infinity },
  { id: '' },
  { id: 'x'.repeat(257) },
  { mission: {} },
  { mission: 'unknown' },
  { early: true },
  { companion: { key: 'starter', name: 'x'.repeat(81), species: 'BLOB' } },
])
  assert.deepEqual(restoreCompanionMemories([{ ...memory, ...patch }]), []);

const manyMemories = Array.from({ length: memoryLimit + 4 }, (_, i) => ({
  ...memory,
  id: `memory-${i}`,
  recordedAt: 6000 + i,
}));
const restored = restoreCompanionMemories(manyMemories);
assert.equal(restored.length, memoryLimit);
assert.equal(restored[0].id, `memory-${memoryLimit + 3}`);
const resolved = restoreMemoryResolutions([null, '', memory.id, memory.id, 4], [memory]);
assert.deepEqual(resolved, [memory.id]);
assert.deepEqual(restoreMemoryResolutions(null, [memory]), [memory.id]);
assert.equal(
  restoreMemoryResolutions(
    Array.from({ length: 120 }, (_, i) => `id${i}`),
    [],
  ).length,
  memoryResolutionLimit,
);

assert.deepEqual(restorePendingMemories(offers, [receipt], []), offers);
assert.deepEqual(restorePendingMemories([null, ...offers, ...offers], [receipt], []), offers);
assert.deepEqual(
  restorePendingMemories(offers, [], []),
  offers,
  'A structurally valid pending reflection survives archival of its rolling receipt',
);
assert.deepEqual(
  restorePendingMemories(
    [null, {}, { ...offers[0], intention: 'verified' }, { ...offers[0], minutes: Infinity }],
    [],
    [],
  ),
  [],
  'Absent rolling receipts never bypass strict offer validation',
);
assert.deepEqual(restorePendingMemories(offers, [receipt], [receipt.id]), []);
for (const patch of [
  { completedAt: 5999 },
  { minutes: 5 },
  { mission: 'book' },
  { mission: 'book', early: true },
])
  assert.deepEqual(restorePendingMemories([{ ...offers[0], ...patch }], [receipt], []), []);
let queue = offers;
const history = [receipt];
for (let i = 1; i < 8; i++) {
  const item = { ...receipt, id: `settlement${i}`, completedAt: 5000 + i };
  history.push(item);
  queue = offerCompanionMemory({ ...context, breakId: item.id }, item, queue, []);
}
assert.equal(queue.length, pendingMemoryLimit);
assert.equal(queue[0].id, 'settlement3');
assert.equal(queue[4].id, 'settlement7');
assert.deepEqual(restorePendingMemories(queue, history, []), queue);
assert.equal(receipt.grass, 4);
assert.equal(receipt.cards, 0);
assert.equal(player.grass, 50);
assert.equal(player.level, 3);
assert.equal(player.mood, 80);
console.log(
  'PASS: companion memories — immutable starter/visitor snapshots, optional intentions, early returns, bounded queues, resolved IDs and hostile-save sanitising; no reward effects.',
);
