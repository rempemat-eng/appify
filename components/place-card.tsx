import { View } from 'react-native';
import { PixelButton } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { missions, type Player } from '@/lib/game';
import { residentLines } from '@/lib/resident-routes';
import { worldCatalogue } from '@/lib/world-catalogue';
import { stopIds, travelBy, travelRoute, type StopId } from '@/lib/world-places';
import type { Card } from '@/lib/world-cards';

/** Each stop's name on the travel card and the journey's label. */
export const stopNames: Record<StopId, string> = {
  valley: 'THE VALLEY',
  steam: 'COGSWORTH',
  west: 'DUST GULCH',
  lava: 'EMBER CALDERA',
  pier: 'DRIFTWOOD',
  isles: 'TIDEBLOOM ISLES',
  neon: 'NEON HARBOUR',
  space: 'HALCYON STATION',
  moon: 'LUMEN',
};
const stopShort: Record<StopId, string> = {
  valley: 'the valley',
  steam: 'Cogsworth',
  west: 'Dust Gulch',
  lava: 'the caldera',
  pier: 'Driftwood',
  isles: 'the isles',
  neon: 'Neon Harbour',
  space: 'Halcyon',
  moon: 'Lumen',
};

/** What a place's card can do; a card only offers what its place has. */
export type PlaceActions = {
  /** set out on a mission from its place (the store decides whether it may start) */
  startMission: (id: string) => void;
  /** open Moss's stall or the ring (a ring out in the regions has its own backdrop) */
  openShop: () => void;
  openArena: (backdrop?: string) => void;
  /** set off from a station; `route` is the stops on the way, the destination last */
  travel: (here: StopId, route: StopId[]) => void;
  goHome: () => void;
  goInside: () => void;
  stepOutside: () => void;
  decorate: () => void;
};

const title = { fontSize: 16, fontFamily: 'PixelifySans_700Bold' } as const;

/**
 * The body of a place's card out in the world (the world screen and the home hub share
 * it): what the place is and its one action. The actions are the same everywhere; the
 * card itself grants nothing.
 */
export function PlaceCardBody({
  card,
  player,
  away,
  appActive,
  travelling = false,
  found = 0,
  keepsakeCount = 0,
  act,
}: {
  card: Card;
  player: Player;
  /** the companion is away, resting or in a battle: missions and journeys wait */
  away: boolean;
  appActive: boolean;
  travelling?: boolean;
  found?: number;
  keepsakeCount?: number;
  act: PlaceActions;
}) {
  if (card.kind === 'chest')
    return (
      <>
        <BodyText style={title}>THE KEEPSAKE CHEST</BodyText>
        <BodyText style={{ fontSize: 13 }}>
          {found} of {keepsakeCount} keepsakes found. Every place you walk leaves one; set them out
          anywhere in the hut, and move them whenever you like.
        </BodyText>
        <PixelButton small label="DECORATE" onPress={act.decorate} />
      </>
    );
  if (card.kind === 'mission') {
    const mission = missions.find((m) => m.id === card.id);
    if (!mission) return null;
    const locked = player.level < mission.level;
    return (
      <>
        <BodyText style={title}>{mission.name}</BodyText>
        <BodyText style={{ fontSize: 13 }}>{worldCatalogue[card.id].description}</BodyText>
        <BodyText style={{ fontSize: 13 }}>
          {mission.duration} MIN · {mission.reward} Dream Dust ·{' '}
          {mission.id === 'mountain' ? 'EPIC' : 'RARE'} card · postcard
        </BodyText>
        <PixelButton
          small
          label={locked ? `LEVEL ${mission.level} NEEDED` : `START ${mission.name}`}
          disabled={locked || away || !appActive}
          onPress={() => act.startMission(mission.id)}
        />
      </>
    );
  }
  if (card.kind === 'shop' || card.kind === 'arena') {
    const shop = card.kind === 'shop';
    return (
      <>
        <BodyText style={title}>{shop ? "MOSS'S STALL" : 'SPARRING RING'}</BodyText>
        <BodyText style={{ fontSize: 13 }}>
          {shop
            ? 'Moss keeps the stall at the crossroads, with everything to grow your garden.'
            : 'A trodden ring by the square. Spar with Doomscroll Dave and get ready for raids.'}
        </BodyText>
        <PixelButton
          small
          label={shop ? "VISIT MOSS'S STALL" : 'TO THE RING'}
          onPress={() => (shop ? act.openShop() : act.openArena())}
        />
      </>
    );
  }
  if (card.kind === 'ring')
    return (
      <>
        <BodyText style={title}>SPARRING RING</BodyText>
        <BodyText style={{ fontSize: 13 }}>
          The same friendly ring as in town: spar with Doomscroll Dave or get ready for raids.
        </BodyText>
        <PixelButton small label="TO THE RING" onPress={() => act.openArena(card.backdrop)} />
      </>
    );
  if (card.kind === 'chat')
    return (
      <>
        <BodyText style={title}>{card.who.toUpperCase()}</BodyText>
        <BodyText style={{ fontSize: 14 }}>“{residentLines[card.who] ?? 'hello there.'}”</BodyText>
      </>
    );
  if (card.kind === 'garden')
    return (
      <>
        <BodyText style={title}>HOME GARDEN</BodyText>
        <BodyText style={{ fontSize: 13 }}>The meadow, the pond and your companion’s bed.</BodyText>
        <PixelButton small label="BACK TO THE GARDEN" onPress={act.goHome} />
      </>
    );
  if (card.kind === 'hut')
    return (
      <>
        <BodyText style={title}>THE NAP HUT</BodyText>
        <PixelButton small label="GO INSIDE" onPress={act.goInside} />
      </>
    );
  if (card.kind === 'inside')
    return (
      <>
        <BodyText style={title}>THE FRONT DOOR</BodyText>
        <PixelButton small label="STEP OUTSIDE" onPress={act.stepOutside} />
      </>
    );
  // a station: the lines leave from here; further places change on the way
  if (card.kind !== 'travel') return null;
  const here = card.stop;
  const routes = stopIds
    .filter((r) => r !== here)
    .map((r) => ({ r, route: travelRoute(here, r) }))
    .filter((x) => x.route.length > 0)
    .sort((a, b) => a.route.length - b.route.length);
  const direct = routes.filter((x) => x.route.length === 1);
  const further = routes.filter((x) => x.route.length > 1);
  return (
    <>
      <BodyText style={title}>{travelBy[here]}</BodyText>
      <BodyText style={{ fontSize: 13 }}>Where to? The journey is free; skip it any time.</BodyText>
      {[direct, further].map((group, g) =>
        group.length ? (
          <View key={g === 0 ? 'direct' : 'further'} style={{ gap: 4 }}>
            {g === 1 && <BodyText style={{ fontSize: 12 }}>Further, changing on the way:</BodyText>}
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
              {group.map(({ r, route }) => (
                <View key={r} style={{ width: '48%', gap: 2 }}>
                  <PixelButton
                    small
                    light
                    label={stopNames[r]}
                    disabled={away || travelling}
                    onPress={() => act.travel(here, route)}
                  />
                  {route.length > 1 && (
                    <BodyText numberOfLines={1} style={{ fontSize: 11, lineHeight: 13 }}>
                      {route.length === 2
                        ? `via ${stopShort[route[0]]}`
                        : `via ${stopShort[route[0]]} · ${route.length - 1} changes`}
                    </BodyText>
                  )}
                </View>
              ))}
            </View>
          </View>
        ) : null,
      )}
    </>
  );
}
