import type { ComponentProps } from 'react';
import type { Player } from '@/lib/game';
import { guardianPlayer } from '@/lib/visitors';
import { Pet } from '@/components/game-ui';

// Preview the same companion on Home, missions and in the shop.
export function GuardianPet({
  player,
  ...props
}: { player: Player } & Omit<ComponentProps<typeof Pet>, 'species' | 'visitor'>) {
  const guardian = guardianPlayer(player);
  return (
    <Pet
      species={guardian.species}
      visitor={guardian.guardian}
      level={player.level}
      hat={player.hat}
      // greeted by its own name, not its kind
      actionLabel={`Greet ${guardian.pet_name}`}
      {...props}
    />
  );
}
