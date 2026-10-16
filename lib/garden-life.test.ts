import assert from 'node:assert/strict';
import type { BreakIntention, CompanionMemory } from './companion-memories';
import { companionProfile } from './companion-profiles';
import type { Player } from './game';
import {
  gardenKeepsakes,
  gardenMemoryForAction,
  gardenResponse,
  gardenSignature,
  memoryPlace,
  type GardenInteraction,
} from './garden-life';
import { guardianPlayer, visitors } from './visitors';

const player: Player = {
  id: 'gardener',
  code: 'ABCD',
  name: 'GARDENER',
  pet_name: 'ORIGINAL',
  species: 'BLOB',
  level: 3,
  grass: 212,
  mood: 87,
  hat: 'CAP',
  owned_hats: ['CAP'],
  mode: 'awake',
  care_until: 1000,
  recovery_until: 0,
  mission_id: null,
  mission_ends_at: 0,
  offline_seconds: 42,
  last_seen: 1000,
  deck: ['stretch', 'short_walk', 'read_a_chapter'],
  collection: visitors.map((visitor) => ({
    id: visitor.id,
    metAt: 0,
    minutes: 15,
    befriendedAt: 0,
  })),
  guardian: null,
  postcards: [],
};
const actions: GardenInteraction[] = ['read', 'water', 'pond', 'pat', 'lantern'];
const makeMemory = (
  id: string,
  intention: BreakIntention,
  completedAt: number,
  recordedAt = completedAt + 1,
): CompanionMemory => ({
  id,
  intention,
  companion: { key: 'starter', name: 'ORIGINAL AT THE TIME', species: 'BLOB' },
  completedAt,
  recordedAt,
  minutes: 4,
  mission: null,
  early: false,
  source: 'self-reported',
});

assert.deepEqual(gardenKeepsakes(), {});
assert.deepEqual(gardenKeepsakes(Object.freeze([])), {});
for (const action of actions) assert.equal(gardenMemoryForAction(action), null);
const chosenRead = makeMemory('aa-read', 'read', 200, 300);
const movement: CompanionMemory = {
  ...makeMemory('movement', 'move', 100),
  companion: { key: 'trailhop', name: 'TRAILHOP', species: 'RAT' },
};
const memories = [
  makeMemory('late-recorded-old-break', 'read', 100, 900),
  makeMemory('newer-read', 'read', 200, 250),
  makeMemory('zz-read', 'read', 200, 300),
  chosenRead,
  movement,
  makeMemory('rest', 'rest', 110),
  { ...makeMemory('create', 'create', 120), mission: 'book', early: true },
];
const beforeMemories = structuredClone(memories);
for (const memory of memories) {
  Object.freeze(memory.companion);
  Object.freeze(memory);
}
Object.freeze(memories);
for (const order of [
  memories,
  memories.toReversed(),
  [...memories.slice(3), ...memories.slice(0, 3)],
]) {
  const keepsakes = gardenKeepsakes(order);
  assert.equal(keepsakes.read, chosenRead, 'Latest break, latest recording, then lexical ID win');
  assert.equal(keepsakes.move, movement);
  assert.equal(Object.keys(keepsakes).length, 4);
}
for (const [intention, action, label] of [
  ['rest', 'lantern', 'Leaf lantern'],
  ['read', 'read', 'Reading nook'],
  ['move', 'water', 'Flower beds'],
  ['create', 'pond', 'Pondside sketchboard'],
] as const) {
  const place = memoryPlace(intention);
  assert.equal(place.action, action);
  assert.equal(place.label, label);
  assert.ok(place.description.length > 20);
  assert.equal(gardenMemoryForAction(action, memories), gardenKeepsakes(memories)[intention]);
}
assert.equal(gardenMemoryForAction('pat', memories), null, 'Patting stays a companion interaction');
assert.equal(gardenKeepsakes(memories).read!.companion.key, 'starter');
assert.equal(gardenKeepsakes(memories).read!.companion.name, 'ORIGINAL AT THE TIME');
assert.equal(gardenKeepsakes(memories).move!.companion.key, 'trailhop');

for (const [species, family, pose, motif] of [
  ['BLOB', 'REST', 'nestle', 'glow'],
  ['RAT', 'ROAM', 'sniff', 'leaf'],
  ['CUBE', 'FOCUS', 'ponder', 'scribble'],
] as const) {
  const starter = { ...player, species };
  assert.deepEqual(gardenSignature(starter), { family, pose, motif, animated: true });
  assert.deepEqual(gardenSignature(starter, true), { family, pose, motif, animated: false });
  for (const action of actions) {
    const first = gardenResponse(starter, action);
    const next = gardenResponse(starter, action, 1);
    assert.ok(first.startsWith('ORIGINAL '));
    assert.ok(next.startsWith('ORIGINAL '));
    assert.notEqual(first, next, 'Starter family interactions have two short variants');
    assert.equal(gardenResponse(starter, action, 2), first);
    assert.equal(gardenResponse(starter, action, -3), first);
    assert.equal(gardenResponse(starter, action, Infinity), first);
    assert.equal(gardenResponse(starter, action, NaN), first);
    assert.equal(gardenResponse(starter, action, 1.9), next);
  }
}

const beforePlayer = structuredClone(player);
for (const action of actions) {
  const behaviours = new Set<string>();
  for (const visitor of visitors) {
    const selected = { ...player, guardian: visitor.id };
    const profile = companionProfile(selected);
    const response = gardenResponse(selected, action);
    assert.ok(response.startsWith(`${visitor.name} `));
    assert.equal(profile.id, visitor.id);
    assert.equal(gardenSignature(selected).family, visitor.habit);
    assert.equal(gardenSignature(selected, true).animated, false);
    assert.equal(gardenResponse(guardianPlayer(selected), action), response);
    behaviours.add(response.slice(visitor.name.length + 1));
  }
  assert.equal(behaviours.size, 9, `${action} gives each visitor its own behavioural flavour`);
}
const selectedInkling = { ...player, guardian: 'inkling' as const };
const keptReadingLine = gardenResponse(selectedInkling, 'read', 0, memories);
assert.ok(keptReadingLine.includes(chosenRead.companion.name));
assert.ok(keptReadingLine.startsWith('Reading memory:'));
assert.ok(keptReadingLine.length <= 95);
assert.ok(
  !keptReadingLine.includes('INKLING'),
  'A newly selected pet never inherits the original memory',
);
assert.equal(gardenMemoryForAction('read', memories), chosenRead);
assert.equal(
  gardenResponse(selectedInkling, 'read', 1, memories),
  gardenResponse(selectedInkling, 'read'),
  'The second visit gives the active visitor its distinct personality response',
);
assert.equal(gardenResponse(selectedInkling, 'read', 2, memories), keptReadingLine);
assert.notEqual(
  gardenResponse(selectedInkling, 'read', 1, memories),
  gardenResponse(selectedInkling, 'read', 3, memories),
  'Further visits alternate personality and family variation between keepsake lines',
);
assert.equal(
  gardenResponse(selectedInkling, 'pat', 1, memories),
  gardenResponse(selectedInkling, 'pat', 1),
);
for (const action of actions) {
  const response = gardenResponse(selectedInkling, action, 0, memories);
  assert.ok(!response.includes('verified'));
  assert.ok(!response.includes('completed your mission'));
  assert.ok(!response.includes('+'), 'Keepsake feedback never advertises an extra reward');
}
const invalidSelection = { ...player, guardian: 'skyfern' as const, collection: [] };
assert.equal(gardenSignature(invalidSelection).family, 'REST');
assert.ok(gardenResponse(invalidSelection, 'pat').startsWith('ORIGINAL '));
const bot = { ...player, id: 'bot', guardian: 'inkling' as const };
assert.equal(gardenSignature(bot).family, 'REST');
assert.ok(gardenResponse(bot, 'read').startsWith('ORIGINAL '));
assert.deepEqual(memories, beforeMemories);
assert.deepEqual(player, beforePlayer);
console.log(
  'PASS: garden life — deterministic keepsakes, original memory companions, four garden places, all starter families, nine distinct visitor behaviours, current-guardian selection and static reduced-motion signatures; no progress writes.',
);
