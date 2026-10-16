import type { RecentBreak } from '@/lib/break-history';
import type { Player } from '@/lib/game';
import { effectiveGuardianId, isVisitorId, visitorInfo, type VisitorId } from '@/lib/visitors';

export type BreakIntention = 'rest' | 'read' | 'move' | 'create';
export type BreakCompanion = {
  key: 'starter' | VisitorId;
  name: string;
  species: Player['species'];
};
export type ActiveBreakContext = {
  breakId: string;
  playerId: string;
  intention: BreakIntention;
  companion: BreakCompanion;
  startedAt: number;
};
export type CompanionMemoryOffer = {
  id: string;
  intention: BreakIntention;
  companion: BreakCompanion;
  completedAt: number;
  minutes: number;
  mission: string | null;
  early: boolean;
};
export type CompanionMemory = CompanionMemoryOffer & {
  recordedAt: number;
  source: 'self-reported';
};

export const memoryLimit = 30;
export const pendingMemoryLimit = 5;
export const memoryResolutionLimit = 100;
// The current demo treats one elapsed second as one MIN. This is a reflection
// threshold, not evidence that the chosen real-world activity happened.
export const memoryMinimumMinutes = 1;
const intentionLabels: Record<BreakIntention, string> = {
  rest: 'Rest',
  read: 'Read',
  move: 'Move',
  create: 'Create',
};
export function breakIntentionLabel(intention: BreakIntention): string {
  return intentionLabels[intention];
}

export function isBreakIntention(value: unknown): value is BreakIntention {
  return value === 'rest' || value === 'read' || value === 'move' || value === 'create';
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function validText(value: unknown, limit: number): value is string {
  return typeof value === 'string' && value.trim().length > 0 && value.length <= limit;
}
function validTime(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0;
}
function restoreCompanion(value: unknown): BreakCompanion | null {
  if (
    !isRecord(value) ||
    (value.key !== 'starter' && !isVisitorId(value.key)) ||
    !validText(value.name, 80) ||
    (value.species !== 'BLOB' && value.species !== 'RAT' && value.species !== 'CUBE')
  )
    return null;
  // A visitor's family is fixed. Keep the saved display name as the snapshot.
  if (value.key !== 'starter' && visitorInfo(value.key).species !== value.species) return null;
  return { key: value.key, name: value.name, species: value.species };
}

export function breakCompanion(player: Player): BreakCompanion {
  const id = effectiveGuardianId(player);
  const visitor = id ? visitorInfo(id) : null;
  return {
    key: visitor?.id ?? 'starter',
    name: visitor?.name ?? player.pet_name,
    species: visitor?.species ?? player.species,
  };
}

export function restoreActiveBreakContext(
  value: unknown,
  breakId: unknown,
  player: Player | null,
): ActiveBreakContext | null {
  if (
    !player ||
    player.mode === 'awake' ||
    !isRecord(value) ||
    !validText(value.breakId, 256) ||
    value.breakId !== breakId ||
    value.playerId !== player.id ||
    !isBreakIntention(value.intention) ||
    !validTime(value.startedAt)
  )
    return null;
  const companion = restoreCompanion(value.companion);
  return companion
    ? {
        breakId: value.breakId,
        playerId: player.id,
        intention: value.intention,
        companion,
        startedAt: value.startedAt,
      }
    : null;
}

function restoreOffer(value: unknown): CompanionMemoryOffer | null {
  if (
    !isRecord(value) ||
    !validText(value.id, 256) ||
    !isBreakIntention(value.intention) ||
    !validTime(value.completedAt) ||
    !validTime(value.minutes) ||
    value.minutes < memoryMinimumMinutes ||
    !Number.isInteger(value.minutes) ||
    (value.mission !== null &&
      (typeof value.mission !== 'string' ||
        !['park', 'book', 'mountain'].includes(value.mission))) ||
    typeof value.early !== 'boolean' ||
    (value.early && value.mission === null)
  )
    return null;
  const companion = restoreCompanion(value.companion);
  return companion
    ? {
        id: value.id,
        intention: value.intention,
        companion,
        completedAt: value.completedAt,
        minutes: value.minutes,
        mission: value.mission,
        early: value.early,
      }
    : null;
}

export function restoreCompanionMemories(value: unknown): CompanionMemory[] {
  if (!Array.isArray(value)) return [];
  const memories: CompanionMemory[] = [];
  for (const entry of value) {
    const offer = restoreOffer(entry);
    if (
      !offer ||
      !isRecord(entry) ||
      entry.source !== 'self-reported' ||
      !validTime(entry.recordedAt) ||
      entry.recordedAt < offer.completedAt ||
      memories.some((memory) => memory.id === offer.id)
    )
      continue;
    memories.push({ ...offer, recordedAt: entry.recordedAt, source: 'self-reported' });
  }
  return memories.sort((a, b) => b.recordedAt - a.recordedAt).slice(0, memoryLimit);
}

export function restoreMemoryResolutions(value: unknown, memories: CompanionMemory[]): string[] {
  const ids = Array.isArray(value) ? value.filter((id) => validText(id, 256)) : [];
  return [...new Set([...ids, ...memories.map((memory) => memory.id)])].slice(
    -memoryResolutionLimit,
  );
}

export function restorePendingMemories(
  value: unknown,
  history: RecentBreak[],
  resolvedIds: string[],
): CompanionMemoryOffer[] {
  if (!Array.isArray(value)) return [];
  const offers: CompanionMemoryOffer[] = [];
  for (const entry of value) {
    const offer = restoreOffer(entry);
    if (!offer || resolvedIds.includes(offer.id) || offers.some((saved) => saved.id === offer.id))
      continue;
    const receipt = history.find((saved) => saved.id === offer.id);
    // Receipts roll off after 20 breaks; pending reflections have their own
    // bounded queue and must survive that archival. When a receipt is still
    // available it provides an additional consistency check. Structural
    // validation above always applies, and offers never settle game rewards.
    if (
      receipt &&
      (receipt.completedAt !== offer.completedAt ||
        receipt.minutes !== offer.minutes ||
        receipt.mission !== offer.mission ||
        receipt.early !== offer.early)
    )
      continue;
    offers.push(offer);
  }
  return offers.sort((a, b) => a.completedAt - b.completedAt).slice(-pendingMemoryLimit);
}

export function offerCompanionMemory(
  context: ActiveBreakContext | null,
  receipt: RecentBreak,
  pending: CompanionMemoryOffer[],
  resolvedIds: string[],
): CompanionMemoryOffer[] {
  if (
    !context ||
    context.breakId !== receipt.id ||
    receipt.completedAt < context.startedAt ||
    receipt.minutes < memoryMinimumMinutes ||
    pending.some((offer) => offer.id === receipt.id) ||
    resolvedIds.includes(receipt.id)
  )
    return pending;
  const offer: CompanionMemoryOffer = {
    id: receipt.id,
    intention: context.intention,
    companion: { ...context.companion },
    completedAt: receipt.completedAt,
    minutes: receipt.minutes,
    mission: receipt.mission,
    early: receipt.early,
  };
  return [...pending, offer].slice(-pendingMemoryLimit);
}
