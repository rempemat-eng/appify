import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  accountPlay,
  bot,
  gameStore,
  resolveTogetherSession,
  type Player,
  type TogetherSession,
} from '@/lib/game';
import {
  advanceBudget,
  bumpDay,
  dayKey,
  emptyDay,
  freshRules,
  gardenStreak,
  previousDay,
  recordOffline,
  remainingPlay,
  sparringReward,
  PLAY_LIMIT_MS,
  PLAY_WINDOW_MS,
} from '@/lib/offline-rules';
import { startingDeck } from '@/lib/cards';
import { backendConfigured, backendUnavailableMessage } from '@/lib/bilt';
export async function runOfflineRuleChecks(
  onProgress?: (lines: string[]) => void,
): Promise<string[]> {
  const lines: string[] = [];
  const check = (ok: boolean, label: string) => {
    if (!ok) throw new Error(label);
    lines.push(`PASS: ${label}`);
    onProgress?.([...lines]);
  };
  const origin = Date.now();
  let budget = advanceBudget({ startedAt: 0, usedMs: 0 }, origin + 179000, 179000);
  check(remainingPlay(budget, origin + 179000) === 1, '179 real seconds leaves one second');
  budget = advanceBudget(budget, origin + 180000, 1000);
  check(remainingPlay(budget, origin + 180000) === 0, '3 real minutes triggers pause');
  check(
    remainingPlay(advanceBudget(budget, origin + PLAY_WINDOW_MS, 0), origin + PLAY_WINDOW_MS) ===
      180,
    '30-minute window resets budget',
  );
  check(
    advanceBudget(budget, origin + 181000, 0).usedMs === PLAY_LIMIT_MS,
    'Overlays add no active time',
  );
  let rules = freshRules();
  rules = bumpDay(rules, '2026-10-12', { offline: 120 });
  rules = bumpDay(rules, '2026-10-13', { offline: 120 });
  check(gardenStreak(rules, '2026-10-14').streak === 2, '120 offline MIN qualifies a day');
  check(
    gardenStreak(rules, '2026-10-15').streak === 2 && gardenStreak(rules, '2026-10-15').forgiven,
    'One missed day in Monday–Sunday week is forgiven',
  );
  rules = bumpDay(rules, '2026-10-15', { offline: 120 });
  check(
    gardenStreak(rules, '2026-10-15').streak === 3,
    'Qualified day continues streak after grace',
  );
  check(
    gardenStreak(rules, '2026-10-17').streak === 0,
    'Second missed day in same week resets streak',
  );
  check(
    gardenStreak(freshRules(), '2026-10-15').streak === 0,
    'Opening alone never earns a streak',
  );
  const midnight = new Date('2026-10-15T23:59:50').getTime();
  const split = recordOffline(freshRules(midnight), midnight, 30, 30);
  check(
    split.days['2026-10-15'].offline === 10 && split.days['2026-10-16'].offline === 20,
    'Offline time splits across local midnight',
  );
  check(
    sparringReward({ ...emptyDay(), sparringWins: 2 }, true) === 5 &&
      sparringReward({ ...emptyDay(), sparringWins: 3 }, true) === 0,
    'Only first three sparring wins pay GRASS',
  );
  const pa: Player = {
    id: '00000000-0000-4000-8000-000000000001',
    code: 'DEMO',
    name: 'JUNIPER',
    pet_name: 'MOSS',
    species: 'BLOB',
    level: 1,
    grass: 500,
    mood: 40,
    hat: null,
    owned_hats: [],
    mode: 'awake',
    care_until: 0,
    recovery_until: 0,
    mission_id: null,
    mission_ends_at: 0,
    offline_seconds: 0,
    last_seen: origin,
    deck: [...startingDeck],
    collection: [],
    guardian: null,
    postcards: [],
  };
  const pb: Player = { ...pa, id: '00000000-0000-4000-8000-000000000002', name: 'ROWAN' };
  const snapshot = gameStore.getState();
  const originalWrite = AsyncStorage.setItem;
  AsyncStorage.setItem = async (key, value) => {
    if (key !== 'screenagotchi-v1') await originalWrite(key, value);
  };
  try {
    const baseline = { ...freshRules(), recapDay: dayKey() };
    gameStore.setState({
      player: pa,
      ready: true,
      recap: null,
      battle: null,
      alerts: [],
      flash: null,
      cardReward: null,
      deckOpen: false,
      rules: baseline,
      identity: pa.id,
      sync: async () => {},
      pendingTogetherWakes: [],
      togetherId: null,
      togetherSettled: [],
      seenSessions: [],
      sessions: [],
    });
    accountPlay(origin);
    accountPlay(origin + 180000);
    check(
      remainingPlay(gameStore.getState().rules.budget, origin + 180000) === 0,
      'Store active-time meter reaches zero',
    );
    gameStore.setState({
      rules: {
        ...gameStore.getState().rules,
        budget: { startedAt: Date.now(), usedMs: PLAY_LIMIT_MS },
      },
    });
    const grass = gameStore.getState().player!.grass;
    gameStore.getState().feed();
    gameStore.getState().levelUp();
    gameStore.getState().hatAction('CAP');
    await gameStore.getState().startBattle(bot(pa), true);
    check(
      gameStore.getState().player!.grass === grass && !gameStore.getState().battle,
      'Budget blocks feeding, shopping and sparring',
    );
    await gameStore.getState().startBattle(pb);
    check(!gameStore.getState().battle, 'Budget also blocks raiding');
    gameStore.getState().sleep();
    gameStore.setState({ tickAt: Date.now() - 10000 });
    gameStore.getState().tick();
    check(
      gameStore.getState().player!.offline_seconds >= 10 &&
        remainingPlay(gameStore.getState().rules.budget) === 180,
      '10 demo MIN screen-off resets budget',
    );
    await gameStore.getState().wake();
    gameStore.getState().resetBudget();
    check(remainingPlay(gameStore.getState().rules.budget) === 180, 'Hourglass demo reset works');
    gameStore.setState({ player: pa, rules: baseline, cardReward: null });
    for (let i = 0; i < 4; i++) {
      gameStore.setState({ battle: { target: bot(pa), practice: true } });
      gameStore.getState().finishBattle(true, bot(pa), true);
    }
    check(
      gameStore.getState().player!.grass === pa.grass + 15,
      'Four simulated wins pay exactly 15 GRASS',
    );
    check(gameStore.getState().rules.days[dayKey()].raids === 0, 'Sparring never spends raids');
    gameStore.setState({ player: pa, rules: baseline, cardReward: null, battle: null });
    gameStore.getState().sleep();
    gameStore.setState({ tickAt: Date.now() - 31000 });
    gameStore.getState().tick();
    check(
      gameStore.getState().collectedCards.length === 2 &&
        gameStore.getState().rules.days[dayKey()].cards === 2,
      '31 offline MIN earns exactly two cards',
    );
    await gameStore.getState().wake();
    gameStore.setState({
      rules: { ...baseline, recapDay: previousDay(dayKey()) },
      cardReward: null,
    });
    gameStore.getState().openDaily();
    check(gameStore.getState().recap === previousDay(dayKey()), 'First open shows yesterday recap');
    gameStore.getState().dismissRecap();
    gameStore.getState().openDaily();
    check(!gameStore.getState().recap, 'Same-day reopen never repeats recap');
    gameStore.setState({
      player: pa,
      rules: bumpDay(baseline, dayKey(), { raids: 3 }),
      battle: null,
      recap: null,
      cardReward: null,
    });
    await gameStore.getState().startBattle(pb);
    check(
      !gameStore.getState().battle &&
        (backendConfigured
          ? gameStore.getState().message?.includes('NO RAIDS') === true
          : gameStore.getState().message === backendUnavailableMessage),
      backendConfigured
        ? 'Store blocks fourth raid'
        : 'Local mode blocks player raids without a backend',
    );
    const done: TogetherSession = {
      id: 'qa-done',
      player_a: pa.id,
      player_b: pb.id,
      status: 'done',
      started_at: new Date(origin).toISOString(),
      failed_by: null,
      woke_a_at: new Date(origin + 12000).toISOString(),
      woke_b_at: new Date(origin + 14000).toISOString(),
      grass_a: 12,
      grass_b: 14,
    };
    gameStore.setState({
      player: pa,
      rivals: [pb],
      rules: baseline,
      togetherSettled: [],
      seenSessions: [],
    });
    resolveTogetherSession(done);
    check(
      gameStore.getState().player!.grass === pa.grass + 6 &&
        gameStore.getState().rules.togetherBadges === 1,
      'Player A receives +50% and Together badge',
    );
    resolveTogetherSession(done);
    check(
      gameStore.getState().player!.grass === pa.grass + 6,
      'Repeated polling cannot duplicate Together bonus',
    );
    gameStore.setState({ player: pb, rivals: [pa], rules: baseline, togetherSettled: [] });
    resolveTogetherSession(done);
    check(
      gameStore.getState().player!.grass === pb.grass + 7 &&
        gameStore.getState().rules.togetherBadges === 1,
      'Player B receives +50% and Together badge',
    );
    const failed: TogetherSession = {
      ...done,
      id: 'qa-failed',
      status: 'failed',
      failed_by: pa.id,
      grass_a: 5,
      woke_a_at: new Date(origin + 5000).toISOString(),
      woke_b_at: null,
    };
    gameStore.setState({ player: pb, rules: baseline, seenSessions: [], cardReward: null });
    resolveTogetherSession(failed);
    check(
      gameStore.getState().player!.grass === pb.grass &&
        gameStore.getState().message === 'TOGETHER ENDED EARLY. ORDINARY REWARDS KEPT.',
      'Rival sees neutral early-return message and no bonus',
    );
    gameStore.setState({ player: pa, rivals: [pb], seenSessions: [] });
    resolveTogetherSession(failed);
    check(
      gameStore.getState().message === 'TOGETHER ENDED EARLY. ORDINARY REWARDS KEPT.',
      'Early-waking player sees same failure message',
    );
    const active: TogetherSession = {
      ...done,
      id: 'qa-offline-wake',
      status: 'active',
      woke_a_at: null,
      woke_b_at: null,
    };
    gameStore.setState({
      player: { ...pa, mode: 'screen_off', offline_seconds: 12 },
      offStart: 0,
      tickAt: Date.now(),
      sessions: [active],
      togetherId: active.id,
      pendingTogetherWakes: [],
      rules: baseline,
      recap: null,
    });
    await gameStore.getState().wake();
    check(
      gameStore.getState().player!.mode === 'awake' &&
        gameStore.getState().pendingTogetherWakes[0]?.minutes === 12,
      'Wake works offline and saves a durable shared report',
    );
  } finally {
    gameStore.setState(snapshot, true);
    await new Promise<void>((resolve) => setTimeout(resolve, 100));
    AsyncStorage.setItem = originalWrite;
  }
  return lines;
}
