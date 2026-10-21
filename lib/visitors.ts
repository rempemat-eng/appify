import type { Player } from '@/lib/game';
import { dayKey, previousDay, type OfflineRules } from '@/lib/offline-rules';

export const visitors = [
  { id: 'dozebud', name: 'DOZEBUD', habit: 'REST', rarity: 'COMMON', species: 'BLOB' },
  { id: 'mosspuff', name: 'MOSSPUFF', habit: 'REST', rarity: 'UNCOMMON', species: 'BLOB' },
  { id: 'lullapine', name: 'LULLAPINE', habit: 'REST', rarity: 'RARE', species: 'BLOB' },
  { id: 'trailhop', name: 'TRAILHOP', habit: 'ROAM', rarity: 'COMMON', species: 'RAT' },
  { id: 'burrbound', name: 'BURRBOUND', habit: 'ROAM', rarity: 'UNCOMMON', species: 'RAT' },
  { id: 'skyfern', name: 'SKYFERN', habit: 'ROAM', rarity: 'RARE', species: 'RAT' },
  { id: 'inkling', name: 'INKLING', habit: 'FOCUS', rarity: 'COMMON', species: 'CUBE' },
  { id: 'pagemoth', name: 'PAGEMOTH', habit: 'FOCUS', rarity: 'UNCOMMON', species: 'CUBE' },
  { id: 'lanternroot', name: 'LANTERNROOT', habit: 'FOCUS', rarity: 'RARE', species: 'CUBE' },
] as const;
export type VisitorId = (typeof visitors)[number]['id'];
export type Encounter = {
  id: VisitorId;
  metAt: number;
  minutes: number;
  befriendedAt: number | null;
};
export type WaitingVisitor = { id: VisitorId; expiresAt: number };
export type Postcard = { id: string; mission: 'park' | 'book' | 'mountain'; at: number };
export type WelcomeReward = {
  settlementId?: string;
  deckBefore?: import('@/lib/cards').CardId[];
  sessionId?: string | null;
  cards: import('@/lib/cards').CardId[];
  minutes: number;
  mission: string | null;
  grass: number; // Dream Dust (saved name kept from GRASS)
  visitor: VisitorId | null;
  postcard: Postcard | null;
  hat: string | null;
  early: boolean;
};
export const isVisitorId = (id: unknown): id is VisitorId => visitors.some((v) => v.id === id);
export const visitorInfo = (id: VisitorId) => visitors.find((v) => v.id === id)!;
export function collectionOf(p: Player): Encounter[] {
  if (!Array.isArray(p.collection)) return [];
  return p.collection.flatMap((entry) => {
    if (typeof entry !== 'object' || !entry || Array.isArray(entry)) return [];
    const { id, metAt, minutes, befriendedAt } = entry;
    return isVisitorId(id) &&
      typeof metAt === 'number' &&
      typeof minutes === 'number' &&
      (befriendedAt === null || typeof befriendedAt === 'number')
      ? [{ id, metAt, minutes, befriendedAt }]
      : [];
  });
}
export function postcardsOf(p: Player): Postcard[] {
  if (!Array.isArray(p.postcards)) return [];
  return p.postcards.flatMap((entry) => {
    if (typeof entry !== 'object' || !entry || Array.isArray(entry)) return [];
    const { id, mission, at } = entry;
    return typeof id === 'string' &&
      (mission === 'park' || mission === 'book' || mission === 'mountain') &&
      typeof at === 'number'
      ? [{ id, mission, at }]
      : [];
  });
}
export function guardianPlayer(p: Player): Player {
  const id = effectiveGuardianId(p);
  // The stored name and species always belong to the starter. Clear a stale
  // selection in this view too: the sprite renderer also reads guardian.
  if (!id) return p.guardian === null ? p : { ...p, guardian: null };
  const v = visitorInfo(id);
  return { ...p, species: v.species, pet_name: v.name };
}
export function befriendedVisitorIds(p: Player): VisitorId[] {
  if (p.id === 'bot') return [];
  const owned = new Set(
    collectionOf(p)
      .filter((v) => v.befriendedAt !== null && Number.isFinite(v.befriendedAt))
      .map((v) => v.id),
  );
  return visitors.filter((v) => owned.has(v.id)).map((v) => v.id);
}
export function effectiveGuardianId(p: Player): VisitorId | null {
  return isVisitorId(p.guardian) && befriendedVisitorIds(p).includes(p.guardian)
    ? p.guardian
    : null;
}
export function consecutiveOfflineDays(rules: OfflineRules, today = dayKey()) {
  let key = (rules.days[today]?.offline ?? 0) >= 120 ? today : previousDay(today);
  let count = 0;
  while ((rules.days[key]?.offline ?? 0) >= 120) {
    count++;
    key = previousDay(key);
  }
  return count;
}
// One roll per ended offline session; uniform draw from unlocked species.
export function rollVisitor(minutes: number, days: number, random = Math.random): VisitorId | null {
  if (minutes < 15 || random() >= (minutes >= 60 ? 0.8 : 0.4)) return null;
  const pool = visitors.filter(
    (v) =>
      v.rarity === 'COMMON' ||
      (v.rarity === 'UNCOMMON' && minutes >= 60) ||
      (v.rarity === 'RARE' && (minutes >= 120 || days >= 3)),
  );
  return pool[Math.min(pool.length - 1, Math.floor(random() * pool.length))].id;
}
// Minimum break length for the guaranteed first visitor, so the Field Journal
// shows up within a single short demo nap.
export const FIRST_VISITOR_MIN = 10;
// The first visitor is guaranteed: the common visitor that shares the
// Grassling's habit, on the first nap or mission of FIRST_VISITOR_MIN or more.
// After that, rollVisitor's normal odds apply.
export function visitorForBreak(
  p: Player,
  minutes: number,
  days: number,
  random = Math.random,
): VisitorId | null {
  if (collectionOf(p).length === 0) {
    if (minutes < FIRST_VISITOR_MIN) return null;
    const habit = { BLOB: 'REST', RAT: 'ROAM', CUBE: 'FOCUS' }[p.species];
    return visitors.find((v) => v.rarity === 'COMMON' && v.habit === habit)?.id ?? 'dozebud';
  }
  return rollVisitor(minutes, days, random);
}
// One-line hint for how to meet a visitor of this rarity (mirrors rollVisitor).
export function visitorHint(rarity: (typeof visitors)[number]['rarity']) {
  return rarity === 'COMMON'
    ? 'naps of 15+ MIN'
    : rarity === 'UNCOMMON'
      ? 'naps of 60+ MIN'
      : '2 h naps or 3 calm days';
}
export function meetVisitor(p: Player, id: VisitorId | null, minutes: number, at: number): Player {
  if (!id || collectionOf(p).some((v) => v.id === id)) return p;
  return { ...p, collection: [...collectionOf(p), { id, minutes, metAt: at, befriendedAt: null }] };
}
