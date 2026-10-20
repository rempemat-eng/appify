import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import {
  fixtureNow,
  saveFixtures,
  currentSaveFixture,
  layoutSaveFixtures,
  keepsakeSaveFixture,
  worldAccountFixture,
} from './fixtures/save-fixtures';
import { FutureSaveError, GAME_SAVE_KEY, readSave, SAVE_VERSION, writeSave } from './save-data';
import { meadowSummary } from './garden-growth';
import { startingDeck } from './cards';
import {
  SAVE_BACKUP_PREFIX,
  backupBeforeFreshStart,
  SaveRecoveryChangedError,
} from './save-recovery';

// Same native boundaries as check:game; the store, migrations and rules are real.
const values = new Map<string, string>();
let failReads = false;
let failWrites = false;
let writes = 0;
let failWriteKey: ((key: string) => boolean) | null = null;
let beforeWrite: ((key: string) => Promise<void>) | null = null;
let beforeRead: (() => Promise<void>) | null = null;
const operations: { kind: 'read' | 'write'; key: string; value?: string }[] = [];
const storage = {
  async getItem(key: string) {
    operations.push({ kind: 'read', key });
    await beforeRead?.();
    if (failReads) throw new Error('Test storage read failed');
    return values.get(key) ?? null;
  },
  async setItem(key: string, value: string) {
    operations.push({ kind: 'write', key, value });
    await beforeWrite?.(key);
    if (failWrites || failWriteKey?.(key)) throw new Error('Test storage write failed');
    writes++;
    values.set(key, value);
  },
};
const boundaryKey = Symbol.for('napattack.save-test.storage');
Object.defineProperty(globalThis, boundaryKey, { value: storage, configurable: true });
const boundaries = new Map([
  [
    '@react-native-async-storage/async-storage',
    `export default globalThis[Symbol.for('napattack.save-test.storage')];`,
  ],
  [
    'react-native',
    `export const Platform = { OS: 'web' };
     export const AppState = { currentState: 'active', addEventListener() { return { remove() {} }; } };
     export const Vibration = { vibrate() {} };`,
  ],
  [
    'expo-crypto',
    `import { randomBytes } from 'node:crypto';
     export { randomUUID } from 'node:crypto';
     export function getRandomBytes(size) { return new Uint8Array(randomBytes(size)); }`,
  ],
  [
    'expo-haptics',
    `export const ImpactFeedbackStyle = { Heavy: 'heavy' };
     export const NotificationFeedbackType = { Success: 'success', Error: 'error' };
     export async function impactAsync() {};
     export async function selectionAsync() {};
     export async function notificationAsync() {};`,
  ],
]);
const hooks = registerHooks({
  resolve(specifier, context, nextResolve) {
    const boundary = boundaries.get(specifier);
    return boundary === undefined
      ? nextResolve(specifier, context)
      : { url: `data:text/javascript,${encodeURIComponent(boundary)}`, shortCircuit: true };
  },
  load(url, context, nextLoad) {
    const prefix = 'data:text/javascript,';
    return url.startsWith(prefix)
      ? {
          format: 'module',
          source: decodeURIComponent(url.slice(prefix.length)),
          shortCircuit: true,
        }
      : nextLoad(url, context);
  },
});

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function record(value: unknown): Record<string, unknown> {
  assert.ok(isRecord(value), 'Expected a saved record');
  return value;
}
function records(value: unknown): Record<string, unknown>[] {
  assert.ok(Array.isArray(value), 'Expected saved records');
  return value.map(record);
}
function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

async function main() {
  const realNow = Date.now;
  const realFetch = globalThis.fetch;
  const oldUrl = process.env.EXPO_PUBLIC_BILT_URL;
  const oldKey = process.env.EXPO_PUBLIC_BILT_ANON_KEY;
  delete process.env.EXPO_PUBLIC_BILT_URL;
  delete process.env.EXPO_PUBLIC_BILT_ANON_KEY;
  Date.now = () => fixtureNow;
  globalThis.fetch = async () => {
    throw new Error('Save checks must never use the network');
  };
  try {
    const { gameStore, flushGameSave } = await import('./game');
    const load = async (raw: string | null) => {
      await flushGameSave();
      if (raw === null) values.delete(GAME_SAVE_KEY);
      else values.set(GAME_SAVE_KEY, raw);
      gameStore.setState({ ready: false, player: null, message: null });
      await gameStore.getState().init();
      await flushGameSave();
    };
    const disk = (): Record<string, unknown> => JSON.parse(values.get(GAME_SAVE_KEY)!);
    const reload = async () => load(values.get(GAME_SAVE_KEY)!);
    for (const fixture of saveFixtures) {
      const raw = JSON.stringify(fixture.saved);
      const original = JSON.parse(raw);
      await load(raw);
      const after = gameStore.getState();
      const before = original.player;
      assert.ok(after.player, fixture.name);
      for (const key of [
        'id',
        'name',
        'pet_name',
        'species',
        'level',
        'grass',
        'hat',
        'owned_hats',
        'offline_seconds',
      ] as const)
        assert.deepEqual(after.player[key], before[key], `${fixture.name}: ${key}`);
      assert.deepEqual(
        meadowSummary(after.player.offline_seconds),
        meadowSummary(before.offline_seconds),
      );
      if ('deck' in before) {
        const expected =
          fixture === saveFixtures[1]
            ? [...before.deck, 'glass_of_water', 'short_walk']
            : before.deck;
        assert.deepEqual(after.player.deck, expected, `${fixture.name}: deck`);
      } else assert.deepEqual(after.player.deck, [...startingDeck, 'digital_sunset']);
      for (const key of ['collection', 'postcards', 'guardian'] as const)
        if (key in before)
          assert.deepEqual(after.player[key], before[key], `${fixture.name}: ${key}`);
      for (const key of [
        'rules',
        'recentBreaks',
        'companionMemories',
        'memoryResolvedIds',
        'quietView',
        'missionReturnPending',
        'offDeck',
        'collectedCards',
        'togetherSettled',
        'seenSessions',
        'outgoing',
        'staged',
        'alerts',
        'applied',
      ] as const)
        if (key in original) assert.deepEqual(after[key], original[key], `${fixture.name}: ${key}`);
      if (original.cardReward)
        for (const [key, value] of Object.entries(original.cardReward))
          assert.deepEqual(record(after.cardReward)[key], value, `${fixture.name}: reward ${key}`);
      assert.equal(disk().saveVersion, SAVE_VERSION);
      const first = disk();
      await reload();
      assert.deepEqual(disk(), first, `${fixture.name}: second load is idempotent`);
      assert.equal(JSON.stringify(fixture.saved), raw, `${fixture.name}: fixture unchanged`);
      console.log(
        `PASS: ${fixture.name} (${fixture.sha.slice(0, 7)}) keeps progress across load/write/reload`,
      );
    }

    // C26 exercises the actual store migration + persistence boundary, rather
    // than substituting a test-only restoreWorld/restoreDecor implementation.
    for (const fixture of layoutSaveFixtures) {
      const raw = JSON.stringify(worldAccountFixture(fixture.world));
      await load(raw);
      assert.deepEqual(gameStore.getState().world, fixture.expected, fixture.name);
      assert.deepEqual(record(disk().world), fixture.expected, `${fixture.name}: written layout`);
      assert.equal(gameStore.getState().player!.grass, 437.125);
      assert.equal(record(disk().player).grass, 437.125);
      assert.deepEqual(disk().futureWorldNote, { kept: true });
      assert.deepEqual(record(disk().player).futureTrait, { colour: 'violet' });
      const migrated = disk();
      await reload();
      assert.deepEqual(disk(), migrated, `${fixture.name}: reload cannot migrate twice`);
      assert.equal(
        JSON.stringify(worldAccountFixture(fixture.world)),
        raw,
        'fixture input stays unchanged',
      );
      console.log(
        `PASS: C26 ${fixture.name} survives actual load/write/reload without balance loss`,
      );
    }
    {
      const fixture = keepsakeSaveFixture;
      const input = worldAccountFixture(fixture.world, fixture.decor);
      const before = JSON.stringify(input);
      await load(before);
      assert.deepEqual(
        gameStore.getState().decor,
        fixture.expected,
        'C26 valid hut/garden entries survive once each',
      );
      assert.equal(
        gameStore.getState().decor.some((p) => p.item === 'dragon_plush'),
        false,
        'unfound dropped',
      );
      assert.equal(
        gameStore.getState().decor.some((p) => p.item === 'town_lantern'),
        false,
        'no-fit dropped',
      );
      const stored = records(disk().decor);
      assert.equal(stored.length, 2);
      assert.deepEqual(stored.find((p) => p.item === 'stool')?.futurePatina, { colour: 'copper' });
      assert.equal(stored.find((p) => p.item === 'cairn')?.futurePlaque, 'kept');
      assert.equal(record(disk().player).grass, 437.125);
      assert.deepEqual(disk().futureWorldNote, { kept: true });
      const migrated = disk();
      await reload();
      assert.deepEqual(gameStore.getState().decor, fixture.expected);
      assert.deepEqual(disk(), migrated, 'C26 decor cleanup is idempotent across reload');
      assert.equal(JSON.stringify(input), before, 'C26 fixture object not mutated');
      console.log(
        'PASS: C26 hut/garden decor deduplicates, drops unfound/no-fit placements and keeps opaque fields',
      );
    }

    const extra = currentSaveFixture();
    const p = record(extra.player);
    const rules = record(extra.rules);
    const day = record(record(rules.days)['2026-10-17']);
    const memories = records(extra.companionMemories);
    const history = records(extra.recentBreaks);
    extra.saveVersion = SAVE_VERSION;
    extra.futureWorld = { seasons: ['autumn'], weather: { selected: null } };
    extra.tick = 'future data, never an action';
    extra.sync = { future: true };
    extra.ready = false;
    p.futureTrait = { colour: 'violet' };
    rules.futureRule = { enabled: false };
    record(rules.budget).futureBudget = 77;
    day.futureDay = 'kept';
    history[0].futureReceipt = ['kept'];
    memories[0].futureMemory = true;
    record(memories[0].companion).futureBond = 12;
    records(p.collection)[0].futureVisit = { gift: 'flower' };
    records(p.postcards)[0].futurePostmark = 'gold';
    record(extra.cardReward).futureReward = 'kept';
    record(extra.waitingVisitor).futureGreeting = 'hello';
    extra.pendingMemories = [
      {
        id: 'pending-reflection',
        intention: 'read',
        companion: { key: 'inkling', name: 'INKLING', species: 'CUBE', futureBond: 19 },
        completedAt: fixtureNow - 20_000,
        minutes: 10,
        mission: null,
        early: false,
        futureOffer: 'kept',
      },
    ];
    await load(JSON.stringify(extra));
    assert.equal(typeof gameStore.getState().tick, 'function');
    assert.equal(typeof gameStore.getState().sync, 'function');
    assert.equal(gameStore.getState().ready, true);
    assert.equal(Object.hasOwn(gameStore.getState(), 'futureWorld'), false);
    assert.equal(Object.hasOwn(gameStore.getState().player!, 'futureTrait'), false);
    gameStore.getState().setQuietView(false);
    gameStore.getState().selectGuardian('dozebud');
    await flushGameSave();
    await reload();
    const kept = disk();
    assert.deepEqual(kept.futureWorld, extra.futureWorld);
    assert.deepEqual(kept.tick, extra.tick);
    assert.deepEqual(kept.sync, extra.sync);
    assert.equal(kept.ready, false);
    assert.deepEqual(record(kept.player).futureTrait, p.futureTrait);
    assert.deepEqual(record(kept.rules).futureRule, rules.futureRule);
    assert.equal(record(record(kept.rules).budget).futureBudget, 77);
    assert.equal(record(record(record(kept.rules).days)['2026-10-17']).futureDay, 'kept');
    assert.deepEqual(records(kept.recentBreaks)[0].futureReceipt, ['kept']);
    const keptMemory = records(kept.companionMemories)[0];
    assert.equal(keptMemory.futureMemory, true);
    assert.equal(record(keptMemory.companion).futureBond, 12);
    const keptPlayer = record(kept.player);
    assert.deepEqual(records(keptPlayer.collection)[0].futureVisit, {
      gift: 'flower',
    });
    assert.equal(records(keptPlayer.postcards)[0].futurePostmark, 'gold');
    assert.equal(record(kept.cardReward).futureReward, 'kept');
    assert.equal(record(kept.waitingVisitor).futureGreeting, 'hello');
    assert.equal(records(kept.pendingMemories)[0].futureOffer, 'kept');
    assert.equal(record(records(kept.pendingMemories)[0].companion).futureBond, 19);
    assert.equal(keptPlayer.guardian, 'dozebud');
    assert.equal(kept.quietView, false);
    console.log(
      'PASS: future fields round-trip at every progress boundary without replacing actions',
    );
    gameStore.getState().dismissCompanionMemory('pending-reflection');
    await flushGameSave();
    await reload();
    assert.deepEqual(disk().pendingMemories, []);
    assert.deepEqual(disk().futureWorld, extra.futureWorld);
    assert.ok(gameStore.getState().memoryResolvedIds.includes('pending-reflection'));
    console.log(
      'PASS: explicitly dismissed reflections and their extra fields stay dismissed after reload',
    );

    const decoded = readSave(JSON.stringify(extra), (value) => value);
    assert.deepEqual(decoded.source, extra, 'Decoding must not mutate the original snapshot');
    const known = record(decoded.data);
    const knownPlayer = record(known.player);
    const originalCollection = records(knownPlayer.collection);
    knownPlayer.collection = originalCollection.toReversed();
    const reversed = record(writeSave(known, decoded.source).source);
    const reversedCollection = records(record(reversed.player).collection);
    assert.equal(reversedCollection[0].id, 'inkling');
    assert.equal(Object.hasOwn(reversedCollection[0], 'futureVisit'), false);
    assert.deepEqual(reversedCollection[1].futureVisit, { gift: 'flower' });
    knownPlayer.collection = [originalCollection[1]];
    known.cardReward = null;
    known.recentBreaks = [];
    known.companionMemories = [];
    known.pendingMemories = [];
    const removed = record(writeSave(known, decoded.source).source);
    assert.equal(records(record(removed.player).collection).length, 1);
    assert.equal(removed.cardReward, null);
    assert.deepEqual(removed.recentBreaks, []);
    assert.deepEqual(removed.companionMemories, []);
    assert.deepEqual(removed.pendingMemories, []);
    known.cardReward = { ...record(extra.cardReward), settlementId: 'a-different-reward' };
    delete record(known.cardReward).futureReward;
    const newReward = record(writeSave(known, decoded.source).source);
    assert.equal(Object.hasOwn(record(newReward.cardReward), 'futureReward'), false);
    console.log(
      'PASS: array identity survives reordering; removals and nulls never resurrect progress',
    );

    const raidSave = currentSaveFixture();
    const attacker = {
      ...record(raidSave.player),
      id: 'save-fixture-attacker',
      grass: 90,
      futureTrait: { temperament: 'patient' },
    };
    const raid = {
      id: 'saved-outgoing-raid',
      attacker_id: attacker.id,
      defender_id: record(raidSave.player).id,
      created_at: new Date(fixtureNow).toISOString(),
      attacker_won: true,
      grass_amount: 12,
      seen_by_defender: false,
      futureRaid: { season: 'autumn' },
    };
    const incoming = {
      raid: { ...raid, id: 'saved-incoming-raid' },
      attacker,
      futureIncoming: { note: 'kept with this raid' },
    };
    raidSave.outgoing = [raid];
    raidSave.staged = [incoming];
    raidSave.alerts = [{ ...incoming, raid: { ...raid, id: 'saved-alert-raid' } }];
    await load(JSON.stringify(raidSave));
    const loadedRaids = gameStore.getState();
    assert.equal(Object.hasOwn(loadedRaids.outgoing[0], 'futureRaid'), false);
    assert.equal(Object.hasOwn(loadedRaids.staged[0], 'futureIncoming'), false);
    assert.equal(Object.hasOwn(loadedRaids.staged[0].attacker!, 'futureTrait'), false);
    gameStore.setState({
      outgoing: loadedRaids.outgoing.map((savedRaid) => ({ ...savedRaid, grass_amount: 17 })),
      staged: loadedRaids.staged.map((entry) => ({
        ...entry,
        raid: { ...entry.raid, seen_by_defender: true },
        attacker: { ...entry.attacker!, grass: 73 },
      })),
    });
    gameStore.getState().setQuietView(false);
    await flushGameSave();
    await reload();
    const keptRaids = disk();
    const keptOutgoing = records(keptRaids.outgoing)[0];
    const keptStaged = records(keptRaids.staged)[0];
    const keptAlert = records(keptRaids.alerts)[0];
    assert.equal(keptOutgoing.grass_amount, 17);
    assert.deepEqual(keptOutgoing.futureRaid, raid.futureRaid);
    assert.equal(record(keptStaged.raid).seen_by_defender, true);
    assert.deepEqual(record(keptStaged.raid).futureRaid, raid.futureRaid);
    assert.equal(record(keptStaged.attacker).grass, 73);
    assert.deepEqual(record(keptStaged.attacker).futureTrait, attacker.futureTrait);
    assert.deepEqual(keptStaged.futureIncoming, incoming.futureIncoming);
    assert.equal(record(keptAlert.attacker).grass, 90);
    assert.deepEqual(record(keptAlert.attacker).futureTrait, attacker.futureTrait);
    assert.deepEqual(record(keptAlert.raid).futureRaid, raid.futureRaid);
    assert.deepEqual(keptAlert.futureIncoming, incoming.futureIncoming);
    gameStore.getState().dismissAlert();
    await flushGameSave();
    await reload();
    assert.deepEqual(disk().alerts, []);
    console.log(
      'PASS: nonempty raids and attacker snapshots retain opaque fields alongside current values and dismissal',
    );

    const active = JSON.parse(JSON.stringify(extra));
    active.player.mode = 'screen_off';
    active.offStart = active.player.offline_seconds;
    active.breakId = 'active-intended-break';
    active.activeBreakContext = {
      breakId: active.breakId,
      playerId: active.player.id,
      intention: 'rest',
      companion: { key: 'inkling', name: 'INKLING', species: 'CUBE', futureBond: 23 },
      startedAt: fixtureNow,
      futureContext: { kept: true },
    };
    await load(JSON.stringify(active));
    await reload();
    assert.deepEqual(record(disk().activeBreakContext).futureContext, { kept: true });
    assert.equal(record(record(disk().activeBreakContext).companion).futureBond, 23);
    assert.equal(Object.hasOwn(gameStore.getState().activeBreakContext!, 'futureContext'), false);
    await gameStore.getState().wake();
    await flushGameSave();
    await reload();
    assert.equal(disk().activeBreakContext, null);
    console.log('PASS: active-break extensions survive reload and clear normally on return');

    for (const raw of [
      '{broken json',
      'null',
      JSON.stringify({ ...extra, player: { ...p, grass: 'broken' } }),
      JSON.stringify({ ...extra, saveVersion: -1 }),
      JSON.stringify({ ...extra, saveVersion: 1.5 }),
      JSON.stringify({ ...extra, saveVersion: '1' }),
      JSON.stringify({ ...extra, saveVersion: SAVE_VERSION + 1 }),
    ]) {
      await load(raw);
      const beforeWrites = writes;
      gameStore.getState().setQuietView(true);
      await gameStore.getState().hatch('REPLACEMENT', 'NEW PET', 'BLOB');
      gameStore.getState().tick();
      await flushGameSave();
      assert.equal(values.get(GAME_SAVE_KEY), raw);
      assert.equal(writes, beforeWrites);
      assert.equal(gameStore.getState().player, null);
    }
    assert.throws(
      () => readSave(JSON.stringify({ saveVersion: 2 }), (value) => value),
      FutureSaveError,
    );
    console.log(
      'PASS: invalid/newer saves remain byte-identical after attempted hatch and preference writes',
    );

    const protectedBytes = JSON.stringify(extra);
    values.set(GAME_SAVE_KEY, protectedBytes);
    failReads = true;
    await load(protectedBytes);
    failReads = false;
    await gameStore.getState().hatch('REPLACEMENT', 'NEW PET', 'BLOB');
    await flushGameSave();
    assert.equal(values.get(GAME_SAVE_KEY), protectedBytes);
    await reload();
    assert.equal(gameStore.getState().player?.id, record(extra.player).id);
    const beforeFailedWrite = values.get(GAME_SAVE_KEY);
    failWrites = true;
    gameStore.getState().setQuietView(false);
    await flushGameSave();
    assert.equal(values.get(GAME_SAVE_KEY), beforeFailedWrite);
    failWrites = false;
    gameStore.getState().setQuietView(false);
    await flushGameSave();
    assert.deepEqual(disk().futureWorld, extra.futureWorld);
    console.log(
      'PASS: failed reads/writes protect existing bytes and a subsequent successful save retains extras',
    );

    await load(null);
    await gameStore.getState().hatch('NEW GARDENER', 'SPROUT', 'BLOB');
    await flushGameSave();
    assert.equal(gameStore.getState().player?.grass, 20);
    assert.deepEqual(gameStore.getState().player?.deck, startingDeck);
    assert.equal(Object.hasOwn(disk(), 'futureWorld'), false);
    assert.equal(disk().saveVersion, SAVE_VERSION);
    console.log(
      'PASS: genuinely empty storage still creates the original starter without another account’s extensions',
    );

    const backupValues = () =>
      new Map([...values].filter(([key]) => key.startsWith(SAVE_BACKUP_PREFIX)));
    const request = () => {
      const token = gameStore.getState().requestSaveRecovery();
      assert.ok(token, 'Unreadable save must expose deliberate recovery');
      return token;
    };
    const rejected = ` \n${JSON.stringify({ ...extra, player: { ...p, grass: 'unreadable' } })}\n `;
    await load(rejected);
    const oldIdentity = gameStore.getState().identity;
    const untouched = new Map(values);
    const beforeRecovery = operations.length;
    assert.equal(await gameStore.getState().confirmSaveRecovery('unrequested'), false);
    const cancelled = request();
    gameStore.getState().cancelSaveRecovery();
    assert.equal(await gameStore.getState().confirmSaveRecovery(cancelled), false);
    const superseded = request();
    const current = request();
    assert.notEqual(current, superseded);
    assert.equal(await gameStore.getState().confirmSaveRecovery(superseded), false);
    await gameStore.getState().retrySaveLoad();
    assert.equal(await gameStore.getState().confirmSaveRecovery(current), false);
    assert.deepEqual(values, untouched, 'Request/cancel/reload/stale confirmations write nothing');
    assert.equal(
      operations.slice(beforeRecovery).some((op) => op.kind === 'write'),
      false,
    );
    console.log(
      'PASS: recovery requires the current explicit confirmation; cancel and reload invalidate it',
    );

    const start = operations.length;
    assert.equal(await gameStore.getState().confirmSaveRecovery(request()), true);
    const recoveryOps = operations.slice(start);
    const recoveryWrites = recoveryOps.filter((op) => op.kind === 'write');
    assert.equal(recoveryWrites.length, 2);
    assert.ok(recoveryWrites[0].key.startsWith(SAVE_BACKUP_PREFIX));
    assert.equal(recoveryWrites[0].value, rejected, 'Keep exact bytes, including whitespace');
    assert.equal(recoveryWrites[1].key, GAME_SAVE_KEY);
    const backupKey = recoveryWrites[0].key;
    assert.equal(values.get(backupKey), rejected);
    assert.equal(gameStore.getState().saveLoadProblem, null);
    assert.equal(gameStore.getState().player, null, 'Successful recovery returns to onboarding');
    assert.notEqual(gameStore.getState().identity, oldIdentity);
    assert.equal(disk().player, null);
    assert.equal(Object.hasOwn(disk(), 'futureWorld'), false);
    for (const field of [
      'recentBreaks',
      'tips',
      'pendingMemories',
      'companionMemories',
      'outgoing',
      'staged',
      'applied',
      'alerts',
      'collectedCards',
      'pendingTogetherWakes',
      'togetherSettled',
      'seenSessions',
    ])
      assert.deepEqual(disk()[field], [], `Fresh garden clears ${field}`);
    for (const field of [
      'breakId',
      'activeBreakContext',
      'offDeck',
      'waitingVisitor',
      'cardReward',
      'togetherId',
    ])
      assert.equal(disk()[field], null, `Fresh garden clears ${field}`);
    assert.equal(disk().missionReturnPending, false);
    assert.equal(disk().quietView, false);
    const recoveredIdentity = gameStore.getState().identity;
    await reload();
    assert.equal(gameStore.getState().saveLoadProblem, null);
    assert.equal(gameStore.getState().player, null);
    assert.equal(gameStore.getState().identity, recoveredIdentity);
    assert.equal(values.get(backupKey), rejected);
    await gameStore.getState().hatch('RECOVERED', 'SPROUT', 'BLOB');
    await reload();
    assert.equal(gameStore.getState().player?.grass, 20);
    assert.deepEqual(gameStore.getState().player?.deck, startingDeck);
    assert.equal(Object.hasOwn(disk(), 'futureWorld'), false);
    assert.equal(values.get(backupKey), rejected);
    console.log(
      'PASS: raw backup precedes fresh save; onboarding/reload keeps starter rules and never carries rejected extensions',
    );

    await load('{double tap');
    const entered = deferred();
    const release = deferred();
    beforeWrite = async (key) => {
      if (key.startsWith(SAVE_BACKUP_PREFIX)) {
        entered.resolve();
        await release.promise;
      }
    };
    const busyToken = request();
    const completion = gameStore.getState().confirmSaveRecovery(busyToken);
    await entered.promise;
    assert.equal(gameStore.getState().requestSaveRecovery(), null);
    assert.equal(await gameStore.getState().confirmSaveRecovery(busyToken), false);
    gameStore.getState().cancelSaveRecovery();
    await gameStore.getState().retrySaveLoad();
    const busyProblem = gameStore.getState().saveLoadProblem;
    assert.equal(busyProblem?.kind === 'unreadable' && busyProblem.busy, true);
    await gameStore.getState().hatch('TOO EARLY', 'WAIT', 'BLOB');
    gameStore.getState().setQuietView(true);
    assert.equal(values.get(GAME_SAVE_KEY), '{double tap');
    assert.equal(gameStore.getState().player, null);
    let flushed = false;
    const flush = flushGameSave().then(() => {
      flushed = true;
    });
    await Promise.resolve();
    assert.equal(flushed, false, 'Flush must wait for the recovery transaction');
    release.resolve();
    assert.equal(await completion, true);
    await flush;
    beforeWrite = null;
    assert.equal(flushed, true);
    assert.equal(gameStore.getState().quietView, false);
    console.log(
      'PASS: double taps, hatch, cancel and retry cannot interrupt an in-flight backup; flush waits',
    );

    for (const failAt of ['backup', 'primary', 'read'] as const) {
      const raw = `{failed ${failAt}`;
      await load(raw);
      const before = backupValues();
      failWriteKey = (key) =>
        failAt === 'backup'
          ? key.startsWith(SAVE_BACKUP_PREFIX)
          : failAt === 'primary' && key === GAME_SAVE_KEY;
      failReads = failAt === 'read';
      assert.equal(await gameStore.getState().confirmSaveRecovery(request()), false);
      failReads = false;
      failWriteKey = null;
      assert.equal(values.get(GAME_SAVE_KEY), raw);
      const problem = gameStore.getState().saveLoadProblem;
      assert.equal(problem?.kind, 'unreadable');
      assert.equal(problem?.kind === 'unreadable' && problem.busy, false);
      assert.equal(problem?.kind === 'unreadable' && problem.confirmationId, null);
      for (const [key, value] of before) assert.equal(values.get(key), value);
      assert.equal(backupValues().size - before.size, failAt === 'primary' ? 1 : 0);
      const retained = backupValues();
      assert.equal(await gameStore.getState().confirmSaveRecovery(request()), true);
      for (const [key, value] of retained) assert.equal(values.get(key), value);
      assert.equal(backupValues().size, retained.size + 1, 'A retry uses a new backup key');
    }
    console.log(
      'PASS: backup/read/replacement failures keep primary bytes and all earlier backups; retries use unique keys',
    );

    for (const duringBackup of [false, true]) {
      const raw = '{changed in another tab';
      await load(raw);
      const token = request();
      const before = backupValues();
      if (duringBackup)
        beforeWrite = async (key) => {
          if (key.startsWith(SAVE_BACKUP_PREFIX)) values.set(GAME_SAVE_KEY, protectedBytes);
        };
      else values.set(GAME_SAVE_KEY, protectedBytes);
      assert.equal(await gameStore.getState().confirmSaveRecovery(token), false);
      beforeWrite = null;
      assert.equal(values.get(GAME_SAVE_KEY), protectedBytes);
      assert.equal(gameStore.getState().saveLoadProblem?.kind, 'storage');
      assert.equal(gameStore.getState().requestSaveRecovery(), null);
      assert.equal(backupValues().size - before.size, duringBackup ? 1 : 0);
      await gameStore.getState().retrySaveLoad();
      assert.equal(gameStore.getState().player?.id, record(extra.player).id);
      assert.equal(gameStore.getState().saveLoadProblem, null);
      assert.equal(await gameStore.getState().confirmSaveRecovery(token), false);
    }
    console.log(
      'PASS: a changed primary save aborts recovery before replacement and can be loaded normally',
    );

    const keysBefore = new Map(values);
    for (const newer of [true, false]) {
      if (newer) await load(JSON.stringify({ ...extra, saveVersion: SAVE_VERSION + 1 }));
      else {
        failReads = true;
        await load(protectedBytes);
        failReads = false;
      }
      assert.equal(gameStore.getState().saveLoadProblem?.kind, newer ? 'newer' : 'storage');
      assert.equal(gameStore.getState().requestSaveRecovery(), null);
      const writesBefore = writes;
      assert.equal(await gameStore.getState().confirmSaveRecovery('never'), false);
      assert.equal(writes, writesBefore);
      if (newer) assert.match(gameStore.getState().message!, /UPDATE THE APP/);
    }
    for (const [key, value] of keysBefore)
      if (key !== GAME_SAVE_KEY) assert.equal(values.get(key), value);
    assert.equal(
      operations.some((op) => op.kind === 'read' && op.key.startsWith(SAVE_BACKUP_PREFIX)),
      false,
      'Backups must never be read by the app',
    );
    console.log(
      'PASS: future versions and storage failures expose no fresh-start action; backups are never read or removed',
    );

    const readEntered = deferred();
    const readRelease = deferred();
    let loadReads = 0;
    beforeRead = async () => {
      loadReads++;
      readEntered.resolve();
      await readRelease.promise;
    };
    values.set(GAME_SAVE_KEY, protectedBytes);
    gameStore.setState({ ready: false });
    const firstLoad = gameStore.getState().init();
    const secondLoad = gameStore.getState().init();
    await readEntered.promise;
    assert.equal(loadReads, 1);
    readRelease.resolve();
    await Promise.all([firstLoad, secondLoad]);
    beforeRead = null;
    await flushGameSave();
    assert.equal(gameStore.getState().player?.id, record(extra.player).id);
    assert.deepEqual(disk().futureWorld, extra.futureWorld);
    console.log('PASS: concurrent initialization shares one read and preserves valid progress');

    values.set(GAME_SAVE_KEY, '{retry from a subscriber');
    gameStore.setState({ ready: false });
    let retry = Promise.resolve();
    let retried = false;
    const unsubscribe = gameStore.subscribe((state) => {
      if (!state.saveLoadProblem || retried) return;
      retried = true;
      values.set(GAME_SAVE_KEY, protectedBytes);
      retry = state.retrySaveLoad();
    });
    await gameStore.getState().init();
    await retry;
    unsubscribe();
    await flushGameSave();
    assert.equal(retried, true);
    assert.equal(gameStore.getState().ready, true);
    assert.equal(gameStore.getState().saveLoadProblem, null);
    assert.equal(gameStore.getState().player?.id, record(extra.player).id);
    console.log(
      'PASS: a retry requested during a failing load performs a new read after it settles',
    );

    let live = true;
    const raw = '{stale generation';
    const simulated = new Map([[GAME_SAVE_KEY, raw]]);
    const calls: string[] = [];
    await assert.rejects(
      backupBeforeFreshStart(
        {
          async getItem(key) {
            return simulated.get(key) ?? null;
          },
          async setItem(key, value) {
            calls.push(key);
            simulated.set(key, value);
            live = false;
          },
        },
        { expectedRaw: raw, freshRaw: '{}', backupId: 'test-generation', isCurrent: () => live },
      ),
      SaveRecoveryChangedError,
    );
    assert.deepEqual(calls, [SAVE_BACKUP_PREFIX + 'test-generation']);
    assert.equal(simulated.get(GAME_SAVE_KEY), raw);
    await assert.rejects(
      backupBeforeFreshStart(storage, {
        expectedRaw: raw,
        freshRaw: '{}',
        backupId: ' ',
        isCurrent: () => true,
      }),
      /backup ID/,
    );
    console.log('PASS: a stale generation after backup cannot replace primary data');
  } finally {
    Date.now = realNow;
    globalThis.fetch = realFetch;
    if (oldUrl === undefined) delete process.env.EXPO_PUBLIC_BILT_URL;
    else process.env.EXPO_PUBLIC_BILT_URL = oldUrl;
    if (oldKey === undefined) delete process.env.EXPO_PUBLIC_BILT_ANON_KEY;
    else process.env.EXPO_PUBLIC_BILT_ANON_KEY = oldKey;
    delete (globalThis as Record<symbol, unknown>)[boundaryKey];
    hooks.deregister();
  }
}

void main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
