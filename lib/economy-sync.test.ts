import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import type { Player, Raid } from './game';

// Real game/store/persistence source, substituted native and backend boundaries.
// These are payload/settlement checks, not a live multiplayer or server test.
const fixtureKey = Symbol.for('napattack.economy-sync.fixture');
const fixture = {
  storage: new Map<string, string>(),
  uploads: [] as { table: string; data: Record<string, unknown> }[],
  incoming: [] as Raid[],
  failRaidUpload: true,
};
Reflect.set(globalThis, fixtureKey, fixture);
const boundaries = new Map([
  [
    '@react-native-async-storage/async-storage',
    `
    const f = globalThis[Symbol.for('napattack.economy-sync.fixture')];
    export default {
      async getItem(key) { return f.storage.get(key) ?? null; },
      async setItem(key, value) { f.storage.set(key, value); }
    };
  `,
  ],
  [
    'react-native',
    `
    export const Platform = { OS: 'web' };
    export const AppState = { currentState: 'active', addEventListener() { return {remove(){}}; } };
    export const Vibration = { vibrate() {} };
  `,
  ],
  [
    'expo-crypto',
    `
    export { randomUUID } from 'node:crypto';
    export function getRandomBytes(size) { return new Uint8Array(size); }
  `,
  ],
  [
    'expo-haptics',
    `
    export const ImpactFeedbackStyle = {};
    export const NotificationFeedbackType = {};
    export async function impactAsync() {}
    export async function selectionAsync() {}
    export async function notificationAsync() {}
  `,
  ],
  [
    '@/lib/bilt',
    `
    const f = globalThis[Symbol.for('napattack.economy-sync.fixture')];
    export const backendUnavailableMessage = 'test backend boundary';
    export const bilt = {
      from(table) {
        const q = {
          select() { return q; }, eq() { return q; },
          or() { return q; }, order() { return q; }, update() { return q; },
          async maybeSingle() { return {data:null,error:null}; },
          async upsert(data) {
            f.uploads.push({table, data: {...data}});
            return {error: table === 'raids' && f.failRaidUpload ? {message:'offline'} : null};
          },
          then(resolve,reject) {
            return Promise.resolve({data:table === 'raids' ? f.incoming : [],error:null}).then(resolve,reject);
          }
        };
        return q;
      }
    };
  `,
  ],
]);
const hooks = registerHooks({
  resolve(specifier, context, next) {
    const source =
      boundaries.get(specifier) ??
      (specifier.endsWith('/lib/bilt.ts') ? boundaries.get('@/lib/bilt') : undefined);
    return source === undefined
      ? next(specifier, context)
      : {
          url: `data:text/javascript,${encodeURIComponent(source)}`,
          shortCircuit: true,
        };
  },
  load(url, context, next) {
    const prefix = 'data:text/javascript,';
    return url.startsWith(prefix)
      ? {
          format: 'module',
          source: decodeURIComponent(url.slice(prefix.length)),
          shortCircuit: true,
        }
      : next(url, context);
  },
});

async function main() {
  delete process.env.EXPO_PUBLIC_BILT_URL;
  delete process.env.EXPO_PUBLIC_BILT_ANON_KEY;
  const originalFetch = globalThis.fetch;
  let networkRequests = 0;
  globalThis.fetch = async () => {
    networkRequests++;
    throw new Error('Network not allowed in economy test');
  };
  try {
    const { gameStore, flushGameSave } = await import('./game');
    const { GAME_SAVE_KEY } = await import('./save-data');
    const { startingDeck } = await import('./cards');
    await gameStore.getState().init();
    const player: Player = {
      id: 'wallet-owner',
      code: 'ABCD',
      name: 'GARDENER',
      pet_name: 'SPROUT',
      species: 'BLOB',
      level: 1,
      grass: 500.25,
      mood: 80,
      hat: null,
      owned_hats: [],
      mode: 'awake',
      care_until: 0,
      recovery_until: 0,
      mission_id: null,
      mission_ends_at: 0,
      offline_seconds: 0,
      last_seen: Date.now(),
      deck: [...startingDeck],
      collection: [],
      postcards: [],
      guardian: null,
    };
    const legacyOutgoing: Raid = Object.freeze({
      id: 'pending-old-raid',
      attacker_id: player.id,
      defender_id: 'rival',
      attacker_won: true,
      grass_amount: 321,
      created_at: '2026-10-16T12:00:00Z',
      seen_by_defender: false,
    });
    const legacyIncoming: Raid = {
      ...legacyOutgoing,
      id: 'incoming-old-raid',
      attacker_id: 'rival',
      defender_id: player.id,
      grass_amount: 999999,
    };
    gameStore.setState({
      player,
      outgoing: [legacyOutgoing],
      pollTogether: async () => {},
      staged: [{ raid: legacyIncoming, attacker: null }],
    });
    // Persist the seeded pre-upgrade queue without launching another sync.
    gameStore.getState().setQuietView(gameStore.getState().quietView);
    await flushGameSave();
    await gameStore.getState().sync();
    await flushGameSave();
    assert.ok(
      fixture.uploads.some((x) => x.table === 'raids'),
      'Actual sync must reach the substituted raid transport',
    );
    assert.equal(fixture.uploads.find((x) => x.table === 'raids')!.data.grass_amount, 0);
    assert.equal(gameStore.getState().outgoing[0].grass_amount, 321);
    assert.equal(JSON.parse(fixture.storage.get(GAME_SAVE_KEY)!).outgoing[0].grass_amount, 321);
    assert.equal(legacyOutgoing.grass_amount, 321);
    assert.equal(gameStore.getState().player!.grass, 500.25);

    fixture.failRaidUpload = false;
    await gameStore.getState().sync();
    await flushGameSave();
    assert.equal(gameStore.getState().outgoing.length, 0);
    assert.equal(
      gameStore.getState().player!.grass,
      500.25,
      'Staged legacy loot is ignored on a lost defence',
    );
    assert.equal(
      gameStore.getState().alerts[0].raid.grass_amount,
      999999,
      'Legacy history is retained',
    );
    assert.deepEqual(gameStore.getState().applied, [legacyIncoming.id]);
    const uploads = fixture.uploads.filter((x) => x.table === 'raids');
    assert.equal(uploads.length, 2, 'Failed upload was retried once');
    for (const { data } of uploads) assert.deepEqual(data, { ...legacyOutgoing, grass_amount: 0 });

    fixture.incoming = [legacyIncoming];
    await gameStore.getState().sync();
    assert.equal(
      gameStore.getState().player!.grass,
      500.25,
      'Replayed incoming raid is not applied twice',
    );
    assert.equal(gameStore.getState().alerts.length, 1);
    fixture.incoming = [{ ...legacyIncoming, id: 'repelled-old-raid', attacker_won: false }];
    await gameStore.getState().sync();
    await gameStore.getState().sync();
    await flushGameSave();
    assert.equal(gameStore.getState().player!.grass, 520.25, 'Old defence reward is credited once');
    assert.equal(gameStore.getState().alerts.length, 2);
    assert.equal(networkRequests, 0);
    console.log(
      'PASS: actual raid sync sends zero-debit legacy retries, retains history and settles incoming raids once; no real backend.',
    );
  } finally {
    globalThis.fetch = originalFetch;
    hooks.deregister();
    Reflect.deleteProperty(globalThis, fixtureKey);
  }
}
void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
