/**
 * Fight content as data: a PROPOSAL (Claude L, gameplay mechanics, 21 Oct).
 *
 * Nothing here is read by the game. It is the input to the balance simulation in
 * `lib/fight-sim.ts` (run with `npm run sim:fights`), and it becomes game data only after
 * Matt decides (docs/mechanics/fight-content.md). Folk and their mechanics come from
 * docs/vision/cast.md, the numbers from docs/vision/fights.md section 5, retuned by the
 * simulation. Fights stay Pokemon-style: the separate battle screen, turn-based cards
 * (Matt, 21 Oct 10:03).
 *
 * Rules every entry keeps (AGENTS.md, cast.md section 6): no time-of-day bonus; a still
 * turn banks at most one point of one stack and every stack is capped at 3; guard is a
 * simple rule; a doze is once a fight and never in a raid against an absent player;
 * signature cards have no habit, so the familiar's family still decides which habit cards
 * hit harder; nothing here pays or costs Dream Dust.
 */

export type Family = 'REST' | 'ROAM' | 'FOCUS';
/** The saved species behind each family (`lib/battle.ts` matchup). */
export const familySpecies = { REST: 'BLOB', ROAM: 'RAT', FOCUS: 'CUBE' } as const;
export const families: Family[] = ['REST', 'ROAM', 'FOCUS'];

/** A signature card. Every number is a first-pass value for the simulation. */
export type SignatureCard = {
  id: string;
  name: string;
  cost: number;
  text: string;
  /** Damage before + 2 x level, the 0 to 3 roll and the matchup. */
  power?: number;
  ignoreGuard?: boolean;
  heal?: number;
  /** Halve the next hit (Cairn's passive makes it two hits). */
  guard?: boolean;
  energyNow?: number;
  energyNext?: number;
  draw?: number;
  /** Adds to your own stack (Aim, Dusk, drops, heat...), capped at 3. */
  gainStack?: number;
  /** Takes from your own stack. */
  loseStack?: number;
  /** Scales with your own stack. `spend` empties it. */
  perStack?: { power?: number; heal?: number; spend?: boolean; spendOne?: boolean };
  /** Puffcap's spores on the foe. */
  spores?: number;
  /** Heal at the start of each of your next turns. */
  mend?: { amount: number; turns: number };
  /** Bramble's arrows spend Aim (the passive). */
  arrow?: boolean;
  /** Extra power while you are guarded; `spendGuard` uses the guard up. */
  whileGuarded?: { power?: number; energyNext?: number; spendGuard?: boolean };
  /** Extra power if a trick was muted or reflected this fight (Nix). */
  afterTrick?: number;
  /** Extra power per card in hand (Tally). */
  perCardInHand?: number;
  /** One-off behaviours the engine knows by name. */
  special?:
    | 'flipTide'
    | 'cleanse'
    | 'stardust'
    | 'forgeRest'
    | 'removeFoeGuard'
    | 'drainOnEbb'
    | 'nockSteady'
    | 'pour';
  /** Ebb/flow bonus on Puddle's cards: flow power replaces the passive's +3. */
  flowPower?: number;
  noEbbSoak?: boolean;
};

export type PassiveId =
  | 'steady'
  | 'drowsy'
  | 'dim'
  | 'bedrock'
  | 'minuteSlow'
  | 'tide'
  | 'seep'
  | 'bankedFire'
  | 'doNotDisturb'
  | 'dream'
  | 'countingSheep'
  | 'bothy'
  | 'overgrow'
  | 'sleepCycle';

export type Passive = {
  id: PassiveId;
  name: string;
  text: string;
  /** The stack's name on the plate, if any. */
  stack?: string;
  /** Numbers the engine reads. */
  n: Record<string, number>;
};

/** A choice between two variants of one signature card at a shared level. */
export type VariantChoice = {
  level: 4 | 8 | 12;
  card: string;
  a: { name: string; text: string; patch: Partial<SignatureCard> };
  b: { name: string; text: string; patch: Partial<SignatureCard> };
};

export type Folk = {
  id: string;
  name: string;
  role: string;
  /** cast.md: the night on the circle of fourteen stones (1 to 3 are the starters). */
  night: number;
  unlock: string;
  passive: Passive;
  cards: [SignatureCard, SignatureCard, SignatureCard, SignatureCard];
  variants: [VariantChoice, VariantChoice, VariantChoice];
};

const P = (p: Passive) => p;

export const folk: Folk[] = [
  {
    id: 'bramble',
    name: 'Bramble',
    role: 'striker',
    night: 1,
    unlock: 'starter',
    passive: P({
      id: 'steady',
      name: 'Steady',
      text: 'End your turn with energy unspent: +1 Aim (max 3). An arrow spends all Aim for +4 power each.',
      stack: 'Aim',
      n: { perAim: 4 },
    }),
    cards: [
      {
        id: 'nock',
        name: 'NOCK',
        cost: 0,
        draw: 1,
        special: 'nockSteady',
        text: 'Draw 1. Steady counts this turn even with no energy left.',
      },
      { id: 'loose', name: 'LOOSE', cost: 1, power: 9, arrow: true, text: 'Arrow, power 9.' },
      {
        id: 'long_shot',
        name: 'LONG SHOT',
        cost: 2,
        power: 12,
        arrow: true,
        ignoreGuard: true,
        perStack: { power: 1 },
        text: 'Arrow, power 12, +5 per Aim instead of +4, ignores guard.',
      },
      {
        id: 'take_cover',
        name: 'TAKE COVER',
        cost: 1,
        guard: true,
        gainStack: 1,
        text: 'Guard, +1 Aim.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'loose',
        a: {
          name: 'QUICK LOOSE',
          text: '0 energy, power 6.',
          patch: { cost: 0, power: 6 },
        },
        b: {
          name: 'HEAVY LOOSE',
          text: '1 energy, power 9, +1 per Aim more.',
          patch: { power: 9, perStack: { power: 1 } },
        },
      },
      {
        level: 8,
        card: 'nock',
        a: { name: 'NOCK', text: 'Draw 1.', patch: {} },
        b: {
          name: 'NOCK AND DRAW',
          text: 'Draw 2, Steady does not count.',
          patch: { draw: 2, special: undefined },
        },
      },
      {
        level: 12,
        card: 'long_shot',
        a: { name: 'LONG SHOT', text: 'Ignores guard.', patch: {} },
        b: {
          name: 'HEAVY SHOT',
          text: 'Power 14, keeps guard.',
          patch: { power: 14, ignoreGuard: false },
        },
      },
    ],
  },
  {
    id: 'puffcap',
    name: 'Puffcap',
    role: 'soother',
    night: 2,
    unlock: 'starter',
    passive: P({
      id: 'drowsy',
      name: 'Drowsy',
      text: 'Spores on the foe (max 3). At three it dozes through its next action, once a fight; after that, three spores soften its next card by a third. In a raid: always the softening.',
      stack: 'spores',
      n: {},
    }),
    cards: [
      {
        id: 'spore_puff',
        name: 'SPORE PUFF',
        cost: 0,
        power: 6,
        spores: 1,
        text: 'Power 6, +1 spore.',
      },
      { id: 'lull', name: 'LULL', cost: 1, spores: 2, text: '+2 spores.' },
      {
        id: 'soft_landing',
        name: 'SOFT LANDING',
        cost: 1,
        heal: 5,
        mend: { amount: 5, turns: 2 },
        text: 'Heal 5 now and 5 at the start of each of your next two turns.',
      },
      {
        id: 'toadstool_ring',
        name: 'TOADSTOOL RING',
        cost: 2,
        power: 11,
        guard: true,
        text: 'Power 11 and guard.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'lull',
        a: { name: 'LULL', text: '+2 spores.', patch: {} },
        b: {
          name: 'LULLABY',
          text: '+1 spore, heal 6.',
          patch: { spores: 1, heal: 6 },
        },
      },
      {
        level: 8,
        card: 'soft_landing',
        a: { name: 'SOFT LANDING', text: 'Over two turns.', patch: {} },
        b: {
          name: 'SLOW LANDING',
          text: 'Heal 3 now, 4 a turn over three turns.',
          patch: { heal: 3, mend: { amount: 4, turns: 3 } },
        },
      },
      {
        level: 12,
        card: 'spore_puff',
        a: { name: 'SPORE PUFF', text: 'Power 6, +1 spore.', patch: {} },
        b: {
          name: 'SPORE BURST',
          text: '1 energy, power 9, +1 spore.',
          patch: { cost: 1, power: 9 },
        },
      },
    ],
  },
  {
    id: 'velvet',
    name: 'Velvet',
    role: 'shade',
    night: 3,
    unlock: 'starter',
    passive: P({
      id: 'dim',
      name: 'Dim',
      text: "She starts each fight with 1 Dusk; a still turn: +1 Dusk (max 3). Each Dusk is spent on the foe's next damaging card, which deals a third less (one Dusk a hit).",
      stack: 'Dusk',
      n: { start: 1 },
    }),
    cards: [
      {
        id: 'shutter',
        name: 'SHUTTER',
        cost: 0,
        guard: true,
        text: 'Guard (a still turn, so Dim banks a Dusk).',
      },
      { id: 'lamp_low', name: 'LAMP LOW', cost: 1, heal: 9, text: 'Heal 9.' },
      {
        id: 'moth_wing',
        name: 'MOTH WING',
        cost: 1,
        power: 10,
        perStack: { power: 3 },
        text: 'Power 10, +3 per Dusk held (not spent).',
      },
      {
        id: 'night_falls',
        name: 'NIGHT FALLS',
        cost: 2,
        power: 6,
        perStack: { power: 6, spend: true },
        ignoreGuard: true,
        text: 'Power 6 and 6 per Dusk, spending all, ignores guard.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'moth_wing',
        a: { name: 'MOTH WING', text: '+3 per Dusk held.', patch: {} },
        b: {
          name: 'MOTH SWOOP',
          text: 'Power 10, spends one Dusk for +7.',
          patch: { perStack: { power: 7, spendOne: true } },
        },
      },
      {
        level: 8,
        card: 'lamp_low',
        a: { name: 'LAMP LOW', text: 'Heal 9.', patch: {} },
        b: {
          name: 'LAMP SHADE',
          text: 'Heal 5, +1 Dusk.',
          patch: { heal: 5, gainStack: 1 },
        },
      },
      {
        level: 12,
        card: 'night_falls',
        a: { name: 'NIGHT FALLS', text: '6 per Dusk at 2.', patch: {} },
        b: {
          name: 'DEEP NIGHT',
          text: '3 energy, 8 per Dusk.',
          patch: { cost: 3, perStack: { power: 8, spend: true } },
        },
      },
    ],
  },
  {
    id: 'tally',
    name: 'Tally',
    role: 'herder',
    night: 4,
    unlock: "the drover's story (the Brackens)",
    passive: P({
      id: 'countingSheep',
      name: 'Counting Sheep',
      text: 'A still turn: a sheep hops into the fold (max 3). At the start of your next turn each sheep adds a card to your hand (never energy).',
      stack: 'sheep',
      n: {},
    }),
    cards: [
      {
        id: 'fold_bell',
        name: 'FOLD BELL',
        cost: 0,
        guard: true,
        text: 'Guard.',
      },
      { id: 'shearing', name: 'SHEARING', cost: 1, power: 11, text: 'Power 11.' },
      {
        id: 'stampede',
        name: 'STAMPEDE',
        cost: 2,
        power: 7,
        perCardInHand: 3,
        text: 'Power 7, +3 per other card in your hand.',
      },
      {
        id: 'wool_blanket',
        name: 'WOOL BLANKET',
        cost: 1,
        heal: 9,
        draw: 1,
        text: 'Heal 9, draw 1.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'shearing',
        a: { name: 'SHEARING', text: 'Power 11.', patch: {} },
        b: {
          name: 'CLIPPING',
          text: '0 energy, power 6.',
          patch: { cost: 0, power: 6 },
        },
      },
      {
        level: 8,
        card: 'wool_blanket',
        a: { name: 'WOOL BLANKET', text: 'Heal 9, draw 1.', patch: {} },
        b: {
          name: 'WARM FLEECE',
          text: 'Heal 5 and guard.',
          patch: { heal: 5, guard: true, draw: 0 },
        },
      },
      {
        level: 12,
        card: 'stampede',
        a: { name: 'STAMPEDE', text: '+3 per card.', patch: {} },
        b: {
          name: 'THE WHOLE FLOCK',
          text: 'Power 12, +1 per card, ignores guard.',
          patch: { power: 12, perCardInHand: 1, ignoreGuard: true },
        },
      },
    ],
  },
  {
    id: 'tam',
    name: 'Tam',
    role: 'keeper',
    night: 5,
    unlock: "the hut warden's story (the Frostline)",
    passive: P({
      id: 'bothy',
      name: 'Bothy',
      text: 'A still turn banks Warmth (max 3). Once a fight, a blow that would knock her out finds her curled up at 1 HP, healed 3 per Warmth.',
      stack: 'Warmth',
      n: { healPerWarmth: 3 },
    }),
    cards: [
      { id: 'kettle_on', name: 'KETTLE ON', cost: 0, heal: 4, text: 'Heal 4.' },
      {
        id: 'bobble_hat',
        name: 'BOBBLE HAT',
        cost: 1,
        guard: true,
        energyNext: 1,
        text: 'Guard, +1 energy next turn.',
      },
      { id: 'ice_axe', name: 'ICE AXE', cost: 1, power: 8, text: 'Power 8.' },
      {
        id: 'avalanche',
        name: 'AVALANCHE',
        cost: 2,
        power: 11,
        perStack: { power: 1 },
        text: 'Power 11, +1 per Warmth held.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'kettle_on',
        a: { name: 'KETTLE ON', text: 'Heal 4.', patch: {} },
        b: {
          name: 'STRONG TEA',
          text: '1 energy, heal 9.',
          patch: { cost: 1, heal: 9 },
        },
      },
      {
        level: 8,
        card: 'ice_axe',
        a: { name: 'ICE AXE', text: 'Power 8.', patch: {} },
        b: {
          name: 'CRAMPON KICK',
          text: 'Power 5, +1 energy next turn.',
          patch: { power: 5, energyNext: 1 },
        },
      },
      {
        level: 12,
        card: 'avalanche',
        a: { name: 'AVALANCHE', text: '+1 per Warmth.', patch: {} },
        b: {
          name: 'WHITEOUT',
          text: 'Power 13, ignores guard.',
          patch: { power: 13, perStack: undefined, ignoreGuard: true },
        },
      },
    ],
  },
  {
    id: 'puddle',
    name: 'Puddle',
    role: 'trickster',
    night: 6,
    unlock: "the bargee's story (the Lull)",
    passive: P({
      id: 'tide',
      name: 'Tide',
      text: "His turns alternate, ebb then flow. On ebb his damaging cards soak (the foe's next card costs 1 more; if it cannot pay, it holds that card back). On flow they splash: +2 power.",
      n: { flow: 2 },
    }),
    cards: [
      { id: 'puddle_jump', name: 'PUDDLE JUMP', cost: 0, power: 5, text: 'Power 5.' },
      {
        id: 'undertow',
        name: 'UNDERTOW',
        cost: 1,
        power: 7,
        special: 'drainOnEbb',
        text: 'Power 7; on ebb also -1 energy to the foe.',
      },
      {
        id: 'turn_the_tide',
        name: 'TURN THE TIDE',
        cost: 0,
        special: 'flipTide',
        draw: 1,
        text: 'Flip the tide now, draw 1.',
      },
      {
        id: 'spring_tide',
        name: 'SPRING TIDE',
        cost: 2,
        power: 10,
        flowPower: 5,
        text: 'Power 10; on flow +5 instead of +2.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'turn_the_tide',
        a: { name: 'TURN THE TIDE', text: 'Flip, draw 1.', patch: {} },
        b: {
          name: 'SEA WALL',
          text: '1 energy: flip and guard.',
          patch: { cost: 1, draw: 0, guard: true },
        },
      },
      {
        level: 8,
        card: 'undertow',
        a: { name: 'UNDERTOW', text: 'Drain on ebb.', patch: {} },
        b: {
          name: 'RIP CURRENT',
          text: 'Power 8, draw 1.',
          patch: { special: undefined, draw: 1 },
        },
      },
      {
        level: 12,
        card: 'spring_tide',
        a: { name: 'SPRING TIDE', text: '+5 on flow.', patch: {} },
        b: {
          name: 'KING TIDE',
          text: 'Power 12, never soaks.',
          patch: { power: 12, flowPower: 2, noEbbSoak: true },
        },
      },
    ],
  },
  {
    id: 'cairn',
    name: 'Cairn',
    role: 'guardian',
    night: 7,
    unlock: "the gardener's story (the woodland circle)",
    passive: P({
      id: 'bedrock',
      name: 'Bedrock',
      text: 'His guard halves two hits, not one.',
      n: { hits: 2 },
    }),
    cards: [
      { id: 'stand_fast', name: 'STAND FAST', cost: 0, guard: true, text: 'Guard.' },
      {
        id: 'moss_over',
        name: 'MOSS OVER',
        cost: 1,
        guard: true,
        heal: 6,
        text: 'Guard, heal 6.',
      },
      {
        id: 'shoulder_charge',
        name: 'SHOULDER CHARGE',
        cost: 2,
        power: 10,
        whileGuarded: { power: 8, spendGuard: true },
        text: 'Power 10; while guarded +8 and the guard is spent.',
      },
      {
        id: 'standing_stone',
        name: 'STANDING STONE',
        cost: 1,
        power: 8,
        whileGuarded: { energyNext: 1 },
        text: 'Power 8; while guarded +1 energy next turn.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'stand_fast',
        a: { name: 'STAND FAST', text: 'Guard.', patch: {} },
        b: {
          name: 'DIG IN',
          text: '1 energy: guard, +1 energy next turn.',
          patch: { cost: 1, energyNext: 1 },
        },
      },
      {
        level: 8,
        card: 'moss_over',
        a: { name: 'MOSS OVER', text: 'Guard, heal 6.', patch: {} },
        b: {
          name: 'DEEP MOSS',
          text: '2 energy: guard, heal 11.',
          patch: { cost: 2, heal: 11 },
        },
      },
      {
        level: 12,
        card: 'shoulder_charge',
        a: { name: 'SHOULDER CHARGE', text: '+8, spends the guard.', patch: {} },
        b: {
          name: 'BULWARK CHARGE',
          text: '+5, keeps the guard.',
          patch: { whileGuarded: { power: 5 } },
        },
      },
    ],
  },
  {
    id: 'pendle',
    name: 'Pendle',
    role: 'caster',
    night: 8,
    unlock: "the tinkerer's story (Cogsworth)",
    passive: P({
      id: 'minuteSlow',
      name: 'A Minute Slow',
      text: 'Instead of playing a card, set it on the clock: pay its cost now; it lands at the start of your next turn with +3 (power or heal). One card on the clock.',
      n: { bonus: 3 },
    }),
    cards: [
      {
        id: 'wind_the_spring',
        name: 'WIND THE SPRING',
        cost: 0,
        energyNext: 1,
        text: '+1 energy next turn.',
      },
      { id: 'signal_lamp', name: 'SIGNAL LAMP', cost: 1, power: 8, text: 'Power 8.' },
      {
        id: 'station_bell',
        name: 'STATION BELL',
        cost: 2,
        power: 10,
        ignoreGuard: true,
        text: 'Power 10, ignores guard (+3 from the clock).',
      },
      {
        id: 'platform_tea',
        name: 'PLATFORM TEA',
        cost: 1,
        heal: 7,
        draw: 1,
        text: 'Heal 7, draw 1.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'signal_lamp',
        a: { name: 'SIGNAL LAMP', text: 'Power 8.', patch: {} },
        b: {
          name: 'SIGNAL FLARE',
          text: 'Power 6, draw 1.',
          patch: { power: 6, draw: 1 },
        },
      },
      {
        level: 8,
        card: 'platform_tea',
        a: { name: 'PLATFORM TEA', text: 'Heal 7, draw 1.', patch: {} },
        b: {
          name: 'DINING CAR',
          text: '2 energy: heal 14.',
          patch: { cost: 2, heal: 14, draw: 0 },
        },
      },
      {
        level: 12,
        card: 'station_bell',
        a: { name: 'STATION BELL', text: 'Ignores guard.', patch: {} },
        b: {
          name: 'LAST CALL',
          text: '1 energy, power 10, keeps guard.',
          patch: { cost: 1, power: 10, ignoreGuard: false },
        },
      },
    ],
  },
  {
    id: 'mirra',
    name: 'Mirra',
    role: 'support',
    night: 9,
    unlock: "the oasis trader's story (Sunstone)",
    passive: P({
      id: 'seep',
      name: 'Seep',
      text: 'A still turn adds a drop to her flask (max 3). Pouring is not a still turn. She never guards.',
      stack: 'drops',
      n: {},
    }),
    cards: [
      {
        id: 'pour',
        name: 'POUR',
        cost: 0,
        special: 'pour',
        perStack: { heal: 8, spend: true },
        text: 'Heal 8 per drop, emptying the flask.',
      },
      {
        id: 'clear_water',
        name: 'CLEAR WATER',
        cost: 1,
        special: 'cleanse',
        heal: 8,
        text: 'Cleanse (softening, soak, spores) and heal 8.',
      },
      {
        id: 'divining_rod',
        name: 'DIVINING ROD',
        cost: 0,
        power: 8,
        draw: 1,
        text: 'Power 8, draw 1.',
      },
      { id: 'water_hammer', name: 'WATER HAMMER', cost: 2, power: 15, text: 'Power 15.' },
    ],
    variants: [
      {
        level: 4,
        card: 'pour',
        a: { name: 'POUR', text: '8 per drop, all.', patch: {} },
        b: {
          name: 'SIP',
          text: 'One drop for 10.',
          patch: { perStack: { heal: 10, spendOne: true } },
        },
      },
      {
        level: 8,
        card: 'clear_water',
        a: { name: 'CLEAR WATER', text: 'Cleanse, heal 8.', patch: {} },
        b: {
          name: 'SPRING WATER',
          text: '2 energy: cleanse, heal 13.',
          patch: { cost: 2, heal: 13 },
        },
      },
      {
        level: 12,
        card: 'divining_rod',
        a: { name: 'DIVINING ROD', text: 'Power 8, draw 1.', patch: {} },
        b: {
          name: 'DOWSING STRIKE',
          text: 'Power 11, no draw.',
          patch: { power: 11, draw: 0 },
        },
      },
    ],
  },
  {
    id: 'ashe',
    name: 'Ashe',
    role: 'bruiser',
    night: 10,
    unlock: "the smith's story (the fire country)",
    passive: P({
      id: 'bankedFire',
      name: 'Banked fire',
      text: 'Heat +1 at the start of each of her turns (max 3); damaging cards +2 power per heat. When heat would pass 3 the bell tolls: she rests that turn, heals 12 and heat falls to 0.',
      stack: 'heat',
      n: { perHeat: 2, bellHeal: 12 },
    }),
    cards: [
      {
        id: 'bank_the_fire',
        name: 'BANK THE FIRE',
        cost: 0,
        loseStack: 1,
        guard: true,
        text: 'Heat -1 and guard.',
      },
      { id: 'ember_swing', name: 'EMBER SWING', cost: 1, power: 8, text: 'Power 8 (+2 per heat).' },
      {
        id: 'bell_toll',
        name: 'BELL TOLL',
        cost: 2,
        power: 11,
        special: 'removeFoeGuard',
        gainStack: 1,
        text: "Power 11 (+2 per heat), removes the foe's guard, +1 heat.",
      },
      {
        id: 'forge_rest',
        name: 'FORGE REST',
        cost: 1,
        special: 'forgeRest',
        perStack: { heal: 5, spend: true },
        text: 'Heat to 0, heal 5 per heat let go.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'bank_the_fire',
        a: { name: 'BANK THE FIRE', text: '-1 heat, guard.', patch: {} },
        b: {
          name: 'DAMP THE COALS',
          text: '-2 heat, no guard, heal 4.',
          patch: { loseStack: 2, guard: false, heal: 4 },
        },
      },
      {
        level: 8,
        card: 'ember_swing',
        a: { name: 'EMBER SWING', text: 'Power 8.', patch: {} },
        b: {
          name: 'STOKE',
          text: 'Power 6, +1 heat.',
          patch: { power: 6, gainStack: 1 },
        },
      },
      {
        level: 12,
        card: 'forge_rest',
        a: { name: 'FORGE REST', text: '5 per heat.', patch: {} },
        b: {
          name: 'QUENCH',
          text: '0 energy, 4 per heat.',
          patch: { cost: 0, perStack: { heal: 4, spend: true } },
        },
      },
    ],
  },
  {
    id: 'tuff',
    name: 'Tuff',
    role: 'grower',
    night: 11,
    unlock: "the naturalist's story (the Tidebloom Isles)",
    passive: P({
      id: 'overgrow',
      name: 'Overgrow',
      text: 'A still turn grows a layer (max 3): each adds +3 power to his damaging cards. A hit of 15 or more knocks the top layer off.',
      stack: 'layers',
      n: { perLayer: 3, heavy: 15 },
    }),
    cards: [
      { id: 'take_root', name: 'TAKE ROOT', cost: 0, guard: true, text: 'Guard.' },
      { id: 'sea_thrift', name: 'SEA THRIFT', cost: 1, heal: 8, text: 'Heal 8.' },
      { id: 'rock_slide', name: 'ROCK SLIDE', cost: 1, power: 9, text: 'Power 9.' },
      {
        id: 'column_fall',
        name: 'COLUMN FALL',
        cost: 2,
        power: 12,
        ignoreGuard: true,
        text: 'Power 12, ignores guard.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'take_root',
        a: { name: 'TAKE ROOT', text: 'Guard.', patch: {} },
        b: {
          name: 'DEEP ROOTS',
          text: '1 energy: guard, heal 4.',
          patch: { cost: 1, heal: 4 },
        },
      },
      {
        level: 8,
        card: 'rock_slide',
        a: { name: 'ROCK SLIDE', text: 'Power 9.', patch: {} },
        b: {
          name: 'PEBBLE SHOWER',
          text: '0 energy, power 5.',
          patch: { cost: 0, power: 5 },
        },
      },
      {
        level: 12,
        card: 'column_fall',
        a: { name: 'COLUMN FALL', text: 'Ignores guard.', patch: {} },
        b: {
          name: 'BASALT FIST',
          text: 'Power 15, keeps guard.',
          patch: { power: 15, ignoreGuard: false },
        },
      },
    ],
  },
  {
    id: 'nix',
    name: 'Nix',
    role: 'ward',
    night: 12,
    unlock: "Dave's story (Neon Harbour)",
    passive: P({
      id: 'doNotDisturb',
      name: 'Do Not Disturb',
      text: "After a still turn the foe's next trick (a card's extra effect: a skip, a soak, energy, ignoring guard, spores) is muted; after two still turns in a row it is reflected onto the foe instead, once a fight.",
      n: {},
    }),
    cards: [
      {
        id: 'silent_mode',
        name: 'SILENT MODE',
        cost: 0,
        energyNext: 1,
        draw: 1,
        text: '+1 energy next turn, draw 1.',
      },
      { id: 'out_of_office', name: 'OUT OF OFFICE', cost: 1, heal: 8, text: 'Heal 8.' },
      { id: 'courier_dash', name: 'COURIER DASH', cost: 1, power: 12, text: 'Power 12.' },
      {
        id: 'return_to_sender',
        name: 'RETURN TO SENDER',
        cost: 2,
        power: 13,
        afterTrick: 6,
        text: 'Power 13, +6 if she muted or reflected a trick this fight.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'silent_mode',
        a: { name: 'SILENT MODE', text: '+1 energy next turn, draw 1.', patch: {} },
        b: {
          name: 'FOCUS MODE',
          text: 'Draw 2.',
          patch: { energyNext: 0, draw: 2 },
        },
      },
      {
        level: 8,
        card: 'out_of_office',
        a: { name: 'OUT OF OFFICE', text: 'Heal 8.', patch: {} },
        b: {
          name: 'AUTO REPLY',
          text: 'Heal 4 and guard.',
          patch: { heal: 4, guard: true },
        },
      },
      {
        level: 12,
        card: 'return_to_sender',
        a: { name: 'RETURN TO SENDER', text: '+6 after a trick.', patch: {} },
        b: {
          name: 'SIGNED FOR',
          text: 'Power 16 always.',
          patch: { power: 16, afterTrick: 0 },
        },
      },
    ],
  },
  {
    id: 'bunk',
    name: 'Bunk',
    role: 'cycler',
    night: 13,
    unlock: "the sleep-bay keeper's story (Halcyon Station)",
    passive: P({
      id: 'sleepCycle',
      name: 'Sleep Cycle',
      text: 'A two-stage dial turns each turn: deep heals 2 at the start of the turn; dream gives your next damaging card +2 power. A still turn holds the stage.',
      n: { deepHeal: 2, echo: 2 },
    }),
    cards: [
      {
        id: 'dim_visor',
        name: 'DIM VISOR',
        cost: 0,
        energyNext: 1,
        text: '+1 energy next turn.',
      },
      {
        id: 'mag_boots',
        name: 'MAG BOOTS',
        cost: 1,
        guard: true,
        heal: 4,
        text: 'Guard, heal 4.',
      },
      { id: 'airlock', name: 'AIRLOCK', cost: 1, power: 8, text: 'Power 8.' },
      {
        id: 'sleep_bay',
        name: 'SLEEP BAY',
        cost: 2,
        power: 8,
        heal: 6,
        text: 'Power 8, heal 6.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'dim_visor',
        a: { name: 'DIM VISOR', text: '+1 energy next turn.', patch: {} },
        b: {
          name: 'SNOOZE',
          text: 'Heal 5.',
          patch: { energyNext: 0, heal: 5 },
        },
      },
      {
        level: 8,
        card: 'airlock',
        a: { name: 'AIRLOCK', text: 'Power 8.', patch: {} },
        b: {
          name: 'DECOMPRESS',
          text: '2 energy, power 14.',
          patch: { cost: 2, power: 14 },
        },
      },
      {
        level: 12,
        card: 'sleep_bay',
        a: { name: 'SLEEP BAY', text: 'Power 8, heal 6.', patch: {} },
        b: {
          name: 'HYPERSLEEP',
          text: 'Power 11, heal 3.',
          patch: { power: 11, heal: 3 },
        },
      },
    ],
  },
  {
    id: 'mote',
    name: 'Mote',
    role: 'wildcard',
    night: 14,
    unlock: 'the end of the journey (Lumen)',
    passive: P({
      id: 'dream',
      name: 'Dream',
      text: "Once a fight, use your familiar's rested special before it is charged, at half its full strength, without spending the real pips. Never the strongest.",
      n: { strength: 0.5 },
    }),
    cards: [
      { id: 'twinkle', name: 'TWINKLE', cost: 0, power: 6, text: 'Power 6.' },
      {
        id: 'stardust',
        name: 'STARDUST',
        cost: 1,
        special: 'stardust',
        text: 'Play the last card you played again at half strength.',
      },
      { id: 'wish', name: 'WISH', cost: 1, draw: 2, text: 'Draw 2.' },
      {
        id: 'shooting_star',
        name: 'SHOOTING STAR',
        cost: 3,
        power: 18,
        ignoreGuard: true,
        text: 'Power 18, ignores guard.',
      },
    ],
    variants: [
      {
        level: 4,
        card: 'twinkle',
        a: { name: 'TWINKLE', text: 'Power 6.', patch: {} },
        b: {
          name: 'GLIMMER',
          text: 'Power 3, draw 1.',
          patch: { power: 3, draw: 1 },
        },
      },
      {
        level: 8,
        card: 'wish',
        a: { name: 'WISH', text: 'Draw 2.', patch: {} },
        b: {
          name: 'SMALL WISH',
          text: '0 energy, draw 1.',
          patch: { cost: 0, draw: 1 },
        },
      },
      {
        level: 12,
        card: 'shooting_star',
        a: { name: 'SHOOTING STAR', text: '18 at 3.', patch: {} },
        b: {
          name: 'FALLING STAR',
          text: '2 energy, power 13.',
          patch: { cost: 2, power: 13 },
        },
      },
    ],
  },
];

/** The familiar's rested special: one per family, charged by real time away. */
export type RestedSpecial = {
  family: Family;
  id: string;
  name: string;
  text: string;
  perPip: { heal?: number; guard?: boolean; refillEnergy?: boolean; draw?: number; power?: number };
};
export const restedCharge = {
  /** One pip for each 20 minutes of rest since your last spar. */
  minutesPerPip: 20,
  maxPips: 3,
  /** Reads the rest counter zen reads (`offline_seconds`); fighting, walking or an open app add nothing. */
  source: 'rest since the last spar',
  /** Used alongside your card for the turn, not instead of it; once a fight; spends all pips. */
  freeAction: true,
} as const;
export const restedSpecials: RestedSpecial[] = [
  {
    family: 'REST',
    id: 'sleep_it_off',
    name: 'SLEEP IT OFF',
    text: 'Heal 3 per pip; with three pips, guard too.',
    perPip: { heal: 3, guard: true },
  },
  {
    family: 'ROAM',
    id: 'second_wind',
    name: 'SECOND WIND',
    text: '+1 energy per pip (energy still caps at 3); with three pips, draw 1.',
    perPip: { refillEnergy: true, draw: 1 },
  },
  {
    family: 'FOCUS',
    id: 'in_the_zone',
    name: 'IN THE ZONE',
    text: 'Your next damaging card this turn: +1 power per pip, ignores guard.',
    perPip: { power: 1 },
  },
];

export function pipsFor(restMinutesSinceLastSpar: number) {
  return Math.max(
    0,
    Math.min(
      restedCharge.maxPips,
      Math.floor(restMinutesSinceLastSpar / restedCharge.minutesPerPip),
    ),
  );
}

/** A ring rival: a resident with a fixed family, a deck of habit cards in their region's
 *  style and at most one passive from the folk list (cast.md: a quarter of a folk's cost).
 *  Rings and rivals follow Claude K's progression spine (art/story/progression.json, #197). */
export type Rival = {
  id: string;
  region: string;
  ring: string;
  who: string;
  family: Family | 'mirror';
  /** The shared level the ring is balanced for (a proposal for Claude K's unlock table). */
  level: number;
  /** A rival's own zen (F4), never a copy of yours. */
  zen: number;
  deck: string[];
  passive?: PassiveId;
  /** Built today (`lib/world-places.ts` rings) or planned by the atlas. */
  status: 'today' | 'planned';
};

/** A rival's deck: the same middling habit deck a player has at that level (so a ring
 *  measures the folk, not the cards), with the region's flavour swapped in. */
export function rivalDeck(level: number, swaps: [out: string, inn: string][] = []) {
  const deck = habitDeckAt(level);
  for (const [out, inn] of swaps) {
    const at = deck.indexOf(out);
    if (at >= 0) deck[at] = inn;
  }
  return deck;
}

export const rivals: Rival[] = [
  {
    id: 'dave',
    region: 'the home valley',
    ring: 'the green in Crossroads',
    who: 'Doomscroll Dave, as the tutor',
    family: 'mirror',
    level: 1,
    zen: 0,
    deck: [
      'stretch',
      'stretch',
      'stretch',
      'stretch',
      'stretch',
      'stretch',
      'short_walk',
      'short_walk',
      'glass_of_water',
      'glass_of_water',
    ],
    status: 'today',
  },
  {
    id: 'hut_warden',
    region: 'the Frostline',
    ring: 'a snowy clearing by the bothy',
    who: 'the hut warden',
    family: 'REST',
    level: 3,
    zen: 0,
    deck: rivalDeck(3, [['stretch', 'deep_breath']]),
    passive: 'bedrock',
    status: 'planned',
  },
  {
    id: 'tinkerer',
    region: 'Cogsworth',
    ring: 'the plaza',
    who: 'the tinkerer',
    family: 'FOCUS',
    level: 4,
    zen: 0,
    deck: rivalDeck(4, [['short_walk', 'read_a_chapter']]),
    passive: 'minuteSlow',
    status: 'today',
  },
  {
    id: 'cowhand',
    region: 'Sunstone Reach',
    ring: 'the dusty corral in Dust Gulch',
    who: 'the cowhand',
    family: 'ROAM',
    level: 5,
    zen: 0,
    deck: rivalDeck(5, [
      ['stretch', 'short_walk'],
      ['glass_of_water', 'deep_breath'],
    ]),
    passive: 'countingSheep',
    status: 'planned',
  },
  {
    id: 'smith',
    region: 'the fire country',
    ring: 'the basalt ring by the lava',
    who: 'the smith',
    family: 'FOCUS',
    level: 7,
    zen: 0,
    deck: rivalDeck(7, [['glass_of_water', 'stretch']]),
    passive: 'bankedFire',
    status: 'today',
  },
  {
    id: 'neon_dave',
    region: 'Neon Harbour',
    ring: 'the Neon court',
    who: "Doomscroll Dave, at home (his own deck, stronger than the tutor's)",
    family: 'mirror',
    level: 8,
    zen: 0,
    deck: rivalDeck(8, [
      ['deep_breath', 'morning_walk'],
      ['glass_of_water', 'short_walk'],
    ]),
    passive: 'doNotDisturb',
    status: 'today',
  },
  {
    id: 'botanist',
    region: 'Halcyon Station',
    ring: 'the padded ring',
    who: 'the station botanist',
    family: 'REST',
    level: 10,
    zen: 0,
    deck: rivalDeck(10, [['stretch', 'early_night']]),
    passive: 'overgrow',
    status: 'planned',
  },
  {
    id: 'stargazer',
    region: 'Lumen',
    ring: 'the sparring crater',
    who: 'the stargazer',
    family: 'FOCUS',
    level: 12,
    zen: 0,
    deck: rivalDeck(12, [['short_walk', 'read_a_chapter']]),
    passive: 'tide',
    status: 'today',
  },
];

/** Regions with no ring, by design (cast.md, world-atlas.md). */
export const noRing = [
  { region: 'the Brackens', why: "the drover's story is a story, not a ring" },
  {
    region: 'Hearthold',
    why: "the fire country's ring is the smith's, by the lava (Claude K's spine)",
  },
  { region: 'the Lull', why: 'the bargee teaches rest; Puddle is his apprentice' },
  { region: 'the Tidebloom Isles', why: 'the quiet place with no ring' },
];

/**
 * The player's habit deck at a shared level, for the simulation. Rest builds the deck
 * (one common per 15 minutes, a rare or epic per outing, up to 20, `lib/cards.ts`); this is
 * a fixed, middling deck for a player who rests about an hour a day, so every folk is
 * measured against the same cards. Level 3 adds DIGITAL SUNSET, as `levelUp` does today.
 */
export function habitDeckAt(level: number): string[] {
  const deck = [
    'stretch',
    'stretch',
    'stretch',
    'deep_breath',
    'deep_breath',
    'glass_of_water',
    'short_walk',
  ];
  const commons = ['stretch', 'short_walk', 'glass_of_water', 'deep_breath'];
  const rares = ['morning_walk', 'read_a_chapter', 'early_night'];
  const epics = ['call_a_friend'];
  for (let i = 0; i < Math.min(10, 2 * (level - 1)); i++) deck.push(commons[i % commons.length]);
  for (let i = 0; i < Math.floor(level / 3); i++) deck.push(rares[i % rares.length]);
  if (level >= 3) deck.push('digital_sunset');
  for (let i = 0; i < Math.floor(level / 8); i++) deck.push(epics[i % epics.length]);
  return deck.slice(0, 20);
}

/**
 * What fights need from characters and animation (for Claude J), as data. Frame counts
 * follow fights.md section 6; east-facing is the player's side, west-facing is drawn (not
 * mirrored, light comes from the upper left) for rivals and raids. Each beat is a moment the
 * engine reaches and the battle screen will key on.
 */
export type FightBeat =
  | 'ready'
  | 'windup'
  | 'strike'
  | 'impact'
  | 'cast'
  | 'guard'
  | 'hit'
  | 'heal'
  | 'stack'
  | 'special'
  | 'doze'
  | 'bell'
  | 'sitDown'
  | 'cheer'
  | 'bow';

export const fightAnimation = {
  folkPoses: {
    perFacing: [
      { pose: 'ready', frames: 2, beat: 'ready', note: 'breathing loop while you choose' },
      {
        pose: 'wind-up',
        frames: 1,
        beat: 'windup',
        note: 'anticipation, 100 ms (the impact frame shows within the 200 ms step of the battle screen; art/characters/animation-spec.json fightBeats)',
      },
      {
        pose: 'strike',
        frames: 2,
        beat: 'strike',
        note: 'the second frame is the impact the NICE press keys on',
      },
      { pose: 'guard', frames: 1, beat: 'guard', note: 'held while guarded (Cairn: two hits)' },
      { pose: 'hit', frames: 1, beat: 'hit', note: 'recoil, then settle back to ready' },
      {
        pose: 'cast',
        frames: 2,
        beat: 'cast',
        note: 'heals, stacks, the clock, spores: every non-strike signature card',
      },
      {
        pose: 'sits down',
        frames: 1,
        beat: 'sitDown',
        note: 'the loser takes a breather; never a faint',
      },
      {
        pose: 'cheer',
        frames: 2,
        beat: 'cheer',
        note: 'the winner; both then bow (shared bow beat)',
      },
    ],
    facings: ['east', 'west'],
    leanSet: ['ready x 2', 'wind-up', 'strike', 'guard', 'hit', 'sits down', 'cheer'],
  },
  /** One effect per signature card, 3 to 4 frames, by folk. */
  cardEffects: Object.fromEntries(
    folk.map((f) => [
      f.id,
      f.cards.map((c) => {
        const beat: FightBeat = c.power ? 'impact' : 'cast';
        return { card: c.id, frames: 3, beat };
      }),
    ]),
  ),
  /** The passive's pip or status icon on the plate, and its cue when it changes. */
  passiveCues: Object.fromEntries(
    folk.map((f) => [f.id, { icon: f.passive.stack ?? f.passive.name, beat: 'stack' }]),
  ),
  familiar: {
    perFamilyAndFacing: [
      { pose: 'idle on the shoulder', frames: 2 },
      { pose: 'cling (the folk is hit)', frames: 1 },
      { pose: 'cheer', frames: 1 },
      { pose: 'cast the rested special', frames: 2 },
    ],
    specials: restedSpecials.map((s) => ({
      id: s.id,
      family: s.family,
      frames: 6,
      beat: 'special',
    })),
    /** The shoulder anchor is data per folk frame, not art. */
    anchor: 'per folk frame: (x, y) of the shoulder in art px',
  },
  rival: { facing: 'west', poses: 'the folk set (12) or the lean set (8)', effects: 2 },
  shared: [
    { effect: 'hit spark', frames: 4 },
    { effect: 'NICE ring closing on the target', frames: 3 },
    { effect: 'ground puff tinted by the ring', frames: 4 },
    { effect: 'doze glyph over the foe (Puffcap)', frames: 2 },
    { effect: 'bell toll ring (Ashe)', frames: 3 },
    { effect: 'intent icons: hit, heal, guard, trick', frames: 1 },
    {
      effect: 'pip icons: rested pip, Aim, Dusk, spore, drop, heat, sheep, Warmth, layer',
      frames: 1,
    },
  ],
  reducedMotion: 'held stills of 300 ms for wind-up and recoil; no flash, no shake; effects finite',
} as const;
