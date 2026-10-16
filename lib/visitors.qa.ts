import { createCombat, chooseAI, resolveMove, beginTurn } from '@/lib/battle';
import type { Player } from '@/lib/game';
import { emptyDay, freshRules, previousDay, dayKey } from '@/lib/offline-rules';
import {
  collectionOf,
  consecutiveOfflineDays,
  guardianPlayer,
  meetVisitor,
  rollVisitor,
  visitorForBreak,
  visitors,
} from '@/lib/visitors';
import { visitorPixels } from '@/lib/visitor-art';

function rolls(chance: number, pick: number) {
  let draw = 0;
  return () => (draw++ === 0 ? chance : pick);
}
export function verifyVisitors(player: Player, dave: Player) {
  const checks: string[] = [];
  const check = (condition: boolean, name: string) => {
    if (!condition) throw new Error(name);
    checks.push(name);
  };
  check(rollVisitor(14, 3, () => 0) === null, 'Under 15 MIN never rolls a visitor');
  check(
    rollVisitor(15, 0, rolls(0.399, 0)) === 'dozebud',
    '15 MIN has 40% chance and commons only',
  );
  check(rollVisitor(15, 0, rolls(0.4, 0)) === null, '40% chance boundary');
  check(rollVisitor(60, 0, rolls(0.799, 0.2)) === 'mosspuff', '60 MIN unlocks uncommon at 80%');
  check(rollVisitor(60, 0, rolls(0.8, 0)) === null, '80% chance boundary');
  check(rollVisitor(120, 0, rolls(0, 0.3)) === 'lullapine', '120 MIN unlocks rare');
  check(
    rollVisitor(15, 3, rolls(0, 0.2)) === 'lullapine',
    'Three consecutive offline days unlock rare',
  );
  let rules = freshRules();
  let day = dayKey();
  for (let i = 0; i < 3; i++) {
    rules.days[day] = { ...emptyDay(), offline: 120 };
    day = previousDay(day);
  }
  check(consecutiveOfflineDays(rules) === 3, 'Consecutive offline days calculated');
  rules.days[previousDay(dayKey())].offline = 119;
  check(consecutiveOfflineDays(rules) === 1, 'Grace day does not unlock rare visitor');
  const fresh: Player = { ...player, species: 'RAT', collection: [] };
  check(visitorForBreak(fresh, 9, 0, () => 0) === null, 'First visitor needs 10 MIN');
  check(
    visitorForBreak(fresh, 10, 0, () => 0.99) === 'trailhop',
    'First 10 MIN break guarantees the habit-matched common visitor',
  );
  const met = meetVisitor(player, 'dozebud', 15, 1000);
  check(
    visitorForBreak(met, 15, 0, () => 0.99) === null,
    'After the first visitor, normal odds apply',
  );
  const repeat = meetVisitor(met, 'dozebud', 60, 2000);
  check(
    collectionOf(repeat).length === 1 && collectionOf(repeat)[0].minutes === 15,
    'Journal retains first offline meeting',
  );
  const friend: Player = {
    ...met,
    guardian: 'dozebud',
    collection: collectionOf(met).map((v) => ({ ...v, befriendedAt: 1001 })),
  };
  const guardian = guardianPlayer(friend);
  check(
    guardian.pet_name === 'DOZEBUD' &&
      guardian.species === 'BLOB' &&
      friend.species === player.species &&
      guardian.deck === friend.deck &&
      guardian.level === friend.level &&
      guardian.hat === friend.hat,
    'Guardian reuses account deck, level and hat without altering stored species',
  );
  let combat = createCombat(guardian, dave, () => 0.5);
  for (let i = 0; i < 30 && combat.result === null; i++) {
    const side = combat.side;
    combat = resolveMove(
      combat,
      chooseAI(combat[side], side === 'a' ? guardian : dave),
      { a: guardian, d: dave },
      side === 'a' ? 1.5 : 1,
      side === 'd',
      () => 0.5,
    ).state;
    if (combat.result === null)
      combat = beginTurn(combat, side === 'a' ? 'd' : 'a', () => 0.5).state;
  }
  check(combat.result !== null, 'Visitor guardian sparring resolves to win or loss');
  check(
    visitors.every((v) => visitorPixels(v.id).length > 0),
    'Nine visitor pixel sprites render',
  );
  return checks;
}
