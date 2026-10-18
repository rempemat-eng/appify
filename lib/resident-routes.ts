import type { ZoneId } from './zone-maps';

/**
 * Where each resident walks (world-atlas.md, "A world that feels alive"): a short
 * route of two points in zone pixels (their feet), walked there and back with a
 * pause at each end. Routes stay on open ground and clear of every prop, so a
 * resident never walks behind a building (checked in region-walk.test.ts).
 * Presentation only: residents never block the companion and grant nothing.
 */
export type ResidentRoute = {
  zone: ZoneId;
  from: readonly [number, number];
  to: readonly [number, number];
};

export const residentRoutes: Record<string, ResidentRoute> = {
  gardener: { zone: 'town', from: [70, 260], to: [170, 260] },
  baker: { zone: 'town', from: [184, 250], to: [184, 350] },
  fisher: { zone: 'harbour', from: [192, 290], to: [280, 290] },
  keeper: { zone: 'harbour', from: [66, 300], to: [66, 394] },
  steward: { zone: 'castle', from: [84, 222], to: [184, 222] },
  tinkerer: { zone: 'junction', from: [94, 372], to: [194, 372] },
  boatwoman: { zone: 'canal', from: [148, 170], to: [248, 170] },
  cowhand: { zone: 'gulch', from: [130, 224], to: [130, 324] },
  saloon: { zone: 'gulch', from: [100, 380], to: [200, 380] },
  trader: { zone: 'oasis', from: [208, 546], to: [302, 546] },
  smith: { zone: 'caldera', from: [20, 434], to: [120, 434] },
  attendant: { zone: 'springs', from: [110, 516], to: [210, 516] },
  vendor: { zone: 'neon', from: [68, 332], to: [162, 332] },
  courier: { zone: 'neon', from: [20, 184], to: [120, 184] },
  porter: { zone: 'skyport', from: [92, 250], to: [174, 250] },
  botanist: { zone: 'station', from: [62, 330], to: [162, 330] },
};
