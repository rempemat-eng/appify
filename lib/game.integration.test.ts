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
      const values = new Map();
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
    const { gameStore, flushGameSave, bot } = await import('./game');
    const { bilt, backendConfigured, backendUnavailableMessage } = await import('./bilt');
    const { collectionOf } = await import('./visitors');
    const { runRefinementChecks } = await import('./refinement.qa');
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
    lines.push(...(await runRefinementChecks()));
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
