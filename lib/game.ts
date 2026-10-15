import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';
import * as Crypto from 'expo-crypto';
import * as Haptics from 'expo-haptics';
import { AppState, Platform, Vibration } from 'react-native';
import type { Database, Tables } from '@biltme/backend';
import {
  advanceBudget,
  bumpDay,
  budgetVoice,
  dayKey,
  emptyDay,
  freshRules,
  gardenStreak,
  isOfflineRules,
  previousDay,
  recordOffline,
  remainingPlay,
  sparringReward,
  type OfflineRules,
} from '@/lib/offline-rules';
export type TogetherSession = Tables<'touch_grass_sessions'>;
import {
  collectionOf,
  consecutiveOfflineDays,
  isVisitorId,
  meetVisitor,
  postcardsOf,
  rollVisitor,
  visitorInfo,
  type Postcard,
  type VisitorId,
  type WaitingVisitor,
  type WelcomeReward,
} from '@/lib/visitors';
import { bilt } from '@/lib/bilt';
import { launchCareUntil, isGardenTip, type GardenTipId } from '@/lib/first-session';
import {
  addCard,
  daveDeck,
  isCardId,
  offlineCards,
  startingDeck,
  upgradeStarterDeck,
  type CardId,
} from '@/lib/cards';

export type Player = Database['public']['Tables']['players']['Row'];
export type Raid = Database['public']['Tables']['raids']['Row'];
export const ink = '#4A3B35';
export const palette = {
  ink,
  buttonInk: '#2F251F',
  shade: '#6B5545',
  body: '#D9B48F',
  paper: '#F2E6C9',
  positive: '#5FA35A',
  moss: '#3E7D44',
  error: '#A85A43',
  terracotta: '#944C3A',
  danger: '#973D35',
  amber: '#D8AF5E',
  night: '#3A3F5C',
  slate: '#8FA3BD',
  gold: '#C8A457',
  stone: '#B3A57E',
  flash: '#FFFFFF',
  weed: '#89908B',
  wilt: '#A3A59C',
};
export const hats = [
  { id: 'CAP', emoji: '🧢', cost: 30 },
  { id: 'SHADES', emoji: '🕶', cost: 40 },
  { id: 'TOP HAT', emoji: '🎩', cost: 60 },
  { id: 'CROWN', emoji: '👑', cost: 150 },
];
export const missions = [
  { id: 'park', name: 'PARK PATROL', duration: 15, reward: 20, level: 1 },
  { id: 'book', name: 'BOOK CLUB', duration: 30, reward: 60, level: 1 },
  { id: 'mountain', name: 'MOUNTAIN RETREAT', duration: 60, reward: 150, level: 2 },
];
export function status(p: Player, now = Date.now()) {
  if (p.mode !== 'awake') return { label: 'SCREEN OFF', left: 0, kind: 'safe' };
  if (p.recovery_until > now)
    return { label: 'RECOVERING', left: Math.ceil((p.recovery_until - now) / 1000), kind: 'safe' };
  if (p.care_until > now)
    return { label: 'CARE WINDOW', left: Math.ceil((p.care_until - now) / 1000), kind: 'care' };
  return { label: 'EXPOSED', left: 0, kind: 'exposed' };
}
export function clock(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}
export function feedback(kind: 'success' | 'error' | 'hit' | 'raid' | 'select' = 'success') {
  if (Platform.OS === 'web') return;
  if (kind === 'hit' || kind === 'raid') {
    if (kind === 'raid') Vibration.vibrate([0, 180, 80, 220]);
    else Vibration.vibrate(60);
    void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy).catch(() => {});
  } else if (kind === 'select') {
    void Haptics.selectionAsync().catch(() => {});
  } else {
    void Haptics.notificationAsync(
      kind === 'success'
        ? Haptics.NotificationFeedbackType.Success
        : Haptics.NotificationFeedbackType.Error,
    ).catch(() => {});
  }
}
function code() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  return Array.from(Crypto.getRandomBytes(4), (n) => chars[n % chars.length]).join('');
}
export type Incoming = { raid: Raid; attacker: Player | null };
export type BattleRequest = { target: Player; practice: boolean };
type Saved = {
  lastActiveAt: number;
  tips: GardenTipId[];
  firstWake: boolean;
  rules: OfflineRules;
  togetherId: string | null;
  pendingTogetherWakes: { sid: string; at: string; minutes: number }[];
  togetherSettled: string[];
  seenSessions: string[];
  player: Player | null;
  identity: string;
  tickAt: number;
  offStart: number;
  offGrass: number;
  outgoing: Raid[];
  staged: Incoming[];
  applied: string[];
  alerts: Incoming[];
  collectedCards: CardId[];
  waitingVisitor: WaitingVisitor | null;
  cardReward: WelcomeReward | null;
};
type Game = Saved & {
  befriendVisitor: () => void;
  selectGuardian: (id: VisitorId | null) => void;
  homeTipActive: 'phone' | 'wake' | null;
  seeTip: (id: GardenTipId) => void;
  sessions: TogetherSession[];
  togetherPending: string | null;
  recap: string | null;
  resetBudget: () => void;
  openDaily: () => void;
  dismissRecap: () => void;
  inviteTogether: (rival: Player) => Promise<void>;
  acceptTogether: (session: TogetherSession) => Promise<void>;
  pollTogether: () => Promise<void>;
  guideOpen: boolean;
  deckOpen: boolean;
  ready: boolean;
  live: boolean;
  rivals: Player[];
  now: number;
  message: string | null;
  voice: string | null;
  battle: BattleRequest | null;
  flash: string | null;
  syncing: boolean;
  init: () => Promise<void>;
  hatch: (name: string, pet: string, species: Player['species']) => Promise<void>;
  change: (patch: Partial<Player>) => void;
  tick: () => void;
  sync: () => Promise<void>;
  pair: (code: string) => Promise<string | null>;
  sleep: (mission?: string) => void;
  wake: () => Promise<void>;
  feed: () => void;
  levelUp: () => void;
  hatAction: (hat: string) => void;
  startBattle: (target: Player, practice?: boolean, revenge?: boolean) => Promise<void>;
  finishBattle: (won: boolean, target: Player, practice: boolean) => void;
  incomingBot: () => void;
  dismissCards: () => void;
  dismissAlert: () => void;
  notify: (message: string, error?: boolean) => void;
};
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item: unknown) => typeof item === 'string');
}
function isPlayer(value: unknown): value is Player {
  if (!isRecord(value)) return false;
  return (
    ['id', 'code', 'name', 'pet_name'].every((key) => typeof value[key] === 'string') &&
    (value.species === 'BLOB' || value.species === 'RAT' || value.species === 'CUBE') &&
    (value.mode === 'awake' || value.mode === 'screen_off' || value.mode === 'mission') &&
    [
      'level',
      'grass',
      'mood',
      'care_until',
      'recovery_until',
      'mission_ends_at',
      'offline_seconds',
      'last_seen',
    ].every((key) => typeof value[key] === 'number') &&
    (value.hat === null || typeof value.hat === 'string') &&
    (value.mission_id === null || typeof value.mission_id === 'string') &&
    isStringArray(value.owned_hats) &&
    Array.isArray(value.collection) &&
    Array.isArray(value.postcards) &&
    (value.guardian === null || isVisitorId(value.guardian)) &&
    Array.isArray(value.deck) &&
    value.deck.length > 0 &&
    value.deck.length <= 20 &&
    value.deck.every(isCardId)
  );
}
function migrateSaved(value: unknown) {
  if (!isRecord(value)) return value;
  const migratePlayer = (p: unknown) => {
    if (isRecord(p)) {
      if (!Array.isArray(p.collection)) p.collection = [];
      if (!Array.isArray(p.postcards)) p.postcards = [];
      if (p.guardian === undefined) p.guardian = null;
    }
    if (isRecord(p) && p.deck === undefined)
      p.deck =
        typeof p.level === 'number' && p.level >= 3
          ? [...startingDeck, 'digital_sunset']
          : [...startingDeck];
  };
  migratePlayer(value.player);
  if (isRecord(value.player) && isStringArray(value.player.deck))
    value.player.deck = upgradeStarterDeck(value.player.deck);
  if (typeof value.lastActiveAt !== 'number')
    value.lastActiveAt = typeof value.tickAt === 'number' ? value.tickAt : 0;
  if (!Array.isArray(value.tips)) value.tips = [];
  if (typeof value.firstWake !== 'boolean') value.firstWake = false;
  for (const key of ['staged', 'alerts']) {
    const list = value[key];
    if (Array.isArray(list))
      for (const item of list) if (isRecord(item)) migratePlayer(item.attacker);
  }
  if (!isOfflineRules(value.rules)) value.rules = freshRules();
  if (value.togetherId === undefined) value.togetherId = null;
  if (!Array.isArray(value.pendingTogetherWakes)) value.pendingTogetherWakes = [];
  if (value.togetherSettled === undefined) value.togetherSettled = [];
  if (value.seenSessions === undefined) value.seenSessions = [];
  if (value.collectedCards === undefined) value.collectedCards = [];
  if (value.waitingVisitor === undefined) value.waitingVisitor = null;
  if (value.cardReward === undefined) value.cardReward = null;
  if (isRecord(value.cardReward))
    value.cardReward = {
      grass: 0,
      visitor: null,
      postcard: null,
      hat: null,
      early: false,
      ...value.cardReward,
    };
  return value;
}
function isRaid(value: unknown): value is Raid {
  if (!isRecord(value)) return false;
  return (
    ['id', 'attacker_id', 'defender_id', 'created_at'].every(
      (key) => typeof value[key] === 'string',
    ) &&
    typeof value.attacker_won === 'boolean' &&
    typeof value.grass_amount === 'number' &&
    typeof value.seen_by_defender === 'boolean'
  );
}
function isIncoming(value: unknown): value is Incoming {
  return (
    isRecord(value) && isRaid(value.raid) && (value.attacker === null || isPlayer(value.attacker))
  );
}
function isSaved(value: unknown): value is Saved {
  return (
    isRecord(value) &&
    typeof value.lastActiveAt === 'number' &&
    typeof value.firstWake === 'boolean' &&
    Array.isArray(value.tips) &&
    value.tips.every(isGardenTip) &&
    isOfflineRules(value.rules) &&
    (value.togetherId === null || typeof value.togetherId === 'string') &&
    Array.isArray(value.pendingTogetherWakes) &&
    value.pendingTogetherWakes.every(
      (x) =>
        isRecord(x) &&
        typeof x.sid === 'string' &&
        typeof x.at === 'string' &&
        typeof x.minutes === 'number',
    ) &&
    isStringArray(value.togetherSettled) &&
    isStringArray(value.seenSessions) &&
    (value.player === null || isPlayer(value.player)) &&
    typeof value.identity === 'string' &&
    ['tickAt', 'offStart', 'offGrass'].every((key) => typeof value[key] === 'number') &&
    Array.isArray(value.outgoing) &&
    value.outgoing.every(isRaid) &&
    Array.isArray(value.staged) &&
    value.staged.every(isIncoming) &&
    isStringArray(value.applied) &&
    Array.isArray(value.alerts) &&
    value.alerts.every(isIncoming) &&
    Array.isArray(value.collectedCards) &&
    value.collectedCards.every(isCardId) &&
    (value.waitingVisitor === null ||
      (isRecord(value.waitingVisitor) &&
        isVisitorId(value.waitingVisitor.id) &&
        typeof value.waitingVisitor.expiresAt === 'number')) &&
    (value.cardReward === null ||
      (isRecord(value.cardReward) &&
        Array.isArray(value.cardReward.cards) &&
        value.cardReward.cards.every(isCardId) &&
        typeof value.cardReward.minutes === 'number' &&
        (value.cardReward.mission === null || typeof value.cardReward.mission === 'string')))
  );
}
const KEY = 'screenagotchi-v1';
let persistence = Promise.resolve();
let active = true;
let syncRequested = false;
let battleGeneration = 0;
let playAt = Date.now();
let playEligible = false;
let accounting = false;
export function playPaused() {
  const s = gameStore.getState();
  return remainingPlay(s.rules.budget) === 0;
}
function eligiblePlay() {
  const s = gameStore.getState();
  return (
    active &&
    s.ready &&
    s.player?.mode === 'awake' &&
    !s.battle &&
    !s.alerts.length &&
    !s.flash &&
    !s.deckOpen &&
    !s.guideOpen &&
    !s.cardReward &&
    !s.recap
  );
}
export function accountPlay(now = Date.now()) {
  if (accounting) return;
  accounting = true;
  const s = gameStore.getState();
  const before = remainingPlay(s.rules.budget, now);
  const budget = advanceBudget(s.rules.budget, now, playEligible ? Math.max(0, now - playAt) : 0);
  playAt = now;
  playEligible = eligiblePlay();
  if (budget.startedAt !== s.rules.budget.startedAt || budget.usedMs !== s.rules.budget.usedMs) {
    gameStore.setState({
      rules: { ...s.rules, budget },
      ...(before > 0 && remainingPlay(budget, now) === 0 ? { voice: budgetVoice } : {}),
    });
    void persist();
  }
  accounting = false;
}
function beginTogether(session: TogetherSession) {
  const s = gameStore.getState();
  if (!s.player || !session.started_at) return;
  const at = Date.parse(session.started_at);
  gameStore.setState({
    togetherId: session.id,
    seenSessions: [...s.seenSessions, session.id],
    sessions: [...s.sessions.filter((x) => x.id !== session.id), session],
    offStart: s.player.offline_seconds,
    offGrass: s.player.grass,
    tickAt: at,
    battle: null,
    recap: null,
    message: null,
    voice: null,
    player: { ...s.player, mode: 'screen_off', mission_id: null, mission_ends_at: 0 },
  });
  gameStore.getState().tick();
  changed();
}
export function resolveTogetherSession(session: TogetherSession) {
  const s = gameStore.getState();
  const p = s.player;
  if (!p || (p.id !== session.player_a && p.id !== session.player_b)) return;
  const ownWake = session.player_a === p.id ? session.woke_a_at : session.woke_b_at;
  if (session.status === 'done' && ownWake && !s.togetherSettled.includes(session.id)) {
    const bonus = Math.floor((session.player_a === p.id ? session.grass_a : session.grass_b) * 0.5);
    gameStore.setState({
      player: { ...p, grass: p.grass + bonus },
      rules: {
        ...bumpDay(s.rules, dayKey(Date.parse(ownWake)), { grass: bonus }),
        togetherBadges: s.rules.togetherBadges + 1,
      },
      togetherSettled: [...s.togetherSettled, session.id],
      cardReward:
        s.cardReward?.sessionId === session.id
          ? { ...s.cardReward, grass: s.cardReward.grass + bonus }
          : s.cardReward,
      message: s.cardReward?.sessionId === session.id ? null : `TOGETHER! +${bonus} BONUS GRASS`,
      voice: 'we touched grass together.',
    });
    feedback();
    void persist();
  }
  if (session.status === 'failed' && !s.seenSessions.includes(`failed:${session.id}`)) {
    const name =
      session.failed_by === p.id
        ? p.name
        : (s.rivals.find((x) => x.id === session.failed_by)?.name ?? 'YOUR RIVAL');
    gameStore.setState({
      seenSessions: [...s.seenSessions, `failed:${session.id}`],
      message: `${name} PICKED UP THEIR PHONE.`,
      voice: 'our together bonus wilted.',
    });
    feedback('error');
    void persist();
  }
}
function persist() {
  const s = gameStore.getState();
  const saved: Saved = {
    lastActiveAt: s.lastActiveAt,
    tips: s.tips,
    firstWake: s.firstWake,
    rules: s.rules,
    pendingTogetherWakes: s.pendingTogetherWakes,
    togetherId: s.togetherId,
    togetherSettled: s.togetherSettled,
    seenSessions: s.seenSessions,
    player: s.player,
    identity: s.identity,
    tickAt: s.tickAt,
    offStart: s.offStart,
    offGrass: s.offGrass,
    outgoing: s.outgoing,
    staged: s.staged,
    applied: s.applied,
    alerts: s.alerts,
    collectedCards: s.collectedCards,
    cardReward: s.cardReward,
    waitingVisitor: s.waitingVisitor,
  };
  const value = JSON.stringify(saved);
  persistence = persistence
    .then(() => AsyncStorage.setItem(KEY, value))
    .catch(() => {
      gameStore.setState({ message: 'COULD NOT SAVE. KEEP THE APP OPEN.' });
      feedback('error');
    });
  return persistence;
}
function changed() {
  void persist().then(() => gameStore.getState().sync());
}
function applyIncoming(item: Incoming) {
  const s = gameStore.getState();
  const p = s.player;
  if (!p || s.applied.includes(item.raid.id)) return;
  const lost = item.raid.attacker_won;
  gameStore.setState({
    player: {
      ...p,
      grass: lost ? Math.max(0, p.grass - item.raid.grass_amount) : p.grass + 20,
      mood: lost ? Math.max(0, p.mood - 20) : p.mood,
      recovery_until: Date.now() + 60000,
    },
    rules: bumpDay(s.rules, dayKey(), { grass: lost ? 0 : 20 }),
    applied: [...s.applied, item.raid.id],
    alerts: [...s.alerts, item],
    staged: s.staged.filter((x) => x.raid.id !== item.raid.id),
    voice: 'i saw the light. it was your screen.',
  });
  feedback('raid');
}
export const gameStore = create<Game>((set, get) => ({
  lastActiveAt: 0,
  tips: [],
  firstWake: false,
  seeTip: (id) => {
    if (get().tips.includes(id)) return;
    set({ tips: [...get().tips, id] });
    void persist();
  },
  rules: freshRules(),
  pendingTogetherWakes: [],
  togetherId: null,
  togetherSettled: [],
  seenSessions: [],
  sessions: [],
  togetherPending: null,
  recap: null,
  resetBudget: () => {
    set({ rules: { ...get().rules, budget: { startedAt: 0, usedMs: 0 } } });
    playAt = Date.now();
    void persist();
    feedback();
  },
  openDaily: () => {
    const s = get();
    if (!active || !s.player || (s.rules.recapDay === dayKey() && s.rules.checkedDay === dayKey()))
      return;
    const today = dayKey();
    let rules = s.rules;
    if (rules.checkedDay !== today && gardenStreak(rules, today).forgiven)
      set({ message: 'YOUR GARDEN WAITED FOR YOU', voice: 'your garden waited for you.' });
    rules = { ...rules, checkedDay: today };
    if (rules.recapDay !== today) {
      set({ recap: previousDay(today) });
      rules = { ...rules, recapDay: today };
    }
    set({ rules });
    void persist();
  },
  dismissRecap: () => {
    set({ recap: null });
  },
  inviteTogether: async (rival) => {
    const p = get().player;
    if (!p || get().togetherPending || get().togetherId) return;
    set({ togetherPending: rival.id });
    try {
      await get().sync();
      const r = await bilt
        .from('touch_grass_sessions')
        .insert({ player_a: p.id, player_b: rival.id })
        .select()
        .single();
      if (r.error) throw r.error;
      set({ sessions: [...get().sessions, r.data] });
      feedback();
    } catch (error) {
      get().notify(
        error instanceof Error
          ? error.message
          : isRecord(error) && typeof error.message === 'string'
            ? error.message
            : 'COULD NOT SEND INVITE. TRY AGAIN.',
        true,
      );
    } finally {
      set({ togetherPending: null });
    }
  },
  acceptTogether: async (session) => {
    const p = get().player;
    if (!p || p.mode !== 'awake' || get().battle || get().togetherPending || get().togetherId)
      return;
    set({ togetherPending: session.player_a });
    try {
      await get().sync();
      const r = await bilt.rpc('accept_touch_grass', { sid: session.id, pid: p.id });
      if (r.error) throw r.error;
      const accepted = r.data?.[0];
      if (!accepted) throw new Error('BOTH GARDENERS MUST BE AWAKE. TRY AGAIN.');
      beginTogether(accepted);
      feedback();
    } catch (error) {
      get().notify(
        isRecord(error) && typeof error.message === 'string'
          ? error.message
          : 'COULD NOT ACCEPT. TRY AGAIN.',
        true,
      );
    } finally {
      set({ togetherPending: null });
    }
  },
  pollTogether: async () => {
    const p = get().player;
    if (!p) return;
    for (const wake of get().pendingTogetherWakes) {
      const report = await bilt.rpc('report_touch_grass_wake', {
        sid: wake.sid,
        pid: p.id,
        woke_at: wake.at,
        minutes: wake.minutes,
      });
      if (report.error) {
        get().notify(report.error.message, true);
        throw report.error;
      }
      set({ pendingTogetherWakes: get().pendingTogetherWakes.filter((x) => x.sid !== wake.sid) });
      await persist();
    }
    const r = await bilt
      .from('touch_grass_sessions')
      .select('*')
      .or(`player_a.eq.${p.id},player_b.eq.${p.id}`);
    if (r.error) throw r.error;
    set({ sessions: r.data ?? [] });
    for (const session of r.data ?? []) {
      const ownWake = session.player_a === p.id ? session.woke_a_at : session.woke_b_at;
      resolveTogetherSession(session);
      if (
        (session.status === 'active' || session.status === 'done') &&
        !ownWake &&
        !get().seenSessions.includes(session.id) &&
        !get().togetherId
      )
        beginTogether(session);
    }
  },
  player: null,
  identity: '',
  ready: false,
  live: false,
  rivals: [],
  now: Date.now(),
  tickAt: Date.now(),
  offStart: 0,
  offGrass: 0,
  outgoing: [],
  staged: [],
  applied: [],
  alerts: [],
  collectedCards: [],
  cardReward: null,
  waitingVisitor: null,
  homeTipActive: null,
  befriendVisitor: () => {
    const s = get();
    const v = s.waitingVisitor;
    if (!s.player || !v || v.expiresAt === 0) return;
    if (Date.now() >= v.expiresAt) {
      get().tick();
      return;
    }
    const collection = collectionOf(s.player).map((entry) =>
      entry.id === v.id ? { ...entry, befriendedAt: entry.befriendedAt ?? Date.now() } : entry,
    );
    set({
      player: { ...s.player, collection },
      waitingVisitor: null,
      voice: 'a new friend. all thanks to real life.',
    });
    changed();
    feedback();
  },
  selectGuardian: (id) => {
    const s = get();
    if (!s.player || s.battle || s.player.mode !== 'awake') return;
    if (id && !collectionOf(s.player).some((v) => v.id === id && v.befriendedAt !== null)) return;
    set({ player: { ...s.player, guardian: id } });
    changed();
    feedback('select');
  },
  guideOpen: false,
  deckOpen: false,
  message: null,
  voice: null,
  battle: null,
  flash: null,
  syncing: false,
  init: async () => {
    if (get().ready) return;
    try {
      const raw = await AsyncStorage.getItem(KEY);
      const parsed: unknown = migrateSaved(raw ? JSON.parse(raw) : null);
      if (parsed !== null && !isSaved(parsed)) throw new Error('Invalid saved game');
      const saved = parsed;
      const now = Date.now();
      set({ ...saved, identity: saved?.identity || Crypto.randomUUID(), ready: true, now });
      if (get().player?.mode === 'awake') {
        set({
          player: {
            ...get().player!,
            care_until: launchCareUntil(get().player!.care_until, get().lastActiveAt, now),
          },
          tickAt: now,
        });
      }
      set({ lastActiveAt: now });
      playAt = now;
      get().tick();
      get().openDaily();
      await persist();
      void get().sync();
    } catch {
      set({
        ready: true,
        identity: Crypto.randomUUID(),
        message: 'COULD NOT LOAD YOUR GRASSLING. TRY REOPENING THE APP.',
      });
      feedback('error');
    }
  },
  hatch: async (name, pet, species) => {
    const now = Date.now();
    const player: Player = {
      id: get().identity,
      code: code(),
      name: name.trim().toUpperCase(),
      pet_name: (pet.trim() || 'PIXEL').toUpperCase(),
      species,
      level: 1,
      grass: 20,
      mood: 80,
      hat: null,
      owned_hats: [],
      mode: 'awake',
      care_until: now + 30000,
      recovery_until: 0,
      mission_id: null,
      mission_ends_at: 0,
      offline_seconds: 0,
      last_seen: now,
      deck: [...startingDeck],
      collection: [],
      guardian: null,
      postcards: [],
    };
    set({
      player,
      now,
      lastActiveAt: now,
      tickAt: now,
      rules: { ...freshRules(now), recapDay: dayKey(now) },
      voice: "hi. i grow when you're not on your phone.",
    });
    await persist();
    feedback();
    void get().sync();
  },
  change: (patch) => {
    const p = get().player;
    if (!p) return;
    set({ player: { ...p, ...patch } });
    changed();
  },
  notify: (message, error = false) => {
    set({ message });
    if (error) feedback('error');
  },
  tick: () => {
    accountPlay();
    const s = get();
    const p = s.player;
    const now = Date.now();
    if (s.waitingVisitor && s.waitingVisitor.expiresAt > 0 && now >= s.waitingVisitor.expiresAt) {
      set({
        waitingVisitor: null,
        message: `${visitorInfo(s.waitingVisitor.id).name} wandered off.`,
      });
      void persist();
    }
    set({ now, ...(active ? { lastActiveAt: now } : {}) });
    if (active) void persist();
    if (!p) return;
    const seconds = Math.floor((now - s.tickAt) / 1000);
    if (seconds < 1) return;
    if (p.mode !== 'awake') {
      const end = p.mode === 'mission' ? Math.min(now, p.mission_ends_at) : now;
      const elapsed = Math.max(0, Math.floor((end - s.tickAt) / 1000));
      const completedMission =
        p.mode === 'mission' && now >= p.mission_ends_at ? (p.mission_id ?? undefined) : undefined;
      const rewardCards = offlineCards(
        p.deck,
        p.offline_seconds,
        p.offline_seconds + elapsed,
        completedMission,
      );
      const collectedCards = [...s.collectedCards, ...rewardCards.earned];
      let next: Player = {
        ...p,
        deck: rewardCards.deck,
        grass: p.grass + (p.mode === 'screen_off' ? elapsed : 0),
        mood: Math.min(100, p.mood + elapsed),
        offline_seconds: p.offline_seconds + elapsed,
      };
      let missionHat: string | null = null;
      if (p.mode === 'mission' && now >= p.mission_ends_at) {
        const m = missions.find((x) => x.id === p.mission_id);
        if (m) {
          let reward = m.reward;
          const unowned = hats.filter((h) => !p.owned_hats.includes(h.id));
          let hat: string | null = null;
          if (m.id === 'mountain') {
            if (unowned.length) hat = unowned[Math.floor(Math.random() * unowned.length)].id;
            else reward += 50;
          }
          missionHat = hat;
          next = {
            ...next,
            grass: next.grass + reward,
            owned_hats: hat ? [...p.owned_hats, hat] : p.owned_hats,
            mode: 'awake',
            mission_id: null,
            mission_ends_at: 0,
            care_until: now + 30000,
          };
          set({
            firstWake: true,
            message: null,
            voice: 'i saw a real tree. it was huge.',
          });
          feedback();
        }
      }
      let rules = recordOffline(
        get().rules,
        s.tickAt,
        elapsed,
        p.mode === 'screen_off' ? elapsed : 0,
      );
      for (
        let threshold = (Math.floor(p.offline_seconds / 15) + 1) * 15;
        threshold <= next.offline_seconds;
        threshold += 15
      )
        rules = bumpDay(rules, dayKey(s.tickAt + (threshold - p.offline_seconds) * 1000), {
          cards: 1,
        });
      rules = bumpDay(rules, dayKey(end), {
        cards: completedMission ? 1 : 0,
        grass: completedMission ? next.grass - p.grass : 0,
      });
      if (next.offline_seconds - s.offStart >= 10)
        rules = { ...rules, budget: { startedAt: 0, usedMs: 0 } };
      const minutes = next.offline_seconds - s.offStart;
      const visitor = completedMission ? rollVisitor(minutes, consecutiveOfflineDays(rules)) : null;
      const postcard: Postcard | null =
        completedMission === 'park' ||
        completedMission === 'book' ||
        completedMission === 'mountain'
          ? { id: Crypto.randomUUID(), mission: completedMission, at: end }
          : null;
      if (completedMission) {
        next = meetVisitor(next, visitor, minutes, now);
        if (postcard) next = { ...next, postcards: [...postcardsOf(next), postcard] };
      }
      set({
        rules,
        player: next,
        tickAt: s.tickAt + seconds * 1000,
        collectedCards: completedMission ? [] : collectedCards,
        ...(completedMission
          ? {
              waitingVisitor: visitor ? { id: visitor, expiresAt: 0 } : get().waitingVisitor,
              voice: visitor ? 'someone visited while you were gone!' : get().voice,
              cardReward: {
                cards: collectedCards,
                minutes,
                mission: completedMission,
                grass: next.grass - s.offGrass,
                visitor,
                postcard,
                hat: missionHat,
                early: false,
              },
            }
          : {}),
      });
      changed();
    } else {
      const ticks = Math.floor((now - s.tickAt) / 3000);
      if (ticks > 0) {
        if (active) {
          set({
            player: { ...p, mood: Math.max(0, p.mood - ticks) },
            tickAt: s.tickAt + ticks * 3000,
          });
          changed();
        } else set({ tickAt: now });
      }
      if (
        p.care_until > 0 &&
        s.now < p.care_until &&
        now >= p.care_until &&
        p.recovery_until <= now
      )
        set({ voice: "care window's over. we're exposed now." });
    }
    if (active && get().rules.recapDay !== dayKey()) get().openDaily();
  },
  sync: async () => {
    if (!get().player) return;
    if (get().syncing) {
      syncRequested = true;
      return;
    }
    syncRequested = false;
    let succeeded = false;
    set({ syncing: true });
    try {
      let p = get().player!;
      const snapshot = p;
      const result = await bilt
        .from('players')
        .upsert({ ...p, last_seen: Date.now() }, { onConflict: 'id' });
      if (result.error) {
        if (result.error.code === '23505') {
          set({ player: { ...get().player!, code: code() } });
          await persist();
        }
        throw result.error;
      }
      if (get().player === snapshot) set({ player: { ...snapshot, last_seen: Date.now() } });
      for (const raid of get().outgoing) {
        const r = await bilt
          .from('raids')
          .upsert(raid, { onConflict: 'id', ignoreDuplicates: true });
        if (r.error) throw r.error;
        set({ outgoing: get().outgoing.filter((x) => x.id !== raid.id) });
        await persist();
      }
      p = get().player!;
      const pairs = await bilt
        .from('pairs')
        .select('*')
        .or(`player_a.eq.${p.id},player_b.eq.${p.id}`);
      if (pairs.error) throw pairs.error;
      const ids = (pairs.data ?? []).map((x) => (x.player_a === p.id ? x.player_b : x.player_a));
      if (ids.length) {
        const rivals = await bilt.from('players').select('*').in('id', ids);
        if (rivals.error) throw rivals.error;
        set({ rivals: rivals.data ?? [] });
      } else set({ rivals: [] });
      await get().pollTogether();
      const daily = await bilt.from('garden_daily').select('*').eq('player_id', p.id);
      if (daily.error) throw daily.error;
      let rules = get().rules;
      for (const d of daily.data ?? [])
        rules = {
          ...rules,
          days: {
            ...rules.days,
            [d.day]: {
              ...emptyDay(),
              ...rules.days[d.day],
              raids: d.raids,
              blocked: Math.max(d.blocked, rules.days[d.day]?.blocked ?? 0),
            },
          },
        };
      set({ rules });
      await persist();
      if (get().player?.mode === 'awake' && !get().battle) {
        const raids = await bilt
          .from('raids')
          .select('*')
          .eq('defender_id', p.id)
          .eq('seen_by_defender', false)
          .order('created_at');
        if (raids.error) throw raids.error;
        for (const raid of raids.data ?? []) {
          if (
            !get().staged.some((x) => x.raid.id === raid.id) &&
            !get().applied.includes(raid.id)
          ) {
            const attacker = await bilt
              .from('players')
              .select('*')
              .eq('id', raid.attacker_id)
              .maybeSingle();
            if (attacker.error) throw attacker.error;
            set({ staged: [...get().staged, { raid, attacker: attacker.data }] });
            await persist();
          }
        }
        for (const item of get().staged) {
          if (get().player?.mode !== 'awake' || get().battle) break;
          const mark = await bilt
            .from('raids')
            .update({ seen_by_defender: true })
            .eq('id', item.raid.id);
          if (mark.error) throw mark.error;
          if (get().player?.mode !== 'awake' || get().battle) break;
          applyIncoming(item);
          await persist();
        }
        const update = await bilt.from('players').upsert(get().player!, { onConflict: 'id' });
        if (update.error) throw update.error;
      }
      succeeded = true;
      set({ live: true });
    } catch {
      set({ live: false });
    } finally {
      set({ syncing: false });
      if (syncRequested && succeeded) void get().sync();
    }
  },
  pair: async (input) => {
    const p = get().player;
    if (!p) return 'PLANT YOUR SEED FIRST';
    await get().sync();
    try {
      const found = await bilt
        .from('players')
        .select('*')
        .eq('code', input.trim().toUpperCase())
        .maybeSingle();
      if (found.error) throw found.error;
      const rival = found.data;
      if (!rival) return 'NO PLAYER WITH THAT CODE';
      if (rival.id === p.id) return "THAT'S YOU";
      const [a, b] = [p.id, rival.id].sort();
      const result = await bilt.from('pairs').insert({ player_a: a, player_b: b });
      if (result.error?.code === '23505') return 'ALREADY PAIRED';
      if (result.error) throw result.error;
      feedback();
      await get().sync();
      return null;
    } catch {
      set({ live: false });
      return 'COULD NOT PAIR. TRY AGAIN.';
    }
  },
  sleep: (mission) => {
    const p = get().player;
    if (!p || p.mode !== 'awake' || get().battle) return;
    const m = missions.find((x) => x.id === mission);
    if (m && p.level < m.level) return;
    const now = Date.now();
    set({
      offStart: p.offline_seconds,
      offGrass: p.grass,
      tickAt: now,
      player: {
        ...p,
        mode: m ? 'mission' : 'screen_off',
        mission_id: m?.id ?? null,
        mission_ends_at: m ? now + m.duration * 1000 : 0,
      },
    });
    changed();
    feedback();
  },
  wake: async () => {
    get().tick();
    const togetherId = get().togetherId;
    if (togetherId && get().player) {
      const s = get();
      set({
        pendingTogetherWakes: [
          ...s.pendingTogetherWakes,
          {
            sid: togetherId,
            at: new Date().toISOString(),
            minutes: s.player!.offline_seconds - s.offStart,
          },
        ],
        togetherId: null,
      });
    }
    const s = get();
    const p = s.player;
    if (!p || p.mode === 'awake') return;
    const elapsed = p.offline_seconds - s.offStart;
    const failed = p.mode === 'mission';
    const visitor = rollVisitor(elapsed, consecutiveOfflineDays(s.rules));
    const met = meetVisitor(p, visitor, elapsed, Date.now());
    set({
      player: {
        ...met,
        mode: 'awake',
        mission_id: null,
        mission_ends_at: 0,
        care_until: !failed && elapsed >= 10 ? Date.now() + 30000 : p.care_until,
      },
      firstWake: true,
      tickAt: Date.now(),
      collectedCards: [],
      waitingVisitor: visitor ? { id: visitor, expiresAt: 0 } : s.waitingVisitor,
      cardReward: {
        sessionId: togetherId,
        cards: s.collectedCards,
        minutes: elapsed,
        mission: failed ? p.mission_id : null,
        grass: p.grass - s.offGrass,
        visitor,
        postcard: null,
        hat: null,
        early: failed,
      },
      message: null,
      ...(visitor ? { voice: 'someone visited while you were gone!' } : {}),
    });
    changed();
    feedback(failed ? 'error' : 'success');
  },
  feed: () => {
    accountPlay();
    const p = get().player;
    if (!p || p.mode !== 'awake' || playPaused() || p.grass < 5 || p.mood >= 100) return;
    get().change({ grass: p.grass - 5, mood: Math.min(100, p.mood + 20) });
    feedback();
  },
  levelUp: () => {
    accountPlay();
    const p = get().player;
    if (!p || p.mode !== 'awake' || playPaused() || p.grass < 50 * p.level) return;
    const level = p.level + 1;
    get().change({
      level,
      grass: p.grass - 50 * p.level,
      deck: level === 3 ? addCard(p.deck, 'digital_sunset') : p.deck,
    });
    set({
      flash: `${level <= 3 ? 'YOUR GRASSLING BLOOMED!' : 'LEVEL UP!'}\nLV ${level}${level === 2 ? '\n4-CARD HAND UNLOCKED' : level === 3 ? '\nDIGITAL SUNSET ADDED' : ''}`,
    });
    feedback();
  },
  hatAction: (id) => {
    accountPlay();
    const p = get().player;
    const h = hats.find((x) => x.id === id);
    if (!p || p.mode !== 'awake' || playPaused() || !h) return;
    if (p.owned_hats.includes(id)) get().change({ hat: p.hat === id ? null : id });
    else if (p.grass >= h.cost)
      get().change({ grass: p.grass - h.cost, owned_hats: [...p.owned_hats, id], hat: id });
    else return;
    feedback();
  },
  startBattle: async (target, practice = false, revenge = false) => {
    accountPlay();
    const p = get().player;
    if (!p || p.mode !== 'awake' || get().battle || playPaused()) return;
    if (!practice && (get().rules.days[dayKey()]?.raids ?? 0) >= 3) {
      get().notify('NO RAIDS LEFT TODAY. COME BACK TOMORROW.');
      return;
    }
    const generation = ++battleGeneration;
    if (!practice) {
      const fresh = await bilt.from('players').select('*').eq('id', target.id).maybeSingle();
      if (fresh.error || !fresh.data) {
        set({ live: false });
        get().notify('COULD NOT START RAID. TRY AGAIN.', true);
        return;
      }
      if (status(fresh.data).kind !== 'exposed') {
        if (fresh.data.mode !== 'awake') {
          const blocked = await bilt.rpc('record_offline_block', {
            target: target.id,
            day_key: dayKey(),
          });
          if (blocked.error) {
            get().notify(blocked.error.message, true);
            return;
          }
        }
        get().notify(
          revenge ? "THEY'RE HIDING. TRY AGAIN LATER." : 'RAID BLOCKED. THEY PUT THEIR PHONE DOWN.',
          true,
        );
        return;
      }
      target = fresh.data;
    }
    if (
      !active ||
      generation !== battleGeneration ||
      get().player?.mode !== 'awake' ||
      get().battle
    )
      return;
    if (playPaused()) return;
    if (!practice) {
      const result = await bilt.rpc('reserve_garden_raid', {
        pid: p.id,
        target: target.id,
        day_key: dayKey(),
      });
      if (result.error) {
        get().notify(result.error.message, true);
        return;
      }
      const count = result.data?.[0];
      if (count === undefined) {
        get().notify('RAID UNAVAILABLE OR DAILY LIMIT REACHED.');
        void get().sync();
        return;
      }
      const rules = get().rules;
      set({
        rules: {
          ...rules,
          days: {
            ...rules.days,
            [dayKey()]: { ...emptyDay(), ...rules.days[dayKey()], raids: count },
          },
        },
      });
      await persist();
      if (
        !active ||
        generation !== battleGeneration ||
        get().player?.mode !== 'awake' ||
        get().battle ||
        playPaused()
      )
        return;
    }
    set({ battle: { target, practice } });
  },
  finishBattle: (won, target, practice) => {
    const p = get().player;
    if (!p || !get().battle) return;
    const day = get().rules.days[dayKey()] ?? emptyDay();
    const practiceGrass = sparringReward(day, won);
    const amount = raidGrass(won, target);
    const raid: Raid = {
      id: Crypto.randomUUID(),
      attacker_id: p.id,
      defender_id: target.id,
      attacker_won: won,
      grass_amount: amount,
      created_at: new Date().toISOString(),
      seen_by_defender: false,
    };
    set({
      rules: bumpDay(get().rules, dayKey(), {
        sparringWins: practice && won ? 1 : 0,
        grass: practice ? practiceGrass : won ? amount : 0,
      }),
      player: {
        ...p,
        grass: practice ? p.grass + practiceGrass : Math.max(0, p.grass + (won ? amount : -amount)),
      },
      outgoing: practice ? get().outgoing : [...get().outgoing, raid],
      battle: null,
      message: practice
        ? won
          ? practiceGrass > 0
            ? 'SPARRING WON! +5 GRASS'
            : 'DAVE IS TIRED. COME BACK TOMORROW.'
          : 'SPARRING LOST. TRY AGAIN.'
        : won
          ? `VICTORY! YOU STOLE ${amount} GRASS`
          : `RAID FAILED. -${amount} GRASS`,
      voice: won ? (Math.random() < 0.5 ? 'gg ez' : "that's what doomscrolling gets you.") : null,
    });
    changed();
    feedback(won ? 'success' : 'error');
  },
  incomingBot: () => {
    const p = get().player;
    if (!p) return;
    if (status(p).kind !== 'exposed') {
      if (p.mode !== 'awake') set({ rules: bumpDay(get().rules, dayKey(), { blocked: 1 }) });
      changed();
      get().notify('RAID BLOCKED. YOUR GARDEN WAS SAFE.');
      return;
    }
    const won = Math.random() < 0.5;
    const raid: Raid = {
      id: Crypto.randomUUID(),
      attacker_id: 'bot',
      defender_id: p.id,
      attacker_won: won,
      grass_amount: won ? Math.min(p.grass, Math.max(10, Math.floor(p.grass * 0.3))) : 0,
      created_at: new Date().toISOString(),
      seen_by_defender: true,
    };
    applyIncoming({ raid, attacker: bot(p) });
    changed();
  },
  dismissCards: () => {
    const s = get();
    set({
      cardReward: null,
      deckOpen: false,
      ...(s.waitingVisitor?.expiresAt === 0
        ? { waitingVisitor: { ...s.waitingVisitor, expiresAt: Date.now() + 10000 } }
        : {}),
    });
    void persist();
  },
  dismissAlert: () => {
    set({ alerts: get().alerts.slice(1) });
    changed();
  },
}));
gameStore.subscribe(() => {
  if (!accounting && eligiblePlay() !== playEligible) accountPlay();
});
export const useGame = gameStore;
export function raidGrass(won: boolean, target: Player) {
  return won ? Math.min(target.grass, Math.max(10, Math.floor(target.grass * 0.3))) : 10;
}
export function bot(p: Player): Player {
  return {
    ...p,
    id: 'bot',
    guardian: null,
    name: 'DOOMSCROLL DAVE',
    pet_name: 'DOOMSCROLL DAVE',
    species: 'RAT',
    mood: 50,
    hat: null,
    mode: 'awake',
    care_until: 0,
    recovery_until: 0,
    grass: 50,
    deck: [...daveDeck],
  };
}
let stop: (() => void) | null = null;
export function startGame() {
  if (stop) return stop;
  void gameStore.getState().init();
  const tick = setInterval(() => gameStore.getState().tick(), 1000);
  const sync = setInterval(() => {
    if (active) void gameStore.getState().sync();
  }, 3000);
  const sub = AppState.addEventListener('change', (state) => {
    accountPlay();
    const wasActive = active;
    active = state === 'active';
    if (wasActive === active) return;
    accountPlay();
    if (!active) {
      gameStore.setState({ lastActiveAt: Date.now() });
      battleGeneration += 1;
      gameStore.setState({ battle: null });
      void persist();
    } else {
      const s = gameStore.getState();
      if (s.player?.mode === 'awake') {
        s.change({ care_until: launchCareUntil(s.player.care_until, s.lastActiveAt, Date.now()) });
        gameStore.setState({ tickAt: Date.now() });
      }
      s.tick();
      s.openDaily();
      void s.sync();
    }
  });
  const visibility = () => {
    accountPlay();
    const visible = !document.hidden;
    if (active === visible) return;
    if (document.hidden) {
      active = false;
      battleGeneration += 1;
      gameStore.setState({ battle: null, lastActiveAt: Date.now() });
      void persist();
    } else {
      active = true;
      const s = gameStore.getState();
      if (s.player?.mode === 'awake') {
        gameStore.setState({ tickAt: Date.now() });
        s.change({ care_until: launchCareUntil(s.player.care_until, s.lastActiveAt, Date.now()) });
      }
      s.tick();
      s.openDaily();
      void s.sync();
    }
    accountPlay();
  };
  if (Platform.OS === 'web') document.addEventListener('visibilitychange', visibility);
  stop = () => {
    clearInterval(tick);
    clearInterval(sync);
    sub.remove();
    if (Platform.OS === 'web') document.removeEventListener('visibilitychange', visibility);
    stop = null;
  };
  return stop;
}
