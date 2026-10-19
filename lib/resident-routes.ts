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
  fisher: { zone: 'harbour', from: [172, 290], to: [212, 290] },
  keeper: { zone: 'harbour', from: [80, 252], to: [80, 330] },
  steward: { zone: 'hearthold', from: [146, 296], to: [196, 296] },
  tinkerer: { zone: 'junction', from: [96, 372], to: [184, 372] },
  boatwoman: { zone: 'canal', from: [136, 170], to: [224, 170] },
  cowhand: { zone: 'gulch', from: [132, 200], to: [132, 288] },
  saloon: { zone: 'gulch', from: [102, 380], to: [190, 380] },
  trader: { zone: 'oasis', from: [210, 546], to: [298, 546] },
  smith: { zone: 'caldera', from: [18, 434], to: [106, 434] },
  attendant: { zone: 'springs', from: [106, 516], to: [184, 516] },
  vendor: { zone: 'neon', from: [70, 332], to: [158, 332] },
  courier: { zone: 'neon', from: [18, 184], to: [106, 184] },
  porter: { zone: 'skyport', from: [52, 240], to: [140, 240] },
  farmer: { zone: 'halt', from: [202, 448], to: [262, 448] },
  hiker: { zone: 'ridge', from: [130, 228], to: [130, 316] },
  forager: { zone: 'woodland', from: [146, 268], to: [206, 268] },
  picnicker: { zone: 'park', from: [18, 100], to: [106, 100] },
  angler: { zone: 'riverside', from: [154, 362], to: [242, 362] },
  botanist: { zone: 'station', from: [64, 330], to: [152, 330] },
  stargazer: { zone: 'lumen', from: [176, 362], to: [264, 362] },
  warden: { zone: 'saddle', from: [152, 240], to: [168, 330] },
  skater: { zone: 'snowmelt', from: [162, 300], to: [208, 292] },
  ferryman: { zone: 'landing', from: [128, 360], to: [200, 364] },
  naturalist: { zone: 'rainforest', from: [200, 440], to: [194, 520] },
  beachcomber: { zone: 'cove', from: [130, 396], to: [206, 396] },
};

/** What each resident says when the companion stops beside them (decoration only). */
export const residentLines: Record<string, string> = {
  gardener: 'the beans are climbing again. slow is how they like it.',
  baker: 'the rolls come out at noon. come by when the bell rings.',
  fisher: 'the tide is turning. no hurry, the fish know the way.',
  keeper: 'i light the lamp at dusk and then i read till morning.',
  steward: 'the castle is quiet today. even the dragon is dozing.',
  tinkerer: 'every clock in cogsworth is a minute slow. on purpose.',
  boatwoman: 'the lock takes its time. so do we.',
  cowhand: 'the cattle know when to rest. wish folks did.',
  saloon: 'lemonade on the house for anyone off their phone.',
  trader: 'the spring never runs dry. the dunes keep its secret.',
  smith: 'the forge cools at sunset. even fire needs a nap.',
  attendant: 'the top pool is the warmest. towels are by the door.',
  vendor: 'noodles, no notifications. best deal in the harbour.',
  courier: 'i deliver everything except screens. those can wait.',
  porter: 'mind the gap. the stars will still be there.',
  farmer: 'the pumpkins grow while you sleep. funny, that.',
  hiker: 'the view from the ridge is better with your phone away.',
  forager: 'mushrooms come up after rain. you just have to look down.',
  picnicker: 'there is always room on the blanket.',
  angler: 'i have not caught a thing all day. perfect.',
  botanist: 'plants in space still want the same thing: light and quiet.',
  stargazer: 'i count the stars until one of us falls asleep.',
  warden: 'the bothy is always open. the kettle is always on.',
  skater: 'the lake thaws a little more each day. i like watching it.',
  ferryman: 'the ferry leaves when you are ready. the island will wait.',
  naturalist: 'there are frogs here no bigger than a fingernail. listen.',
  beachcomber: 'the black sand is warm by noon. lie down a while.',
};
