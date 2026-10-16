import type { BreakIntention, CompanionMemory } from '@/lib/companion-memories';
import { companionProfile, type CompanionHabit } from '@/lib/companion-profiles';
import type { Player } from '@/lib/game';
import type { VisitorId } from '@/lib/visitors';

export type GardenInteraction = 'read' | 'water' | 'pond' | 'pat' | 'lantern';
export type GardenKeepsakes = Partial<Record<BreakIntention, CompanionMemory>>;
export type MemoryPlace = {
  action: GardenInteraction;
  label: string;
  description: string;
};
export type GardenSignature = {
  family: CompanionHabit;
  pose: 'nestle' | 'sniff' | 'ponder';
  motif: 'glow' | 'leaf' | 'scribble';
  animated: boolean;
};

const places: Record<BreakIntention, MemoryPlace> = {
  rest: {
    action: 'lantern',
    label: 'Leaf lantern',
    description: 'Your rest keepsake sits beside the leaf lantern.',
  },
  read: {
    action: 'read',
    label: 'Reading nook',
    description: 'A reading keepsake marks a quiet page in the nook.',
  },
  move: {
    action: 'water',
    label: 'Flower beds',
    description: 'Your movement memory becomes a pressed leaf by the flowers.',
  },
  create: {
    action: 'pond',
    label: 'Pondside sketchboard',
    description: 'Your creative memory sits on a little board beside the pond.',
  },
};

export function memoryPlace(intention: BreakIntention): Readonly<MemoryPlace> {
  return places[intention];
}

// The game store already validates these records. This view selects keepsakes;
// it does not create memories, verify activities, or settle any game progress.
export function gardenKeepsakes(memories: readonly CompanionMemory[] = []): GardenKeepsakes {
  const keepsakes: GardenKeepsakes = {};
  for (const memory of memories) {
    const current = keepsakes[memory.intention];
    if (
      !current ||
      memory.completedAt > current.completedAt ||
      (memory.completedAt === current.completedAt && memory.recordedAt > current.recordedAt) ||
      (memory.completedAt === current.completedAt &&
        memory.recordedAt === current.recordedAt &&
        memory.id < current.id)
    )
      keepsakes[memory.intention] = memory;
  }
  return keepsakes;
}

const actionIntentions: Record<GardenInteraction, BreakIntention | null> = {
  read: 'read',
  water: 'move',
  pond: 'create',
  lantern: 'rest',
  pat: null,
};

export function gardenMemoryForAction(
  action: GardenInteraction,
  memories: readonly CompanionMemory[] = [],
): CompanionMemory | null {
  const intention = actionIntentions[action];
  return intention ? (gardenKeepsakes(memories)[intention] ?? null) : null;
}

const familyBehaviour = {
  REST: {
    read: ['settles into the softest corner of the reading nook.', 'lets the page turn slowly.'],
    water: ['rests beside the newly watered flowers.', 'waits for the last droplet to fall.'],
    pond: ['finds a quiet spot beside the water.', 'watches the ripples soften.'],
    pat: ['nestles a little closer.', 'settles into a contented little heap.'],
    lantern: ['curls up beside the gentle glow.', 'makes a cosy corner of the lamplight.'],
  },
  ROAM: {
    read: ['searches the pages for a new place to explore.', 'checks the edge of the bookmark.'],
    water: ['sniffs a freshly watered leaf.', 'investigates the path between the flowers.'],
    pond: ['peers over the bank with curious eyes.', 'follows a ripple along the shore.'],
    pat: ['leans in, then perks up for another adventure.', 'answers with an eager little wiggle.'],
    lantern: [
      'checks the leaves just beyond the light.',
      'sniffs the evening air beside the lantern.',
    ],
  },
  FOCUS: {
    read: ['studies the page with a thoughtful little pause.', 'holds a place for the next idea.'],
    water: ['studies the pattern of the water drops.', 'arranges a fallen petal beside the can.'],
    pond: ['traces a ripple-shaped idea on the sketchboard.', 'ponders the circles on the water.'],
    pat: ['pauses its thinking for a tiny hello.', 'sets an idea aside for a moment with you.'],
    lantern: ['finds a bright spot for a quiet idea.', 'studies the shapes inside the glow.'],
  },
} as const satisfies Record<CompanionHabit, Record<GardenInteraction, readonly [string, string]>>;

// These small behaviours extend the existing profiles. They do not add pet
// powers or alter the family effects described by companionProfile.
const visitorBehaviour = {
  dozebud: {
    read: 'nods off between two pages.',
    water: 'leans against the can for a tiny rest.',
    pond: 'finds the sleepiest patch of shade by the pond.',
    pat: 'nuzzles into your hand.',
    lantern: 'settles beside the warm glow.',
  },
  mosspuff: {
    read: 'spots a pressed leaf between the pages.',
    water: 'checks the smallest new leaf.',
    pond: 'notices a frog-shaped ripple.',
    pat: 'leans closer, quietly.',
    lantern: 'watches the shadows soften.',
  },
  lullapine: {
    read: 'keeps your page while the breeze passes.',
    water: 'waits for the last droplet to settle.',
    pond: 'watches a cloud drift through the water.',
    pat: 'rests beneath your hand.',
    lantern: 'stands a peaceful little watch.',
  },
  trailhop: {
    read: 'checks whether the next page has a map.',
    water: 'takes the long way round the flower bed.',
    pond: 'hops after a frog, then stops at the bank.',
    pat: 'bounces back for another hello.',
    lantern: 'checks the path just beyond the glow.',
  },
  burrbound: {
    read: 'inspects a crumb caught in the spine.',
    water: 'sniffs each flower in turn.',
    pond: 'follows one ripple all the way to the bank.',
    pat: 'returns with a leaf stuck to its fur.',
    lantern: 'examines the little latch.',
  },
  skyfern: {
    read: 'pauses to watch a cloud above the page.',
    water: 'watches a droplet catch the sky.',
    pond: 'studies the clouds reflected in the pond.',
    pat: 'lands lightly beside you.',
    lantern: 'looks from the glow to the open sky.',
  },
  inkling: {
    read: 'imagines a different ending.',
    water: 'sketches a flower in the damp soil.',
    pond: 'traces a ripple-shaped idea.',
    pat: 'offers a tiny flourish.',
    lantern: 'finds a quiet spot for a new idea.',
  },
  pagemoth: {
    read: 'tries to turn two pages at once.',
    water: 'wonders which flower the bees will choose.',
    pond: 'studies the ripples like a mystery.',
    pat: 'keeps one eye on the next chapter.',
    lantern: 'curls up where the page catches the light.',
  },
  lanternroot: {
    read: 'lines up the bookmark before reading.',
    water: 'gives each stem a careful little sip.',
    pond: 'counts the rings until the water is still.',
    pat: 'sets its little tools aside.',
    lantern: 'checks the latch, then admires the glow.',
  },
} as const satisfies Record<VisitorId, Record<GardenInteraction, string>>;

const memoryPrefixes: Record<BreakIntention, string> = {
  rest: 'Rest memory:',
  read: 'Reading memory:',
  move: 'Movement memory:',
  create: 'Creative memory:',
};
function memoryLine(memory: CompanionMemory): string {
  return `${memoryPrefixes[memory.intention]} ${memory.companion.name}.`;
}

export function gardenResponse(
  player: Player,
  action: GardenInteraction,
  count = 0,
  memories: readonly CompanionMemory[] = [],
): string {
  const profile = companionProfile(player);
  const turn = Number.isFinite(count) ? Math.max(0, Math.floor(count)) : 0;
  const memory = gardenMemoryForAction(action, memories);
  if (memory && turn % 2 === 0) return memoryLine(memory);
  const behaviourTurn = memory ? Math.floor(turn / 2) : turn;
  const behaviour =
    profile.id && behaviourTurn % 2 === 0
      ? visitorBehaviour[profile.id][action]
      : familyBehaviour[profile.habit][action][behaviourTurn % 2];
  return `${profile.name} ${behaviour}`;
}

const signatures = {
  REST: { pose: 'nestle', motif: 'glow' },
  ROAM: { pose: 'sniff', motif: 'leaf' },
  FOCUS: { pose: 'ponder', motif: 'scribble' },
} as const satisfies Record<CompanionHabit, Pick<GardenSignature, 'pose' | 'motif'>>;

// A rendering hint only: the view reuses its existing finite reaction clock.
// Reduced motion keeps the same signature as a static pose or motif.
export function gardenSignature(player: Player, reducedMotion = false): GardenSignature {
  const family = companionProfile(player).habit;
  return { family, ...signatures[family], animated: !reducedMotion };
}
