import type { WorldId } from './world-maps';
import type { VisitorId } from './visitors';

/** Presentation belongs to a place ID, never its position in the mission list. */
export const worldCatalogue: Record<
  WorldId,
  {
    description: string;
    postcardTitle: string;
    resident: VisitorId;
  }
> = {
  park: {
    description: 'Pond paths, curious neighbours and a little room to wander.',
    postcardTitle: 'PARK',
    resident: 'trailhop',
  },
  book: {
    description: 'A library lane where your companion can linger over a story.',
    postcardTitle: 'LIBRARY',
    resident: 'pagemoth',
  },
  mountain: {
    description: 'A quiet ridge above the garden, with a cabin to return to.',
    postcardTitle: 'MOUNTAIN',
    resident: 'lullapine',
  },
};
