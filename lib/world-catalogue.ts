import type { WorldId } from './world-maps';
import type { VisitorId } from './visitors';

/** Presentation belongs to a place ID, never its position in the mission list. */
export const worldCatalogue: Record<
  WorldId,
  {
    description: string;
    postcardTitle: string;
    resident: VisitorId;
    /** Existing map object whose complete silhouette anchors mission previews. */
    previewLandmark: string;
  }
> = {
  park: {
    description: 'Pond paths, curious neighbours and a little room to wander.',
    postcardTitle: 'PARK',
    resident: 'trailhop',
    previewLandmark: 'fountain',
  },
  book: {
    description: 'A library lane where your companion can linger over a story.',
    postcardTitle: 'LIBRARY',
    resident: 'pagemoth',
    previewLandmark: 'library',
  },
  mountain: {
    description: 'A quiet ridge above the garden, with a cabin to return to.',
    postcardTitle: 'MOUNTAIN',
    resident: 'lullapine',
    previewLandmark: 'cabin',
  },
};
