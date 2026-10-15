import type { Player } from '@/lib/game';
import { grasslingName } from '@/lib/grasslings';

export type Side = 'a' | 'd';
export type Move = 'quick' | 'signature' | 'guard' | 'heal' | 'break';
export type Fighter = {
  hp: number;
  energy: number;
  heals: number;
  breakUsed: boolean;
  guard: boolean;
  slowed: boolean;
  notified: boolean;
  doom: boolean;
  turns: number;
};
export type Combat = {
  a: Fighter;
  d: Fighter;
  side: Side;
  result: boolean | null;
  timedOut: boolean;
};
export type Impact = { side: Side; amount: number; hp: number };
export const signature = { BLOB: 'MOSS MIST', RAT: 'SEED FLURRY', CUBE: 'LAMP GLARE' };
export const costs: Record<Move, number> = { quick: 0, signature: 2, guard: 0, heal: 2, break: 3 };
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
export function moveName(move: Move, p: Player) {
  return move === 'signature'
    ? p.id === 'bot'
      ? 'PING SPAM'
      : signature[p.species]
    : { quick: 'QUICK HIT', guard: 'GUARD', heal: 'TOUCH GRASS', break: 'SCREEN BREAK' }[move];
}
export const damaging = (move: Move) =>
  move === 'quick' || move === 'signature' || move === 'break';
export function createCombat(a: Player, d: Player): Combat {
  const fighter = (p: Player): Fighter => ({
    hp: maxHp(p),
    energy: 1,
    heals: 0,
    breakUsed: false,
    guard: false,
    slowed: false,
    notified: false,
    doom: false,
    turns: 0,
  });
  const state: Combat = { a: fighter(a), d: fighter(d), side: 'a', result: null, timedOut: false };
  return beginTurn(state, 'a').state;
}
export function available(move: Move, fighter: Fighter, p: Player) {
  return (
    fighter.energy >= costs[move] &&
    (move !== 'heal' || fighter.heals < 2) &&
    (move !== 'break' || (p.level >= 2 && !fighter.breakUsed))
  );
}
export function chooseAI(f: Fighter, p: Player, random = Math.random): Move {
  if (f.hp < maxHp(p) * 0.35 && available('heal', f, p)) return 'heal';
  if (available('break', f, p)) return 'break';
  if (f.energy >= 2) return random() < 0.6 ? 'signature' : 'quick';
  return random() < 0.2 ? 'guard' : 'quick';
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
export function beginTurn(state: Combat, side: Side): { state: Combat; skipped: boolean } {
  // A full round consists of one turn for each pet, including skipped turns.
  if (state.d.turns >= 12)
    return { state: { ...state, result: false, timedOut: true }, skipped: false };
  const f = state[side];
  const skipped = f.notified;
  return {
    state: {
      ...state,
      side,
      [side]: {
        ...f,
        energy: Math.min(3, f.energy + 1),
        turns: f.turns + 1,
        slowed: false,
        notified: false,
        doom: skipped ? false : f.doom,
      },
    },
    skipped,
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
  const next: Combat = { ...state, a: { ...state.a }, d: { ...state.d } };
  const side = state.side;
  const dest: Side = side === 'a' ? 'd' : 'a';
  const actor = next[side];
  const victim = next[dest];
  const source = players[side];
  const target = players[dest];
  const impacts: Impact[] = [];
  if (state.result !== null || !available(move, actor, source)) return { state, impacts, log: '' };
  actor.energy -= costs[move];
  const doom = actor.doom;
  actor.doom = false;
  let log = `${grasslingName(source)}: ${moveName(move, source)}!`;
  if (move === 'guard') {
    actor.guard = true;
    actor.energy = Math.min(3, actor.energy + 1);
    return { state: next, impacts, log: `${log} GUARDED.` };
  }
  if (move === 'heal') {
    const heal = Math.min(15, maxHp(source) - actor.hp);
    actor.hp += heal;
    actor.heals++;
    return { state: next, impacts, log: `${log} +${heal} HP.` };
  }
  if (move === 'break') actor.breakUsed = true;
  const selfHit = doom && random() < 0.5;
  const victimSide = selfHit ? side : dest;
  const hitFighter = selfHit ? actor : victim;
  const hitPlayer = selfHit ? source : target;
  const power =
    move === 'quick'
      ? 8
      : move === 'break'
        ? 25
        : source.species === 'RAT'
          ? 5
          : source.species === 'BLOB'
            ? 12
            : 16;
  const hits = move === 'signature' && source.species === 'RAT' ? 3 : 1;
  const type = matchup(source.species, hitPlayer.species);
  let total = 0;
  for (let i = 0; i < hits && hitFighter.hp > 0; i++) {
    const guarded = hitFighter.guard && move !== 'break';
    const amount = Math.max(
      1,
      Math.floor(
        (power + 2 * source.level + Math.floor(random() * 4)) *
          type *
          timing *
          (source.mood < 30 ? 0.7 : 1) *
          (hitPlayer.level >= 3 ? 0.8 : 1) *
          (guarded ? 0.5 : 1) *
          (1 - zen(hitPlayer)) *
          (selfHit ? 0.5 : blocked ? 0.7 : 1),
      ),
    );
    hitFighter.guard = false;
    hitFighter.hp = Math.max(0, hitFighter.hp - amount);
    total += amount;
    impacts.push({ side: victimSide, amount, hp: hitFighter.hp });
  }
  log += ` -${total}${impacts.length > 1 ? ` (${impacts.length} HITS)` : ''}`;
  if (selfHit) log = `IT'S DOOMSCROLLING... ${log} SELF HIT!`;
  else {
    if (type > 1) log += ' HABIT ADVANTAGE!';
    if (type < 1) log += ' HABIT DISADVANTAGE...';
    if (blocked) log += ' BLOCKED!';
    if (timing === 1.5) log += ' PERFECT!';
    if (timing === 0.6) log += ' WEAK...';
    if (move === 'signature' && victim.hp > 0) {
      if (source.species === 'BLOB' && random() < 0.3) {
        victim.energy = Math.max(0, victim.energy - 1);
        victim.slowed = true;
        log += ' SLOWED!';
      }
      if (source.species === 'RAT' && random() < 0.25) {
        victim.notified = true;
        log += ' NOTIFIED!';
      }
      if (source.species === 'CUBE' && random() < 0.25) {
        victim.doom = true;
        log += ' DOOMSCROLLING!';
      }
    }
  }
  if (next.a.hp <= 0) next.result = false;
  else if (next.d.hp <= 0) next.result = true;
  if (next.a.hp <= 0) log += ` ${grasslingName(players.a)} WILTED!`;
  else if (next.d.hp <= 0) log += ` ${grasslingName(players.d)} WILTED!`;
  return { state: next, impacts, log };
}
