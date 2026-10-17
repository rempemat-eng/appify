export const gardenTips = {
  phone: { control: 'Take a nap', text: "take a nap. put your phone down and i'll grow." },
  wake: {
    control: 'Garden status',
    text: 'welcome back! the garden stayed safe while we napped. it is open to visitors again now.',
  },
  arena: {
    control: 'Pair and spar',
    text: 'pair with a friend by code. spar with dave to learn the cards.',
  },
  card: { control: 'Habit cards', text: 'tap to lift, tap again to play' },
  timing: { control: 'Timing bar', text: 'tap in the middle' },
  budget: {
    control: 'Play budget',
    text: "i want you out in the world, not grinding here. take a nap and i'll grow and guard the garden.",
  },
} as const;
export type GardenTipId = keyof typeof gardenTips;
export const isGardenTip = (value: unknown): value is GardenTipId =>
  typeof value === 'string' && Object.hasOwn(gardenTips, value);
export function launchCareUntil(current: number, lastActiveAt: number, now: number) {
  return lastActiveAt > 0 && now - lastActiveAt >= 10_000 ? now + 30_000 : current;
}
