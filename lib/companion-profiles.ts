import type { Player } from '@/lib/game';
import { grasslings } from '@/lib/grasslings';
import {
  befriendedVisitorIds,
  effectiveGuardianId,
  visitorInfo,
  type VisitorId,
} from '@/lib/visitors';

export type CompanionHabit = 'REST' | 'ROAM' | 'FOCUS';
type Personality = {
  traits: readonly [string, string];
  description: string;
  invitation: { title: string; body: string };
};
export type CompanionProfile = Personality & {
  id: VisitorId | null;
  name: string;
  species: Player['species'];
  habit: CompanionHabit;
  battleNote: string;
};

const starterPersonalities = {
  BLOB: {
    traits: ['Patient', 'Comforting'],
    description:
      'A steady little moss companion who likes an unhurried day and a soft place to land.',
    invitation: {
      title: 'Make room for rest',
      body: 'If you feel like it, put your phone aside and get comfortable for a quiet pause.',
    },
  },
  RAT: {
    traits: ['Adventurous', 'Sociable'],
    description:
      'An eager explorer who finds something interesting on even the most familiar route.',
    invitation: {
      title: 'A change of scene',
      body: 'Try a short stroll, roll or a little movement that suits you. Watching the world from a window works too.',
    },
  },
  CUBE: {
    traits: ['Thoughtful', 'Inventive'],
    description:
      'A small, solid thinker who enjoys a good question and making things one piece at a time.',
    invitation: {
      title: 'One small thing',
      body: 'You could leave your phone aside while you read, sketch or spend a little time on something you care about.',
    },
  },
} as const satisfies Record<Player['species'], Personality>;

const visitorPersonalities = {
  dozebud: {
    traits: ['Drowsy', 'Affectionate'],
    description: 'The first to find a cosy corner and the last to let a friend rest alone.',
    invitation: {
      title: 'Find your cosy corner',
      body: 'If a pause sounds good, settle somewhere comfortable and let your shoulders relax for a moment.',
    },
  },
  mosspuff: {
    traits: ['Gentle', 'Observant'],
    description:
      'Notices the tiny things: a new leaf, a patch of sunlight, a friend who needs some quiet.',
    invitation: {
      title: 'Notice something small',
      body: 'You could set your phone aside and notice a plant, a texture or the light around you. Indoors is fine.',
    },
  },
  lullapine: {
    traits: ['Dreamy', 'Reassuring'],
    description: 'Keeps a peaceful watch over the garden as the bustle of the day fades.',
    invitation: {
      title: 'A softer end to the day',
      body: 'When winding down suits you, try leaving your phone aside while you do something quiet and familiar.',
    },
  },
  trailhop: {
    traits: ['Playful', 'Energetic'],
    description:
      'Turns every little outing into an expedition, even when the destination is just the next tree.',
    invitation: {
      title: 'A little outing',
      body: 'If you fancy a change, take a short stroll, roll or seated movement break at your own pace.',
    },
  },
  burrbound: {
    traits: ['Curious', 'Persistent'],
    description:
      'Always investigating the path less travelled, usually with a few leaves caught in its fur.',
    invitation: {
      title: 'Something new on a familiar route',
      body: 'On your next outing, you could notice one detail you usually pass by. A view from a window can hold surprises too.',
    },
  },
  skyfern: {
    traits: ['Free-spirited', 'Attentive'],
    description: 'Loves an open sky and pauses mid-adventure to watch the clouds drift.',
    invitation: {
      title: 'Look a little further',
      body: 'If you have a safe, comfortable spot, leave your phone aside and spend a moment looking at the sky or a distant view.',
    },
  },
  inkling: {
    traits: ['Imaginative', 'Expressive'],
    description:
      'Collects half-formed ideas and is happiest turning one into a scribble, a story or a plan.',
    invitation: {
      title: 'Give an idea a place to land',
      body: 'You could put your phone aside and doodle, jot down an idea or make something small with whatever is nearby.',
    },
  },
  pagemoth: {
    traits: ['Bookish', 'Inquisitive'],
    description: 'Gets lost in a good story and returns with more questions than it started with.',
    invitation: {
      title: 'Stay with a story',
      body: 'If you feel like reading, try a page or a chapter with your phone out of reach. An audiobook is welcome too.',
    },
  },
  lanternroot: {
    traits: ['Methodical', 'Resourceful'],
    description: 'Keeps a small light burning for the satisfying work of figuring something out.',
    invitation: {
      title: 'A small pool of focus',
      body: 'You could choose one manageable part of a study, creative or practical task and give it a quiet stretch of attention.',
    },
  },
} as const satisfies Record<VisitorId, Personality>;

const battleNotes = {
  REST: 'Stronger against FOCUS, weaker against ROAM. REST has no damaging habit cards for a +3 power bonus. HP is the same for all companions at the same level.',
  ROAM: 'Adds 3 power to Short Walk and Morning Walk. Stronger against REST, weaker against FOCUS. HP is the same for all companions at the same level.',
  FOCUS:
    'Adds 3 power to Stretch and Read a Chapter. Stronger against ROAM, weaker against REST. HP is the same for all companions at the same level.',
} as const satisfies Record<CompanionHabit, string>;

// Profiles are views of the account, never a replacement for its starter or
// shared progress. Explicit null previews the starter; undefined uses selection.
export function companionProfile(
  player: Player,
  id: VisitorId | null = effectiveGuardianId(player),
): CompanionProfile {
  const selected =
    id !== null && befriendedVisitorIds(player).includes(id) ? visitorInfo(id) : null;
  const species = selected?.species ?? player.species;
  const habit = grasslings[species].habit;
  const personality = selected ? visitorPersonalities[selected.id] : starterPersonalities[species];
  return {
    id: selected?.id ?? null,
    name: selected?.name ?? player.pet_name,
    species,
    habit,
    ...personality,
    battleNote: battleNotes[habit],
  };
}

export function companionOptions(player: Player): CompanionProfile[] {
  return [
    companionProfile(player, null),
    ...befriendedVisitorIds(player).map((id) => companionProfile(player, id)),
  ];
}
