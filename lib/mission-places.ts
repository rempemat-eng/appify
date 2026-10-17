import type { missions } from './game';
import { worldCatalogue } from './world-catalogue';

export type MissionRule = Readonly<(typeof missions)[number]>;
export type MissionWorldId = keyof typeof worldCatalogue;
export type MissionPlaceId = MissionWorldId | 'garden' | 'arena' | 'shop';

type PlaceConnections = {
  readonly neighbours: readonly MissionPlaceId[];
};

export type MissionWorldPlace = PlaceConnections & {
  readonly id: MissionWorldId;
  readonly opens: {
    readonly kind: 'select-mission';
    readonly path: '/missions';
    readonly missionId: MissionWorldId;
  };
  readonly locked: boolean;
  readonly mission: MissionRule;
  readonly world: Readonly<(typeof worldCatalogue)[MissionWorldId]>;
};

export type MissionRoutePlace = PlaceConnections & {
  readonly id: 'garden' | 'arena' | 'shop';
  readonly opens: {
    readonly kind: 'route';
    readonly path: '/' | '/arena' | '/shop';
  };
  readonly locked: false;
};

export type MissionPlace = MissionWorldPlace | MissionRoutePlace;
export type MissionPlaces = Readonly<
  Record<MissionWorldId, MissionWorldPlace> & Record<'garden' | 'arena' | 'shop', MissionRoutePlace>
>;

/** Direct buttons remain available alongside the map's walkable destinations. */
export const missionPlaceShortcuts = ['arena', 'shop'] as const satisfies readonly MissionPlaceId[];

/**
 * Pass the existing `missions` and player level; this module never loads the
 * store, starts a break or navigates. Selecting a mission still needs the
 * existing explicit departure action and its live-state checks.
 *
 * `locked` describes the existing mission level gate, not permission to spend,
 * fight or start a break. Those actions keep their own existing store guards.
 * Layout, art and travel animation belong to the renderer.
 */
export function getMissionPlaces(
  missionRules: readonly MissionRule[],
  level: number,
): MissionPlaces {
  for (const rule of missionRules) {
    if (!Object.hasOwn(worldCatalogue, rule.id))
      throw new Error(`Mission ${rule.id} needs a world catalogue entry.`);
  }
  const worldPlace = (id: MissionWorldId): MissionWorldPlace => {
    const matches = missionRules.filter((mission) => mission.id === id);
    if (matches.length !== 1)
      throw new Error(`Place ${id} needs exactly one mission rule; found ${matches.length}.`);
    const mission = matches[0];
    return {
      id,
      neighbours: ['garden'],
      opens: { kind: 'select-mission', path: '/missions', missionId: id },
      locked: level < mission.level,
      mission,
      world: worldCatalogue[id],
    };
  };
  const worlds = {
    park: worldPlace('park'),
    book: worldPlace('book'),
    mountain: worldPlace('mountain'),
  } satisfies Record<MissionWorldId, MissionWorldPlace>;

  // All existing destinations are independent outings from the garden. The
  // graph adds no sequential unlocks, shortcuts through locked worlds or costs.
  return {
    garden: {
      id: 'garden',
      neighbours: [...Object.values(worlds).map((place) => place.id), ...missionPlaceShortcuts],
      opens: { kind: 'route', path: '/' },
      locked: false,
    },
    ...worlds,
    arena: {
      id: 'arena',
      neighbours: ['garden'],
      opens: { kind: 'route', path: '/arena' },
      locked: false,
    },
    shop: {
      id: 'shop',
      neighbours: ['garden'],
      opens: { kind: 'route', path: '/shop' },
      locked: false,
    },
  };
}
