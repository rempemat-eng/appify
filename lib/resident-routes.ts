import type { ZoneId } from './zone-maps';

/**
 * Where each resident walks (world-atlas.md, "A world that feels alive"): a short
 * route of two points in zone pixels (their feet), walked there and back with a
 * pause at each end. Routes stay on open ground and never pass behind a prop (they
 * are drawn above the props; checked in region-walk.test.ts).
 * Presentation only: residents never block the companion and grant nothing.
 */
export type ResidentRoute = {
  zone: ZoneId;
  from: readonly [number, number];
  to: readonly [number, number];
};

export const residentRoutes: Record<string, ResidentRoute> = {
  gardener: { zone: 'town', from: [72, 260], to: [160, 260] },
  baker: { zone: 'town', from: [186, 212], to: [186, 300] },
  fisher: { zone: 'harbour', from: [152, 290], to: [240, 290] },
  keeper: { zone: 'harbour', from: [66, 276], to: [66, 364] },
  steward: { zone: 'castle', from: [84, 222], to: [172, 222] },
  tinkerer: { zone: 'junction', from: [96, 372], to: [184, 372] },
  boatwoman: { zone: 'canal', from: [136, 170], to: [224, 170] },
  cowhand: { zone: 'gulch', from: [132, 200], to: [132, 288] },
  saloon: { zone: 'gulch', from: [102, 380], to: [190, 380] },
  trader: { zone: 'oasis', from: [210, 546], to: [298, 546] },
  smith: { zone: 'caldera', from: [18, 434], to: [106, 434] },
  attendant: { zone: 'springs', from: [96, 516], to: [184, 516] },
  vendor: { zone: 'neon', from: [70, 332], to: [158, 332] },
  courier: { zone: 'neon', from: [18, 184], to: [106, 184] },
  porter: { zone: 'skyport', from: [52, 240], to: [140, 240] },
  farmer: { zone: 'halt', from: [202, 448], to: [290, 448] },
  hiker: { zone: 'ridge', from: [130, 228], to: [130, 316] },
  forager: { zone: 'woodland', from: [108, 278], to: [196, 278] },
  picnicker: { zone: 'park', from: [18, 100], to: [106, 100] },
  angler: { zone: 'riverside', from: [154, 362], to: [242, 362] },
  botanist: { zone: 'station', from: [64, 330], to: [152, 330] },
};
