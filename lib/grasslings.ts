import type { Player } from '@/lib/game';

export const grasslings = {
  BLOB: {
    name: 'MOSSLING',
    habit: 'REST',
    line: 'rests hard. hits soft. never quits.',
    advantage: 'blocked the burnout',
  },
  RAT: {
    name: 'ROAMLING',
    habit: 'ROAM',
    line: 'gets out. gets around.',
    advantage: 'got you moving',
  },
  CUBE: {
    name: 'PEBBLING',
    habit: 'FOCUS',
    line: 'reads books. breaks rocks.',
    advantage: 'stayed on track',
  },
} as const;
export function growthStage(level: number) {
  return level === 1 ? 'SPROUT' : level === 2 ? 'BUD' : 'BLOOM';
}
export function grasslingName(p: Player) {
  return p.id === 'bot' ? 'DOOMSCROLL DAVE' : p.pet_name;
}
