export const gardenTips = {
  phone: { control: 'Put phone down', text: "put the phone down and i'll grow. try it for a bit." },
  wake: {
    control: 'Garden status',
    text: "while your phone was down, nobody could touch us. now it's up, raiders can come.",
  },
  arena: {
    control: 'Pair and spar',
    text: 'pair with a friend by code. spar with dave to learn the cards.',
  },
  card: { control: 'Habit cards', text: 'tap to lift, tap again to play' },
  timing: { control: 'Timing bar', text: 'tap in the middle' },
  budget: {
    control: 'Play budget',
    text: "i want you out in the world, not grinding here. offline time is how i grow. put the phone down and i'll guard the garden.",
  },
} as const;
export type GardenTipId = keyof typeof gardenTips;
export const isGardenTip = (value: unknown): value is GardenTipId =>
  typeof value === 'string' && Object.hasOwn(gardenTips, value);
export function launchCareUntil(current: number, lastActiveAt: number, now: number) {
  return lastActiveAt > 0 && now - lastActiveAt >= 10_000 ? now + 30_000 : current;
}
