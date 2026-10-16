import { createClient } from '@biltme/backend';
import { bilt, backendUnavailableMessage } from '@/lib/bilt';
import {
  accountPlay,
  bot,
  flushGameSave,
  gameStore,
  resolveTogetherSession,
  type Player,
  type TogetherSession,
} from '@/lib/game';
import { cardIds, startingDeck, summarizeCardRewards } from '@/lib/cards';
import { dayKey, freshRules, remainingPlay } from '@/lib/offline-rules';
import { collectionOf, guardianPlayer, meetVisitor, postcardsOf } from '@/lib/visitors';
import { verifyFirstSession } from '@/lib/first-session.qa';
import { verifyVisitors } from '@/lib/visitors.qa';
import { runOfflineRuleChecks } from '@/lib/offline-rules.qa';

export function qaPlayer(at = Date.now()): Player {
  return {
    id: '00000000-0000-4000-8000-00000000aa01',
    code: 'QAAB',
    name: 'JUNIPER',
    pet_name: 'MOSS',
    species: 'BLOB',
    level: 1,
    grass: 20,
    mood: 80,
    mode: 'awake',
    care_until: at + 30000,
    recovery_until: 0,
    mission_id: null,
    mission_ends_at: 0,
    offline_seconds: 0,
    last_seen: at,
    owned_hats: [],
    hat: null,
    deck: [...startingDeck],
    collection: [],
    postcards: [],
    guardian: null,
  };
}
function stableSnapshot(value: unknown): string {
  return JSON.stringify(value, (_key: string, item: unknown) => {
    if (item === null || typeof item !== 'object' || Array.isArray(item)) return item;
    return Object.fromEntries(
      Object.entries(item).sort(([left], [right]) => left.localeCompare(right)),
    );
  });
}

async function reload() {
  await flushGameSave();
  gameStore.setState({ ready: false, player: null });
  await gameStore.getState().init();
}

// Call only from an isolated test harness with storage and sync replaced.
export async function runRefinementChecks(): Promise<string[]> {
  const lines: string[] = [];
  const check = (condition: boolean, label: string) => {
    if (!condition) throw new Error(label);
    lines.push(`PASS: ${label}`);
  };
  const realNow = Date.now;
  let time = realNow();
  const player = qaPlayer(time);
  const originalRpc = bilt?.rpc.bind(bilt);
  const base = gameStore.getState();
  const reset = (patch: Partial<Player> = {}) => {
    gameStore.setState({
      ...base,
      ready: true,
      identity: player.id,
      player: { ...player, ...patch },
      tickAt: time,
      offStart: 0,
      offGrass: player.grass,
      offDeck: null,
      rules: { ...freshRules(time), recapDay: dayKey(time) },
      cardReward: null,
      collectedCards: [],
      battle: null,
      alerts: [],
      outgoing: [],
      applied: [],
      staged: [],
      waitingVisitor: null,
      recap: null,
      message: null,
      guideOpen: false,
      deckOpen: false,
      togetherId: null,
      togetherSettled: [],
      pendingTogetherWakes: [],
      seenSessions: [],
      sessions: [],
      sync: async () => {},
    });
    accountPlay(time);
  };
  const advance = (seconds: number) => {
    time += seconds * 1000;
    gameStore.getState().tick();
  };
  try {
    lines.push(...verifyFirstSession(player, bot(player)).checks.map((line) => `PASS: ${line}`));
    lines.push(...verifyVisitors(player, bot(player)).map((line) => `PASS: ${line}`));
    lines.push(...(await runOfflineRuleChecks()));
    Date.now = () => time;
    reset();
    gameStore.getState().sleep();
    await flushGameSave();
    time += 31_000;
    await reload();
    await gameStore.getState().wake();
    await flushGameSave();
    const first = gameStore.getState();
    check(
      first.player!.grass === 51 &&
        first.player!.offline_seconds === 31 &&
        first.cardReward?.cards.length === 2,
      '31-MIN break across reload gives 31 GRASS and exactly 2 cards',
    );
    const settled = stableSnapshot({
      deck: first.player!.deck,
      grass: first.player!.grass,
      collection: first.player!.collection,
      reward: first.cardReward,
    });
    await reload();
    await gameStore.getState().wake();
    gameStore.getState().tick();
    const restored = stableSnapshot({
      deck: gameStore.getState().player!.deck,
      grass: gameStore.getState().player!.grass,
      collection: gameStore.getState().player!.collection,
      reward: gameStore.getState().cardReward,
    });
    check(
      restored === settled,
      'Repeated reload/wake preserves cards, GRASS and visitor roll exactly once',
    );
    reset();
    gameStore.getState().sleep('park');
    await flushGameSave();
    time += 16_000;
    await reload();
    check(
      gameStore.getState().player!.mode === 'awake' &&
        gameStore.getState().player!.grass === 40 &&
        gameStore.getState().cardReward?.minutes === 15 &&
        gameStore.getState().cardReward?.cards.length === 2 &&
        postcardsOf(gameStore.getState().player!).length === 1,
      'Cold mission restore settles Park once with 20 GRASS, 2 cards and 1 postcard',
    );
    reset();
    gameStore.getState().sleep('park');
    advance(7);
    await reload();
    advance(9);
    check(
      gameStore.getState().player!.grass === 40 &&
        gameStore.getState().cardReward?.grass === 20 &&
        gameStore.getState().cardReward?.minutes === 15 &&
        gameStore.getState().cardReward?.cards.length === 2,
      'Park at 15 real demo seconds gives 20 GRASS, 1 common + 1 rare, not 35 GRASS',
    );
    const park = stableSnapshot(gameStore.getState().cardReward);
    await reload();
    gameStore.getState().tick();
    await gameStore.getState().wake();
    check(
      postcardsOf(gameStore.getState().player!).length === 1 &&
        stableSnapshot(gameStore.getState().cardReward) === park &&
        gameStore.getState().player!.grass === 40,
      'Completed Park resume adds no duplicate cards, postcard, visitor or GRASS',
    );
    reset();
    gameStore.getState().sleep('book');
    advance(16);
    await gameStore.getState().wake();
    check(
      gameStore.getState().player!.grass === 20 &&
        gameStore.getState().cardReward?.cards.length === 1 &&
        gameStore.getState().cardReward?.early === true &&
        postcardsOf(gameStore.getState().player!).length === 0,
      'Interrupted Book keeps offline common card, no mission GRASS/rare/postcard',
    );
    reset();
    gameStore.getState().sleep('book');
    advance(30);
    check(
      gameStore.getState().player!.grass === 80 &&
        gameStore.getState().cardReward?.cards.length === 3,
      'Book completion gives 60 GRASS and 2 common + 1 rare',
    );
    reset({ level: 2 });
    gameStore.getState().sleep('mountain');
    advance(60);
    check(
      gameStore.getState().player!.grass === 170 &&
        gameStore.getState().player!.owned_hats.length === 1 &&
        gameStore.getState().cardReward?.cards.length === 5,
      'Mountain gives 150 GRASS, unowned hat, 4 common + 1 epic',
    );
    reset({ level: 2, owned_hats: ['CAP', 'SHADES', 'TOP HAT', 'CROWN'] });
    gameStore.getState().sleep('mountain');
    advance(60);
    check(
      gameStore.getState().player!.grass === 220 && gameStore.getState().cardReward?.hat === null,
      'Mountain all-hats fallback adds 50 GRASS',
    );
    reset({ offline_seconds: 14 });
    gameStore.getState().sleep();
    advance(520);
    await gameStore.getState().wake();
    const long = gameStore.getState();
    const summary = summarizeCardRewards(long.offDeck!, long.cardReward!.cards);
    check(
      long.cardReward!.cards.length === 35 &&
        long.player!.deck.length === 20 &&
        JSON.stringify(summary.deck) === JSON.stringify(long.player!.deck) &&
        summary.kept + summary.earnedReplaced === 35,
      '520-MIN return rolls all 35 cards, caps deck at 20, retention/replacement summary matches',
    );
    reset();
    const met = meetVisitor(player, 'trailhop', 15, time);
    gameStore.setState({
      player: met,
      waitingVisitor: { id: 'trailhop', expiresAt: 0 },
      cardReward: {
        cards: [],
        grass: 15,
        minutes: 15,
        mission: null,
        visitor: 'trailhop',
        postcard: null,
        hat: null,
        early: false,
      },
    });
    advance(20);
    check(
      gameStore.getState().waitingVisitor?.expiresAt === 0,
      'Visitor does not expire while WELCOME BACK is open',
    );
    gameStore.getState().befriendVisitor();
    gameStore.getState().befriendVisitor();
    check(
      collectionOf(gameStore.getState().player!).length === 1 &&
        collectionOf(gameStore.getState().player!)[0].befriendedAt !== null &&
        gameStore.getState().waitingVisitor === null,
      'Welcome befriending clears waiting interaction immediately; repeated taps add no companions',
    );
    gameStore.getState().selectGuardian('trailhop');
    await reload();
    const guardian = guardianPlayer(gameStore.getState().player!);
    check(
      guardian.guardian === 'trailhop' &&
        guardian.species === 'RAT' &&
        gameStore.getState().player!.species === 'BLOB' &&
        guardian.deck === gameStore.getState().player!.deck,
      'Guardian survives saved reload and shares account deck while starter species stays BLOB',
    );
    reset();
    gameStore.setState({
      player: met,
      waitingVisitor: { id: 'trailhop', expiresAt: 0 },
      cardReward: {
        cards: [],
        grass: 0,
        minutes: 15,
        mission: null,
        visitor: 'trailhop',
        postcard: null,
        hat: null,
        early: false,
      },
    });
    gameStore.getState().dismissCards();
    advance(9);
    check(
      gameStore.getState().waitingVisitor !== null,
      'Visitor still actionable 9 demo MIN after welcome',
    );
    advance(1);
    check(
      gameStore.getState().waitingVisitor === null,
      'Visitor expires at existing 10-demo-MIN garden deadline',
    );
    reset();
    gameStore.setState({ battle: { target: bot(player), practice: true } });
    advance(180);
    check(
      remainingPlay(gameStore.getState().rules.budget, time) === 0 &&
        gameStore.getState().battle !== null,
      'Foreground sparring consumes 3 real minutes; fight stays open when budget ends',
    );
    gameStore.getState().finishBattle(false, bot(player), true);
    check(
      gameStore.getState().player!.grass === 20 &&
        gameStore.getState().outgoing.length === 0 &&
        (gameStore.getState().rules.days[dayKey(time)]?.raids ?? 0) === 0 &&
        gameStore.getState().message === null,
      'Sparring loss pays zero, no raid record/allowance and no second result toast',
    );
    await gameStore.getState().startBattle(bot(player), true);
    check(
      gameStore.getState().battle === null,
      'Exhausted allowance prevents a new spar after safe settlement',
    );
    reset({ grass: 500, care_until: 0 });
    gameStore.getState().incomingBot();
    const afterRaid = gameStore.getState().player!.grass;
    const raidId = gameStore.getState().alerts[0]?.raid.id;
    check(
      Boolean(raidId) && gameStore.getState().applied.includes(raidId),
      'Simulated incoming raid settles and opens one defender alert',
    );
    await reload();
    check(
      gameStore.getState().player!.grass === afterRaid &&
        gameStore.getState().applied.filter((id) => id === raidId).length === 1,
      'Incoming raid settlement survives reload without duplicate GRASS',
    );
    reset();
    const session: TogetherSession = {
      id: 'qa-together-early',
      player_a: player.id,
      player_b: '00000000-0000-4000-8000-00000000aa02',
      status: 'failed',
      failed_by: player.id,
      started_at: new Date(time).toISOString(),
      woke_a_at: new Date(time + 5000).toISOString(),
      woke_b_at: null,
      grass_a: 5,
      grass_b: 0,
    };
    gameStore.getState().sleep();
    advance(5);
    await gameStore.getState().wake();
    resolveTogetherSession(session);
    check(
      gameStore.getState().player!.grass === 25 && gameStore.getState().rules.togetherBadges === 0,
      'Together early return retains ordinary GRASS, no bonus',
    );
    gameStore.setState({
      cardReward: null,
      pendingTogetherWakes: [{ sid: session.id, at: new Date(time).toISOString(), minutes: 5 }],
    });
    if (bilt) {
      const failingClient = createClient('https://refinement-qa.invalid', 'qa-only', {
        auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
        global: {
          fetch: async () =>
            new Response(JSON.stringify({ message: 'Connection unavailable' }), {
              status: 503,
              headers: { 'Content-Type': 'application/json' },
            }),
        },
      });
      bilt.rpc = failingClient.rpc.bind(failingClient);
    }
    try {
      await gameStore.getState().pollTogether();
    } catch {
      /* Expected transport failure, not a session outcome. */
    }
    check(
      gameStore.getState().pendingTogetherWakes.length === 1 &&
        (bilt
          ? gameStore.getState().message?.startsWith('Together report pending.') === true
          : gameStore.getState().message === backendUnavailableMessage) &&
        !gameStore.getState().message?.includes('PICKED UP') &&
        gameStore.getState().player!.grass === 25,
      'Unavailable online play retains wake for retry and rewards; never accuses rival',
    );
    check(cardIds.length === 9, 'No new cards or progression systems');
    await flushGameSave();
    return lines;
  } finally {
    Date.now = realNow;
    if (bilt && originalRpc) bilt.rpc = originalRpc;
  }
}
