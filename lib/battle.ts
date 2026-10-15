import type { Player } from '@/lib/game';
import { grasslingName } from '@/lib/grasslings';
import {
  cards,
  cardPower,
  drawHand,
  handSize,
  isCardId,
  shuffle,
  type CardId,
  type CardPiles,
} from '@/lib/cards';

export type Side = 'a' | 'd';
export type Move = CardId | 'pass';
export type Fighter = CardPiles & {
  hp: number;
  energy: number;
  nextEnergy: number;
  guard: boolean;
  notified: boolean;
  turns: number;
  handLimit: number;
};
export type Combat = {
  a: Fighter;
  d: Fighter;
  side: Side;
  result: boolean | null;
  timedOut: boolean;
};
export type Impact = { side: Side; amount: number; hp: number };
export const maxHp = (p: Player) => 60 + 10 * p.level;
export const zen = (p: Player) => Math.min(0.3, Math.floor(p.offline_seconds / 10) * 0.01);
export function matchup(source: Player['species'], target: Player['species']) {
  if (source === target) return 1;
  return (source === 'BLOB' && target === 'CUBE') ||
    (source === 'CUBE' && target === 'RAT') ||
    (source === 'RAT' && target === 'BLOB')
    ? 1.5
    : 0.67;
}
export function moveName(move: Move) {
  return move === 'pass' ? 'PASS' : cards[move].name;
}
export const damaging = (move: Move) => move !== 'pass' && cards[move].power > 0;
export function createCombat(a: Player, d: Player, random = Math.random): Combat {
  const fighter = (p: Player): Fighter => ({
    hp: maxHp(p),
    energy: 1,
    nextEnergy: 0,
    guard: false,
    notified: false,
    turns: 0,
    handLimit: handSize(p.level),
    ...drawHand(
      { hand: [], draw: shuffle(p.deck.filter(isCardId), random), discard: [] },
      handSize(p.level),
      random,
    ),
  });
  return beginTurn(
    { a: fighter(a), d: fighter(d), side: 'a', result: null, timedOut: false },
    'a',
    random,
  ).state;
}
export function available(move: Move, fighter: Fighter) {
  return move === 'pass' || (fighter.hand.includes(move) && fighter.energy >= cards[move].cost);
}
export function chooseAI(f: Fighter, p: Player): Move {
  const affordable = f.hand.filter((id) => available(id, f));
  if (f.hp < maxHp(p) * 0.35) {
    const heals = affordable
      .filter((id) => cards[id].heal > 0)
      .sort((a, b) => cards[b].heal - cards[a].heal);
    if (heals.length) return heals[0];
  }
  const attacks = affordable
    .filter((id) => cards[id].power > 0)
    .sort((a, b) => cardPower(b, p.species) - cardPower(a, p.species));
  if (attacks.length) return attacks[0];
  if (affordable.includes('deep_breath')) return 'deep_breath';
  if (affordable.length) return affordable.sort((a, b) => cards[b].heal - cards[a].heal)[0];
  return 'pass';
}
export function computerTiming(random = Math.random) {
  const roll = random();
  return roll < 0.2 ? 1.5 : roll < 0.8 ? 1 : 0.6;
}
export function timingAt(progress: number) {
  return progress >= 0.46 && progress <= 0.54
    ? 1.5
    : progress >= 0.28 && progress <= 0.72
      ? 1
      : 0.6;
}
export function beginTurn(
  state: Combat,
  side: Side,
  random = Math.random,
): { state: Combat; skipped: boolean } {
  if (state.d.turns >= 12)
    return { state: { ...state, result: false, timedOut: true }, skipped: false };
  const f = state[side];
  return {
    state: {
      ...state,
      side,
      [side]: {
        ...f,
        ...drawHand(f, f.handLimit, random),
        energy: Math.min(3, f.energy + 1 + f.nextEnergy),
        nextEnergy: 0,
        turns: f.turns + 1,
        notified: false,
      },
    },
    skipped: f.notified,
  };
}
export function resolveMove(
  state: Combat,
  move: Move,
  players: Record<Side, Player>,
  timing: number,
  blocked: boolean,
  random = Math.random,
) {
  const side = state.side;
  const dest: Side = side === 'a' ? 'd' : 'a';
  const impacts: Impact[] = [];
  if (state.result !== null || !available(move, state[side])) return { state, impacts, log: '' };
  const next: Combat = { ...state, a: { ...state.a }, d: { ...state.d } };
  const actor = next[side];
  const victim = next[dest];
  const source = players[side];
  const target = players[dest];
  let log = `${grasslingName(source)}: ${moveName(move)}!`;
  if (move === 'pass') {
    actor.energy = Math.min(3, actor.energy + 1);
    return { state: next, impacts, log: `${log} +1 ENERGY.` };
  }
  const card = cards[move];
  actor.energy -= card.cost;
  const hand = [...actor.hand];
  hand.splice(hand.indexOf(move), 1);
  actor.hand = hand;
  actor.discard = [...actor.discard, move];
  if (move === 'deep_breath') {
    actor.guard = true;
    actor.energy = Math.min(3, actor.energy + 1);
    log += ' GUARDED. +1 ENERGY.';
  }
  if (move === 'morning_walk') actor.nextEnergy += 1;
  if (card.heal > 0) {
    const heal = Math.min(card.heal, maxHp(source) - actor.hp);
    actor.hp += heal;
    log += ` +${heal} HP.`;
  }
  if (card.power > 0) {
    const type = matchup(source.species, target.species);
    const guarded = victim.guard && move !== 'digital_sunset';
    const amount = Math.max(
      1,
      Math.floor(
        (cardPower(move, source.species) + 2 * source.level + Math.floor(random() * 4)) *
          type *
          timing *
          (source.mood < 30 ? 0.7 : 1) *
          (guarded ? 0.5 : 1) *
          (1 - zen(target)) *
          (blocked ? 0.7 : 1),
      ),
    );
    victim.guard = false;
    victim.hp = Math.max(0, victim.hp - amount);
    impacts.push({ side: dest, amount, hp: victim.hp });
    log += ` -${amount} HP.`;
    if (card.habit === source.species) log += ' +3 HABIT POWER!';
    if (type > 1) log += ' HABIT ADVANTAGE!';
    if (type < 1) log += ' HABIT DISADVANTAGE...';
    if (blocked) log += ' BLOCKED!';
    if (timing === 1.5) log += ' PERFECT!';
    if (timing === 0.6) log += ' WEAK...';
    if (move === 'read_a_chapter' && victim.hp > 0 && random() < 0.3) {
      victim.notified = true;
      log += ' DISTRACTED!';
    }
  }
  if (next.a.hp <= 0) {
    next.result = false;
    log += ` ${grasslingName(players.a)} WILTED!`;
  } else if (next.d.hp <= 0) {
    next.result = true;
    log += ` ${grasslingName(players.d)} WILTED!`;
  }
  return { state: next, impacts, log };
}
