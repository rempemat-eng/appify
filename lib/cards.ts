import type { Player } from '@/lib/game';

export type Rarity = 'COMMON' | 'RARE' | 'EPIC';
export const cards = {
  stretch: {
    name: 'STRETCH',
    rarity: 'COMMON',
    cost: 0,
    power: 8,
    heal: 0,
    effect: 'HIT 8',
    habit: 'CUBE',
  },
  deep_breath: {
    name: 'DEEP BREATH',
    rarity: 'COMMON',
    cost: 0,
    power: 0,
    heal: 0,
    effect: 'GUARD +1E',
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
    effect: 'HIT 12',
    habit: 'RAT',
  },
  morning_walk: {
    name: 'MORNING WALK',
    rarity: 'RARE',
    cost: 2,
    power: 16,
    heal: 0,
    effect: '16 +1E',
    habit: 'RAT',
  },
  read_a_chapter: {
    name: 'READ A CHAPTER',
    rarity: 'RARE',
    cost: 2,
    power: 10,
    heal: 0,
    effect: '10 SKIP?',
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
    effect: '20 +10HP',
    habit: null,
  },
  digital_sunset: {
    name: 'DIGITAL SUNSET',
    rarity: 'EPIC',
    cost: 3,
    power: 25,
    heal: 0,
    effect: '25 PIERCE',
    habit: null,
  },
} as const;
export type CardId = keyof typeof cards;
export const cardDetails: Record<CardId, string> = {
  stretch: 'POWER 8 · FOCUS +3 POWER',
  deep_breath: 'HALVE NEXT HIT · +1 ENERGY',
  glass_of_water: 'HEAL 10 HP',
  short_walk: 'POWER 12 · ROAM +3 POWER',
  morning_walk: 'POWER 16 · +1 ENERGY NEXT TURN · ROAM +3 POWER',
  read_a_chapter: 'POWER 10 · 30% DISTRACT: SKIP NEXT TURN · FOCUS +3 POWER',
  early_night: 'HEAL 20 HP',
  call_a_friend: 'POWER 20 · HEAL 10 HP',
  digital_sunset: 'POWER 25 · IGNORE GUARD',
};
export const startingDeck: CardId[] = [
  'stretch',
  'stretch',
  'stretch',
  'stretch',
  'deep_breath',
  'deep_breath',
];
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
