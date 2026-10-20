import type { WelcomeReward } from '@/lib/visitors';

export type RecentBreak = {
  id: string;
  completedAt: number;
  mission: string | null;
  early: boolean;
  minutes: number;
  grass: number; // Dream Dust the break paid (saved name kept from GRASS)
  cards: number;
  sessionId: string | null;
};

// A read-only receipt of an already settled recap, never a source of rewards.
export function breakReceipt(id: string, completedAt: number, reward: WelcomeReward): RecentBreak {
  return {
    id,
    completedAt,
    mission: reward.mission,
    early: reward.early,
    minutes: reward.minutes,
    grass: reward.grass,
    cards: reward.cards.length,
    sessionId: reward.sessionId ?? null,
  };
}
export function appendBreak(history: RecentBreak[], receipt: RecentBreak): RecentBreak[] {
  if (history.some((entry) => entry.id === receipt.id)) return history;
  return [receipt, ...history].sort((a, b) => b.completedAt - a.completedAt).slice(0, 20);
}
export function addTogetherReceiptBonus(history: RecentBreak[], sessionId: string, bonus: number) {
  return history.map((entry) =>
    entry.sessionId === sessionId ? { ...entry, grass: entry.grass + bonus } : entry,
  );
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

export function restoreBreakHistory(value: unknown): RecentBreak[] {
  if (!Array.isArray(value)) return [];
  const receipts: RecentBreak[] = [];
  for (const r of value) {
    if (!isRecord(r)) continue;
    if (
      typeof r.id === 'string' &&
      typeof r.completedAt === 'number' &&
      Number.isFinite(r.completedAt) &&
      (r.mission === null || typeof r.mission === 'string') &&
      typeof r.early === 'boolean' &&
      typeof r.minutes === 'number' &&
      Number.isFinite(r.minutes) &&
      typeof r.grass === 'number' &&
      Number.isFinite(r.grass) &&
      typeof r.cards === 'number' &&
      Number.isFinite(r.cards) &&
      (r.sessionId === null || typeof r.sessionId === 'string')
    ) {
      receipts.push({
        id: r.id,
        completedAt: r.completedAt,
        mission: r.mission,
        early: r.early,
        minutes: r.minutes,
        grass: r.grass,
        cards: r.cards,
        sessionId: r.sessionId,
      });
    }
  }
  return receipts.reduce<RecentBreak[]>((history, receipt) => appendBreak(history, receipt), []);
}
