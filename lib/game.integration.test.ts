import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { isDeepStrictEqual } from 'node:util';
import type { TogetherSession } from './game';

// Test-only native boundaries. Game rules, store methods, cards, visitors and
// backend availability are all imported from the actual source below.
const boundaries = new Map([
  [
    '@react-native-async-storage/async-storage',
    `
      // tsx can load a boundary through both import paths. Both handles must
      // address the same simulated device storage for save-migration checks.
      const storageKey = Symbol.for('napattack.integration.storage');
      const values = globalThis[storageKey] ??= new Map();
      export default {
        async getItem(key) { return values.get(key) ?? null; },
        async setItem(key, value) { values.set(key, value); },
        async removeItem(key) { values.delete(key); },
        async clear() { values.clear(); },
        async getAllKeys() { return [...values.keys()]; }
      };
    `,
  ],
  [
    'react-native',
    `
      export const Platform = { OS: 'web' };
      export const AppState = {
        currentState: 'active',
        addEventListener() { return { remove() {} }; }
      };
      export const Vibration = { vibrate() {} };
    `,
  ],
  [
    'expo-crypto',
    `
      import { randomBytes } from 'node:crypto';
      export { randomUUID } from 'node:crypto';
      export function getRandomBytes(size) { return new Uint8Array(randomBytes(size)); }
    `,
  ],
  [
    'expo-haptics',
    `
      export const ImpactFeedbackStyle = { Light: 'light', Medium: 'medium', Heavy: 'heavy' };
      export const NotificationFeedbackType = { Success: 'success', Error: 'error' };
      export async function impactAsync() {}
      export async function selectionAsync() {}
      export async function notificationAsync() {}
    `,
  ],
]);

const hooks = registerHooks({
  resolve(specifier, context, nextResolve) {
    const source = boundaries.get(specifier);
    return source === undefined
      ? nextResolve(specifier, context)
      : { url: `data:text/javascript,${encodeURIComponent(source)}`, shortCircuit: true };
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

async function main() {
  delete process.env.EXPO_PUBLIC_BILT_URL;
  delete process.env.EXPO_PUBLIC_BILT_ANON_KEY;
  const realNow = Date.now;
  const realFetch = globalThis.fetch;
  let now = realNow();
  let requests = 0;
  Date.now = () => now;
  globalThis.fetch = async () => {
    requests++;
    throw new Error('Unexpected network request in source integration check');
  };
  try {
    const { gameStore, flushGameSave, bot, accountPlay, status } = await import('./game');
    const { bilt, backendConfigured, backendUnavailableMessage } = await import('./bilt');
    const { collectionOf, guardianPlayer } = await import('./visitors');
    const { runRefinementChecks, qaPlayer } = await import('./refinement.qa');
    const lines: string[] = [];
    const check = (ok: boolean, label: string) => {
      assert.ok(ok, label);
      lines.push(`PASS: ${label}`);
    };
    const reload = async () => {
      await flushGameSave();
      gameStore.setState({ ready: false, player: null });
      await gameStore.getState().init();
      await flushGameSave();
    };

    check(bilt === null && !backendConfigured, 'Actual backend boundary starts in local mode');
    await gameStore.getState().init();
    check(
      gameStore.getState().ready && !gameStore.getState().player,
      'Empty storage opens onboarding state',
    );
    await gameStore.getState().hatch('GARDENER', 'SPROUT', 'BLOB');
    const identity = gameStore.getState().player!.id;
    check(
      gameStore.getState().player!.grass === 20 && gameStore.getState().player!.deck.length === 7,
      'Actual hatch creates the original 20-GRASS, seven-card starter',
    );
    gameStore.getState().sleep();
    now += 31_000;
    gameStore.getState().tick();
    await gameStore.getState().wake();
    await flushGameSave();
    const reward = gameStore.getState().cardReward!;
    const receipt = gameStore.getState().recentBreaks[0];
    check(
      reward.minutes === 31 &&
        reward.grass === 31 &&
        reward.cards.length === 2 &&
        gameStore.getState().player!.grass === 51 &&
        receipt.id === reward.settlementId &&
        receipt.minutes === 31 &&
        receipt.grass === 31 &&
        receipt.cards === 2,
      'Hatch → 31-MIN nap → wake creates the matching settled receipt',
    );
    const settled = structuredClone({ player: gameStore.getState().player, reward, receipt });
    await reload();
    await gameStore.getState().wake();
    check(
      gameStore.getState().player!.id === identity &&
        isDeepStrictEqual(
          {
            player: gameStore.getState().player,
            reward: gameStore.getState().cardReward,
            receipt: gameStore.getState().recentBreaks[0],
          },
          settled,
        ),
      'Reload keeps identity, rewards and receipt without a second settlement',
    );
    const visitor = gameStore.getState().waitingVisitor!.id;
    gameStore.getState().befriendVisitor();
    gameStore.getState().befriendVisitor();
    gameStore.getState().selectGuardian(visitor);
    await reload();
    check(
      collectionOf(gameStore.getState().player!).length === 1 &&
        collectionOf(gameStore.getState().player!)[0].befriendedAt !== null &&
        gameStore.getState().player!.guardian === visitor &&
        !gameStore.getState().waitingVisitor,
      'Actual first visitor can be befriended once and selected across reload',
    );
    const beforeSwitching = structuredClone(gameStore.getState().player!);
    gameStore.getState().selectGuardian('skyfern');
    check(
      isDeepStrictEqual(gameStore.getState().player, beforeSwitching),
      'An unbefriended companion cannot be selected',
    );
    const roster = [
      ...collectionOf(beforeSwitching),
      { id: 'trailhop' as const, metAt: now, minutes: 15, befriendedAt: 0 },
      { id: 'inkling' as const, metAt: now, minutes: 15, befriendedAt: now },
    ];
    gameStore.getState().change({ collection: roster });
    for (const [id, species] of [
      ['trailhop', 'RAT'],
      ['inkling', 'CUBE'],
    ] as const) {
      const before = structuredClone(gameStore.getState().player!);
      gameStore.getState().selectGuardian(id);
      await reload();
      const after = gameStore.getState().player!;
      check(
        after.guardian === id && guardianPlayer(after).species === species,
        `Switching to ${id} persists the effective battle and mission family`,
      );
      check(
        isDeepStrictEqual({ ...after, guardian: before.guardian }, before),
        `Switching to ${id} preserves all account progress and costs no GRASS`,
      );
    }
    gameStore.getState().change({ mode: 'mission' });
    gameStore.getState().selectGuardian('trailhop');
    check(
      gameStore.getState().player!.guardian === 'inkling',
      'Companions cannot change during a mission',
    );
    gameStore.getState().change({ mode: 'screen_off' });
    gameStore.getState().selectGuardian('trailhop');
    check(
      gameStore.getState().player!.guardian === 'inkling',
      'Companions cannot change during a nap',
    );
    gameStore.getState().change({ mode: 'awake' });
    gameStore.setState({ battle: { target: bot(beforeSwitching), practice: true } });
    gameStore.getState().selectGuardian('trailhop');
    check(
      gameStore.getState().player!.guardian === 'inkling',
      'Companions cannot change during a battle',
    );
    gameStore.setState({ battle: null });
    gameStore.getState().selectGuardian(null);
    await reload();
    check(
      gameStore.getState().player!.guardian === null &&
        guardianPlayer(gameStore.getState().player!).pet_name === beforeSwitching.pet_name &&
        guardianPlayer(gameStore.getState().player!).species === beforeSwitching.species,
      'Returning to the starter restores the original name and family across reload',
    );
    gameStore.getState().change(beforeSwitching);
    await reload();
    gameStore.getState().hatAction('CAP');
    await reload();
    check(
      gameStore.getState().player!.grass === 21 &&
        gameStore.getState().player!.hat === 'CAP' &&
        gameStore.getState().player!.owned_hats.includes('CAP'),
      'Local hat purchase debits its actual price and persists ownership/equipment',
    );
    const rival = bot(gameStore.getState().player!);
    const pairing = await gameStore.getState().pair(rival.code === 'ZZZZ' ? 'YYYY' : 'ZZZZ');
    check(
      pairing === backendUnavailableMessage,
      'Pairing returns an explicit no-backend explanation',
    );
    await gameStore.getState().inviteTogether(rival);
    check(
      gameStore.getState().message === backendUnavailableMessage &&
        !gameStore.getState().togetherPending,
      'Together invitation stops cleanly without leaving a connecting state',
    );
    const invitation: TogetherSession = {
      id: 'integration-invitation',
      player_a: rival.id,
      player_b: identity,
      status: 'invited',
      started_at: null,
      woke_a_at: null,
      woke_b_at: null,
      failed_by: null,
      grass_a: 0,
      grass_b: 0,
    };
    await gameStore.getState().acceptTogether(invitation);
    check(
      gameStore.getState().message === backendUnavailableMessage &&
        !gameStore.getState().togetherId &&
        !gameStore.getState().togetherPending,
      'Together acceptance does not manufacture an online session',
    );
    await gameStore.getState().startBattle(rival);
    check(
      gameStore.getState().message === backendUnavailableMessage &&
        !gameStore.getState().battle &&
        gameStore.getState().player!.grass === 21,
      'Player raid is blocked without spending GRASS or creating a battle',
    );
    await gameStore.getState().startBattle(rival, true);
    check(Boolean(gameStore.getState().battle?.practice), 'Local sparring can still start');
    gameStore.getState().finishBattle(true, rival, true);
    check(
      gameStore.getState().player!.grass === 26 &&
        !gameStore.getState().battle &&
        gameStore.getState().outgoing.length === 0,
      'Actual sparring win pays 5 GRASS and creates no player raid',
    );
    await flushGameSave();
    // C9: real store settlements in disposable storage. A precondition battle
    // fixture exercises finishBattle; it does not simulate online authorisation.
    {
      const baseCurrencyState = gameStore.getState();
      const baseCurrencyPlayer = baseCurrencyState.player!;
      const { default: currencyStorage } =
        await import('@react-native-async-storage/async-storage');
      const { GAME_SAVE_KEY } = await import('./save-data');
      const { moveTo } = await import('./world-save');
      const { regionPoint, travelPoints } = await import('./world-places');
      const originalCurrencySave = await currencyStorage.getItem(GAME_SAVE_KEY);
      assert.ok(originalCurrencySave);
      const originalRandom = Math.random;
      const resetCurrency = (grass: number, mood = 80) => {
        gameStore.setState({
          ...baseCurrencyState,
          player: { ...baseCurrencyPlayer, grass, mood, care_until: 0, recovery_until: 0 },
          rules: { ...baseCurrencyState.rules, budget: { startedAt: 0, usedMs: 0 }, days: {} },
          battle: null,
          alerts: [],
          staged: [],
          outgoing: [],
          applied: [],
          recap: null,
          flash: null,
        });
        accountPlay(now);
      };
      try {
        const legacyWallet = JSON.parse(originalCurrencySave);
        delete legacyWallet.saveVersion;
        legacyWallet.player.grass = 500.25;
        legacyWallet.player.care_until = 0;
        legacyWallet.player.recovery_until = 0;
        legacyWallet.player.collection = [
          { id: 'inkling', metAt: now, minutes: 15, befriendedAt: now },
        ];
        legacyWallet.player.guardian = 'inkling';
        legacyWallet.futureEconomyField = { keep: 'verbatim' };
        legacyWallet.player.futureWalletField = ['keep', 17];
        const station = regionPoint(travelPoints.west!);
        const visitedWorld = moveTo(null, 'west', station.x, station.y);
        legacyWallet.world = { ...visitedWorld, futureTravelField: { keep: 'verbatim' } };
        await currencyStorage.setItem(GAME_SAVE_KEY, JSON.stringify(legacyWallet));
        await reload();
        check(
          gameStore.getState().player!.grass === 500.25,
          'C9 legacy migration keeps the exact wallet',
        );
        check(
          isDeepStrictEqual(gameStore.getState().world, visitedWorld),
          'C9 legacy wallet migration retains the current world spot and visits',
        );
        Math.random = () => 0.25;
        gameStore.getState().incomingBot();
        const raid = gameStore.getState().alerts.at(-1)!.raid;
        check(
          raid.attacker_won &&
            raid.grass_amount === 0 &&
            gameStore.getState().player!.grass === 500.25,
          'C9 simulated lost defence has zero transfer and never debits GRASS',
        );
        await reload();
        check(
          gameStore.getState().player!.grass === 500.25 &&
            gameStore.getState().applied.filter((id) => id === raid.id).length === 1,
          'C9 lost defence reload keeps wallet and one settlement marker',
        );
        const savedCurrency = JSON.parse((await currencyStorage.getItem(GAME_SAVE_KEY))!);
        check(
          isDeepStrictEqual(savedCurrency.futureEconomyField, legacyWallet.futureEconomyField) &&
            isDeepStrictEqual(
              savedCurrency.player.futureWalletField,
              legacyWallet.player.futureWalletField,
            ),
          'C9 settlement preserves unknown root and player save fields',
        );
        check(
          savedCurrency.saveVersion === 1 &&
            isDeepStrictEqual(gameStore.getState().world, visitedWorld) &&
            isDeepStrictEqual(savedCurrency.world, legacyWallet.world),
          'C9 defence settlement preserves optional world and unknown world fields in the v1 save',
        );
        for (const key of [
          'level',
          'owned_hats',
          'hat',
          'deck',
          'collection',
          'postcards',
          'guardian',
          'offline_seconds',
        ] as const)
          check(
            isDeepStrictEqual(gameStore.getState().player![key], legacyWallet.player[key]),
            `C9 lost defence/reload preserves ${key}`,
          );

        resetCurrency(500);
        Math.random = () => 0.75;
        gameStore.getState().incomingBot();
        check(
          gameStore.getState().player!.grass === 520,
          'C9 successful defence retains the old +20 reward',
        );
        await reload();
        check(gameStore.getState().player!.grass === 520, 'C9 defence reload never credits twice');

        for (const won of [false, true]) {
          resetCurrency(500);
          const target = { ...baseCurrencyPlayer, id: 'currency-rival', grass: 100 };
          gameStore.setState({ battle: { target, practice: false } });
          gameStore.getState().finishBattle(won, target, false);
          const raidCurrencyState = gameStore.getState();
          check(
            raidCurrencyState.player!.grass === (won ? 530 : 500) &&
              raidCurrencyState.outgoing[0].grass_amount === 0,
            `C9 attacker ${won ? 'win keeps its reward' : 'loss keeps its wallet'} with zero wire debit`,
          );
          check(target.grass === 100, 'C9 settlement never mutates the rival wallet');
          gameStore.getState().finishBattle(won, target, false);
          check(
            gameStore.getState().player!.grass === raidCurrencyState.player!.grass &&
              gameStore.getState().outgoing.length === 1,
            'C9 duplicate finish cannot settle or enqueue twice',
          );
          await reload();
          check(
            gameStore.getState().player!.grass === raidCurrencyState.player!.grass &&
              gameStore.getState().outgoing[0].grass_amount === 0,
            'C9 attacker settlement and safe pending transport survive reload',
          );
        }

        for (const won of [false, true]) {
          resetCurrency(500.25);
          gameStore.setState({ world: visitedWorld });
          const target = { ...baseCurrencyPlayer, id: 'world-rival', grass: 100 };
          gameStore.setState({ battle: { target, practice: false } });
          gameStore.getState().finishBattle(won, target, false);
          await reload();
          check(
            isDeepStrictEqual(gameStore.getState().world, visitedWorld) &&
              gameStore.getState().player!.grass === (won ? 530.25 : 500.25),
            `C9 attacking ${won ? 'win' : 'loss'} keeps world progress alongside fractional wallet`,
          );
        }

        resetCurrency(100, 50);
        gameStore.getState().feed();
        check(gameStore.getState().player!.grass === 95, 'C9 feeding still deliberately costs 5');
        resetCurrency(100);
        const levelCost = 50 * baseCurrencyPlayer.level;
        gameStore.getState().levelUp();
        check(
          gameStore.getState().player!.grass === 100 - levelCost,
          'C9 level purchase keeps its old cost',
        );
        resetCurrency(100);
        gameStore.setState({
          player: { ...gameStore.getState().player!, owned_hats: [], hat: null },
        });
        gameStore.getState().hatAction('CAP');
        check(
          gameStore.getState().player!.grass === 70,
          'C9 hat purchase still deliberately costs 30',
        );
      } finally {
        Math.random = originalRandom;
        await flushGameSave();
        await currencyStorage.setItem(GAME_SAVE_KEY, originalCurrencySave);
        gameStore.setState(baseCurrencyState);
        await reload();
      }
    }
    lines.push(...(await runRefinementChecks()));
    const { freshRules } = await import('./offline-rules');
    const { default: storage } = await import('@react-native-async-storage/async-storage');
    now += 3_600_000;
    const memoryPlayer = qaPlayer(now);
    gameStore.setState({
      player: {
        ...memoryPlayer,
        collection: [{ id: 'inkling', metAt: now, minutes: 15, befriendedAt: now }],
      },
      identity: memoryPlayer.id,
      tickAt: now,
      rules: freshRules(now),
      battle: null,
      togetherId: null,
      cardReward: null,
      waitingVisitor: null,
      recentBreaks: [],
      breakId: null,
      activeBreakContext: null,
      pendingMemories: [],
      companionMemories: [],
      memoryResolvedIds: [],
    });
    gameStore.getState().sleep(undefined, 'read');
    const originalContext = structuredClone(gameStore.getState().activeBreakContext);
    gameStore.getState().change({ guardian: 'inkling', pet_name: 'LATER NAME' });
    await reload();
    check(
      isDeepStrictEqual(gameStore.getState().activeBreakContext, originalContext),
      'An active intention and the original starter identity survive reload and later account edits',
    );
    now += 4_000;
    gameStore.getState().tick();
    check(
      gameStore.getState().companionMemories.length === 0 &&
        gameStore.getState().pendingMemories.length === 0,
      'Elapsed time alone never records an activity or creates a pre-settlement reflection',
    );
    await gameStore.getState().wake();
    const starterOffer = gameStore.getState().pendingMemories[0];
    check(
      starterOffer.id === gameStore.getState().cardReward!.settlementId &&
        starterOffer.companion.key === 'starter' &&
        starterOffer.companion.name === memoryPlayer.pet_name &&
        starterOffer.intention === 'read' &&
        starterOffer.minutes === 4 &&
        !gameStore.getState().activeBreakContext,
      'A settled break offers a reflection for the companion and intention captured at its start',
    );
    const progressSnapshot = () =>
      structuredClone({
        player: gameStore.getState().player,
        rules: gameStore.getState().rules,
        reward: gameStore.getState().cardReward,
        history: gameStore.getState().recentBreaks,
      });
    const beforeRecording = progressSnapshot();
    gameStore.getState().recordCompanionMemory(starterOffer.id);
    gameStore.getState().recordCompanionMemory(starterOffer.id);
    gameStore.getState().dismissCompanionMemory(starterOffer.id);
    await reload();
    await gameStore.getState().wake();
    check(
      gameStore.getState().companionMemories.length === 1 &&
        gameStore.getState().companionMemories[0].source === 'self-reported' &&
        gameStore.getState().companionMemories[0].companion.key === 'starter' &&
        gameStore.getState().pendingMemories.length === 0,
      'Explicit acknowledgement records once across repeated actions and reload, even after changing pets',
    );
    check(
      isDeepStrictEqual(progressSnapshot(), beforeRecording),
      'Recording a memory changes no currency, level, mood, cards, rewards, history or budget',
    );
    gameStore.getState().sleep('book', 'create');
    now += 3_000;
    await gameStore.getState().wake();
    const earlyOffer = gameStore.getState().pendingMemories[0];
    check(
      earlyOffer.companion.key === 'inkling' &&
        earlyOffer.companion.species === 'CUBE' &&
        earlyOffer.early &&
        earlyOffer.mission === 'book' &&
        earlyOffer.intention === 'create' &&
        gameStore.getState().cardReward!.early &&
        !gameStore.getState().cardReward!.postcard,
      'An early mission return offers an honest optional reflection without claiming mission completion',
    );
    const beforeSkipping = progressSnapshot();
    gameStore.getState().dismissCompanionMemory(earlyOffer.id);
    gameStore.getState().recordCompanionMemory(earlyOffer.id);
    await reload();
    check(
      !gameStore.getState().pendingMemories.length &&
        gameStore.getState().companionMemories.length === 1 &&
        gameStore.getState().memoryResolvedIds.includes(earlyOffer.id) &&
        isDeepStrictEqual(progressSnapshot(), beforeSkipping),
      'Skipping survives reload, cannot later record the dismissed offer and affects no progress',
    );
    now += 1000;
    gameStore.getState().sleep('park', 'move');
    now += 15_000;
    gameStore.getState().tick();
    const missionOffer = structuredClone(gameStore.getState().pendingMemories[0]);
    const pendingMission = structuredClone({
      player: gameStore.getState().player,
      reward: gameStore.getState().cardReward,
      history: gameStore.getState().recentBreaks,
      budget: gameStore.getState().rules.budget,
    });
    check(
      gameStore.getState().missionReturnPending &&
        status(gameStore.getState().player!, now).kind === 'safe',
      'Completed Park stays in its shielded mission until an explicit return',
    );
    gameStore.getState().setQuietView(true);
    now += 90_000;
    gameStore.getState().tick();
    accountPlay(now);
    await reload();
    check(
      gameStore.getState().missionReturnPending &&
        gameStore.getState().quietView &&
        isDeepStrictEqual(
          {
            player: gameStore.getState().player,
            reward: gameStore.getState().cardReward,
            history: gameStore.getState().recentBreaks,
            budget: gameStore.getState().rules.budget,
          },
          pendingMission,
        ),
      'Waiting 90 seconds and reloading spends no play time, changes no mood and repeats no settlement',
    );
    const returnAt = now;
    gameStore.getState().dismissCards();
    const returned = gameStore.getState();
    check(
      !returned.missionReturnPending &&
        returned.player!.mode === 'awake' &&
        returned.player!.care_until === returnAt + 30_000 &&
        returned.player!.mission_id === null &&
        returned.player!.mission_ends_at === 0 &&
        !returned.cardReward &&
        isDeepStrictEqual(returned.recentBreaks, pendingMission.history),
      'Returning to the garden starts a full care window without adding rewards or history',
    );
    now += 3_000;
    gameStore.getState().tick();
    gameStore.getState().dismissCards();
    check(
      gameStore.getState().rules.budget.usedMs === 3_000 &&
        gameStore.getState().player!.mood === pendingMission.player!.mood - 1 &&
        gameStore.getState().player!.care_until === returnAt + 30_000,
      'Play time and mood resume after return; repeated dismissal does not renew the care window',
    );
    gameStore.getState().sleep('park');
    check(gameStore.getState().quietView, 'Quiet view remains selected for the next break');
    now += 15_000;
    // A direct wake at the deadline must complete, never forfeit the mission.
    await gameStore.getState().wake();
    check(
      !gameStore.getState().missionReturnPending &&
        gameStore.getState().player!.mode === 'awake' &&
        gameStore.getState().cardReward?.early === false &&
        gameStore.getState().cardReward?.grass === 20,
      'Wake at the exact mission deadline preserves successful completion',
    );
    await reload();
    await gameStore.getState().wake();
    gameStore.getState().tick();
    check(
      gameStore.getState().player!.mode === 'awake' &&
        missionOffer.mission === 'park' &&
        !missionOffer.early &&
        isDeepStrictEqual(gameStore.getState().pendingMemories, [missionOffer]) &&
        !gameStore.getState().activeBreakContext &&
        gameStore.getState().companionMemories.length === 1,
      'Automatic mission settlement offers once; reload and wake never auto-acknowledge or duplicate it',
    );
    for (let i = 0; i < 6; i++) {
      now += 1000;
      gameStore.getState().sleep(undefined, 'rest');
      now += 1000;
      await gameStore.getState().wake();
    }
    await reload();
    const queued = gameStore.getState().pendingMemories;
    check(
      queued.length === 5 && new Set(queued.map((offer) => offer.id)).size === 5,
      'Repeated intended breaks queue separate reflections in a bounded five-offer backlog across reload',
    );
    const beforeUnintended = structuredClone(queued);
    now += 1000;
    gameStore.getState().sleep();
    now += 2000;
    await gameStore.getState().wake();
    now += 1000;
    gameStore.getState().sleep(undefined, 'rest');
    await gameStore.getState().wake();
    check(
      isDeepStrictEqual(gameStore.getState().pendingMemories, beforeUnintended) &&
        !gameStore.getState().activeBreakContext,
      'Just-a-break and zero-length intended breaks add no offer and leave no stale intention',
    );
    const loadPatchedSave = async (patch: (saved: Record<string, unknown>) => void) => {
      await flushGameSave();
      const saved = JSON.parse((await storage.getItem('screenagotchi-v1'))!);
      patch(saved);
      await storage.setItem('screenagotchi-v1', JSON.stringify(saved));
      gameStore.setState({ ready: false, player: null });
      await gameStore.getState().init();
      await flushGameSave();
    };
    await loadPatchedSave((saved) => {
      saved.pendingMemories = [null, { id: 'forged' }, ...queued, ...queued];
      saved.companionMemories = [null, {}, ...gameStore.getState().companionMemories];
      saved.memoryResolvedIds = ['', null, 8, ...gameStore.getState().memoryResolvedIds];
      saved.activeBreakContext = originalContext;
      saved.missionReturnPending = true;
      saved.quietView = 'not a preference';
    });
    check(
      gameStore.getState().player?.id === memoryPlayer.id &&
        gameStore.getState().pendingMemories.length === 5 &&
        gameStore.getState().companionMemories.length === 1 &&
        !gameStore.getState().activeBreakContext &&
        !gameStore.getState().missionReturnPending &&
        !gameStore.getState().quietView &&
        gameStore.getState().message !== 'COULD NOT LOAD YOUR GRASSLING. TRY REOPENING THE APP.',
      'Malformed optional save fields are sanitised without losing the valid account or existing memories',
    );
    now += 1000;
    gameStore.getState().sleep(undefined, 'read');
    await loadPatchedSave((saved) => {
      delete saved.activeBreakContext;
      delete saved.pendingMemories;
      delete saved.companionMemories;
      delete saved.memoryResolvedIds;
      delete saved.missionReturnPending;
      delete saved.quietView;
    });
    now += 2000;
    await gameStore.getState().wake();
    check(
      gameStore.getState().player?.id === memoryPlayer.id &&
        !gameStore.getState().activeBreakContext &&
        gameStore.getState().pendingMemories.length === 0 &&
        gameStore.getState().companionMemories.length === 0,
      'Legacy active-break saves default to no intention and do not invent an activity offer',
    );
    check(
      !gameStore.getState().missionReturnPending && !gameStore.getState().quietView,
      'Legacy saves preserve the account with safe defaults for return protection and Quiet view',
    );
    now += 1000;
    gameStore.getState().sleep(undefined, 'rest');
    now += 2000;
    await gameStore.getState().wake();
    check(
      gameStore.getState().pendingMemories.length === 1,
      'A new intended break still works after legacy migration',
    );
    const deferredOffer = structuredClone(gameStore.getState().pendingMemories[0]);
    for (let i = 0; i < 21; i++) {
      now += 1000;
      gameStore.getState().sleep();
      now += 2000;
      await gameStore.getState().wake();
    }
    check(
      gameStore.getState().recentBreaks.length === 20 &&
        !gameStore.getState().recentBreaks.some((entry) => entry.id === deferredOffer.id),
      'More than 20 ordinary breaks archive the deferred reflection’s original reward receipt',
    );
    await reload();
    check(
      isDeepStrictEqual(gameStore.getState().pendingMemories, [deferredOffer]),
      'A deferred reflection survives reload after its rolling receipt has been archived',
    );
    const beforeDeferredRecording = progressSnapshot();
    gameStore.getState().recordCompanionMemory(deferredOffer.id);
    gameStore.getState().recordCompanionMemory(deferredOffer.id);
    await reload();
    gameStore.getState().recordCompanionMemory(deferredOffer.id);
    check(
      gameStore.getState().pendingMemories.length === 0 &&
        gameStore.getState().companionMemories.filter((entry) => entry.id === deferredOffer.id)
          .length === 1 &&
        isDeepStrictEqual(progressSnapshot(), beforeDeferredRecording),
      'The archived-receipt reflection can be recorded exactly once without altering any progress',
    );
    await gameStore.getState().hatch('NEW GARDENER', 'NEW PET', 'RAT');
    check(
      gameStore.getState().companionMemories.length === 0 &&
        gameStore.getState().pendingMemories.length === 0 &&
        gameStore.getState().memoryResolvedIds.length === 0 &&
        !gameStore.getState().activeBreakContext,
      'Hatching a fresh profile clears all previous companion memory state',
    );
    await flushGameSave();
    check(requests === 0, 'All credential-free integration paths made zero network requests');
    for (const line of lines) console.log(line);
    console.log(
      `PASS: ${lines.length} source integration checks; native boundaries substituted, no visual or real multiplayer validation.`,
    );
  } finally {
    Date.now = realNow;
    globalThis.fetch = realFetch;
    hooks.deregister();
  }
}

void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
