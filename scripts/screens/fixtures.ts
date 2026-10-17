import { breakReceipt, type RecentBreak } from '../../lib/break-history';
import { offlineCards, startingDeck, type CardId } from '../../lib/cards';
import {
  breakCompanion,
  type CompanionMemory,
  type CompanionMemoryOffer,
} from '../../lib/companion-memories';
import type { GardenTipId } from '../../lib/first-session';
import type { Player } from '../../lib/game';
import { emptyDay, freshRules } from '../../lib/offline-rules';
import type { Encounter, Postcard, WelcomeReward } from '../../lib/visitors';

/**
 * Synthetic progress for a disposable browser profile, never a production save.
 * The runner uses UTC so the saved day keys agree with the emulated browser even
 * when the machine building these fixtures uses a different local timezone.
 * All runtime imports are pure rules; importing this file does not start a store
 * or load React Native, storage, network, audio or crypto implementations.
 */
export function makeSavedGame(now: number, welcome = false) {
  if (!Number.isFinite(now) || now < 300_000) {
    throw new Error('Screenshot fixtures require a finite timestamp after the Unix epoch.');
  }

  const identity = '11111111-1111-4111-8111-111111111111';
  const today = new Date(now).toISOString().slice(0, 10);
  const previousBookAt = now - 120_000;
  const previousNapAt = now - 60_000;
  const completedAt = now - 5_000;
  const beforeDeck: CardId[] = [...startingDeck, 'read_a_chapter'];
  const missionCards = offlineCards(beforeDeck, 300, 330, 'book', () => 0.5);
  const oldPostcard: Postcard = {
    id: 'screens-postcard-park',
    mission: 'park',
    at: previousBookAt - 60_000,
  };
  const newPostcard: Postcard = {
    id: 'screens-postcard-book',
    mission: 'book',
    at: completedAt,
  };
  const collection: Encounter[] = [
    {
      id: 'dozebud',
      metAt: now - 240_000,
      minutes: 30,
      befriendedAt: now - 239_000,
    },
    {
      id: 'trailhop',
      metAt: now - 180_000,
      minutes: 15,
      befriendedAt: now - 179_000,
    },
    ...(welcome
      ? [{ id: 'inkling' as const, metAt: completedAt, minutes: 30, befriendedAt: null }]
      : []),
  ];
  const player: Player = {
    id: identity,
    code: 'TEST',
    name: 'ROWAN',
    // Starter identity remains canonical while DOZEBUD is the selected guardian.
    pet_name: 'PIXEL',
    species: 'RAT',
    level: 2,
    grass: welcome ? 240 : 180,
    mood: welcome ? 100 : 86,
    hat: 'CAP',
    owned_hats: ['CAP', 'SHADES'],
    mode: welcome ? 'mission' : 'awake',
    care_until: welcome ? 0 : now + 30_000,
    recovery_until: 0,
    mission_id: welcome ? 'book' : null,
    mission_ends_at: welcome ? completedAt : 0,
    // Existing growth reads this lifetime value, so beds and trees are populated.
    offline_seconds: welcome ? 330 : 300,
    last_seen: now,
    deck: welcome ? missionCards.deck : [...beforeDeck],
    collection,
    guardian: 'dozebud',
    postcards: welcome ? [oldPostcard, newPostcard] : [oldPostcard],
  };
  const priorReward: WelcomeReward = {
    cards: ['glass_of_water', 'short_walk', 'read_a_chapter'],
    minutes: 30,
    mission: 'book',
    grass: 60,
    visitor: null,
    postcard: null,
    hat: null,
    early: false,
  };
  const recentBreaks: RecentBreak[] = [
    breakReceipt('screens-previous-nap', previousNapAt, {
      ...priorReward,
      cards: ['deep_breath'],
      minutes: 20,
      mission: null,
      grass: 20,
    }),
    breakReceipt('screens-previous-book', previousBookAt, priorReward),
  ];
  const companion = breakCompanion(player);
  const companionMemories: CompanionMemory[] = [
    {
      id: 'screens-previous-book',
      intention: 'read',
      companion,
      completedAt: previousBookAt,
      minutes: 30,
      mission: 'book',
      early: false,
      recordedAt: previousBookAt + 1_000,
      source: 'self-reported',
    },
  ];
  const settlementId = `${identity}:book:${completedAt}`;
  const cardReward: WelcomeReward | null = welcome
    ? {
        settlementId,
        deckBefore: [...beforeDeck],
        cards: [...missionCards.earned],
        minutes: 30,
        mission: 'book',
        grass: 60,
        visitor: 'inkling',
        postcard: newPostcard,
        hat: null,
        early: false,
      }
    : null;
  const pendingMemories: CompanionMemoryOffer[] = [];
  if (cardReward) {
    recentBreaks.unshift(breakReceipt(settlementId, completedAt, cardReward));
    pendingMemories.push({
      id: settlementId,
      intention: 'read',
      companion,
      completedAt,
      minutes: 30,
      mission: 'book',
      early: false,
    });
  }
  const rules = {
    ...freshRules(now),
    checkedDay: today,
    recapDay: today,
    days: {
      [today]: {
        ...emptyDay(),
        offline: welcome ? 80 : 50,
        grass: welcome ? 140 : 80,
        cards: welcome ? 7 : 4,
      },
    },
  };

  return {
    missionReturnPending: welcome,
    quietView: false,
    recentBreaks,
    breakId: null,
    activeBreakContext: null,
    pendingMemories,
    companionMemories,
    memoryResolvedIds: companionMemories.map((memory) => memory.id),
    lastActiveAt: now,
    tips: ['arena', 'budget', 'card', 'phone', 'timing', 'wake'] satisfies GardenTipId[],
    firstWake: true,
    rules,
    togetherId: null,
    pendingTogetherWakes: [],
    togetherSettled: [],
    seenSessions: [],
    player,
    identity,
    tickAt: now,
    offStart: welcome ? 300 : 0,
    offDeck: welcome ? [...beforeDeck] : null,
    offGrass: welcome ? 180 : 0,
    outgoing: [],
    staged: [],
    applied: [],
    alerts: [],
    collectedCards: [],
    waitingVisitor: welcome ? { id: 'inkling' as const, expiresAt: 0 } : null,
    cardReward,
  };
}

export type ScreenshotSavedGame = ReturnType<typeof makeSavedGame>;
