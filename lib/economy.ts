/** C9 currency-safety slice. Care, gifts and protected-hour earning follow separately. */
export const RAID_TRANSFER_GRASS = 0;

export type RaidCurrencySettlement = {
  balance: number;
  earned: number;
  transferred: 0;
};

/** Preserve the existing victory reward. Defeat is not a purchase and costs nothing. */
export function attackingRaidReward(won: boolean, targetGrass: number): number {
  if (!won || !Number.isFinite(targetGrass) || targetGrass < 0) return 0;
  return Math.min(targetGrass, Math.max(10, Math.floor(targetGrass * 0.3)));
}

function credit(balance: number, reward: number): RaidCurrencySettlement {
  const next = balance + reward;
  // Never normalise a legacy wallet or introduce infinity through a credit.
  // The save/recovery boundary remains responsible for rejecting corrupt saves.
  if (!Number.isFinite(balance) || !Number.isFinite(next) || next < balance)
    return { balance, earned: 0, transferred: RAID_TRANSFER_GRASS };
  return { balance: next, earned: next - balance, transferred: RAID_TRANSFER_GRASS };
}

export function settleAttackingRaid(
  balance: number,
  won: boolean,
  targetGrass: number,
): RaidCurrencySettlement {
  return credit(balance, attackingRaidReward(won, targetGrass));
}

export function settleDefendingRaid(balance: number, attackerWon: boolean): RaidCurrencySettlement {
  // A successful defence retains its existing +20 reward, independently of loot.
  return credit(balance, attackerWon ? 0 : 20);
}

/** Old queued records keep their history, but must not ask an older client to debit GRASS. */
export function safeRaidTransport<T extends { grass_amount: number }>(raid: T): T {
  return { ...raid, grass_amount: RAID_TRANSFER_GRASS };
}
