import assert from 'node:assert/strict';
import { matchup, maxHp } from './battle';
import { cards, cardPower, isCardId } from './cards';
import { companionOptions, companionProfile } from './companion-profiles';
import type { Player } from './game';
import {
  befriendedVisitorIds,
  effectiveGuardianId,
  guardianPlayer,
  visitors,
  type VisitorId,
} from './visitors';

const starter = (species: Player['species'] = 'BLOB'): Player => ({
  id: 'owner',
  code: 'OWNER',
  name: 'PLAYER',
  pet_name: 'FERN',
  species,
  level: 3,
  grass: 217,
  mood: 83,
  hat: 'CAP',
  owned_hats: ['CAP'],
  mode: 'awake',
  care_until: 1200,
  recovery_until: 1000,
  mission_id: null,
  mission_ends_at: 0,
  offline_seconds: 117,
  last_seen: 1300,
  deck: ['stretch', 'short_walk', 'glass_of_water'],
  collection: [],
  guardian: null,
  postcards: [{ id: 'park-first', mission: 'park', at: 1200 }],
});
const encounter = (id: VisitorId, befriendedAt: number | null = 0) => ({
  id,
  metAt: 0,
  minutes: 15,
  befriendedAt,
});
const allOwned: Player = { ...starter(), collection: visitors.map((v) => encounter(v.id)) };
const before = structuredClone(allOwned);

// Each family has its own personality, with the starter name and identity intact.
const families = (['BLOB', 'RAT', 'CUBE'] as const).map((species) => {
  const player = starter(species);
  const profile = companionProfile(player);
  assert.equal(profile.id, null);
  assert.equal(profile.name, 'FERN');
  assert.equal(profile.species, species);
  assert.equal(companionOptions(player).length, 1);
  assert.equal(guardianPlayer(player), player);
  return profile;
});
assert.deepEqual(
  families.map((p) => p.habit),
  ['REST', 'ROAM', 'FOCUS'],
);
assert.equal(new Set(families.map((p) => p.description)).size, 3);
assert.equal(new Set(families.map((p) => p.traits.join('/'))).size, 3);

// Encounter timestamps can legitimately be epoch zero. Duplicates and merely
// encountered visitors must not expand the available companion roster.
assert.equal(companionOptions(allOwned).length, 10);
assert.deepEqual(
  companionOptions(allOwned)
    .slice(1)
    .map((p) => p.id),
  visitors.map((v) => v.id),
);
const partial: Player = {
  ...starter(),
  collection: [
    encounter('inkling'),
    encounter('dozebud', null),
    encounter('inkling'),
    encounter('skyfern'),
  ],
};
assert.deepEqual(
  companionOptions(partial).map((p) => p.id),
  [null, 'skyfern', 'inkling'],
);
assert.deepEqual(befriendedVisitorIds(partial), ['skyfern', 'inkling']);
assert.equal(companionProfile(partial, 'inkling').id, 'inkling');
assert.equal(companionProfile(partial, 'dozebud').id, null);
assert.equal(companionProfile(partial, 'dozebud').name, 'FERN');
assert.equal(companionProfile(partial, 'dozebud').species, 'BLOB');

const profiles = visitors.map((visitor) => {
  const player = { ...allOwned, guardian: visitor.id };
  const profile = companionProfile(player);
  const rendered = guardianPlayer(player);
  assert.equal(profile.id, visitor.id);
  assert.equal(profile.name, visitor.name);
  assert.equal(profile.species, visitor.species);
  assert.equal(profile.habit, visitor.habit);
  assert.equal(profile.traits.length, 2);
  assert.ok(profile.traits.every((trait) => trait.length > 0));
  assert.ok(profile.description.length > 20);
  assert.ok(profile.invitation.title.length > 0);
  assert.ok(profile.invitation.body.length > 20);
  assert.equal(effectiveGuardianId(player), visitor.id);
  assert.equal(rendered.species, profile.species);
  assert.equal(rendered.pet_name, profile.name);
  assert.equal(rendered.guardian, visitor.id);
  assert.deepEqual(guardianPlayer(rendered), rendered);
  assert.equal(companionProfile(player, null).name, 'FERN');
  assert.equal(companionProfile(player, null).species, 'BLOB');
  // Selecting a companion changes only the rendered identity, never shared progress.
  assert.deepEqual({ ...rendered, species: player.species, pet_name: player.pet_name }, player);
  assert.equal(maxHp(rendered), maxHp(player));
  return profile;
});
assert.equal(new Set(profiles.map((p) => p.traits.join('/'))).size, 9);
assert.equal(new Set(profiles.map((p) => p.description)).size, 9);
assert.equal(new Set(profiles.map((p) => p.invitation.body)).size, 9);

// Restored invalid IDs, unbefriended visitors and deleted collection entries
// must clear guardian as well as retaining the starter's visible identity.
for (const player of [
  { ...starter('RAT'), guardian: 'missing' },
  { ...starter('RAT'), guardian: 'inkling', collection: [encounter('inkling', null)] },
  { ...starter('RAT'), guardian: 'inkling' },
  { ...starter('RAT'), guardian: 'inkling', collection: [encounter('inkling', NaN)] },
  { ...starter('RAT'), guardian: 'inkling', collection: [encounter('inkling', Infinity)] },
]) {
  const original = structuredClone(player);
  const rendered = guardianPlayer(player);
  assert.equal(effectiveGuardianId(player), null);
  assert.equal(rendered.guardian, null);
  assert.equal(rendered.pet_name, 'FERN');
  assert.equal(rendered.species, 'RAT');
  assert.equal(companionProfile(player).id, null);
  assert.equal(companionProfile(player).name, 'FERN');
  assert.equal(companionProfile(player).species, 'RAT');
  assert.deepEqual(guardianPlayer(rendered), rendered);
  assert.deepEqual(player, original);
}
const bot = { ...allOwned, id: 'bot', guardian: 'inkling' };
assert.deepEqual(befriendedVisitorIds(bot), []);
assert.equal(companionOptions(bot).length, 1);
assert.equal(companionProfile(bot).id, null);
assert.equal(guardianPlayer(bot).guardian, null);
assert.equal(guardianPlayer(bot).id, 'bot');
assert.equal(guardianPlayer(bot).pet_name, bot.pet_name);
assert.equal(guardianPlayer(bot).species, bot.species);

// Public attributes describe the existing battle implementation, rather than
// silently introducing rarity bonuses, stronger healing or different HP pools.
for (const profile of profiles) {
  const goodAgainst = { REST: 'CUBE', ROAM: 'BLOB', FOCUS: 'RAT' } as const;
  const weakAgainst = { REST: 'RAT', ROAM: 'CUBE', FOCUS: 'BLOB' } as const;
  assert.equal(matchup(profile.species, goodAgainst[profile.habit]), 1.5);
  assert.equal(matchup(profile.species, weakAgainst[profile.habit]), 0.67);
  const powered = Object.entries(cards).filter(
    ([, card]) => card.habit === profile.species && card.power > 0,
  );
  assert.deepEqual(
    powered.map(([id]) => id),
    {
      REST: [],
      ROAM: ['short_walk', 'morning_walk'],
      FOCUS: ['stretch', 'read_a_chapter'],
    }[profile.habit],
  );
  for (const [id, card] of powered) {
    assert.ok(isCardId(id));
    assert.equal(cardPower(id, profile.species), card.power + 3);
  }
  assert.ok(profile.battleNote.includes('HP is the same'));
  if (profile.habit === 'REST') assert.ok(profile.battleNote.includes('no damaging habit cards'));
}
assert.deepEqual(allOwned, before);
assert.equal(allOwned.grass, 217);
assert.equal(allOwned.level, 3);
assert.equal(allOwned.offline_seconds, 117);
assert.deepEqual(allOwned.deck, before.deck);
assert.deepEqual(allOwned.postcards, before.postcards);
console.log(
  'PASS: companion profiles — all nine identities, owned-only choices, epoch-zero ownership, stale selection fallback, view-only progress and existing battle attributes.',
);
