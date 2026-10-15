import type { Player } from '@/lib/game';

export type Rarity = 'COMMON' | 'RARE' | 'EPIC';
export const cards = {
  stretch: {
    name: 'STRETCH',
    rarity: 'COMMON',
    cost: 0,
    power: 8,
    heal: 0,
    effect: '8 DMG',
    habit: 'CUBE',
  },
  deep_breath: {
    name: 'DEEP BREATH',
    rarity: 'COMMON',
    cost: 0,
    power: 0,
    heal: 0,
    effect: 'BLOCK HALF · +1 ⚡',
    habit: 'BLOB',
  },
  glass_of_water: {
    name: 'GLASS OF WATER',
    rarity: 'COMMON',
    cost: 1,
    power: 0,
    heal: 10,
    effect: 'HEAL 10',
    habit: null,
  },
  short_walk: {
    name: 'SHORT WALK',
    rarity: 'COMMON',
    cost: 1,
    power: 12,
    heal: 0,
    effect: '12 DMG',
    habit: 'RAT',
  },
  morning_walk: {
    name: 'MORNING WALK',
    rarity: 'RARE',
    cost: 2,
    power: 16,
    heal: 0,
    effect: '16 DMG · +1 ⚡',
    habit: 'RAT',
  },
  read_a_chapter: {
    name: 'READ A CHAPTER',
    rarity: 'RARE',
    cost: 2,
    power: 10,
    heal: 0,
    effect: '10 damage · 30% skip turn',
    habit: 'CUBE',
  },
  early_night: {
    name: 'EARLY NIGHT',
    rarity: 'RARE',
    cost: 2,
    power: 0,
    heal: 20,
    effect: 'HEAL 20',
    habit: 'BLOB',
  },
  call_a_friend: {
    name: 'CALL A FRIEND',
    rarity: 'EPIC',
    cost: 3,
    power: 20,
    heal: 10,
    effect: '20 DMG · +10 HP',
    habit: null,
  },
  digital_sunset: {
    name: 'DIGITAL SUNSET',
    rarity: 'EPIC',
    cost: 3,
    power: 25,
    heal: 0,
    effect: '25 DMG · NO BLOCK',
    habit: null,
  },
} as const;
export type CardId = keyof typeof cards;
export const cardDetails: Record<CardId, string> = {
  stretch: 'Power 8; FOCUS guardians add 3 power.',
  deep_breath: 'Halve the next incoming hit and gain 1 energy.',
  glass_of_water: 'Restore 10 HP.',
  short_walk: 'Power 12; ROAM guardians add 3 power.',
  morning_walk: 'Power 16 and gain 1 energy next turn; ROAM adds 3 power.',
  read_a_chapter:
    'Power 10 with a 30% chance to make your opponent skip their next turn; FOCUS adds 3 power.',
  early_night: 'Restore 20 HP.',
  call_a_friend: 'Power 20 and restore 10 HP.',
  digital_sunset: 'Power 25, ignoring the opponent’s guard.',
};
export const startingDeck: CardId[] = [
  'stretch',
  'stretch',
  'stretch',
  'deep_breath',
  'deep_breath',
  'glass_of_water',
  'short_walk',
];
export function upgradeStarterDeck(deck: string[]): string[] {
  return deck.length > 0 && deck.every((id) => id === 'stretch' || id === 'deep_breath')
    ? addCard(addCard(deck, 'glass_of_water'), 'short_walk')
    : deck;
}
export const daveDeck: CardId[] = [
  'stretch',
  'stretch',
  'stretch',
  'stretch',
  'stretch',
  'stretch',
  'short_walk',
  'short_walk',
  'glass_of_water',
  'glass_of_water',
];
export const isCardId = (value: unknown): value is CardId =>
  typeof value === 'string' && Object.hasOwn(cards, value);
export const cardIds = Object.keys(cards).filter(isCardId);
export const handSize = (level: number) => (level >= 2 ? 4 : 3);
export function cardPower(id: CardId, species: Player['species']) {
  const card = cards[id];
  return card.power > 0 ? card.power + (card.habit === species ? 3 : 0) : 0;
}
export function cardStrength(id: CardId) {
  const card = cards[id];
  const tier = { COMMON: 0, RARE: 100, EPIC: 200 }[card.rarity];
  return tier + Math.max(card.power, card.heal, id === 'deep_breath' ? 8 : 0);
}
export function addCard(deck: readonly string[], id: CardId): CardId[] {
  const next = deck.filter(isCardId);
  if (next.length < 20) return [...next, id];
  let weakest = 0;
  for (let i = 1; i < next.length; i++)
    if (cardStrength(next[i]) < cardStrength(next[weakest])) weakest = i;
  next[weakest] = id;
  return next;
}
export function summarizeCardRewards(before: readonly string[], earned: readonly CardId[]) {
  const entries = before.filter(isCardId).map((id) => ({ id, earned: false }));
  let previousReplaced = 0;
  for (const id of earned) {
    if (entries.length < 20) entries.push({ id, earned: true });
    else {
      let weakest = 0;
      for (let i = 1; i < entries.length; i++)
        if (cardStrength(entries[i].id) < cardStrength(entries[weakest].id)) weakest = i;
      if (!entries[weakest].earned) previousReplaced++;
      entries[weakest] = { id, earned: true };
    }
  }
  const kept = entries.filter((entry) => entry.earned).length;
  return {
    kept,
    previousReplaced,
    earnedReplaced: earned.length - kept,
    deck: entries.map((entry) => entry.id),
  };
}
export function randomCard(rarity: Rarity, random = Math.random): CardId {
  const pool = cardIds.filter((id) => cards[id].rarity === rarity);
  return pool[Math.floor(random() * pool.length)];
}
export function offlineCards(
  deck: readonly string[],
  before: number,
  after: number,
  mission?: string,
  random = Math.random,
) {
  const earned: CardId[] = [];
  const count = Math.floor(after / 15) - Math.floor(before / 15);
  for (let i = 0; i < count; i++) earned.push(randomCard('COMMON', random));
  if (mission) earned.push(randomCard(mission === 'mountain' ? 'EPIC' : 'RARE', random));
  return {
    deck: earned.reduce<CardId[]>((result, id) => addCard(result, id), deck.filter(isCardId)),
    earned,
  };
}
export function shuffle(deck: readonly CardId[], random = Math.random) {
  const next = [...deck];
  for (let i = next.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [next[i], next[j]] = [next[j], next[i]];
  }
  return next;
}
export type CardPiles = { hand: CardId[]; draw: CardId[]; discard: CardId[] };
export function drawHand(piles: CardPiles, size: number, random = Math.random): CardPiles {
  const next = { hand: [...piles.hand], draw: [...piles.draw], discard: [...piles.discard] };
  while (next.hand.length < size) {
    if (!next.draw.length) {
      if (!next.discard.length) break;
      next.draw = shuffle(next.discard, random);
      next.discard = [];
    }
    next.hand.push(next.draw.pop()!);
  }
  return next;
}
