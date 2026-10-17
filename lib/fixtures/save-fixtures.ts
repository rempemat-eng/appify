// Synthetic accounts reconstructed from the Saved type, hatch payload and
// migrateSaved at these historical commits. They contain no real player data.
// Keep their field sets independent of today's store/default constructors.
export const fixtureNow = Date.UTC(2026, 9, 17, 12);
const id = 'save-fixture-player';
const day = '2026-10-17';
const original = {
  player: {
    id,
    code: 'TEST',
    name: 'GARDENER',
    pet_name: 'PIXEL',
    species: 'RAT',
    level: 4,
    grass: 437,
    mood: 81,
    hat: 'CROWN',
    owned_hats: ['CAP', 'SHADES', 'CROWN'],
    mode: 'awake',
    care_until: fixtureNow + 60_000,
    recovery_until: 0,
    mission_id: null,
    mission_ends_at: 0,
    offline_seconds: 1080,
    last_seen: fixtureNow,
  },
  identity: id,
  tickAt: fixtureNow,
  offStart: 1000,
  offGrass: 397,
  outgoing: [],
  staged: [],
  applied: ['already-settled-raid'],
  alerts: [],
};
const cards = {
  ...original,
  player: {
    ...original.player,
    // The six-card starter in 07ca7d0, before the existing two-card upgrade.
    deck: ['stretch', 'stretch', 'stretch', 'stretch', 'deep_breath', 'deep_breath'],
  },
  collectedCards: ['short_walk'],
  cardReward: { cards: ['short_walk'], minutes: 40, mission: null },
};
const visitors = {
  ...cards,
  player: {
    ...cards.player,
    deck: [...cards.player.deck, 'glass_of_water', 'short_walk', 'digital_sunset'],
    collection: [
      { id: 'dozebud', metAt: fixtureNow - 80_000, minutes: 30, befriendedAt: fixtureNow - 79_000 },
      { id: 'inkling', metAt: fixtureNow - 60_000, minutes: 30, befriendedAt: fixtureNow - 59_000 },
    ],
    postcards: [{ id: 'postcard-book', mission: 'book', at: fixtureNow - 60_000 }],
    guardian: 'inkling',
  },
  lastActiveAt: fixtureNow,
  tips: ['phone'],
  firstWake: true,
  rules: {
    budget: { startedAt: fixtureNow - 10_000, usedMs: 12_000 },
    days: { [day]: { offline: 240, cards: 9, grass: 160, blocked: 2, raids: 1, sparringWins: 2 } },
    recapDay: day,
    checkedDay: day,
    togetherBadges: 3,
  },
  togetherId: null,
  pendingTogetherWakes: [],
  togetherSettled: ['settled-together'],
  seenSessions: ['seen-together'],
  waitingVisitor: { id: 'dozebud', expiresAt: 0 },
  cardReward: {
    ...cards.cardReward,
    grass: 40,
    visitor: 'dozebud',
    postcard: null,
    hat: null,
    early: false,
  },
};
const receipt = {
  id: 'receipt-book',
  completedAt: fixtureNow - 60_000,
  mission: 'book',
  early: false,
  minutes: 30,
  grass: 60,
  cards: 3,
  sessionId: null,
};
const history = {
  ...visitors,
  offDeck: [...cards.player.deck],
  recentBreaks: [receipt],
  breakId: null,
};
const memoryCompanion = { key: 'inkling', name: 'INKLING', species: 'CUBE' };
const memories = {
  ...history,
  activeBreakContext: null,
  pendingMemories: [],
  companionMemories: [
    {
      id: receipt.id,
      intention: 'read',
      companion: memoryCompanion,
      completedAt: receipt.completedAt,
      minutes: receipt.minutes,
      mission: receipt.mission,
      early: false,
      recordedAt: receipt.completedAt + 1000,
      source: 'self-reported',
    },
  ],
  memoryResolvedIds: [receipt.id],
};
const protectedReturn = {
  ...memories,
  player: {
    ...memories.player,
    mode: 'mission',
    mission_id: 'book',
    mission_ends_at: receipt.completedAt,
  },
  quietView: true,
  missionReturnPending: true,
  cardReward: {
    ...memories.cardReward,
    settlementId: receipt.id,
    cards: ['short_walk', 'read_a_chapter', 'glass_of_water'],
    minutes: 30,
    mission: 'book',
    grass: 60,
  },
};

export const saveFixtures = [
  {
    name: 'original pre-card save',
    sha: '17e484258094d68239bb1220647038f9fc049ca2',
    saved: original,
  },
  { name: 'original card save', sha: '07ca7d07bf43ea7ff23276fb4396e24347960f6e', saved: cards },
  {
    name: 'visitors and postcards',
    sha: 'cba65ce53647f22dfc8c22434f87a9bc7f3ed8a9',
    saved: visitors,
  },
  { name: 'break history', sha: '9d825871396c6a97b9e1e2e29065c0a0ab0b867d', saved: history },
  { name: 'companion memories', sha: 'a8366d2a49960a3425e816eafbd3132437df4911', saved: memories },
  {
    name: 'protected return',
    sha: '8776b39e2ca8a44956268341c7885667d93dec0a',
    saved: protectedReturn,
  },
] as const;

export function currentSaveFixture(): Record<string, unknown> {
  return JSON.parse(JSON.stringify({ ...memories, quietView: true, missionReturnPending: false }));
}
