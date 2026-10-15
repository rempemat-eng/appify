import { launchCareUntil } from '@/lib/first-session';
import { startingDeck, upgradeStarterDeck, cards } from '@/lib/cards';
import { createCombat, beginTurn, chooseAI, resolveMove } from '@/lib/battle';
import type { Player } from '@/lib/game';
export function verifyFirstSession(player: Player, dave: Player) {
  const checks: string[] = [];
  function check(condition: boolean, name: string) {
    if (!condition) throw new Error(name);
    checks.push(name);
  }
  const now = 100_000;
  check(launchCareUntil(0, now - 9999, now) === 0, 'Quick relaunch stays exposed');
  check(launchCareUntil(123456, now - 1000, now) === 123456, 'Quick relaunch does not extend care');
  check(
    launchCareUntil(0, now - 10_000, now) === now + 30_000,
    '10 offline MIN grants 30-second care',
  );
  check(
    startingDeck.length === 7 &&
      startingDeck.filter((id) => id === 'stretch').length === 3 &&
      startingDeck.filter((id) => id === 'deep_breath').length === 2 &&
      startingDeck.includes('glass_of_water') &&
      startingDeck.includes('short_walk'),
    'Seven-card energy-aware starter',
  );
  const old = ['stretch', 'stretch', 'stretch', 'stretch', 'deep_breath', 'deep_breath'];
  const upgraded = upgradeStarterDeck(old);
  check(
    upgraded.length === 8 && upgraded.includes('glass_of_water') && upgraded.includes('short_walk'),
    'Legacy starter gets two cards',
  );
  check(upgradeStarterDeck(upgraded).length === 8, 'Starter upgrade runs once');
  check(upgradeStarterDeck(['stretch', 'short_walk']).length === 2, 'Earned decks left unchanged');
  let combat = createCombat(player, dave, () => 0.5);
  let spentEnergy = false;
  for (let turn = 0; turn < 30 && combat.result === null; turn++) {
    const side = combat.side;
    const actor = side === 'a' ? player : dave;
    const move = chooseAI(combat[side], actor);
    if (side === 'a' && move !== 'pass' && cards[move].cost > 0) spentEnergy = true;
    combat = resolveMove(
      combat,
      move,
      { a: player, d: dave },
      side === 'a' ? 1.5 : 1,
      side === 'd',
      () => 0.5,
    ).state;
    if (combat.result === null)
      combat = beginTurn(combat, side === 'a' ? 'd' : 'a', () => 0.5).state;
  }
  check(combat.result === true, 'Starting-deck spar reaches victory');
  check(spentEnergy, 'First spar spends energy');
  return { checks, combat };
}
